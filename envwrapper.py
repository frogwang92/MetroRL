from __future__ import annotations

import importlib.util

from typing import Dict, List, Optional, Union

import torch
from tensordict import LazyStackedTensorDict, TensorDict, TensorDictBase

from torchrl.data.tensor_specs import (
    Bounded,
    Categorical,
    Composite,
    DEVICE_TYPING,
    MultiCategorical,
    MultiOneHot,
    OneHot,
    StackedComposite,
    TensorSpec,
    Unbounded,
)
from torchrl.data.utils import numpy_to_torch_dtype_dict
from torchrl.envs.common import _EnvWrapper, EnvBase
from torchrl.envs.libs.gym import gym_backend, set_gym_backend
from torchrl.envs.utils import (
    _classproperty,
    _selective_unsqueeze,
    check_marl_grouping,
    MarlGroupMapType,
)

from metro_environment import MetroEnv
from metro_scenario_v1 import MetroScenarioV1


@set_gym_backend("gym")
def _vmas_to_torchrl_spec_transform(
    spec,
    device,
    categorical_action_encoding,
) -> TensorSpec:
    gym_spaces = gym_backend("spaces")
    if isinstance(spec, gym_spaces.discrete.Discrete):
        action_space_cls = Categorical if categorical_action_encoding else OneHot
        dtype = (
            numpy_to_torch_dtype_dict[spec.dtype]
            if categorical_action_encoding
            else torch.long
        )
        return action_space_cls(spec.n, device=device, dtype=dtype)
    elif isinstance(spec, gym_spaces.multi_discrete.MultiDiscrete):
        dtype = (
            numpy_to_torch_dtype_dict[spec.dtype]
            if categorical_action_encoding
            else torch.long
        )
        return (
            MultiCategorical(spec.nvec, device=device, dtype=dtype)
            if categorical_action_encoding
            else MultiOneHot(spec.nvec, device=device, dtype=dtype)
        )
    elif isinstance(spec, gym_spaces.Box):
        shape = spec.shape
        if not len(shape):
            shape = torch.Size([1])
        dtype = numpy_to_torch_dtype_dict[spec.dtype]
        low = torch.tensor(spec.low, device=device, dtype=dtype)
        high = torch.tensor(spec.high, device=device, dtype=dtype)
        is_unbounded = low.isinf().all() and high.isinf().all()
        return (
            Unbounded(shape, device=device, dtype=dtype)
            if is_unbounded
            else Bounded(
                low,
                high,
                shape,
                dtype=dtype,
                device=device,
            )
        )
    elif isinstance(spec, gym_spaces.Dict):
        spec_out = {}
        for key in spec.keys():
            spec_out[key] = _vmas_to_torchrl_spec_transform(
                spec[key],
                device=device,
                categorical_action_encoding=categorical_action_encoding,
            )
        # the batch-size must be set later
        return Composite(spec_out, device=device)
    else:
        raise NotImplementedError(
            f"spec of type {type(spec).__name__} is currently unaccounted for vmas"
        )


class EnvWrapper(_EnvWrapper):
    def __init__(
        self,
        num_envs: int,
        max_steps: int,
        n_agents: int,
        env: MetroEnv = None,
        group_map: MarlGroupMapType | Dict[str, List[str]] | None = None,
        **kwargs,
    ):
        if env is not None:
            kwargs["env"] = env
            if "device" in kwargs.keys() and kwargs["device"] != str(env.device):
                raise TypeError("Env device is different from vmas device")
            kwargs["device"] = str(env.device)
        self.group_map = group_map
        super().__init__(
            num_envs=num_envs,
            max_steps=max_steps,
            n_agents=n_agents,
            **kwargs, allow_done_after_reset=True)

    def _build_env(
        self,
        env: MetroEnv = None,
        **kwargs,
    ):
        # Adjust batch size
        if len(self.batch_size) == 0:
            # Batch size not set
            self.batch_size = torch.Size((env.num_envs,))
        elif len(self.batch_size) == 1:
            # Batch size is set
            if not self.batch_size[0] == env.num_envs:
                raise TypeError(
                    "Batch size used in constructor does not match vmas batch size."
                )
        else:
            raise TypeError(
                "Batch size used in constructor is not compatible with vmas."
            )

        return env

    def _get_default_group_map(self, agent_names: List[str]):
        # This function performs the default grouping in vmas.
        # Agents with names "<name>_<int>" will be grouped in group name "<name>".
        # If any of the agents does not follow the naming convention, we fall back
        # back on having all agents in one group named "agents".
        group_map = {}
        follows_convention = True
        for agent_name in agent_names:
            # See if the agent follows the convention "<name>_<int>"
            agent_name_split = agent_name.split("_")
            if len(agent_name_split) == 1:
                follows_convention = False
            follows_convention = follows_convention and agent_name_split[-1].isdigit()

            if not follows_convention:
                break

            # Group it with other agents that follow the same convention
            group_name = "_".join(agent_name_split[:-1])
            if group_name in group_map:
                group_map[group_name].append(agent_name)
            else:
                group_map[group_name] = [agent_name]

        if not follows_convention:
            group_map = MarlGroupMapType.ALL_IN_ONE_GROUP.get_group_map(agent_names)

        # For BC-compatibility rename the "agent" group to "agents"
        if "agent" in group_map and len(group_map) == 1:
            agent_group = group_map["agent"]
            group_map["agents"] = agent_group
            del group_map["agent"]
        return group_map

    def _make_specs(
        self, env: MetroEnv  # noqa
    ) -> None:
        # Create and check group map
        self.agent_names = [agent.name for agent in self.agents]
        self.agent_names_to_indices_map = {
            agent.name: i for i, agent in enumerate(self.agents)
        }
        if self.group_map is None:
            self.group_map = self._get_default_group_map(self.agent_names)
        elif isinstance(self.group_map, MarlGroupMapType):
            self.group_map = self.group_map.get_group_map(self.agent_names)
        check_marl_grouping(self.group_map, self.agent_names)

        self.unbatched_action_spec = Composite(device=self.device)
        self.unbatched_observation_spec = Composite(device=self.device)
        self.unbatched_reward_spec = Composite(device=self.device)

        self.het_specs = False
        self.het_specs_map = {}
        for group in self.group_map.keys():
            (
                group_observation_spec,
                group_action_spec,
                group_reward_spec,
                group_info_spec,
            ) = self._make_unbatched_group_specs(group)
            self.unbatched_action_spec[group] = group_action_spec
            self.unbatched_observation_spec[group] = group_observation_spec
            self.unbatched_reward_spec[group] = group_reward_spec
            if group_info_spec is not None:
                self.unbatched_observation_spec[(group, "info")] = group_info_spec
            group_het_specs = isinstance(
                group_observation_spec, StackedComposite
            ) or isinstance(group_action_spec, StackedComposite)
            self.het_specs_map[group] = group_het_specs
            self.het_specs = self.het_specs or group_het_specs

        self.unbatched_done_spec = Composite(
            {
                "done": Categorical(
                    n=2,
                    shape=torch.Size((1,)),
                    dtype=torch.bool,
                    device=self.device,
                ),
            },
        )

        self.action_spec = self.unbatched_action_spec.expand(
            *self.batch_size, *self.unbatched_action_spec.shape
        )
        self.observation_spec = self.unbatched_observation_spec.expand(
            *self.batch_size, *self.unbatched_observation_spec.shape
        )
        self.reward_spec = self.unbatched_reward_spec.expand(
            *self.batch_size, *self.unbatched_reward_spec.shape
        )
        self.done_spec = self.unbatched_done_spec.expand(
            *self.batch_size, *self.unbatched_done_spec.shape
        )

    def _make_unbatched_group_specs(self, group: str):
        # Agent specs
        action_specs = []
        observation_specs = []
        reward_specs = []
        info_specs = []
        for agent_name in self.group_map[group]:
            agent_index = self.agent_names_to_indices_map[agent_name]
            agent = self.agents[agent_index]
            action_specs.append(
                Composite(
                    {
                        "action": _vmas_to_torchrl_spec_transform(
                            self.action_space[agent_name],
                            categorical_action_encoding=True,
                            device=self.device,
                        )  # shape = (n_actions_per_agent,)
                    },
                )
            )
            observation_specs.append(
                Composite(
                    {
                        "observation": _vmas_to_torchrl_spec_transform(
                            self.observation_space[agent_name],
                            device=self.device,
                            categorical_action_encoding=True,
                        )  # shape = (n_obs_per_agent,)
                    },
                )
            )
            reward_specs.append(
                Composite(
                    {
                        "reward": Unbounded(
                            shape=torch.Size((1,)),
                            device=self.device,
                        )  # shape = (1,)
                    }
                )
            )
            agent_info = self.scenario.info(agent)
            if len(agent_info):
                info_specs.append(
                    Composite(
                        {
                            key: Unbounded(
                                shape=_selective_unsqueeze(
                                    value, batch_size=self.batch_size
                                ).shape[1:],
                                device=self.device,
                                dtype=torch.float32,
                            )
                            for key, value in agent_info.items()
                        },
                    ).to(self.device)
                )

        # Create multi-agent specs
        group_action_spec = torch.stack(
            action_specs, dim=0
        )  # shape = (n_agents, n_actions_per_agent)
        group_observation_spec = torch.stack(
            observation_specs, dim=0
        )  # shape = (n_agents, n_obs_per_agent)
        group_reward_spec = torch.stack(reward_specs, dim=0)  # shape = (n_agents, 1)
        group_info_spec = None
        if len(info_specs):
            group_info_spec = torch.stack(info_specs, dim=0)

        return (
            group_observation_spec,
            group_action_spec,
            group_reward_spec,
            group_info_spec,
        )

    def _check_kwargs(self, kwargs: Dict):
        pass

    def _init_env(self) -> Optional[int]:
        pass

    def _set_seed(self, seed: Optional[int]):
        self._env.seed(seed)

    def _reset(
        self, tensordict: Optional[TensorDictBase] = None, **kwargs
    ) -> TensorDictBase:
        if tensordict is not None and "_reset" in tensordict.keys():
            _reset = tensordict.get("_reset")
            envs_to_reset = _reset.squeeze(-1)
            if envs_to_reset.all():
                self._env.reset(return_observations=False)
            else:
                for env_index, to_reset in enumerate(envs_to_reset):
                    if to_reset:
                        self._env.reset_at(env_index, return_observations=False)
        else:
            self._env.reset(return_observations=False)

        obs, dones, infos = self._env.get_from_scenario(
            get_observations=True,
            get_infos=True,
            get_rewards=False,
            get_dones=True,
        )
        dones = self.read_done(dones)

        source = {"done": dones, "terminated": dones.clone()}
        for group, agent_names in self.group_map.items():
            agent_tds = []
            for agent_name in agent_names:
                agent_obs = self.read_obs(obs[agent_name])
                agent_info = self.read_info(infos[agent_name])
                agent_td = TensorDict(
                    source={
                        "observation": agent_obs,
                    },
                    batch_size=self.batch_size,
                    device=self.device,
                )
                if agent_info is not None:
                    agent_td.set("info", agent_info)
                agent_tds.append(agent_td)

            agent_tds = LazyStackedTensorDict.maybe_dense_stack(agent_tds, dim=1)
            if not self.het_specs_map[group]:
                agent_tds = agent_tds.to_tensordict()
            source.update({group: agent_tds})

        tensordict_out = TensorDict(
            source=source,
            batch_size=self.batch_size,
            device=self.device,
        )
        return tensordict_out

    def _step(
        self,
        tensordict: TensorDictBase,
    ) -> TensorDictBase:
        agent_indices = {}
        action_list = []
        n_agents = 0
        # print(tensordict)
        for group, agent_names in self.group_map.items():
            group_action = tensordict.get((group, "action"))
            group_action_list = list(self.read_action(group_action, group=group))
            agent_indices.update(
                {
                    self.agent_names_to_indices_map[agent_name]: i + n_agents
                    for i, agent_name in enumerate(agent_names)
                }
            )
            n_agents += len(agent_names)
            action_list += group_action_list
        action = [action_list[agent_indices[i]] for i in range(self.n_agents)]

        obs, rews, dones, infos = self._env.step(action)

        dones = self.read_done(dones)

        source = {"done": dones, "terminated": dones.clone()}
        for group, agent_names in self.group_map.items():
            agent_tds = []
            for agent_name in agent_names:
                agent_obs = self.read_obs(obs[agent_name])
                agent_rew = self.read_reward(rews[agent_name])
                agent_info = self.read_info(infos[agent_name])

                agent_td = TensorDict(
                    source={
                        "observation": agent_obs,
                        "reward": agent_rew,
                    },
                    batch_size=self.batch_size,
                    device=self.device,
                )
                if agent_info is not None:
                    agent_td.set("info", agent_info)
                agent_tds.append(agent_td)

            agent_tds = LazyStackedTensorDict.maybe_dense_stack(agent_tds, dim=1)
            if not self.het_specs_map[group]:
                agent_tds = agent_tds.to_tensordict()
            source.update({group: agent_tds})

        tensordict_out = TensorDict(
            source=source,
            batch_size=self.batch_size,
            device=self.device,
        )
        return tensordict_out

    def read_obs(
        self, observations: Union[Dict, torch.Tensor]
    ) -> Union[Dict, torch.Tensor]:
        if isinstance(observations, torch.Tensor):
            return _selective_unsqueeze(observations, batch_size=self.batch_size)
        return TensorDict(
            source={key: self.read_obs(value) for key, value in observations.items()},
            batch_size=self.batch_size,
        )

    def read_info(self, infos: Dict[str, torch.Tensor]) -> torch.Tensor:
        if len(infos) == 0:
            return None
        infos = TensorDict(
            source={
                key: _selective_unsqueeze(
                    value.to(torch.float32), batch_size=self.batch_size
                )
                for key, value in infos.items()
            },
            batch_size=self.batch_size,
            device=self.device,
        )

        return infos

    def read_done(self, done):
        done = _selective_unsqueeze(done, batch_size=self.batch_size)
        return done

    def read_reward(self, rewards):
        rewards = _selective_unsqueeze(rewards, batch_size=self.batch_size)
        return rewards

    def read_action(self, action, group: str = "agents"):
        agent_actions = action.unbind(dim=1)
        return agent_actions

    def __repr__(self) -> str:
        return (
            f"{self.__class__.__name__}(num_envs={self.num_envs}, n_agents={self.n_agents},"
            f" batch_size={self.batch_size}, device={self.device})"
        )

    def to(self, device: DEVICE_TYPING) -> EnvBase:
        self._env.to(device)
        return super().to(device)


class MetroRLEnv(EnvWrapper):
    def __init__(
        self,
        *,
        num_envs: int,
        max_steps: Optional[int] = None,
        seed: Optional[int] = None,
        group_map: MarlGroupMapType | Dict[str, List[str]] | None = None,
        **kwargs,
    ):
        super().__init__(
            num_envs=num_envs,
            max_steps=max_steps,
            seed=seed,
            group_map=group_map,
            **kwargs,
        )

    def _check_kwargs(self, kwargs: Dict):
        if "num_envs" not in kwargs:
            raise TypeError("Could not find environment key 'num_envs' in kwargs.")

    def _build_env(
        self,
        num_envs: int,
        max_steps: Optional[int],
        seed: Optional[int],
        **scenario_kwargs,
    ) -> MetroEnv:

        # build metro scenario here
        self.scenario = MetroScenarioV1(**scenario_kwargs)

        return super()._build_env(
            env=MetroEnv(
                scenario=self.scenario,
                num_envs=num_envs,
                max_steps=max_steps,
                seed=seed,
            )
        )

    def __repr__(self):
        return f"{super().__repr__()} (scenario={self.scenario_name})"
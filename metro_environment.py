"""
Environment module for managing the metro system simulation as a TorchRL environment.
"""

import math
import random
from ctypes import byref
from typing import Callable, Dict, List, Optional, Sequence, Tuple, Union

import numpy as np
import torch

from gym import spaces
from torch import Tensor

from metro_scenario_v1 import MetroScenarioV1
from torchutils import TorchUtils, override

from metro_agent_v1 import MetroAgentV1

DEVICE_TYPING = Union[torch.device, str, int]

class TorchVectorizedObject(object):
    def __init__(self, batch_dim: int = None, device: torch.device = None):
        # batch dim
        self._batch_dim = batch_dim
        # device
        self._device = device

    @property
    def batch_dim(self):
        return self._batch_dim

    @batch_dim.setter
    def batch_dim(self, batch_dim: int):
        assert self._batch_dim is None, "You can set batch dim only once"
        self._batch_dim = batch_dim

    @property
    def device(self):
        return self._device

    @device.setter
    def device(self, device: torch.device):
        self._device = device

    def _check_batch_index(self, batch_index: int):
        if batch_index is not None:
            assert (
                0 <= batch_index < self.batch_dim
            ), f"Index must be between 0 and {self.batch_dim}, got {batch_index}"

    def to(self, device: torch.device):
        self.device = device
        for attr, value in self.__dict__.items():
            if isinstance(value, Tensor):
                self.__dict__[attr] = value.to(device)


class MetroEnv(TorchVectorizedObject):
    def __init__(
        self,
        scenario: MetroScenarioV1,
        num_envs: int = 32,
        device = "cpu",
        max_steps: Optional[int] = None,
        seed: Optional[int] = None,
        grad_enabled: bool = False,
        terminated_truncated: bool = False,
        **kwargs,
    ):
        self.num_envs = num_envs
        TorchVectorizedObject.__init__(self, num_envs, torch.device(device))
        self.scenario = scenario
        self.world = self.scenario.env_make_world(self.num_envs, self.device, **kwargs)

        self.agents = self.world.agents
        self.n_agents = len(self.agents)
        self.max_steps = max_steps
        self.grad_enabled = grad_enabled
        self.terminated_truncated = terminated_truncated

        observations = self.reset(seed=seed)

        # configure spaces
        self.action_space = self.get_action_space()
        self.observation_space = self.get_observation_space(observations)

        # rendering
        self.viewer = None
        self.headless = None
        self.visible_display = None
        self.text_lines = None

    def reset(
        self,
        seed: Optional[int] = None,
        return_observations: bool = True,
        return_info: bool = False,
        return_dones: bool = False,
    ):
        """
        Resets the environment in a vectorized way
        Returns observations for all envs and agents
        """
        if seed is not None:
            self.seed(seed)
        # reset world
        self.scenario.env_reset_world_at(env_index=None)
        self.steps = torch.zeros(self.num_envs, device=self.device)

        result = self.get_from_scenario(
            get_observations=return_observations,
            get_infos=return_info,
            get_rewards=False,
            get_dones=return_dones,
        )
        return result[0] if result and len(result) == 1 else result

    def reset_at(
        self,
        index: int,
        return_observations: bool = True,
        return_info: bool = False,
        return_dones: bool = False,
    ):
        """
        Resets the environment at index
        Returns observations for all agents in that environment
        """
        self._check_batch_index(index)
        self.scenario.env_reset_world_at(index)
        self.steps[index] = 0

        result = self.get_from_scenario(
            get_observations=return_observations,
            get_infos=return_info,
            get_rewards=False,
            get_dones=return_dones,
        )

        return result[0] if result and len(result) == 1 else result
    
    def get_from_scenario(
        self,
        get_observations: bool,
        get_rewards: bool,
        get_infos: bool,
        get_dones: bool,
        dict_agent_names: Optional[bool] = True,
    ):
        if not get_infos and not get_dones and not get_rewards and not get_observations:
            return

        obs = rewards = infos = terminated = truncated = dones = None

        if get_observations:
            obs = {} if dict_agent_names else []
        if get_rewards:
            rewards = {} if dict_agent_names else []
        if get_infos:
            infos = {} if dict_agent_names else []

        if get_rewards:
            for agent in self.agents:
                reward = self.scenario.reward(agent).clone()
                if dict_agent_names:
                    rewards.update({agent.name: reward})
                else:
                    rewards.append(reward)
        if get_observations:
            for agent in self.agents:
                observation = TorchUtils.recursive_clone(
                    self.scenario.observation(agent)
                )
                if dict_agent_names:
                    obs.update({agent.name: observation})
                else:
                    obs.append(observation)
        if get_infos:
            for agent in self.agents:
                info = TorchUtils.recursive_clone(self.scenario.info(agent))
                if dict_agent_names:
                    infos.update({agent.name: info})
                else:
                    infos.append(info)

        if self.terminated_truncated:
            if get_dones:
                terminated, truncated = self.done()
            result = [obs, rewards, terminated, truncated, infos]
        else:
            if get_dones:
                dones = self.done()
            result = [obs, rewards, dones, infos]

        return [data for data in result if data is not None]
    
    def seed(self, seed=None):
        if seed is None:
            seed = 42
        torch.manual_seed(seed)
        np.random.seed(seed)
        random.seed(seed)
        return [seed]
    
    def step(self, actions: Union[List, Dict]):
        """Performs a vectorized step on all sub environments using `actions`.
        Args:
            actions: Is a list on len 'self.n_agents' of which each element is a torch.Tensor of shape
            '(self.num_envs, action_size_of_agent)'.
        Returns:
            obs: List on len 'self.n_agents' of which each element is a torch.Tensor
                 of shape '(self.num_envs, obs_size_of_agent)'
            rewards: List on len 'self.n_agents' of which each element is a torch.Tensor of shape '(self.num_envs)'
            dones: Tensor of len 'self.num_envs' of which each element is a bool
            infos : List on len 'self.n_agents' of which each element is a dictionary for which each key is a metric
                    and the value is a tensor of shape '(self.num_envs, metric_size_per_agent)'
        """
        if isinstance(actions, Dict):
            actions_dict = actions
            actions = []
            for agent in self.agents:
                try:
                    actions.append(actions_dict[agent.name])
                except KeyError:
                    raise AssertionError(
                        f"Agent '{agent.name}' not contained in action dict"
                    )
            assert (
                len(actions_dict) == self.n_agents
            ), f"Expecting actions for {self.n_agents}, got {len(actions_dict)} actions"

        assert (
            len(actions) == self.n_agents
        ), f"Expecting actions for {self.n_agents}, got {len(actions)} actions"
        for i in range(len(actions)):
            if not isinstance(actions[i], Tensor):
                actions[i] = torch.tensor(
                    actions[i], dtype=torch.float32, device=self.device
                )
            if len(actions[i].shape) == 1:
                actions[i].unsqueeze_(-1)
            assert (
                actions[i].shape[0] == self.num_envs
            ), f"Actions used in input of env must be of len {self.num_envs}, got {actions[i].shape[0]}"
            assert actions[i].shape[1] == self.get_agent_action_size(self.agents[i]), (
                f"Action for agent {self.agents[i].name} has shape {actions[i].shape[1]},"
                f" but should have shape {self.get_agent_action_size(self.agents[i])}"
            )

        # set action for each agent
        for i, agent in enumerate(self.agents):
            self._set_action(actions[i], agent)
        # Scenarios can define a custom action processor. This step takes care also of scripted agents automatically
        for agent in self.world.agents:
            self.scenario.env_process_action(agent)

        # advance world state
        self.scenario.pre_step()
        self.world.step()
        self.scenario.post_step()

        self.steps += 1

        return self.get_from_scenario(
            get_observations=True,
            get_infos=True,
            get_rewards=True,
            get_dones=True,
        )
    
    def done(self):
        terminated = self.scenario.done().clone()

        if self.max_steps is not None:
            truncated = self.steps >= self.max_steps
        else:
            truncated = None

        if self.terminated_truncated:
            if truncated is None:
                truncated = torch.zeros_like(terminated)
            return terminated, truncated
        else:
            if truncated is None:
                return terminated
            return terminated + truncated
        
    def get_action_space(self):
        return spaces.Dict(
            {
                agent.name: self.get_agent_action_space(agent)
                for agent in self.agents
            }
        )

    def get_observation_space(self, observations: Union[List, Dict]):
        return spaces.Dict(
            {
                agent.name: self.get_agent_observation_space(
                    agent, observations[agent.name]
                )
                for agent in self.agents
            }
        )

    def get_agent_action_size(self, agent: MetroAgentV1):
        return 1

    def get_agent_action_space(self, agent: MetroAgentV1):
        return spaces.Discrete(2)

    def get_agent_observation_space(self, agent: MetroAgentV1, obs):
        if isinstance(obs, Tensor):
            return spaces.Box(
                low=0,
                high=10000,
                shape=obs.shape[1:],
                dtype=np.float32
            )
        elif isinstance(obs, Dict):
            return spaces.Dict(
                {
                    key: self.get_agent_observation_space(agent, value)
                    for key, value in obs.items()
                }
            )
        else:
            raise NotImplementedError(
                f"Invalid type of observation {obs} for agent {agent.name}"
            )

    def get_random_action(self, agent: MetroAgentV1) -> torch.Tensor:
        """Returns a random action for the given agent.

        Args:
            agent (Agent): The agent to get the action for

        Returns:
            torch.tensor: the random actions tensor with shape ``(agent.batch_dim, agent.action_size)``

        """
        action_space = self.get_agent_action_space(agent)
        action = torch.randint(
                    low=0,
                    high=action_space.n,
                    size=(1,),
                    device=agent.device,
                )
        
        return action

    def get_random_actions(self) -> Sequence[torch.Tensor]:
        """Returns random actions for all agents that you can feed to :class:`step`

        Returns:
            Sequence[torch.tensor]: the random actions for the agents
        """
        return [self.get_random_action(agent) for agent in self.agents]

    def _check_discrete_action(self, action: Tensor, low: int, high: int, type: str):
        assert torch.all(
            (action >= torch.tensor(low, device=self.device))
            * (action < torch.tensor(high, device=self.device))
        ), f"Discrete {type} actions are out of bounds, allowed int range [{low},{high})"

    # set env action for a particular agent
    def _set_action(self, action, agent):
        action = action.clone()
        if not self.grad_enabled:
            action = action.detach()
        action = action.to(self.device)
        assert not action.isnan().any()
        agent.action.u = torch.zeros(
            self.batch_dim,
            device=self.device
        )
        if action.shape[1] == 3:
            print(action)
        assert action.shape[1] == self.get_agent_action_size(agent), (
            f"Agent {agent.name} has wrong action size, got {action.shape[1]}, "
            f"expected {self.get_agent_action_size(agent)}"
        )
        
        agent.set_action(action)

    @override(TorchVectorizedObject)
    def to(self, device: DEVICE_TYPING):
        device = torch.device(device)
        super().to(device)
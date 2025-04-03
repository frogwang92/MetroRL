from typing import Dict
from networkx import bfs_tree
import torch
from metro_world import MetroWorldV1
from metro_agent_v1 import MetroAgentV1

class MetroScenarioV1:
    """Metro system scenario class, responsible for managing environment states and interaction rules"""
    
    def __init__(self, **kwargs):
        self.world = None
        self.n_agents = kwargs["n_agents"]
        self._init_scenario()

    def _init_scenario(self):
        # Initialize state trackers
        self.passenger_count = {}  # Waiting passengers at each station
        self.congestion = {}      # Congestion levels
        self.delays = {}          # Delay situations

    def env_make_world(self, num_envs: int, device: torch.device, **kwargs):
        """Create vectorized world states"""
        self.num_envs = num_envs
        self.device = device
        
        # Initialize world state
        self.world = MetroWorldV1(
            num_envs=self.num_envs,
            device=self.device,
            **kwargs
        )

        for i in range(self.n_agents):
            agent = MetroAgentV1(
                f"agent_{i}",
                num_envs,
                device
            )
            agent.world = self.world
            # agent.init_random_position(len(self.world.platfrom_nodes))
            self.world.agents.append(agent)
        self.env_reset_world_at()

        return self.world

    def env_reset_world_at(self, env_index=None):
        # init random weights
        self.world.init_random_weights()
        # Reset train positions
        for agent in self.world.agents:
            agent.reset_state(env_index)
            # agent.init_random_position(len(self.world.platfrom_nodes), env_index)

        import random
        if env_index is None:
            random_positions = []
            for env in range(self.num_envs):
                # random_positions.append(random.sample(list(self.world.platfrom_nodes.keys()), self.n_agents))
                random_positions.append(random.sample(list(self.world.nodes.keys()), self.n_agents))

            for i, agent in enumerate(self.world.agents):
                t = torch.zeros(self.num_envs, device=self.device)
                for env in range(self.num_envs):
                    t[env] = random_positions[env][i]
                agent.init_position(t)
        else:
            pass
            # random_positions = random.sample(list(self.world.platfrom_nodes.keys()), self.n_agents)
            # for i, agent in enumerate(self.world.agents):
            #     agent.state.position[env_index] = random_positions[i]

    def pre_step(self):
        potential_next_pos = torch.zeros(self.num_envs, device=self.device)
        for agent in self.world.agents:
            for env in range(self.num_envs):
                if agent.action[env].item() == 1:
                    current_pos = agent.state.position[env].item()
                    potential_next_pos[env] = self.world.get_next_nodes(current_pos)[0].id
                else:
                    potential_next_pos[env] = agent.state.position[env].item()
            agent.potential_step(potential_next_pos.clone())

    def post_step(self):
        pass

    def env_process_action(self, agent: MetroAgentV1):
        pass

    def observation(self, agent: MetroAgentV1) -> Dict[str, torch.Tensor]:
        """Generate agent observations"""
        state = torch.stack([
                agent.state.position,
                # agent.state.is_running,
                agent.state.dwell_time,
                agent.state.current_expected_dwell_time,
                # agent.state.previous_dwell_time,
                # agent.state.previous_expected_dwell_time,
            ], dim=-1)
        state = state.to(torch.float32)
        bfs_tree = torch.zeros(self.num_envs, 100, device=self.device)
        bfs_tree_weight = torch.zeros(self.num_envs, 100, device=self.device)
        bfs_tree_weight_upper_bound = torch.zeros(self.num_envs, 100, device=self.device)
        for i in range(self.num_envs):
            t = self.world.get_node(agent.state.position[i].item()).bfs_tree
            bfs_tree[i] = torch.tensor(t, device=self.device)
            bfs_tree_weight[i] = torch.tensor(self.world.get_node(agent.state.position[i].item()).bfs_tree_weight, device=self.device)
            bfs_tree_weight_upper_bound[i] = torch.tensor(self.world.get_node(agent.state.position[i].item()).bfs_tree_weight_upper_bound, device=self.device)
        return {
            # Train state
            "train_state": state,
            "train_bfs_tree": bfs_tree,
            "train_bfs_tree_weight": bfs_tree_weight,
            "bfs_tree_weight_upper_bound": bfs_tree_weight_upper_bound,
            
            # Global state
            # "global_state": torch.stack([
            #     self.world.adjacency_matrix
            # ], dim=-1)

            # Agent's Future
            
        }

    def reward(self, agent) -> torch.Tensor:
        """Calculate agent rewards"""
        return agent.calc_reward()

    def done(self) -> torch.Tensor:
        """Determine if scenario is finished"""
        return torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)

    def info(self, agent) -> Dict[str, torch.Tensor]:
        return {
        }

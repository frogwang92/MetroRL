from typing import Dict
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
            agent.init_random_position(len(self.world.platfrom_nodes))
            self.world.agents.append(agent)

        return self.world

    def env_reset_world_at(self, env_index=None):
        # Reset train positions
        for agent in self.world.agents:
            agent.reset_state(env_index)
            agent.init_random_position(len(self.world.platfrom_nodes), env_index)

    def pre_step(self):
        potential_next_pos = torch.zeros(self.num_envs, device=self.device)
        for agent in self.world.agents:
            for env in range(self.num_envs):
                if agent.action[env].item() == 1:
                    current_pos = agent.state.position[env].item()
                    potential_next_pos[env] = self.world.get_next_nodes(current_pos)[0].id
                else:
                    potential_next_pos[env] = agent.state.position[env].item()
            agent.potential_step(potential_next_pos)

    def post_step(self):
        pass

    def env_process_action(self, agent: MetroAgentV1):
        pass

    def observation(self, agent: MetroAgentV1) -> Dict[str, torch.Tensor]:
        """Generate agent observations"""
        state = torch.stack([
                agent.state.position,
                agent.state.is_running
            ], dim=-1)
        state = state.to(torch.float32)
        return {
            # Train state
            "train_state": state,
            
            # Global state
            # "global_state": torch.stack([
            #     self.world.adjacency_matrix
            # ], dim=-1)

            # Agent's Future
            
        }

    def reward(self, agent) -> torch.Tensor:
        """Calculate agent rewards"""
        reward = torch.zeros(self.num_envs, device=self.device)
        
        move_reward = agent.action_result - 1

        reward += move_reward
        return reward

    def done(self) -> torch.Tensor:
        """Determine if scenario is finished"""
        return torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)

    def info(self, agent) -> Dict[str, torch.Tensor]:
        return {
        }

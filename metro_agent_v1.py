from dataclasses import dataclass
import math
import torch
from typing import Optional

class MovingState:
    """Environment running state"""
    STOPPED = 0
    RUNNING = 1

class Action:
    """Environment action"""
    STOP = 0
    MOVE_TO_NEXT = 1

@dataclass
class AgentState:
    """Train state"""
    position: torch.Tensor        # Position on the current edge
    current_edge: torch.Tensor    # ID of the current edge
    current_node: torch.Tensor    # ID of the current node
    target_station: torch.Tensor  # ID of the target station
    arrival_time: torch.Tensor    # Arrival time
    schedule_time: torch.Tensor   # Scheduled arrival time
    passenger_count: torch.Tensor # Current number of passengers
    is_running: torch.Tensor      # Whether the train is running
    dwell_time: torch.Tensor      # Dwell time at the node
    current_expected_dwell_time: torch.Tensor # Expected dwell time
    previous_dwell_time: torch.Tensor # Previous dwell time
    previous_expected_dwell_time: torch.Tensor # Previous expected dwell time

class MetroAgentV1:
    """Metro train agent"""

    def __init__(
        self,
        name: str,
        num_envs: int,
        device: torch.device,
        **kwargs
    ):
        self.potential_next_pos = None
        self.action = None
        self.world = None
        self.name = name
        self.num_envs = num_envs
        self.device = device

        self.action_result = None

        # Initialize state
        self.state = None
        self._init_state()

    def _init_state(self):
        """Initialize agent state"""
        self.state = AgentState(
            position=torch.zeros(self.num_envs, device=self.device, dtype=torch.float32),
            current_edge=torch.ones(self.num_envs, device=self.device, dtype=torch.float32),
            current_node=torch.zeros(self.num_envs, device=self.device, dtype=torch.float32),
            target_station=torch.zeros(self.num_envs, device=self.device, dtype=torch.float32),
            arrival_time=torch.zeros(self.num_envs, device=self.device, dtype=torch.float32),
            schedule_time=torch.zeros(self.num_envs, device=self.device, dtype=torch.float32),
            passenger_count=torch.zeros(self.num_envs, device=self.device, dtype=torch.float32),
            is_running=torch.zeros(self.num_envs, device=self.device, dtype=torch.bool),
            dwell_time=torch.zeros(self.num_envs, device=self.device, dtype=torch.float32),
            current_expected_dwell_time=torch.zeros(self.num_envs, device=self.device, dtype=torch.float32),
            previous_dwell_time=torch.zeros(self.num_envs, device=self.device, dtype=torch.float32),
            previous_expected_dwell_time=torch.zeros(self.num_envs, device=self.device, dtype=torch.float32)
        )

        self.potential_next_pos = torch.zeros(self.num_envs, device=self.device, dtype=torch.float32)
        self.action_result = torch.zeros(self.num_envs, device=self.device, dtype=torch.float32)

        # Current action
        self.action = torch.zeros(
            self.num_envs,
            device=self.device
        )

    def reset_state(self, env_index: Optional[int] = None):
        """Reset agent state"""
        if env_index is not None:
            # Reset a single environment
            self.state.position[env_index] = 0
            self.state.current_edge[env_index] = -1
            self.state.target_station[env_index] = 0
            self.state.arrival_time[env_index] = 0
            self.state.schedule_time[env_index] = 0
            self.state.passenger_count[env_index] = 0
            self.action[env_index] = 0
            self.state.dwell_time[env_index] = 0
            self.state.current_expected_dwell_time[env_index] = 0
            self.state.previous_dwell_time[env_index] = 0
            self.state.previous_expected_dwell_time[env_index] = 0
        else:
            # Reset all environments
            self._init_state()

    def init_position(self, position: torch.Tensor):
        # self.state.position = position
        isduplicate = torch.zeros(self.num_envs, device=self.device, dtype=torch.bool)
        self.set_position(position, isduplicate)

    def set_action(self, action: torch.Tensor):
        """Set agent action"""
        # Ensure action is within a reasonable range
        self.action = action.clamp(0, 1)

    def set_position(self, position: torch.Tensor, isduplicate: torch.Tensor):
        """Set agent position"""
        self.state.position = position
        for i in range(self.num_envs):
            if isduplicate[i].item():  # stay in the same position
                self.state.dwell_time[i] = 1 + self.state.dwell_time[i].item()
            else:               # move to the next position
                pos = self.world.get_node(position[i].item())
                
                self.state.previous_dwell_time[i] = self.state.dwell_time[i].item()
                self.state.previous_expected_dwell_time[i] = self.state.current_expected_dwell_time[i].item()

                self.state.dwell_time[i] = 1
                self.state.current_expected_dwell_time[i] = pos.weight


    def calc_reward(self):
        """Calculate agent reward"""
        # Reward for reaching the target station
        reward = torch.zeros(self.num_envs, device=self.device)
        for i in range(self.num_envs):
            if self.state.previous_dwell_time[i].item() == 0:
                reward[i] = 0
            else:
                reward[i] = (-1) * math.fabs(self.state.previous_expected_dwell_time[i] - self.state.previous_dwell_time[i])
        return reward

    def to(self, device: torch.device):
        """Move data to the specified device"""
        self.device = device

        # Move state tensors
        for field in self.state.__dataclass_fields__:
            value = getattr(self.state, field)
            if isinstance(value, torch.Tensor):
                setattr(self.state, field, value.to(device))

        # Move action tensor
        self.action = self.action.to(device)

    def potential_step(self, next_pos: torch.Tensor):
        self.potential_next_pos = next_pos
        # print(self.potential_next_pos)
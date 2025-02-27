from dataclasses import dataclass
import torch
from typing import Optional

class MovingState:
    """环境运行状态"""
    STOPPED = 0
    RUNNING = 1

class Action:
    """环境动作"""
    STOP = 0
    MOVE_TO_NEXT = 1

@dataclass 
class AgentState:
    """列车状态"""
    position: torch.Tensor        # 在当前边上的位置
    current_edge: torch.Tensor   # 当前所在边的ID
    current_node: torch.Tensor   # 当前所在节点ID
    target_station: torch.Tensor # 目标站点ID
    arrival_time: torch.Tensor   # 到站时间
    schedule_time: torch.Tensor  # 计划到站时间
    passenger_count: torch.Tensor # 当前载客数
    is_running: torch.Tensor      # 列车是否在运行

class MetroAgentV1:
    """地铁列车智能体"""
    
    def __init__(
        self,
        name: str,
        num_envs: int,
        device: torch.device,
        **kwargs
    ):
        self.action = None
        self.name = name
        self.num_envs = num_envs
        self.device = device

        self.action_result = None

        # 初始化状态
        self._init_state()

    def _init_state(self):
        """初始化智能体状态"""
        self.state = AgentState(
            position=torch.zeros(self.num_envs, device=self.device, dtype=torch.float32),
            current_edge=torch.ones(self.num_envs, device=self.device, dtype=torch.float32),
            current_node=torch.zeros(self.num_envs, device=self.device, dtype=torch.float32),
            target_station=torch.zeros(self.num_envs, device=self.device, dtype=torch.float32),
            arrival_time=torch.zeros(self.num_envs, device=self.device, dtype=torch.float32),
            schedule_time=torch.zeros(self.num_envs, device=self.device, dtype=torch.float32),
            passenger_count=torch.zeros(self.num_envs, device=self.device, dtype=torch.float32),
            is_running=torch.zeros(self.num_envs, device=self.device, dtype=torch.bool)
        )

        self.potential_next_pos = torch.zeros(self.num_envs, device=self.device, dtype=torch.float32)
        self.action_result = torch.zeros(self.num_envs, device=self.device, dtype=torch.float32)
        
        # 当前动作
        self.action = torch.zeros(
            self.num_envs,
            device=self.device
        )
        
    def reset_state(self, env_index: Optional[int] = None):
        """重置智能体状态"""
        if env_index is not None:
            # 重置单个环境
            self.state.position[env_index] = 0
            self.state.current_edge[env_index] = -1
            self.state.current_node[env_index] = 0
            self.state.target_station[env_index] = 0
            self.state.arrival_time[env_index] = 0
            self.state.schedule_time[env_index] = 0
            self.state.passenger_count[env_index] = 0
            self.action[env_index] = 0
        else:
            # 重置所有环境
            self._init_state()
    
    def init_random_position(self, random_range: int, env_index:Optional[int] = None):
        """初始化随机位置"""
        if env_index is not None:
            self.state.position[env_index] = torch.randint(
                1, random_range, (1,), device=self.device
            )
        else:
            self.state.position = torch.randint(
                1, random_range, (self.num_envs,), device=self.device
            )

    def set_action(self, action: torch.Tensor):
        """设置智能体动作"""
        # 确保动作在合理范围内
        self.action = action.clamp(0, 1)
        
    def to(self, device: torch.device):
        """移动数据到指定设备"""
        self.device = device
        
        # 移动状态张量
        for field in self.state.__dataclass_fields__:
            value = getattr(self.state, field)
            if isinstance(value, torch.Tensor):
                setattr(self.state, field, value.to(device))
                
        # 移动动作张量
        self.action = self.action.to(device)

    def potential_step(self, next_pos: torch.Tensor):
        self.potential_next_pos = next_pos
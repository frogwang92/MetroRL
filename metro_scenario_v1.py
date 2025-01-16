from typing import Dict
import torch
from metro_world import MetroWorldV1
from metro_agent_v1 import MetroAgentV1

class MetroScenarioV1:
    """地铁系统场景类,负责管理环境状态和交互规则"""
    
    def __init__(self):
        self.world = None
        self._init_scenario()

    def _init_scenario(self):
        # 初始化状态追踪器
        self.passenger_count = {}  # 各站点等待乘客
        self.congestion = {}      # 拥挤度
        self.delays = {}          # 延误情况

    def env_make_world(self, num_envs: int, device: torch.device, **kwargs):
        """创建向量化的世界状态"""
        self.num_envs = num_envs
        self.device = device
        
        # 初始化世界状态
        self.world = MetroWorldV1(
            num_envs=num_envs,
            device=device,
            **kwargs
        )
        
        if kwargs.get("num_trains"):
            self.num_trains = kwargs["num_trains"]
            for i in range(kwargs["num_trains"]):
                agent = MetroAgentV1(
                    f"train_{i}",
                    num_envs,
                    device
                )
                agent.init_random_position(len(self.world.platfrom_nodes))
                self.world.agents.append(agent)

        return self.world

    def env_reset_world_at(self, env_index=None):
        # 重置列车位置
        for agent in self.world.agents:
            agent.reset_state(env_index)
            agent.init_random_position(len(self.world.platfrom_nodes), env_index)

    def pre_step(self):
        potential_next_pos = torch.zeros(self.num_envs, device=self.device)
        for agent in self.world.agents:
            for env in self.num_envs:
                if agent.action[env] == 1:
                    current_pos = agent.state.position[env]
                    potential_next_pos[env] = self.world.get_next_nodes(current_pos)[0]
                else:
                    potential_next_pos[env] = agent.state.position[env]
            agent.potential_step(potential_next_pos)

    def post_step(self):
        pass

    def observation(self, agent) -> Dict[str, torch.Tensor]:
        """生成智能体的观测"""
        return {
            # 列车状态
            "train_state": torch.stack([
                agent.state.position
            ], dim=-1),
            
            # 全局状态
            # "global_state": torch.stack([
            #     self.world.adjacency_matrix
            # ], dim=-1)

            # Agent‘s Future
            
        }

    def reward(self, agent) -> torch.Tensor:
        """计算智能体的奖励"""
        reward = torch.zeros(self.num_envs, device=self.device)
        
        move_reward = agent.action_result - 1

        reward += move_reward
        return reward

    def done(self) -> torch.Tensor:
        """判断场景是否结束"""
        return torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)

    def info(self, agent) -> Dict[str, torch.Tensor]:
        return {
        }

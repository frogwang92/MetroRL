import random
import torch
from linedata import platforms, line_segments
from buildtopology import build_topology, calc_coordinates_with_networkx, build_adjacency_matrix

class MetroWorldV1:
    """地铁系统世界类,负责物理模拟和状态更新"""
    
    def __init__(
        self,
        num_envs: int,
        device: torch.device,
        **kwargs
    ):
        self.num_envs = num_envs
        self.device = device
        self.nodes, self.platfrom_nodes, self.edges, self.segments, self.node2segments, self.segment2nodes = build_topology(platforms, line_segments)
        self.adjacency_matrix = build_adjacency_matrix(self.nodes, self.edges)
        self.nodes = calc_coordinates_with_networkx(self.nodes, self.edges)
        
        # 智能体列表
        self.agents = []
        
        # 初始化物理约束
        self._init_constraints()
        
    def _init_constraints(self):
        """初始化物理约束"""
        pass
    
    def step(self):
        self._update_train_positions()
    
    def _update_train_positions(self):
        # for each env, check all the agent's potential next position
        # if there is overlap position, the potential move failed, and the agent's position remains the same
        # if there is no overlap position, the agent's position is updated to the potential next position
        duplicate_masks = []
        new_positions = []
        for env in range(0,self.num_envs):
            # get all the potential next positions for all agents
            potential_next_pos = torch.zeros(len(self.agents), device=self.device)
            for i, agent in enumerate(self.agents):
                potential_next_pos[i] = agent.potential_next_pos[env]
            # check if there is any other agent in the same potential next positions
            duplicate_mask = torch.zeros(len(self.agents), dtype=torch.bool, device=self.device)
            for i in range(len(self.agents)):
                for j in range(i + 1, len(self.agents)):
                    if potential_next_pos[i].item() == potential_next_pos[j].item() and i != j:
                        duplicate_mask[i] = True
                        duplicate_mask[j] = True
            new_position = torch.zeros(len(self.agents), device=self.device)
            for i, agent in enumerate(self.agents):
                if not duplicate_mask[i].item():
                    previous_pos = agent.state.position[env].item()
                    new_pos = potential_next_pos[i].item()
                    new_position[i] = new_pos
                    # if env == 0 or i == 0:
                    #     print(f"Agent {agent.name} moved to {agent.state.position[env]}")
                    if previous_pos != new_pos:
                        agent.action_result[env] = 2
                    else:
                        agent.action_result[env] = 1
                else:
                    previous_pos = agent.state.position[env].item()
                    new_position[i] = previous_pos
                    agent.action_result[env] = 0
            duplicate_masks.append(duplicate_mask)
            new_positions.append(new_position)

        # transform the duplicate masks
        for i, agent in enumerate(self.agents):
            duplicate_mask = torch.zeros(self.num_envs, dtype=torch.bool, device=self.device)
            new_position = torch.zeros(self.num_envs, device=self.device)
            for env in range(self.num_envs):
                duplicate_mask[env] = duplicate_masks[env][i]
                new_position[env] = new_positions[env][i]

            agent.set_position(new_position, duplicate_mask.to(agent.device))


    def to(self, device: torch.device):
        self.device = device
        for agent in self.agents:
            agent.to(device)

    def get_node(self, node_id):
        return self.nodes[node_id]

    def init_random_weights(self):
        for node in self.platfrom_nodes.values():
            # generate random weights for each node
            # a int value between 1 and 10
            node.weight = random.randint(30, 60)

    def get_next_nodes(self, current_node):
        """
        Get all possible next nodes that a train can move to from its current position
        
        Args:
            train: The train object to check movement options for
            
        Returns:
            list: List of node IDs that the train can move to
        """
        possible_nodes = []
        
        # Check all edges for connections to current node
        for edge in self.edges:
            # Check forward direction
            if edge.start_node.id == current_node:
                possible_nodes.append(edge.end_node)
                
            # Check reverse direction
                
        return possible_nodes
"""
Train module for managing train movement and state in the metro system.

This module contains the Train class which represents individual trains in the system.
Each train has a unique ID and tracks its current position and node in the network.

Classes:
    Train: Represents a train with position tracking and movement capabilities
"""

from logger import logger
from typing import Optional
from dataclasses import dataclass
from topology.node import Node


@dataclass
class TrainState:
    """Current state of a train"""
    current_node: Node
    speed: float = 0.0
    status: str = 'stopped'

class Train:
    """
    Represents a train in the metro system
    
    Attributes:
        id (int): Unique identifier for the train
        state (TrainState): Current state of the train
        
    Methods:
        move_to_node: Attempt to move train to specified node
        update_state: Update train's internal state
    """
    def __init__(self, train_id: int, initial_node: Node):
        self.id = train_id
        self.state = TrainState(current_node=initial_node)
        logger.info(f"Train {self.id} initialized at node {initial_node.id}")

    def move_to_node(self, target_node: Optional[Node]) -> bool:
        """
        Move train to target node if possible
        
        Args:
            target_node: Node to move to, or None to stay in place
            
        Returns:
            bool: True if movement successful, False otherwise
        """
        if target_node is None:
            logger.warning(f"Train {self.id} cannot move to None target node")
            return False
            
        logger.info(f"Train {self.id} moving from node {self.state.current_node.id} to node {target_node.id}")
        self.state.current_node = target_node
        self.state.status = 'moving'
        return True

    def __str__(self):
        """String representation of the train"""
        return f"Train {self.id} at node {self.state.current_node.id} with status {self.state.status}"

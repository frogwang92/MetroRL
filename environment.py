"""
Environment module for managing the metro system simulation.

This module contains the Environment class which creates and manages the topology,
trains, and simulation state of the metro system.

Classes:
    Environment: Main simulation environment that manages topology and trains
"""

from buildtopology import build_topology, calc_coordinates_with_networkx
from traincontroller import TrainController
from linedata import platforms, line_segments
from enum import Enum
from typing import Optional, Dict, List
from dataclasses import dataclass
from logger import setup_logger
from config import Config

class Mode(Enum):
    """Operation mode for the environment"""
    SELFROLLING = "self_rolling"  # Environment controls train movement
    DELEGATED = "delegated"      # External system controls train movement

@dataclass
class SimulationState:
    time: int = 0
    is_running: bool = False
    mode: str = 'SELFROLLING'

class Environment:
    def __init__(self, config: Config):
        self.logger = setup_logger('environment', 'simulation.log')
        self.config = config
        self.state = SimulationState(mode=config.sim.default_mode)
        
        # Initialize components
        self._init_topology()
        self._init_controller()
        
    def _init_topology(self):
        """Initialize network topology"""
        try:
            self.nodes, self.edges = build_topology(platforms, line_segments)
            self.nodes = calc_coordinates_with_networkx(self.nodes, self.edges)
        except Exception as e:
            self.logger.error(f"Failed to initialize topology: {e}")
            raise
            
    def _init_controller(self):
        """Initialize train controller"""
        self.train_controller = TrainController()
        self._load_policy()
        
    def _load_policy(self):
        """Load movement policy based on mode"""
        if self.state.mode == 'SELFROLLING':
            from policies.alwaysmovetonext import AlwaysMoveToNextPolicy
            self.policy = AlwaysMoveToNextPolicy()
        else:
            from policies.delegated import DelegatedPolicy
            self.policy = DelegatedPolicy()
        
    def add_train(self, initial_node_id):
        """
        Add a new train to the environment
        
        Args:
            initial_node_id: ID of node where train should start
            
        Returns:
            Created train object or None if node not found
        """
        if initial_node_id not in self.nodes:
            return None
            
        return self.train_controller.create_train(self.nodes[initial_node_id])
        
    def remove_train(self, train_id):
        """
        Remove a train from the environment
        
        Args:
            train_id: ID of train to remove
            
        Returns:
            True if train was removed, False otherwise
        """
        return self.train_controller.remove_train(train_id)
        
    def step(self):
        """
        Advance simulation by one time step
        
        Returns:
            Current simulation time
        """
        if not self.state.is_running:
            return self.state.time
            
        # Update train positions
        for train in self.train_controller.get_all_trains().values():
            if self.state.mode == Mode.SELFROLLING:
                next_node = self.policy.get_action(train, self)
                if next_node != train.current_node:
                    train.move_to(next_node)
            
        self.state.time += 1
        return self.state.time
        
    def start(self):
        """Start the simulation"""
        self.state.is_running = True
        
    def pause(self):
        """Pause the simulation"""
        self.state.is_running = False
        
    def reset(self):
        """Reset the simulation to initial state"""
        self.state.time = 0
        self.state.is_running = False
        self.train_controller = TrainController()
        
    def get_node(self, node_id):
        """Get a node by ID"""
        return self.nodes.get(node_id)
        
    def get_edge(self, edge_id):
        """Get an edge by ID"""
        for edge in self.edges:
            if edge.id == edge_id:
                return edge
        return None
        
    def get_train(self, train_id):
        """Get a train by ID"""
        return self.train_controller.get_train(train_id)
    
    def get_all_trains(self):
        """Get all trains in the environment"""
        return self.train_controller.get_all_trains()

    def can_move_to(self, train, target_node):
        """
        Check if a train can move to the target node
        
        Args:
            train: The train object to check
            target_node: ID of the node to check movement to
            
        Returns:
            bool: True if movement is allowed, False otherwise
        """
        # Get current and target node objects
        current_node = train.current_node
        target = self.get_node(target_node)
        
        if not target:
            return False
            
        # Check if nodes are connected by an edge
        connected = False
        for edge in self.edges:
            if (edge.start_node.id == current_node and edge.end_node.id == target_node) or \
               (edge.end_node.id == current_node and edge.start_node.id == target_node):
                connected = True
                break
                
        if not connected:
            return False
            
        # Check if target node is occupied by another train
        for other_train in self.train_controller.get_all_trains().values():
            if other_train.id != train.id and other_train.current_node == target_node:
                return False
                
        return True
    
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

    # Add a property to access time directly
    @property
    def time(self):
        """Get current simulation time"""
        return self.state.time
    
    # Add a property to access state directly
    @property
    def is_running(self):
        """Get current simulation state"""
        return self.state.is_running
    
    def stop(self):
        """Stop the simulation and perform cleanup"""
        self.reset()  # Assuming reset() exists to restore initial state

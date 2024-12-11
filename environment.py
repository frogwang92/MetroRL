"""
Environment module for managing the metro system simulation.

This module contains the Environment class which creates and manages the topology,
trains, and simulation state of the metro system.

Classes:
    Environment: Main simulation environment that manages topology and trains
"""

import threading
import time
from buildtopology import build_topology, calc_coordinates_with_networkx
from traincontroller import TrainController
from linedata import platforms, line_segments
from enum import Enum
from typing import Optional, Dict, List
from dataclasses import dataclass
from logger import logger
from config import Config

class Mode(Enum):
    """Operation mode for the environment"""
    SELFROLLING = "self_rolling"  # Environment controls train movement
    DELEGATED = "delegated"       # External system controls train movement

class ClockMode(Enum):
    """Clock mode for the environment"""
    INTERNAL = "internal"  # Environment controls time
    EXTERNAL = "external"  # External system controls time

@dataclass
class SimulationState:
    time: int = 0
    is_running: bool = False
    mode: Mode = Mode.SELFROLLING

class Clock:
    def __init__(self, env, mode=ClockMode.INTERNAL, external_clock=None, interval=0.1):
        self.env = env
        self.mode = mode
        self.external_clock = external_clock
        self.time = 0
        self.running = False
        self.interval = interval  # Interval in seconds for self rolling mode

    def tick(self):
        if self.running:
            if self.external_clock:
                self.time = self.external_clock.get_time()
            else:
                self.time += 1
            self.env.step()

    def start(self):
        self.running = True
        if self.mode == ClockMode.INTERNAL:
            threading.Thread(target=self._run).start()

    def _run(self):
        while self.running:
            time.sleep(self.interval)
            self.tick()

    def pause(self):
        self.running = False

    def reset(self):
        self.time = 0
        self.running = False

    def get_time(self):
        return self.time

class Environment:
    def __init__(self, config: Config, clock=None):
        logger.info("Initializing Environment")
        self.config = config
        if config.sim.default_mode == 'self_rolling':
            self.state = SimulationState(mode=Mode.SELFROLLING)
        else:
            self.state = SimulationState(mode=Mode.DELEGATED)
        self.clock = clock if clock else Clock(self)
        
        # Initialize components
        self._init_topology()
        self._init_controller()
        logger.info("Environment initialized")

    def _init_topology(self):
        """Initialize network topology"""
        logger.info("Initializing topology")
        try:
            self.nodes, self.edges, self.segments, self.node2segments, self.segment2nodes = build_topology(platforms, line_segments)
            self.nodes = calc_coordinates_with_networkx(self.nodes, self.edges)
            logger.info("Topology initialized")
        except Exception as e:
            logger.error(f"Failed to initialize topology: {e}")
            raise

    def _init_controller(self):
        """Initialize train controller"""
        logger.info("Initializing train controller")
        self.train_controller = TrainController()
        self._load_policy()
        logger.info("Train controller initialized")

    def _load_policy(self):
        """Load movement policy based on mode"""
        logger.info(f"Loading policy for mode: {self.state.mode}")
        if self.state.mode == Mode.SELFROLLING:
            from policies.alwaysmovetonext import AlwaysMoveToNextPolicy
            self.policy = AlwaysMoveToNextPolicy()
        else:
            from policies.delegated import DelegatedPolicy
            self.policy = DelegatedPolicy()
        logger.info("Policy loaded")

    def add_train(self, initial_node_id):
        """
        Add a new train to the environment

        Args:
            initial_node_id: ID of node where train should start

        Returns:
            Created train object or None if node not found
        """
        logger.info(f"Adding train at node {initial_node_id}")
        if initial_node_id not in self.nodes:
            logger.warning(f"Node {initial_node_id} not found")
            return None

        train = self.train_controller.create_train(self.nodes[initial_node_id])
        logger.info(f"Train added: {train}")
        return train

    def remove_train(self, train_id):
        """
        Remove a train from the environment
        
        Args:
            train_id: ID of train to remove
            
        Returns:
            True if train was removed, False otherwise
        """
        logger.info(f"Removing train with ID {train_id}")
        result = self.train_controller.remove_train(train_id)
        if result:
            logger.info(f"Train {train_id} removed")
        else:
            logger.warning(f"Train {train_id} not found")
        return result
        
    def step(self):
        """
        Advance simulation by one time step
        
        Returns:
            Current simulation time
        """
        if not self.state.is_running:
            return self.state.time

        logger.info("Advancing simulation by one time step")
        # Update train positions
        for train in self.train_controller.get_all_trains().values():
            if self.state.mode == Mode.SELFROLLING:
                next_node = self.policy.get_action(train, self)
                if next_node != train.state.current_node:
                    train.move_to_node(next_node)

        self.state.time = self.clock.get_time()
        logger.info(f"Simulation time: {self.state.time}")
        return self.state.time
        
    def start(self):
        """Start the simulation"""
        logger.info("Starting simulation")
        self.state.is_running = True
        self.clock.start()
        
    def pause(self):
        """Pause the simulation"""
        logger.info("Pausing simulation")
        self.state.is_running = False
        self.clock.pause()
        
    def reset(self):
        """Reset the simulation to initial state"""
        logger.info("Resetting simulation")
        self.state.time = 0
        self.state.is_running = False
        self.train_controller = TrainController()
        self.clock.reset()
        
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
        current_node = train.state.current_node
            
        # Check if nodes are connected by an edge
        connected = False
        for edge in self.edges:
            if (edge.start_node == current_node and edge.end_node == target_node) or \
               (edge.end_node == current_node and edge.start_node == target_node):
                connected = True
                break
                
        if not connected:
            return False
            
        # Check if target node is occupied by another train
        for other_train in self.train_controller.get_all_trains().values():
            if other_train.id != train.id and other_train.state.current_node == target_node:
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
            if edge.start_node == current_node:
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

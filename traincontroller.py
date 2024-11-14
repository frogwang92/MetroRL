"""
TrainController module for managing multiple trains in the metro system.

This module contains the TrainController class which manages the creation, removal
and movement of trains throughout the network.

Classes:
    TrainController: Manages multiple trains and their movements in the system
"""

from train import Train

class TrainController:
    def __init__(self):
        """Initialize the train controller"""
        self.trains = {}  # Dictionary to store trains by ID
        self._next_train_id = 1  # Counter for generating unique train IDs
        
    def create_train(self, initial_node):
        """
        Create a new train and add it to the system
        
        Args:
            initial_node: The starting node for the new train
            
        Returns:
            The created Train object
        """
        train_id = self._next_train_id
        self._next_train_id += 1
        
        train = Train(train_id, initial_node)
        self.trains[train_id] = train
        return train
        
    def remove_train(self, train_id):
        """
        Remove a train from the system
        
        Args:
            train_id: ID of the train to remove
            
        Returns:
            True if train was removed, False if train ID not found
        """
        if train_id in self.trains:
            del self.trains[train_id]
            return True
        return False
        
    def move_to(self, train_id, target_node):
        """
        Move a train to the specified node if possible
        
        Args:
            train_id: ID of the train to move
            target_node: Node to move the train to
            
        Returns:
            True if movement was successful, False otherwise
        """ 
        train = self.trains[train_id]
        return train.move_to_node(target_node)
        
    def get_train(self, train_id):
        """
        Get a train by its ID
        
        Args:
            train_id: ID of the train to retrieve
            
        Returns:
            Train object if found, None otherwise
        """
        return self.trains.get(train_id)
        
    def get_all_trains(self):
        """
        Get all trains in the system
        
        Returns:
            Dictionary of all trains keyed by train ID
        """
        return self.trains

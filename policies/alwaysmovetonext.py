class AlwaysMoveToNextPolicy:
    """A simple policy that always moves trains to the next node if possible"""
    
    def __init__(self):
        pass
        
    def get_action(self, train, env):
        """
        Determine action for the given train in the current environment state.
        Returns the next node ID if movement is possible, or current node ID if blocked.
        
        Args:
            train: The train object to get an action for
            env: The environment object containing current state
            
        Returns:
            int: ID of the node to move to (either next node or current node if blocked)
        """
        current_node = train.state.current_node
        next_nodes = env.get_next_nodes(current_node)
        
        if not next_nodes:
            # No next nodes available, stay in place
            return current_node
            
        import random
        actions = [0, 1]
        action = random.choice(actions)
        if action == 0:
            return current_node
        
        next_node = random.choice(next_nodes)  # Take random available next node
        
        # Check if movement to next node is allowed by environment
        if not env.can_move_to(train, next_node):
            # Movement not allowed, stay in current node
            return current_node
                
        # Next node is free, move there
        return next_node

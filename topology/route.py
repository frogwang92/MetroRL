class Route:
    """
    Represents a connected path through the network.
    
    Attributes:
        id (str): The unique identifier for the route.
        nodes (list[Node]): Ordered list of nodes in the route.
        edges (list[Edge]): Ordered list of edges connecting the nodes.
        
    Methods:
        validate(): Verifies that all nodes in the route are connected.
        add_node(node): Adds a node to the end of the route if it can be connected.
        remove_node(node): Removes a node and updates connections.
        get_next_node(current_node): Gets the next node in the route.
        get_previous_node(current_node): Gets the previous node in the route.
    """
    
    def __init__(self, id, initial_node=None):
        """
        Initialize a route
        
        Args:
            id (str): Unique identifier for the route
            initial_node (Node, optional): First node in the route
        """
        self.id = id
        self.nodes = []
        self.edges = []
        
        if initial_node:
            self.nodes.append(initial_node)
            
    def validate(self):
        """
        Verify that all nodes in the route are connected by edges
        
        Returns:
            bool: True if route is valid, False otherwise
        """
        if len(self.nodes) < 2:
            return True
            
        for i in range(len(self.nodes) - 1):
            current_node = self.nodes[i]
            next_node = self.nodes[i + 1]
            
            # Check if there's a connecting edge
            edge_exists = False
            for edge in self.edges:
                if ((edge.start_node == current_node and edge.end_node == next_node) or
                    (edge.start_node == next_node and edge.end_node == current_node)):
                    edge_exists = True
                    break
                    
            if not edge_exists:
                return False
                
        return True
        
    def add_node(self, node, edge):
        """
        Add a node and its connecting edge to the route
        
        Args:
            node (Node): Node to add
            edge (Edge): Edge connecting the new node to the last node
            
        Returns:
            bool: True if node was added successfully, False otherwise
        """
        if not self.nodes:
            self.nodes.append(node)
            return True
            
        last_node = self.nodes[-1]
        
        # Verify the edge connects the last node to the new node
        if ((edge.start_node == last_node and edge.end_node == node) or
            (edge.start_node == node and edge.end_node == last_node)):
            self.nodes.append(node)
            self.edges.append(edge)
            return True
            
        return False
        
    def remove_node(self, node):
        """
        Remove a node and its connecting edges from the route
        
        Args:
            node (Node): Node to remove
            
        Returns:
            bool: True if node was removed successfully, False otherwise
        """
        if node not in self.nodes:
            return False
            
        node_index = self.nodes.index(node)
        
        # Remove connecting edges
        if node_index > 0:
            self.edges.pop(node_index - 1)
        if node_index < len(self.nodes) - 1:
            self.edges.pop(node_index)
            
        self.nodes.remove(node)
        return True
        
    def get_next_node(self, current_node):
        """
        Get the next node in the route after the current node
        
        Args:
            current_node (Node): Current position in route
            
        Returns:
            Node: Next node in route or None if at end
        """
        try:
            current_index = self.nodes.index(current_node)
            if current_index < len(self.nodes) - 1:
                return self.nodes[current_index + 1]
        except ValueError:
            pass
        return None
        
    def get_previous_node(self, current_node):
        """
        Get the previous node in the route before the current node
        
        Args:
            current_node (Node): Current position in route
            
        Returns:
            Node: Previous node in route or None if at start
        """
        try:
            current_index = self.nodes.index(current_node)
            if current_index > 0:
                return self.nodes[current_index - 1]
        except ValueError:
            pass
        return None
        
    def __str__(self):
        """String representation of the route"""
        return f"Route {self.id}: {' -> '.join(str(node.id) for node in self.nodes)}"
    


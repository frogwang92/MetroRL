class Node:
    """
    A class used to represent a Node.
    Attributes
    ----------
    id : int
        The unique identifier for the node.
    weight : int
        The weight associated with the node.
    Methods
    -------
    __repr__()
        Returns a string representation of the Node instance.
    """
    def __init__(self, id, weight):
        self.id = id
        self.weight = weight
        self.weight_upper_bound = weight
        if self.weight > 1:
            self.weight_upper_bound = self.weight + 10
        self.bfs_tree = None
        self.bfs_tree_weight = None
        self.bfs_tree_weight_upper_bound = None
        self.type : int = 1   # 0: platform, 1: segment 

    def __repr__(self):
        return f"Node(id={self.id}, weight={self.weight})"
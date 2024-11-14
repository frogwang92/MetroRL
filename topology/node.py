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

    def __repr__(self):
        return f"Node(id={self.id}, weight={self.weight})"

class Node:
    """
    A class used to represent a Node.
    Attributes
    ----------
    timespan : int
        The timespan associated with the node.
    Methods
    -------
    __repr__()
        Returns a string representation of the Node instance.
    """
    def __init__(self, timespan):
        self.weight = timespan

    def __repr__(self):
        return f"Node(timespan={self.weight})"
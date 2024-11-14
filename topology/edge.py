class Edge:
    """
    Represents an edge in a graph.
    Attributes:
        start_node (Any): The starting node of the edge.
        end_node (Any): The ending node of the edge.
        weight (int, optional): The weight of the edge. Defaults to 1.
    Methods:
        __repr__(): Returns a string representation of the edge.
    """
    def __init__(self, start_node, end_node, weight=1):
        self.start_node = start_node
        self.end_node = end_node
        self.weight = weight

    def __repr__(self):
        return f"Edge({self.start_node}, {self.end_node}, weight={self.weight})"
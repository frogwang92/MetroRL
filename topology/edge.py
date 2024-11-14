class Edge:
    """
    Represents an edge in a graph.
    Attributes:
        id (str): The unique identifier for the edge.
        start_node (Node): The starting node of the edge.
        end_node (Node): The ending node of the edge.
        weight (int, optional): The weight of the edge. Defaults to 1.
    Methods:
        __repr__(): Returns a string representation of the edge.
    """
    def __init__(self, id, start_node, end_node, weight=1):
        self.id = id
        self.start_node = start_node
        self.end_node = end_node
        self.weight = weight

    def __repr__(self):
        return f"Edge(id={self.id}, start_node={self.start_node}, end_node={self.end_node}, weight={self.weight})"
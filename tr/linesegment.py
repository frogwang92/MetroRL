class LineSegment:
    """
    A class to represent a line segment in a metro system.
    
    Attributes
    ----------
    start_platform : Platform
        The starting platform of the line segment.
    end_platform : Platform
        The ending platform of the line segment.
    travel_time : float
        The travel time between the start and end platforms.
    
    Methods
    -------
    __repr__():
        Returns a string representation of the LineSegment object.
    """
    def __init__(self, start_platform, end_platform, travel_time = 120):
        self.start_platform = start_platform
        self.end_platform = end_platform
        self.weight = travel_time
        self.id = str(start_platform.id) + "-" + str(end_platform.id)

    def __repr__(self):
        return f"LineSegment(start_platform={self.start_platform}, end_platform={self.end_platform}, travel_time={self.weight})"
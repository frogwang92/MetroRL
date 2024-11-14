class Platform:
    """
    A class to represent a platform.
    Attributes
    ----------
    id : int
        The unique identifier for the platform.
    name : str
        The name of the platform.
    dwell : float
        The dwell time of the platform.
    Methods
    -------
    __repr__():
        Returns a string representation of the Platform object.
    """
    def __init__(self, id, name, dwell=30):
        self.id = id
        self.name = name
        self.dwell = dwell

    def __repr__(self):
        return f"Platform(id={self.id}, name='{self.name}', dwell={self.dwell})"
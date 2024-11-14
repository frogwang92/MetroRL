class Switch:
    """
    A class used to represent a Switch.

    Attributes
    ----------
    id : int
        The unique identifier for the switch.
    name : str
        The name of the switch.
    """
    def __init__(self, id, name):
        self.id = id
        self.name = name

    def __repr__(self):
        return f"Switch(id={self.id}, name='{self.name}')"
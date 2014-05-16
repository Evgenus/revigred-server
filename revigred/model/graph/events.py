__all__ = [
    "Merge",
    "Cancel",
    "Confirm",
    ]

class ResultResolution(Exception): pass
class Merge(ResultResolution): pass
class Cancel(ResultResolution): pass
class Confirm(ResultResolution): pass

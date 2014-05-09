import uuid

def make_node_id():
    return "NODE-" + uuid.uuid4().hex

class Counter(object):
    def __init__(self, start=0):
        self._value = start

    @property
    def rev(self):
        old = self._value
        self._value += 1
        return old
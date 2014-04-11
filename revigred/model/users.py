import uuid

from revigred.record import Record

__all__ = [
    "User",
    "Users",
    ]

class User:
    def __init__(self, model):
        self._protocol = None
        self.id = "USER-" + uuid.uuid4().hex
        self.model = model

    def connect(self, protocol):
        self._protocol = protocol

    def disconnect(self):
        self.model.remove_user(self)
        self._protocol = None
        self.model = None

    @property
    def profile(self):
        return Record(id=self.id)

    def channel_opened(self):
        self.send("auth", **self.profile)

    def send(self, __name, *args, **kwargs):
        message = (__name, args, kwargs)
        self._protocol.sendMessage(message)

class Users:
    user_factory = User

    def __init__(self):
        self._users = {}

    def create_new_user(self):
        user = self.user_factory(self)
        self._users[user.id] = user
        return user

    def remove_user(self, user):
        del self._users[user.id]

    def broadcast(self, __name, *args, **kwargs):
        for id, user in self._users.items():
            user.send(__name, *args, **kwargs)


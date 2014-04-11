import uuid
import functools
from .record import Record

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

# ____________________________________________________________________________ #

class ChatUser(User):
    def __init__(self, model, name):
        super().__init__(model)
        self.name = name

    @property
    def profile(self):
        profile = super().profile
        profile.name = self.name
        return profile

    def channel_opened(self):
        super().channel_opened()
        greeting = "{0} entered the chat".format(self.name)
        self.model.broadcast("notify", greeting, name=self.name)

    def on_say(self, text):
        self.model.broadcast("say", text, name=self.name)

class Chat(Users):
    @staticmethod
    def user_factory(self):
        name = self.names_generator()
        return ChatUser(self, name)

    def __init__(self, names_generator):
        super().__init__()
        self.names_generator = names_generator


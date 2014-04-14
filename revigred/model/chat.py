from .users import (
    Users,
    User,
    )

__all__ = [
    "ChatUser", 
    "Chat",
    ]

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

    def dispatch(self, name, *args, **kwargs):
        func = getattr(self.client, "on_" + name, None)
        if func is None:
            raise ValueError("command {} was not found")
        func(*args, **kwargs)

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

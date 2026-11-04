from starlette.websockets import WebSocket
from audience import Audience

class Player:

    _players = {}

    @staticmethod
    def get(username: str) -> Player | None:
        return Player._players.get(username, None)


    def __init__(self, username: str, connection: WebSocket):
        Player._players[username] = self

        self._username = username
        self._connection = connection
        self._speaking = []
        self._listening = []

        self._location = [10, 50, 10]
        self._yaw = 0
        self._pitch = 0

        audience = Audience.get("default")
        if audience: audience.add_listener(self); self.add_speaker(audience)


    def get_username(self):
        return self._username

    def remove(self):
        for listening in self._listening:
            listening.remove_listener(self)

        del Player._players[self._username]

    def add_speaker(self, audience: Audience):
        if audience in self._speaking:
            return

        self._speaking.append(audience)

    def remove_speaker(self, audience: Audience):
        self._speaking.remove(audience)

    def get_speaking(self) -> list[Audience]:
        return self._speaking

    def add_listening(self, audience: Audience):
        if audience in self._listening:
            return

        self._listening.append(audience)

    def remove_listening(self, audience: Audience):
        self._listening.remove(audience)

    async def send_data(self, json):
        if not self._connection:
            return

        await self._connection.send_json(json)
import numpy as np

class Audience:
    """
    Voice chat audience. Players can reside
    in an audience, affecting who they can hear
    and whether it is proximity.
    """

    _channels = {}

    @staticmethod
    def get(identifier: str) -> Audience | None:
        return Audience._channels.get(identifier, None)

    def __init__(self, identifier: str):
        assert identifier not in self._channels, "Audience already exists!"

        self._identifier = identifier
        self._channels[identifier] = self
        self._listeners: list = []

    def add_listener(self, listener):
        if listener in self._listeners:
            return;

        self._listeners.append(listener)
        listener.add_listening(self)

    def remove_listener(self, listener):
        self._listeners.remove(listener)
        listener.remove_listening(self)
        print("removed listener")

    async def broadcast(self, json, broadcaster):
        name = broadcaster.get_username()
        json["speaker"] = name
        json["audience"] = self._identifier
        json["type"] = "audio"

        for player in self._listeners:
            if player == broadcaster:
                continue

            await player.send_data(json)



class ProximityAudience(Audience):

    def __init__(self, identifier: str, min_distance: float, max_distance: float):
        super().__init__(identifier)

        self._max_distance = max_distance
        self._min_distance = min_distance

    async def broadcast(self, json, broadcaster):
        name = broadcaster.get_username()
        json["speaker"] = name
        json["audience"] = self._identifier
        json["type"] = "audio"
        json["proximity"] = True

        json["max"] = self._max_distance
        json["min"] = self._min_distance

        max_squared = self._max_distance**2

        for player in self._listeners:
            if player == broadcaster:
                continue

            relative = np.array(broadcaster._location) - np.array(player._location)

            if np.dot(relative, relative) >= max_squared:
                continue

            yaw = np.radians(-player._yaw)
            pitch = np.radians(-player._pitch)

            r_yaw = np.array([
                [np.cos(yaw), 0, np.sin(yaw)],
                [0, 1, 0],
                [-np.sin(yaw), 0, np.cos(yaw)]
            ])
            relative = r_yaw @ relative

            r_pitch = np.array([
                [1, 0, 0],
                [0, np.cos(pitch), -np.sin(pitch)],
                [0, np.sin(pitch), np.cos(pitch)]
            ])
            relative = r_pitch @ relative


            json["x"], json["y"], json["z"] = relative[0], relative[1], relative[2]

            await player.send_data(json)

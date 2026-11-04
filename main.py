import copy
import time

import uvicorn
from fastapi import FastAPI, Request, Response
from starlette.websockets import WebSocket, WebSocketDisconnect
from audience import Audience, ProximityAudience
from player import Player

app = FastAPI()

class Authentication:

    _codes = {}

    @staticmethod
    def from_code(code: str) -> Authentication | None:
        return Authentication._codes.get(code, None)

    def __init__(self, code: str, username: str, expiry: float):
        self._code = code
        self._expiry = expiry
        self._username = username

        Authentication._codes[code] = self
        print("New authentication code:", code)

    def is_valid(self):
        #del Authentication._codes[self._code]

        return self._expiry > time.time()

    def get_username(self):
        return self._username

# Server <-> Website
@app.websocket("/{auth}")
async def voice_endpoint(websocket: WebSocket, auth: str):

    temp = auth
    auth = Authentication.from_code(auth)

    if not auth:
        print("Auth code does not exist!")
        await websocket.close()
        return

    if not auth.is_valid():
        print("Auth code invalid!")
        await websocket.close()
        return

    await websocket.accept()

    player = Player(auth.get_username(), websocket)

    try:
        await websocket.send_json(
            {
                "type": "init",
                "user": auth.get_username(),
            }
        )

        while True:
            data = await websocket.receive_json()

            for audience in player.get_speaking():
                await audience.broadcast(copy.deepcopy(data), player)


    except WebSocketDisconnect:
        print(f"Disconnected {temp}")
        player.remove()



# Server <-> DiamondFire
@app.post("/df/")
async def diamondfire(request: Request, response: Response):

    response.headers["X-Hypercube-Response"] = "true"
    data: list[dict] = await request.json()


    for entry in data:
        command = entry["type"]

        if command != "position": print(command)

        if command == "auth":
            valid_time = time.time() + 30.
            code = entry["code"]
            name = entry["user"]
            Authentication(code, name, valid_time)
        elif command == "position":
            name = entry["user"]
            player = Player.get(name)

            if not player:
                continue

            player._location = entry["x"], entry["y"], entry["z"]
            player._pitch = entry["pitch"]
            player._yaw = -entry["yaw"]

        elif command == "audience":
            identifier = entry["id"]
            proximity = entry.get("proximity", None)

            if Audience.get(identifier): return;

            print(f"Making new Audience: {identifier}")

            if not proximity:
                Audience(identifier)
                continue

            min_distance = proximity.get("min", 0)
            max_distance = proximity.get("max", 16)

            ProximityAudience(identifier, min_distance, max_distance)

        elif command == "speak":
            name = entry["user"]
            audience = entry["audience"]
            speaking = entry["speaking"] != 0

            player = Player.get(name)
            audience = Audience.get(audience)

            if (not player) or (not audience):
                continue

            print("Processing speak packet for:", entry["audience"])

            if speaking:
                player.add_speaker(audience)
            else:
                player.remove_speaker(audience)

        elif command == "listen":
            name = entry["user"]
            audience = entry["audience"]
            listening = entry["listen"] != 0

            player = Player.get(name)
            audience = Audience.get(audience)

            if (not player) or (not audience):
                continue

            print("Processing listen packet for:", entry["audience"])
            print(listening)

            if listening:
                audience.add_listener(player)
                print("add listen")
            else:
                audience.remove_listener(player)
                print('remove listen')







if __name__ == "__main__":
    Authentication("A", "xtreemes", time.time() + 10000.)
    Authentication("B", "BotNumberTwo", time.time() + 10000.)
    Authentication("C", "anjei", time.time() + 10000.)
    Authentication("D", "endersaltz", time.time() + 10000.)

    uvicorn.run(app, host="0.0.0.0", port=3031, access_log=False)
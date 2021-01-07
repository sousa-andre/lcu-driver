from lcu_driver import Connector

connector = Connector()

async def creat_labby(connection):
  custom = {
    "customGameLobby": {
      "configuration": {
        "gameMode": "PRACTICETOOL",
        "gameMutator": "",
        "gameServerRegion": "",
        "mapId": 11, 
        "mutators": {"id": 1}, 
        "spectatorPolicy": "AllAllowed", 
        "teamSize": 5
      },
      "lobbyName": "Name",
      "lobbyPassword": ""
    },
    "isCustom": True
  }
  
  await connection.request('post', '/lol-lobby/v2/lobby', data=custom)


@connector.ready
async def connect(connection):
    print('LCU API is ready to be used.')
    await creat_labby(connection)


connector.start()

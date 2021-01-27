from lcu_driver import Connector
import os, base64

#---------------------------------------------
# Get Summoner Data
#---------------------------------------------
async def get_summonerdata(connection):
  summoner = await connection.request('GET', '/lol-summoner/v1/current-summoner')
  data = await summoner.json()
  print(f'{data["displayName"]} Lv.{data["summonerLevel"]}')

#---------------------------------------------
# Creat Lobby
#---------------------------------------------
async def creat_lobby(connection):
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
      "lobbyName": "PRACTICETOOL",
      "lobbyPassword": ""
    },
    "isCustom": True
  }
  lobby = await connection.request('POST', '/lol-lobby/v2/lobby', data=custom)
  

#---------------------------------------------
# Add team1 Bots by champion ID
#---------------------------------------------
async def add_bot_t1(connection):
 soraka = { "championId": 16, "botDifficulty": "MEDIUM", "teamId": "100"}
 await connection.request('POST', '/lol-lobby/v1/lobby/custom/bots', data=soraka)


#---------------------------------------------
# Add team2 Bots by champion Name
#---------------------------------------------
async def add_bot_t2(connection):
  activedata = await connection.request('GET', '/lol-lobby/v2/lobby/custom/available-bots')
  champions = { bot['name']: bot['id'] for bot in await activedata.json() }
  
  team2 = ["Caitlyn", "Blitzcrank", "Darius", "Morgana", "Lux"]
  
  for name in team2:
    bots = {
      "championId": champions[name],
      "botDifficulty": "MEDIUM",
      "teamId": "200"
    }
    await connection.request('POST', '/lol-lobby/v1/lobby/custom/bots', data=bots)


#---------------------------------------------
# Start
#---------------------------------------------

async def start_game(connection):
    await connection.request('POST', '/lol-lobby/v1/lobby/custom/start-champ-select')


#---------------------------------------------
#  lockfile
#---------------------------------------------

async def get_lockfile(connection):
    path = os.path.join(connection.installation_path.encode('gbk').decode('utf-8'), 'lockfile')
    if os.path.isfile(path):
        file = open(path, 'r')
        text = file.readline().split(':')
        file.close()
        print(f'riot    {text[3]}')
        return text[3]
    return None

#---------------------------------------------
# Websocket Listening
#---------------------------------------------

connector = Connector()

@connector.ready
async def connect(connection): 
  print(connection.address)
  await get_lockfile(connection)
  await get_summonerdata(connection)
  await creat_lobby(connection)
  await add_bot_t1(connection)
  await add_bot_t2(connection)
  await start_game(connection)

@connector.close
async def disconnect(connection):
    print('The client was closed')
    await connector.stop()

@connector.ws.register('/lol-lobby/v2/lobby', event_types=('CREATE',))
async def icon_changed(connection, event):
    print(f'The summoner {event.data["localMember"]["summonerName"]} created a lobby.')

connector.start()

from lcu_driver import Connector

#---------------------------------------------
# Get Summoner Data
#---------------------------------------------
async def get_summoner_data(connection):
  summoner = await connection.request('GET', '/lol-summoner/v1/current-summoner')
  data = await summoner.json()
  print(f"displayName:    {summoner['displayName']}")
  print(f"summonerId:     {summoner['summonerId']}")
  print(f"puuid:          {summoner['puuid']}")
  print("-")

#---------------------------------------------
# Create Lobby
#---------------------------------------------
async def create_lobby(connection):
  custom = {
    'customGameLobby': {
      'configuration': {
        'gameMode': 'PRACTICETOOL',
        'gameMutator': '',
        'gameServerRegion': '',
        'mapId': 11, 
        'mutators': {'id': 1}, 
        'spectatorPolicy': 'AllAllowed', 
        'teamSize': 5
      },
      'lobbyName': 'PRACTICETOOL',
      'lobbyPassword': ''
    },
    'isCustom': True
  }
  await connection.request('POST', '/lol-lobby/v2/lobby', data=custom) 

        
#---------------------------------------------
# Add Team1 Bots By Champion ID
#---------------------------------------------
async def add_bots_team1(connection):
 soraka = { 'championId':16, 'botDifficulty':'EASY', 'teamId':'100' }
 await connection.request('POST', '/lol-lobby/v1/lobby/custom/bots', data=soraka)


#---------------------------------------------
# Add Team2 Bots By Champion Name
#---------------------------------------------
async def add_bots_team2(connection):
  available_bots = await connection.request('GET', '/lol-lobby/v2/lobby/custom/available-bots')
  champions = { bot['name']: bot['id'] for bot in await available_bots.json() }
  
  team2 = ['Caitlyn', 'Blitzcrank', 'Darius', 'Morgana', 'Lux']
  
  for name in team2:
    bot = { 'championId':champions[name], 'botDifficulty':'MEDIUM', 'teamId':'200' }
    await connection.request('POST', '/lol-lobby/v1/lobby/custom/bots', data=bot)


#---------------------------------------------
#  lockfile
#---------------------------------------------
async def get_lockfile(connection):
    import os
    path = os.path.join(connection.installation_path.encode('gbk').decode('utf-8'), 'lockfile')
    if os.path.isfile(path):
        file = open(path, 'r')
        text = file.readline().split(':')
        file.close()
        print(connection.address)
        print(f'riot    {text[3]}')
        return text[3]
    return None

#---------------------------------------------
# Websocket Listening
#---------------------------------------------
 
connector = Connector()

@connector.ready
async def connect(connection): 
  await get_summoner_data(connection)
  await get_lockfile(connection)
  await create_lobby(connection)
  await add_bots_team1(connection)
  await add_bots_team2(connection)

@connector.close
async def disconnect(connection):
    print('The client was closed')
    await connector.stop()


@connector.ws.register('/lol-lobby/v2/lobby', event_types=('CREATE',))
async def lobby_created(connection, event):
    print(f"The summoner {event.data['localMember']['summonerName']} created a lobby.")


#---------------------------------------------
# main
#---------------------------------------------
connector.start()

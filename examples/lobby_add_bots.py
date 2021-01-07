from lcu_driver import Connector
connector = Connector()

@connector.ready
async def connect(connection):
	await add_bots(connection)
  
async def add_bots(connection):
	champions = [122, 86, 1, 51, 25]
	for id in champions:
		bots = {
			"championId": id,
			"botDifficulty": "MEDIUM",
			"teamId": "200"
		}
		await connection.request('post', '/lol-lobby/v1/lobby/custom/bots', data=bots)

connector.start()

from lcu_driver import Connector
connector = Connector()

@connector.ready
async def connect(connection):
	await get_active_bots(connection)

async def get_active_bots(connection):
	data = await connection.request('GET', '/lol-lobby/v2/lobby/custom/available-bots')
	champions = { bots['name']: bots['id'] for bots in await data.json() }
	print(champions)
 
connector.start()

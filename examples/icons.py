from random import randint

from lcu_driver import Connector

connector = Connector()


async def set_random_icon(connection):
    # random number of a chinese icon
    random_number = randint(50, 78)

    # make the request to set the icon
    icon = await connection.request('put', '/lol-summoner/v1/current-summoner/icon',
                                    data={'profileIconId': random_number})

    # if HTTP status code is 201 the icon was applied successfully
    if icon.status == 201:
        print(f'Chinese icon number {random_number} was set correctly.')
    else:
        print('Unknown problem, the icon was not set.')


# fired when LCU API is ready to be used
@connector.ready
async def connect(connection):
    print('LCU API is ready to be used.')

    # check if the user is already logged into his account
    summoner = await connection.request('get', '/lol-summoner/v1/current-summoner')
    if summoner.status != 200:
        print('Please login into your account to change your icon and restart the script...')
    else:
        print('Setting new icon...')
        await set_random_icon(connection)


# fired when League Client is closed (or disconnected from websocket)
@connector.close
async def disconnect(_):
    print('The client have been closed!')

# starts the connector
connector.start()

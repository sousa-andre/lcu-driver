from lcu_driver import Connector

connector = Connector()


# fired when LCU API is ready to be used
@connector.ready
async def connect(connection):
    print('LCU API is ready to be used.')


# fired when League Client is closed (or disconnected from websocket)
@connector.close
async def disconnect(_):
    print('The client have been closed!')
    await connector.stop()


# subscribe to '/lol-summoner/v1/current-summoner' endpoint for the UPDATE event
# when an update to the user happen (e.g. name change, profile icon change, level, ...) the function will be called
@connector.ws.register('/lol-summoner/v1/current-summoner', event_types=('UPDATE',))
async def icon_changed(connection, event):
    print(f'The summoner {event.data["displayName"]} was updated.')


# starts the connector
connector.start()

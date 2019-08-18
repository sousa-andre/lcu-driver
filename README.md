## lcu-driver

Python interface for LCU API. Only support Windows platform. Inspired in [lcu-connector](https://github.com/Pupix/lcu-connector)

## Download
 - `pip install lcu-driver`

## Code example
##### Change to a random chinese icon every time your run the application.
```python
from json import dumps
from random import randint

from lcu_driver import Connector


connector = Connector()


async def set_random_icon():
    # random number of a chinese icon
    random_number = randint(50, 78)

    # make the request to set the icon
    icon = await connector.request('put', '/lol-summoner/v1/current-summoner/icon',
                                   data=dumps({'profileIconId': random_number}))

    # if HTTP status code is 201 the icon was applied successfully
    if icon.status == 201:
        print(f'Chinese icon number {random_number} was set correctly.')
    else:
        print('Unknown problem, the icon was not set.')

# fired when LCU API is ready to be used
@connector.event
async def connect():
    print('LCU API is ready to be used.')

    # check if the user is already logged into his account
    summoner = await connector.request('get', '/lol-summoner/v1/current-summoner')
    if summoner.status == 200:
        data = await summoner.json()

        # calls login method and update login.left_calls to 0
        # when login.left_calls is 0 the function can't be fired any more neither by websocket nor manually
        await login(None, None, data)

    else:
        print('Please login into your account to change your icon...')


# fired when League Client is closed (or disconnected from websocket)
@connector.event
async def disconnect():
    print('The client have been closed!')

# subscribe to the login websocket event, and calls the function only one time
@connector.ws_events(['/lol-summoner/v1/current-summoner'], event_types=['Update'],
                     max_calls=1)
async def login(typ, uri, data):
    print('Logged as', data['displayName'])
    await set_random_icon()


# opens websocket connection (may be used to wait until the client is closed)
connector.listen()
# starts everything
connector.start()
```

## Classes and methods
### ***class* Connector**
 - #### \_\_init\_\_(self, *, loop=None)
    - **loop**

### Properties
 - #### pid
    Process Id.
 - #### protocols
    Tuple of allowed protocols.
 - #### port
 - #### auth_key
 - #### installation_path
 - #### address
 - #### ws_address
 
### Methods
 - #### start()
    Start the driver.

 - #### listen()
    Keep connected until client closes. (open websocket connection).
    
  - #### *<coroutine>* stop_ws()
    Gracefully stops the websocket loop.
 
 - #### *coroutine* request(method: str, endpoint: str, **kwargs)
    - **method** - HTTP verb.
    - **endpoint** - Resource URL without protocol and host name.
    - **\*\*kwargs**
        - [**<aiohttp.ClientSession>.request**](https://github.com/aio-libs/aiohttp/blob/master/aiohttp/client.py#L279) - function arguments
        - **path** - Alias to *str.format()*
  
 - #### ws_events(endpoints: list, *, event_types: list, max_calls=-1)
    - **endpoints** - List of URIs.
    - **event_types** - List of events types (Create, Update or Delete).
    - **max_calls** - Maximum times an event function can be called either by the websocket or manually. Set it to negative numbers to remove the limit.

### Built-in library events
 - #### connect
    Fired when LCU API starts.
 - #### disconnect
    Fired when the client is closed.

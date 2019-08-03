## lcu-driver

Python interface for LCU API. Only support Windows platform. Inspired in [lcu-connector](https://github.com/Pupix/lcu-connector)

## Download
 - `pip install lcu-driver`
 
 - `pip install git+https://github.com/sousa-andre/lcu-driver.git` (development version)
 
## Code example

Subclassing Connector:
```python
import lcu_driver


class MyConnector(lcu_driver.Connector):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    async def connect(self):
        response = await self.request('get', '/lol-summoner/v1/current-summoner')
        if response.status == 200:
            data = await response.json()
            print('You are already logged as {}.'.format(data['displayName']))
        else:
            print('You\'re not logged.')

    async def disconnect(self):
        print('The client has been closed!')


con = MyConnector()
con.start()
```

Using decorators:
```python
import lcu_driver


con = lcu_driver.Connector()


@con.event
async def connect():
    response = await con.request('get', '/lol-summoner/v1/current-summoner')
    if response.status == 200:
        data = await response.json()
        print('You are logged as {}.'.format(data['displayName']))
    else:
        print('You\'re not logged.')


@con.event
async def disconnect():
    print('The client has been closed!')


con.start()
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
 - #### wait()
    Keep connected until client closes. (open websocket connection).
 - #### start()
    Start looking for client using the settings defined in the constructor.
 - #### request(method: str, endpoint: str, **kwargs)
    - **method** - HTTP verb
    - **endpoint** - Resource URL without protocol and host name.
    - **\*\*kwargs**
        - [**<aiohttp.ClientSession>.request**](https://github.com/aio-libs/aiohttp/blob/master/aiohttp/client.py#L279) - function arguments
        - **path** - Alias to *str.format()*
    
### Events
 - #### connect
    Fired when LCU API start.
 - #### disconnect
    Fired when the client is closed.
    

 
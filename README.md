## lcu-driver

Python interface for LCU API. Only support Windows platform. Inspired in [lcu-connector](https://github.com/Pupix/lcu-connector)

## Download

 - `pip install lcu-driver`
 
 - `pip install git+https://github.com/sousa-andre/lcu-driver.git`
 
## Code example

Subclassing Connector:

```python
import lcu_driver


class MyConnector(lcu_driver.Connector):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.subscribe_event('OnJsonApiEvent_lol-summoner_v1_current-summoner')

    @staticmethod
    def connect(process, api):
        con.subscribe_event('OnJsonApiEvent_lol-summoner_v1_current-summoner')
    
        response = api.fetch('get', '/lol-summoner/v1/current-summoner')
        if response.status_code == 200:
            data = response.json()
            print('You are already logged as {}.'.format(data['displayName']))
        else:
            print('The client is already opened, please login now.')

    @staticmethod
    def disconnect():
        print('The client has been closed!')

    @staticmethod
    def message(data):
        if 'accountId' in data['data']:
            print('Logging in as {}.'.format(data['data']['displayName']))


con = MyConnector()
con.start()
```

Using decorators:

```python
import lcu_driver


con = lcu_driver.Connector()


@con.event
def connect(process, api):
    response = api.fetch('get', '/lol-summoner/v1/current-summoner')
    if response.status_code == 200:
        data = response.json()
        print('You are already logged as {}.'.format(data['displayName']))
    else:
        print('The client is already opened, please login now.')


@con.event
def disconnect():
    print('The client has been closed!')


@con.event
def message(data):
    if 'accountId' in data['data']:
        print('Logging in as {}.'.format(data['data']['displayName']))


con.start()

```

## Classes and methods
### ***class* Connector**
 - #### \_\_init\_\_(keep_running: bool = False, wait_for_client: bool = True, connect_via_websocket: bool = False)
    - **keep_running** - After disconnect will keep looking for other clients.
    - **wait_for_client** - Block execution until find a running client.
    - **connect_via_websocket** - Start websocket connection.
 
### Methods
 
 - #### subscribe_event(*events: str)
    Entitle the events to be subscribed by the websocket connection.
    
 - #### start()
    Start looking for client using the settings defined in the constructor.
    
### Events
 - #### connect
    ##### \<func\>(process: ProcessDTO, api: APIDTO)
    Fired when LCU API start.
 - #### disconnect
    ##### \<func\>()
    Fired when the client is closed.
 - #### message
    ##### \<func\>(data: dict)
    Fired when a websocket event occurs.
    

### ***class* ProcessDTO**
 - #### \_\_init\_\_(**kwargs)
    
### ***class* APIDTO**
 - #### \_\_init\_\_(**kwargs)
 
### Methods

 - #### fetch(method: str, endpoint: str, **kwargs) -> requests.request
    - **method** - HTTP verb
    - **endpoint** - Resource URL without protocol and host name.
    - **\*\*kwargs**
        - [**request.request**](https://2.python-requests.org/en/master/_modules/requests/api/#request) - function arguments
        - **path** - Alias to *str.format()*
 
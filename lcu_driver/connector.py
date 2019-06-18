import threading
import subprocess
import base64
import json
import asyncio
import sys
import typing

import requests
import aiohttp

from .exceptions import PlatformNotSupported


requests.packages.urllib3.disable_warnings()

if sys.platform != 'win32':
    raise PlatformNotSupported('Your OS is not currently supported.')


def _get_process(process: str) -> typing.Dict[str, str]:
    output = subprocess.getoutput("WMIC PROCESS WHERE name='{}' GET commandline".format(process))
    if output[:11] != 'CommandLine':
        return {}

    processes = [k.strip() for k in output[output.find('"'):].strip().split('\n\n')]

    parsed_processes = []
    for num, process in enumerate(processes):
        parsed_processes.append({})
        inside = False
        start = -1
        for pos, char in enumerate(process):
            if char == '"':
                if inside:
                    inside = False
                    if start == 1:
                        parsed_processes[num]['--executable-path'] = processes[num][start:pos]
                    else:
                        key, *value = processes[num][start:pos].split('=')
                        parsed_processes[num][key] = value[0] if len(value) > 0 else None
                elif not inside:
                    inside = True
                    start = pos + 1
    return parsed_processes[-1]


def _instantiate_from_process(parsed_process:  typing.Dict[str, str]):
    authentication = base64.b64encode(b'riot:' + parsed_process['--remoting-auth-token'].
                                      encode('utf-8')).decode('utf-8')

    while True:
        try:
            requests.get('https://127.0.0.1:' + parsed_process['--app-port'],
                         headers={'Authorization': 'Basic ' + authentication}, verify=False)
            break
        except requests.exceptions.ConnectionError:
            pass

    return (
        ProcessDTO(
            pid=parsed_process['--app-pid'],
            install_directory=parsed_process['--install-directory']
        ), APIDTO(
            protocol='https',
            port=parsed_process['--app-port'],
            username='riot',
            password=parsed_process['--remoting-auth-token'],
            credentials={'Authorization': 'Basic ' + authentication}
        )
    )


class DTO:
    def __init__(self, **kwargs):
        self.__dict__ = kwargs

    def __repr__(self) -> str:
        return self.__dict__.__str__()

    def __str__(self) -> str:
        return self.__repr__()


class ProcessDTO(DTO):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)


class APIDTO(DTO):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

    @property
    def address(self) -> str:
        return '{}://{}:{}'.format(self.protocol, '127.0.0.1', self.port)

    def fetch(self, method: str, endpoint: str, **kwargs) -> requests.request:
        url = self.address + endpoint

        if 'headers' in kwargs:
            kwargs['headers'].update({'Content-Type': 'application/json'})
        else:
            kwargs['headers'] = {'Content-Type': 'application/json'}

        kwargs['headers'].update(self.credentials)
        kwargs['headers'].update({'Accept': 'application/json'})

        if 'path' in kwargs:
            url = url.format(**kwargs['path'])
            kwargs.pop('path')

        return requests.request(method, url, **kwargs, verify=False)


class Connector:
    def __init__(self, *, keep_running: bool = False, wait_for_client: bool = True,
                 connect_via_websocket: bool = False):
        self._keep_running = keep_running
        self._block_until_open = wait_for_client
        self._connect_via_websocket = connect_via_websocket
        self._events_to_subscribe = []

    def _run_event(self, event: str, *args, **kwargs):
        if hasattr(self, event):
            thread = threading.Thread(target=getattr(self, event), args=(*args, ), kwargs={**kwargs, }, daemon=True)
            thread.start()

    def event(self, func) -> None:
        """
        Adds the method to the object.
        """
        setattr(self, func.__name__, func)

    @staticmethod
    def _wait_for_client_to_open() -> None:
        process = _get_process('LeagueClientUx.exe')
        while not process:
            process = _get_process('LeagueClientUx.exe')

    async def _connect_ws_coroutine(self, url: str, credentials: typing.Dict[str, str]) -> None:
        session = aiohttp.ClientSession()
        ws = await session.ws_connect(url, headers=credentials, ssl=False)
        for event in self._events_to_subscribe:
            await ws.send_json([5, event])

        while True:
            event = await ws.receive()
            if event.data:
                self._run_event('message', json.loads(event.data)[2])

    def _connect_ws(self, api: APIDTO) -> None:
        loop = asyncio.new_event_loop()
        asyncio.set_event_loop(loop)
        loop.run_until_complete(self._connect_ws_coroutine(
            url='wss://127.0.0.1:' + api.port,
            credentials=api.credentials
        ))

    def subscribe_event(self, *events: str) -> None:
        """
        Set the events to be subscribed by the websocket connection.
        """
        self._connect_via_websocket = True
        for event in events:
            self._events_to_subscribe.append(event)

    def start(self) -> None:
        """
        Start looking for LeagueClientUx.exe.
        """
        try:
            if self._block_until_open:
                self._wait_for_client_to_open()

            process = _get_process('LeagueClientUx.exe')
            if process:
                process, api = _instantiate_from_process(process)
                self._run_event('connect', process, api)
                if self._connect_via_websocket:
                    thread = threading.Thread(target=self._connect_ws, args=(api, ), daemon=True)
                    thread.start()

                while process:
                    process = _get_process('LeagueClientUx.exe')
                self._run_event('disconnect')

                if self._keep_running:
                    self.start()
        except KeyboardInterrupt:
            exit()

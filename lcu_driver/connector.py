import asyncio
from sys import platform
from typing import Optional, Dict, Tuple

import aiohttp
from psutil import process_iter, Process

from .exceptions import CoroutineExpected, EarlyPerform, IntegrityError, PlatformNotSupported


if platform != 'win32':
    raise PlatformNotSupported('OS not currently supported')


class Connector:
    def __init__(self, *, loop=None):
        self.loop = loop or asyncio.get_event_loop()
        self._session = None

        self._pid = None
        self._protocols = None
        self._port = None
        self._auth_key = None
        self._installation_path = None

        self._ws = None
        self._initialize_websocket = False

        self._disconnected_call = False

    @property
    def pid(self) -> int:
        return self._pid

    @property
    def protocols(self) -> Optional[Tuple[str]]:
        return self._protocols

    @property
    def port(self) -> Optional[int]:
        return self._port

    @property
    def auth_key(self) -> Optional[str]:
        return self._auth_key

    @property
    def installation_path(self) -> Optional[str]:
        return self._installation_path

    @property
    def address(self) -> str:
        if self._session is None:
            raise EarlyPerform('address property called with uninitialized API')
        return f'{self._protocols[0]}://127.0.0.1:{self._port}'

    @property
    def ws_address(self) -> str:
        if self._session is None:
            raise EarlyPerform('ws_address property called with uninitialized API')
        return f'{self._protocols[1]}://127.0.0.1:{self._port}'

    async def request(self, method: str, endpoint: str, **kwargs):
        if self._session is None:
            raise EarlyPerform('request tried to be made with uninitialized API')

        url = f'{self.address}{endpoint}'
        if 'path' in kwargs:
            url = url.format(**kwargs['path'])
            kwargs.pop('path')

        try:
            return await self._session.request(method, url, **kwargs, verify_ssl=False)
        except aiohttp.client_exceptions.ClientConnectorError:
            if not self._disconnected_call:
                self._disconnected_call = True
                await self._run_event('disconnect')

    async def _run_event(self, event: str, *args, **kwargs) -> None:
        if hasattr(self, event):
            await getattr(self, event)(*args, **kwargs)

    def event(self, coro) -> None:
        if asyncio.iscoroutinefunction(coro):
            if not hasattr(self, coro.__name__):
                setattr(self, coro.__name__, coro)
            else:
                pass
        else:
            raise CoroutineExpected(f'replace "def {coro.__name__}" by "async def {coro.__name__}"')

    @staticmethod
    def _parse_cmdline_args(cmdline_args) -> Dict[str, str]:
        cmdline_args_parsed = {}
        for cmdline_arg in cmdline_args:
            if '=' in cmdline_arg:
                key, value = cmdline_arg[2:].split('=')
                cmdline_args_parsed[key] = value
        return cmdline_args_parsed

    @staticmethod
    def _return_process(process_name: str) -> Optional[Process]:
        for process in process_iter():
            if process.name() == process_name:
                return process
        return None

    @staticmethod
    async def _return_ux_process_when_available() -> Process:
        process = None
        while process is None:
            process = Connector._return_process('LeagueClientUx.exe')
        return process

    def _clean_attributes(self):
        self._pid = None
        self._protocols = None
        self._port = None
        self._auth_key = None
        self._installation_path = None

        self._ws = None

    async def _start_websocket(self) -> None:
        self._ws = await self._session.ws_connect(self.ws_address, ssl=False)
        async for _ in self._ws:
            pass
        if not self._disconnected_call:
            self._disconnected_call = True
            await self._run_event('disconnect')

    async def _load_api_data(self):
        process = await self._return_ux_process_when_available()
        process_args = Connector._parse_cmdline_args(process.cmdline())

        self._protocols = ('https', 'wss')
        self._port = int(process_args['app-port'])
        self._pid = int(process_args['app-pid'])
        self._auth_key = process_args['remoting-auth-token']
        self._installation_path = process_args['install-directory']
        self._session = aiohttp.ClientSession(auth=aiohttp.BasicAuth('riot', self._auth_key),
                                              headers={'Content-Type': 'application/json',
                                                       'Accept': 'application/json'})

    async def _wait_api_ready(self) -> None:
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'{self.address}/riotclient/region-locale', verify_ssl=False) as _:
                        break
            except aiohttp.client_exceptions.ClientConnectorError:
                pass

    async def _start_all(self) -> None:
        await self._load_api_data()
        await self._wait_api_ready()

        if self._initialize_websocket:
            await asyncio.gather(self._run_event('connect'), self._start_websocket())
        else:
            await self._run_event('connect')
        self._clean_attributes()
        await self._session.close()

    def start(self) -> None:
        self.loop.run_until_complete(self._start_all())

    def wait(self) -> None:
        self._initialize_websocket = True

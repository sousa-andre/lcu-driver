import asyncio
import logging
from json import loads, JSONDecodeError, dumps
from typing import Union, Optional, Tuple

import aiohttp
from aiohttp import ClientConnectorError
from psutil import Process

from .exceptions import EarlyPerform
from .utils import parse_cmdline_args

logger = logging.getLogger('lcu-driver')


class Connection:
    """Connection

    :param connector: Connector instance where connection should look for events handlers
    :type connector: :py:obj:`lcu_driver.connector.Connector`
    :param process_or_string: :py:obj:`psutil.Process` object or lockfile string
    :type process_or_string: :py:obj:`psutil.Process` or string
    """
    def __init__(self, connector, process_or_string: Union[Process, str]):
        self._connector = connector
        self._ws = None
        self.locals = {}
        self.closed = False
        self.session = None

        self._headers = {
            'Content-Type': 'application/json',
            'Accept': 'application/json'
        }

        self._protocols = ('https', 'wss',)
        if isinstance(process_or_string, Process):
            process_args = parse_cmdline_args(process_or_string.cmdline())

            self._lcu_pid = process_or_string.pid
            self._pid = int(process_args['app-pid'])
            self._port = int(process_args['app-port'])
            self._auth_key = process_args['remoting-auth-token']
            self._installation_path = process_args['install-directory']

        elif isinstance(process_or_string, str):
            lockfile_parts = process_or_string.split(':')

            self._lcu_pid = int(lockfile_parts[0])
            self._pid = int(lockfile_parts[1])
            self._port = int(lockfile_parts[2])
            self._auth_key = lockfile_parts[3]
            self._installation_path = None

    async def init(self):
        """Initialize the connection. It's called by the connector when it finds a connection

        :rtype: none
        """
        self.session = aiohttp.ClientSession(auth=aiohttp.BasicAuth('riot', self._auth_key), headers=self._headers)

        setattr(self, 'request', self.request)

        self._connector.register_connection(self)
        tasks = [asyncio.create_task(self._connector.run_event('open', self))]
        await self._wait_api_ready()

        tasks.append(asyncio.create_task(self._connector.run_event('ready', self)))

        try:
            if self._connector.should_run_ws:
                await self.run_ws()
        except ClientConnectorError:
            logger.info('Client closed unexpectedly')
        finally:
            await asyncio.gather(*tasks)
            await self._close()

    async def _close(self):
        self.closed = True
        await self._connector.run_event('close', self)
        self._connector.unregister_connection(self._lcu_pid)
        await self.session.close()

    @property
    def pid(self) -> int:
        """League Client Process Id

        :rtype: int
        """
        return self._pid

    @property
    def protocols(self) -> Tuple[str, str]:
        """Return a tuple with League Client API supported protocols

        :rtype: tuple(str, str)
        """
        return self._protocols

    @property
    def port(self) -> int:
        """Return the League Client API current connection port

        :rtype: int
        """
        return self._port

    @property
    def auth_key(self) -> Optional[str]:
        """Return League Client API current connection password

        :rtype: str or None
        """
        return self._auth_key

    @property
    def installation_path(self) -> Optional[str]:
        """Return League Client installation path

        :return: optional[str]
        """
        return self._installation_path

    @property
    def address(self):
        """Return HTTPS Base URL

        :return: str
        """
        return f'{self._protocols[0]}://127.0.0.1:{self._port}'

    @property
    def ws_address(self):
        """Return Websocket Base URL

        :return: str
        """
        return f'{self._protocols[1]}://127.0.0.1:{self._port}'

    def _produce_url(self, endpoint: str, **kwargs):
        """Return the URL to be requested."""
        if self._pid is None:
            raise EarlyPerform('request tried to be made with uninitialized or closed API')

        url = f'{self.address}{endpoint}'
        if 'path' in kwargs:
            url = url.format(**kwargs['path'])
            kwargs.pop('path')
        return url

    async def request(self, method: str, endpoint: str, **kwargs):
        """Run an HTTP request against the API

        :param method: HTTP method :type method: str :param endpoint: Request Endpoint :type endpoint: str :param
        kwargs: Arguments for `aiohttp.Request
        <https://docs.aiohttp.org/en/stable/client_reference.html#aiohttp.request>`_. The **data** keyworded argument
        will be JSON encoded automatically.
        """
        url = self._produce_url(endpoint, **kwargs)
        if kwargs.get('data'):
            kwargs['data'] = dumps(kwargs['data'])
        return await self.session.request(method, url, verify_ssl=False, **kwargs)

    async def run_ws(self):
        """Start the websoocket connection. This is responsible to raise Connector close event and
        handling the websocket events.

        :return: None
        """
        local_session = aiohttp.ClientSession(auth=aiohttp.BasicAuth('riot', self._auth_key),
                                              headers={'Content-Type': 'application/json',
                                                       'Accept': 'application/json'})
        self._ws = await local_session.ws_connect(self.ws_address, ssl=False)
        await self._ws.send_json([5, 'OnJsonApiEvent'])
        _ = await self._ws.receive()

        while self.closed == False:
            msg = await self._ws.receive()
            logger.debug('Websocket frame received')

            if msg.type == aiohttp.WSMsgType.TEXT:
                try:
                    data = loads(msg.data)[2]
                    self._connector.ws.match_event(self._connector, self, data)
                except JSONDecodeError:
                    logger.warning('Error decoding the following JSON: ', msg.data)

            elif msg.type == aiohttp.WSMsgType.CLOSED:
                break
        await self._ws.close()
        await local_session.close()

    async def _wait_api_ready(self) -> None:
        while True:
            try:
                async with aiohttp.ClientSession() as session:
                    async with session.get(f'{self.address}/riotclient/region-locale', verify_ssl=False) as _:
                        break
            except aiohttp.client_exceptions.ClientConnectorError:
                pass

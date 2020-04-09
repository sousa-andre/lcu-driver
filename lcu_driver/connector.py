import asyncio
import logging
from abc import ABC
from sys import platform
from typing import Union

from psutil import Process

from .connection import Connection
from .events.managers import ConnectorEventManager, WebsocketEventManager
from .utils import _return_ux_process_when_available

logger = logging.getLogger('lcu-driver')


class BaseConnector(ConnectorEventManager):
    def __init__(self, loop=None):
        super().__init__()
        self.loop = loop or asyncio.get_event_loop()
        self.ws = WebsocketEventManager()
        self.connection = None

    def create_connection(self, process_or_string: Union[Process, str]):
        """Creates a connection and saves a reference to it"""
        connection = Connection(self, process_or_string)
        self.connection = connection

    def remove_connection(self):
        """Cancel the connection"""
        self.connection = None


class Connector(BaseConnector):
    def __init__(self, *, loop=None):
        super().__init__(loop)
        self._repeat_flag = True

    def start(self) -> None:
        """Starts the connector. This method should be overridden if different behavior is required.

        :rtype: None
        """
        try:
            def wrapper():
                connection = _return_ux_process_when_available()
                self.create_connection(connection)
                self.loop.run_until_complete(self.connection.init())

                if self._repeat_flag and len(self.ws.registered_uris) > 0:
                    logger.debug('Repeat flag=True. Looking for new clients.')
                    wrapper()

            wrapper()
        except KeyboardInterrupt:
            logger.info('Event loop interrupted by keyboard')

    async def stop(self) -> None:
        """Flag the connector to don't look for more clients once the connection finishes his job.

        :rtype: None
        """
        self._repeat_flag = False

import asyncio
import logging
import time
from abc import ABC, abstractmethod

from .connection import Connection
from .events.managers import ConnectorEventManager, WebsocketEventManager
from .utils import _return_ux_process

logger = logging.getLogger('lcu-driver')


class BaseConnector(ConnectorEventManager, ABC):
    def __init__(self, loop=None):
        super().__init__()
        self.loop = loop or asyncio.get_event_loop()
        self.ws = WebsocketEventManager()

    @abstractmethod
    def register_connection(self, connection: Connection):
        """Creates a connection and saves a reference to it"""
        pass

    @abstractmethod
    def unregister_connection(self, lcu_pid):
        """Cancel the connection"""
        pass

    @property
    def should_run_ws(self) -> bool:
        return True


class Connector(BaseConnector):
    def __init__(self, *, loop=None):
        super().__init__(loop)
        self._repeat_flag = True
        self.connection = None

    def register_connection(self, connection):
        self.connection = connection

    def unregister_connection(self, _):
        self.connection = None

    @property
    def should_run_ws(self) -> bool:
        return len(self.ws.registered_uris) > 0

    def start(self) -> None:
        """Starts the connector. This method should be overridden if different behavior is required.

        :rtype: None
        """
        try:
            def wrapper():
                process = next(_return_ux_process(), None)
                while not process:
                    process = next(_return_ux_process(), None)
                    time.sleep(0.5)

                connection = Connection(self, process)
                self.register_connection(connection)
                self.loop.run_until_complete(connection.init())

                if self._repeat_flag and len(self.ws.registered_uris) > 0:
                    logger.debug('Repeat flag=True. Looking for new clients.')
                    wrapper()

            wrapper()
        except KeyboardInterrupt:
            logger.info('Event loop interrupted by keyboard')
        self.loop.close()

    async def stop(self) -> None:
        """Flag the connector to don't look for more clients once the connection finishes his job.

        :rtype: None
        """
        self._repeat_flag = False
        if self.connection is not None:
            await self.connection._close()


class MultipleClientConnector(BaseConnector):
    def __init__(self, *, loop=None):
        super().__init__(loop=loop)
        self.connections = []

    def register_connection(self, connection):
        self.connections.append(connection)

    def unregister_connection(self, lcu_pid):
        for index, connection in enumerate(self.connections):
            if connection.pid == lcu_pid:
                del connection[index]

    @property
    def should_run_ws(self) -> bool:
        return True

    def _process_was_initialized(self, non_initialized_connection):
        for connection in self.connections:
            if non_initialized_connection.pid == connection.pid:
                return True
        return False

    async def _astart(self):
        tasks = []
        try:
            while True:
                process_iter = _return_ux_process()

                process = next(process_iter, None)
                while process:
                    connection = Connection(self, process)
                    if not self._process_was_initialized(connection):
                        tasks.append(asyncio.create_task(connection.init()))

                    process = next(process_iter, None)
                await asyncio.sleep(0.5)

        except KeyboardInterrupt:
            logger.info('Event loop interrupted by keyboard')
        finally:
            await asyncio.gather(*tasks)

    def start(self) -> None:
        self.loop.run_until_complete(self._astart())

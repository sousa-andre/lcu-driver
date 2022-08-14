import asyncio
import logging
from abc import ABC, abstractmethod

from lcu_driver.connection.connection import Connection
from lcu_driver.connection.connection_options import get_connection_options_from_ux
from lcu_driver.events.managers import ConnectorEventManager, WebsocketEventManager
from lcu_driver.utils import _return_ux_process

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
    def register_connection(self, connection: Connection):
        pass

    def unregister_connection(self, lcu_pid):
        pass

    def __init__(self, *, loop=None):
        super().__init__(loop)
        self._keep_searching_for_clients = True
        self.__first_client_found = True
        self.loop = loop or asyncio.get_event_loop()
        self.ws = WebsocketEventManager()

    @property
    def should_run_ws(self) -> bool:
        return len(self.ws.registered_uris) > 0

    async def _a_start(self) -> None:
        """Starts the connector. This method should be overridden if different behavior is required.

        :rtype: None
        """
        try:
            while self._keep_searching_for_clients:
                connection_opts = await get_connection_options_from_ux()
                if connection_opts is not None:
                    connection = Connection(self, connection_opts)
                    await connection.init()

        except KeyboardInterrupt:
            logger.info('Event loop interrupted by keyboard')

    def start(self):
        self.loop.run_until_complete(self._a_start())

    async def stop_search(self) -> None:
        """Flag the connector to don't look for more clients once the connection finishes his job.

        :rtype: None
        """
        self._keep_searching_for_clients = False


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

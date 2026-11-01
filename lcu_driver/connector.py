import asyncio
import logging
import time
from abc import ABC, abstractmethod
from psutil import Process # Type annotation only

from .connection import Connection
from .events.managers import ConnectorEventManager, WebsocketEventManager
from .utils import _return_ux_process
from .exceptions import NoClientUxDetected # Handles one case of the number of Client Ux processes

logger = logging.getLogger('lcu-driver')

def chooseClient(processList: list[Process]): # Allows users to select one running Ux Client
    if isinstance(processList, list) and all(map(lambda x: isinstance(x, Process), processList)):
        if len(processList) == 0:
            raise NoClientUxDetected()
        elif len(processList) == 1:
            process = processList[0]
        else:
            print('Multiple Ux Clients are detected. Please select one process to continue: (Submit "0" to exit.)')
            # Optimize the prompt layout by formatting each column's width
            indexWidth: int = max(map(lambda x: len(str(x + 1)), range(len(processList)))) + 2
            pidWidth: int = max(map(lambda x: len(str(x.pid)), processList)) + 2
            statusWidth: int = max(map(lambda x: len(str(x.status())), processList)) + 2
            createTimeWidth: int = max(map(lambda x: len(str(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(x.create_time())))), processList)) + 2
            filePathWidth: int = max(map(lambda x: len(str(x.exe())), processList)) + 2
            print("{0:^{5}}{1:^{6}}{2:^{7}}{3:^{8}}{4:^{9}}".format("No.", "pid", "status", "createTime", "filePath", indexWidth, pidWidth, statusWidth, createTimeWidth, filePathWidth))
            latest_index: int = 0 # The index of the process with the latest creation time
            max_procCreateTime: str = "" # An intermediate variable to store the latest creation time. It obeys one-to-one correspondence with the integer timestamp, so comparisons can be made on it
            for i in range(len(processList)):
                process = processList[i]
                procId: int = process.pid
                procStatus: str = process.status() # Based on the status, this table may only display the running processes in a future commit
                procCreateTime: str = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(process.create_time()))
                procFilePath: str = process.exe()
                print("{0:^{5}}{1:^{6}}{2:^{7}}{3:^{8}}{4:^{9}}".format(i + 1, procId, procStatus, procCreateTime, procFilePath, indexWidth, pidWidth, statusWidth, createTimeWidth, filePathWidth))
                if max_procCreateTime < procCreateTime:
                    max_procCreateTime = procCreateTime
                    latest_index = i
            while True:
                processIndex_str: str = input()
                if processIndex_str == "": # Enter nothing to select the default option
                    processIndex: int = latest_index
                    break
                if processIndex_str == "0":
                    exit(0)
                elif processIndex_str in set(map(str, range(1, len(processList) + 1))):
                    processIndex = int(processIndex_str) - 1
                    break
                else:
                    print("Please input an integer between 1 and %d." %(len(processList)))
            process = processList[processIndex]
        return process
    else:
        raise TypeError('invalid type of parameter "processList". Pass a list of Process objects instead')

class BaseConnector(ConnectorEventManager, ABC):
    def __init__(self, loop=None):
        super().__init__()
        if loop is not None:
            self.loop = loop
        else:
            try:
                self.loop = asyncio.get_event_loop()
            except RuntimeError:
                self.loop = asyncio.new_event_loop()
                asyncio.set_event_loop(self.loop)
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
                processList: list[Process] = _return_ux_process()
                process = chooseClient(processList)
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
                processList: list[Process] = _return_ux_process()
                for process in processList:
                    connection = Connection(self, process)
                    if not self._process_was_initialized(connection):
                        tasks.append(asyncio.create_task(connection.init()))
                await asyncio.sleep(0.5)

        except KeyboardInterrupt:
            logger.info('Event loop interrupted by keyboard')
        finally:
            await asyncio.gather(*tasks)

    def start(self) -> None:
        self.loop.run_until_complete(self._astart())

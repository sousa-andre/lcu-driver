import asyncio
import logging
import time
import unicodedata
from wcwidth import wcswidth
from abc import ABC, abstractmethod

from .connection import Connection
from .events.managers import ConnectorEventManager, WebsocketEventManager
from .exceptions import NoLeagueClientDetected
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
            def count_nonASCII(s: str): #统计一个字符串中占用命令行2个宽度单位的字符个数（Count the number of characters that take up 2 width unit in CMD）
                return sum([unicodedata.east_asian_width(character) in ("F", "W") for character in list(str(s))])
            
            def wrapper():
                process_iter = []
                retry = 0
                while retry < 10: #默认一台机器上运行不超过10个客户端。主要是想要达到修改库文件之前立刻就能进入正式程序的效果，特别是当实际上只有一个客户端在运行时（Basically, a device can't run more than 10 League Clients. The reason for setting this standard so small is to achieve the immediate connection to LeagueClientUX, especially when there's only one client running in fact (imagine the program has to check for many times when it'll find only one client running)）
                    process = next(_return_ux_process(processList = process_iter), None)
                    if process and not process in process_iter:
                        process_iter.append(process)
                    retry += 1
                if len(process_iter) > 1:
                    print("检测到您运行了多个客户端。请选择您需要操作的客户端进程：\nDetected multiple clients running. Please select a client process:")
                    lens = {"No.": max(max(map(lambda x: wcswidth(str(x)), range(len(process_iter)))), wcswidth("No."), wcswidth("序号")) + 2, "pid": max(max(map(lambda x: wcswidth(str(x.pid)), process_iter)), wcswidth("pid"), wcswidth("进程序号")) + 2, "filePath": max(max(map(lambda x: wcswidth(x.cmdline()[0]), process_iter)), wcswidth("filePath"), wcswidth("进程文件路径")) + 2, "createTime": max(max(map(lambda x: wcswidth(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(x.create_time()))), process_iter)), wcswidth("createTime"), wcswidth("进程创建时间")) + 2, "status": max(max(map(lambda x: wcswidth(x.status()), process_iter)), wcswidth("status"), wcswidth("状态")) + 2}
                    print("{0:^{w0}}  {1:^{w1}}  {2:^{w2}}  {3:^{w3}}  {4:^{w4}}".format("No.", "pid", "filePath", "createTime", "status", w0 = lens["No."] - count_nonASCII("No."), w1 = lens["pid"] - count_nonASCII("pid"), w2 = lens["filePath"] - count_nonASCII("filePath"), w3 = lens["createTime"] - count_nonASCII("createTime"), w4 = lens["status"] - count_nonASCII("status")))
                    print("{0:^{w0}}  {1:^{w1}}  {2:^{w2}}  {3:^{w3}}  {4:^{w4}}".format("序号", "进程序号", "进程文件路径", "进程创建时间", "状态", w0 = lens["No."] - count_nonASCII("状态"), w1 = lens["pid"] - count_nonASCII("进程序号"), w2 = lens["filePath"] - count_nonASCII("进程文件路径"), w3 = lens["createTime"] - count_nonASCII("进程创建时间"), w4 = lens["status"] - count_nonASCII("状态")))
                    for i in range(len(process_iter)):
                        pid = process_iter[i].pid
                        filePath = process_iter[i].cmdline()[0]
                        createTime = time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(process_iter[i].create_time()))
                        status = process_iter[i].status()
                        print("{0:^{w0}}  {1:^{w1}}  {2:^{w2}}  {3:^{w3}}  {4:^{w4}}".format(i + 1, pid, filePath, createTime, status, w0 = lens["No."] - count_nonASCII(i + 1), w1 = lens["pid"] - count_nonASCII(pid), w2 = lens["filePath"] - count_nonASCII(filePath), w3 = lens["createTime"] - count_nonASCII(createTime), w4 = lens["status"] - count_nonASCII(status)))
                    while True:
                        processIndex = input()
                        if processIndex == "":
                            continue
                        try:
                            processIndex = int(processIndex)
                        except ValueError:
                            print("请输入不超过%d的正整数！\nPlease input an integer not greater than %d!" %(len(process_iter), len(process_iter)))
                        else:
                            if processIndex in range(1, len(process_iter) + 1):
                                process = process_iter[processIndex - 1]
                                break
                            else:
                                print("请输入不超过%d的正整数！\nPlease input an integer not greater than %d!" %(len(process_iter), len(process_iter)))
                elif len(process_iter) == 1: #如果没有后面两个部分，那么在经过10次寻找进程后，由于process_iter中已经包含了所有符合要求的进程，process将成为None，从而导致self.loop.run_until_complete(connection.init())出现self中无_auth_keys的报错（If the following parts don't exist, then after 10 times of searching for the demanding process, since `process_iter` has included all the corresponding processes, `process` will become `None`, which causes an AttributeError that 'Connection' object has no attribute '_auth_key'）
                    process = process_iter[0]
                else:
                    raise NoLeagueClientDetected("The program didn't detect a running League Client.")
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

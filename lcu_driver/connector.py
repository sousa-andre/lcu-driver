import asyncio
import logging
import time
import unicodedata
import pandas as pd
import shutil
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
            
            def format_df(df: pd.DataFrame): #按照每列最长字符串的命令行宽度加上2，再根据每个数据的中文字符数量决定最终格式化输出的字符串宽度（Get the width of the longest string of each column, add it by 2, and substract it by the number of each cell string's Chinese characters to get the final width for each cell to print using `format` function）
                maxLens = {}
                maxWidth = shutil.get_terminal_size()[0]
                fields = df.columns.tolist()
                for field in fields:
                    maxLens[field] = max(max(map(lambda x: wcswidth(str(x)), df[field])), wcswidth(str(field))) + 2
                if sum(maxLens.values()) + 2 * (len(fields) - 1) > maxWidth: #因为输出的时候，相邻两列之间需要有两个空格分隔，所以在计算总宽度的时候必须算上这些空格的宽度（Because two spaces are used between each pair of columns, the width they take up must be taken into consideration）
                    print("单行数据字符串输出宽度超过当前终端窗口宽度！是否继续？（输入任意键继续，否则直接打印该数据框。）\nThe output width of each record string exceeds the current width of the terminal window! Continue? (Input anything to continue, or null to directly print this dataframe.)")
                    if input() == "":
                        #print(df)
                        result = str(df)
                        return (result, maxLens)
                result = ""
                for i in range(df.shape[1]):
                    field = fields[i]
                    tmp = "{0:^{w}}".format(field, w = maxLens[str(field)] - count_nonASCII(str(field)))
                    result += tmp
                    #print(tmp, end = "")
                    if i != df.shape[1] - 1:
                            result += "  "
                        #print("  ", end = "")
                result += "\n"
                #print()
                for i in range(df.shape[0]):
                    for j in range(df.shape[1]):
                        field = fields[j]
                        cell = df[field][i]
                        tmp = "{0:^{w}}".format(cell, w = maxLens[field] - count_nonASCII(str(cell)))
                        result += tmp
                        #print(tmp, end = "")
                        if j != df.shape[1] - 1:
                            result += "  "
                            #print("  ", end = "")
                    if i != df.shape[0] - 1:
                        result += "\n"
                    #print() #注意这里的缩进和上一行不同（Note that here the indentation is different from the last line）
                return (result, maxLens)
            
            def wrapper():
                process_iter = _return_ux_process()
                if len(process_iter) > 1:
                    print("检测到您运行了多个客户端。请选择您需要操作的客户端进程：\nDetected multiple clients running. Please select a client process:")
                    process_dict = {"No.": ["序号"], "pid": ["进程序号"], "filePath": ["进程文件路径"], "createTime": ["进程创建时间"], "status": ["状态"]}
                    for i in range(len(process_iter)):
                        process_dict["No."].append(i + 1)
                        process_dict["pid"].append(process_iter[i].pid)
                        process_dict["filePath"].append(process_iter[i].cmdline()[0])
                        process_dict["createTime"].append(time.strftime("%Y-%m-%d %H:%M:%S", time.localtime(process_iter[i].create_time())))
                        process_dict["status"].append(process_iter[i].status())
                    process_df = pd.DataFrame(process_dict)
                    print(format_df(process_df)[0])
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
                elif len(process_iter) == 1: #如果没有后面两个部分，那么在经过100次寻找进程后，由于process_iter中已经包含了所有符合要求的进程，process将成为None，从而导致self.loop.run_until_complete(connection.init())出现self中无_auth_keys的报错（If the following parts don't exist, then after 100 times of searching for the demanding process, since `process_iter` has included all the corresponding processes, `process` will become `None`, which causes an AttributeError that 'Connection' object has no attribute '_auth_key'）
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

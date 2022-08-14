import dataclasses
from asyncio import sleep
from typing import Dict, Optional

from lcu_driver.utils import _return_ux_process, parse_cmdline_args


@dataclasses.dataclass
class ConnectionOptions:
    lcu_pid: int
    port: int
    auth_key: str
    extras: Dict[str, any] = dataclasses.field(default_factory=dict)


async def get_connection_options_from_ux(interval_seconds: int = 1) -> Optional[ConnectionOptions]:
    process = next(_return_ux_process(), None)
    if process is None:
        return None

    await sleep(interval_seconds)

    process_args = parse_cmdline_args(process.cmdline())
    connection_opts = ConnectionOptions(
        int(process_args['app-pid']),
        int(process_args['app-port']),
        process_args['remoting-auth-token'],
        {
            'installation_path': process_args['install-directory']
        }
    )

    return connection_opts

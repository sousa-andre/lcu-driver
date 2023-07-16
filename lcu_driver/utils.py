from typing import Dict, Generator

from psutil import process_iter, Process, STATUS_ZOMBIE


def parse_cmdline_args(cmdline_args) -> Dict[str, str]:
    cmdline_args_parsed = {}
    for cmdline_arg in cmdline_args:
        if len(cmdline_arg) > 0 and '=' in cmdline_arg:
            key, value = cmdline_arg[2:].split('=', 1)
            cmdline_args_parsed[key] = value
    return cmdline_args_parsed


def _return_ux_process() -> Generator[Process, None, None]:
    for process in process_iter():
        if process.status() == STATUS_ZOMBIE:
            continue

        if process.name() in ['LeagueClientUx.exe', 'LeagueClientUx']:
            yield process

        elif process.name() in ['League of Legends.exe', 'League of Legends']:
            process.terminate()

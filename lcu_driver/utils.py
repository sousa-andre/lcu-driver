from typing import Dict, List, Optional

from psutil import process_iter, Process


def parse_cmdline_args(cmdline_args) -> Dict[str, str]:
    cmdline_args_parsed = {}
    for cmdline_arg in cmdline_args:
        if len(cmdline_arg) > 0 and '=' in cmdline_arg:
            key, value = cmdline_arg[2:].split('=')
            cmdline_args_parsed[key] = value
    return cmdline_args_parsed


def return_process(process_name: List[str]) -> Optional[Process]:
    for process in process_iter():
        if process.name() in process_name:
            return process
    return None


def _return_ux_process_when_available() -> Process:
    process = None
    while not process:
        process = return_process(['LeagueClientUx.exe', 'LeagueClientUx'])
    return process

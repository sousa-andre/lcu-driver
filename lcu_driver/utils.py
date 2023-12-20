from typing import Dict, Generator, List

from psutil import STATUS_ZOMBIE, Process, process_iter


def parse_cmdline_args(cmdline_args) -> Dict[str, str]:
    cmdline_args_parsed = {}
    for cmdline_arg in cmdline_args:
        if len(cmdline_arg) > 0 and "=" in cmdline_arg:
            key, value = cmdline_arg[2:].split("=", 1)
            cmdline_args_parsed[key] = value
    return cmdline_args_parsed


def _return_ux_process() -> Generator[Process, None, None]:
    for process in process_iter(attrs=["cmdline"]):
        if process.status() == STATUS_ZOMBIE:
            continue

        cmdline: List[str] = process.info.get("cmdline", [])

        if process.name() in ["LeagueClientUx.exe", "LeagueClientUx"]:
            yield process

        # Check cmdline for the executable, especially useful in Linux environments
        # where process names might differ due to compatibility layers like wine.
        if cmdline and cmdline[0].endswith("LeagueClientUx.exe"):
            yield process

import platform
from psutil import ZombieProcess, AccessDenied, Process, process_iter


def parse_cmdline_args(cmdline_args: list[str]) -> dict[str, str]:
    cmdline_args_parsed: dict[str, str] = {}
    for cmdline_arg in cmdline_args:
        if len(cmdline_arg) > 0 and "=" in cmdline_arg:
            key, value = cmdline_arg.split("=", 1)
            cmdline_args_parsed[key] = value
    return cmdline_args_parsed


def _return_ux_process() -> list[Process]:
    processList: list[Process] = []
    osPlatform: str = platform.system() # Distinguish the operating system preemptively
    seen_pid: set[int] = set() # Ensure processList's uniqueness
    for process in process_iter(): #attrs=["cmdline"] greatly increases time cost on Windows
        try:
            name: str = process.name()
            if osPlatform in {"Linux", "Darwin"}:
                cmdline: list[str] = process.cmdline()
        except (ZombieProcess, AccessDenied): # Accessing the status method significantly increases time expense. This try-except statement should optimize this issue
            continue
        else:
            if name in {"LeagueClientUx.exe", "LeagueClientUx", "TFTClient-Win64-Shipping.exe", "TFTClient-Win64-Shipping"}:
                processList.append(process)
                seen_pid.add(process.pid)

            if osPlatform in {"Linux", "Darwin"}: # In case the same process would be added multiple times on Windows
                # Check cmdline for the executable, especially useful in Linux environments
                # where process names might differ due to compatibility layers like wine.
                if cmdline and (cmdline[0].endswith("LeagueClientUx.exe") or cmdline[0].endswith("TFTClient-Win64-Shipping.exe")) and not process.pid in seen_pid:
                    processList.append(process)
                    seen_pid.add(process.pid)
    return processList

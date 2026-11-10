import asyncio
import ipaddress
import os
import re
import shlex
import shutil
import signal

from logger import log_execution


# Execution configuration
TIMEOUT_SECONDS = 45
MAX_OUTPUT_LENGTH = 3000


# Restrict targets to RFC1918 private IPv4 networks
PRIVATE_NETWORKS = [
    ipaddress.ip_network("10.0.0.0/8"),
    ipaddress.ip_network("172.16.0.0/12"),
    ipaddress.ip_network("192.168.0.0/16"),
]


def private_ipv4(value):
    try:
        address = ipaddress.ip_address(value)

        return (
            isinstance(address, ipaddress.IPv4Address)
            and any(address in network for network in PRIVATE_NETWORKS)
        )

    except ValueError:
        return False


# Validate Nmap port specifications
def valid_ports(value):
    if not re.fullmatch(
        r"\d+(?:-\d+)?(?:,\d+(?:-\d+)?)*",
        value,
    ):
        return False

    total = 0

    for part in value.split(","):
        if "-" in part:
            start, end = map(int, part.split("-"))

            if not (1 <= start <= end <= 65535):
                return False

            total += end - start + 1

        else:
            port = int(part)

            if not 1 <= port <= 65535:
                return False

            total += 1

    return total <= 1000


# Dedicated Nmap argument validator
def validate_nmap(options):

    allowed_flags = {
        "-F",
        "-sT",
        "-sV",
        "-Pn",
        "-n",
        "--open",
        "--reason",
        "-T2",
        "-T3",
    }

    validated = []
    target = None
    used = set()
    i = 0

    while i < len(options):

        option = options[i]

        if option in used:
            return None

        if option == "-p":

            if i + 1 >= len(options):
                return None

            ports = options[i + 1]

            if not valid_ports(ports):
                return None

            validated.extend(["-p", ports])
            used.add(option)
            i += 2
            continue

        if option == "--top-ports":

            if i + 1 >= len(options):
                return None

            count = options[i + 1]

            if (
                not count.isdigit()
                or not 1 <= int(count) <= 1000
            ):
                return None

            validated.extend(["--top-ports", count])
            used.add(option)
            i += 2
            continue

        if option.startswith("-"):

            if option not in allowed_flags:
                return None

            validated.append(option)
            used.add(option)
            i += 1
            continue

        # Only one explicitly supplied target is accepted
        if target is not None:
            return None

        if not private_ipv4(option):
            return None

        target = option
        i += 1

    if target is None:
        return None

    # Reject incompatible combinations
    if "-F" in used and (
        "-p" in used or "--top-ports" in used
    ):
        return None

    if "-p" in used and "--top-ports" in used:
        return None

    if "-T2" in used and "-T3" in used:
        return None

    return ["nmap", *validated, target]


# General command validation
def validate_command(command_text):

    try:
        args = shlex.split(command_text)

    except ValueError:
        return None, "Invalid command syntax."

    if not args:
        return None, "Please provide a command."

    command = args[0]
    options = args[1:]

    # Basic Linux commands
    basic_commands = {
        "whoami": [],
        "uname": ["-a"],
        "df": ["-h"],
        "free": ["-h"],
    }

    if command in basic_commands:
        if options == basic_commands[command]:
            return [command, *options], None

    # Network information
    if command == "ip":
        allowed_ip_options = [
            ["a"],
            ["addr"],
            ["address"],
            ["route"],
        ]

        if options in allowed_ip_options:
            return ["ip", *options], None

    # Ping validation
    if command == "ping":

        if (
            len(options) == 3
            and options[0] == "-c"
            and options[1].isdigit()
            and 1 <= int(options[1]) <= 4
            and private_ipv4(options[2])
        ):
            return ["ping", *options], None

    # Nmap validation
    if command == "nmap":

        validated = validate_nmap(options)

        if validated is not None:
            return validated, None

    return None, (
        "Command rejected or unsupported.\n"
        "Only approved commands and arguments are allowed.\n"
        "Use /help to see supported commands."
    )


# Read output with a strict size limit
async def read_limited(stream, limit):

    chunks = []
    total = 0

    while True:

        remaining = limit + 1 - total

        chunk = await stream.read(
            min(1024, remaining)
        )

        if not chunk:
            return b"".join(chunks), False

        chunks.append(chunk)
        total += len(chunk)

        if total > limit:
            return b"".join(chunks)[:limit], True


# Safely terminate the process group
def stop_process_group(process):

    try:
        os.killpg(process.pid, signal.SIGKILL)

    except ProcessLookupError:
        pass


# Remote command execution
async def execute_command(command_text, user_id):

    argv, error = validate_command(command_text)

    if error:

        log_execution(
            user_id,
            command_text,
            "REJECTED",
        )

        return error

    executable = shutil.which(argv[0])

    if not executable:

        log_execution(
            user_id,
            command_text,
            "NOT_INSTALLED",
        )

        return f"Required command not installed: {argv[0]}"

    process = None

    async def collect_output():

        output, truncated = await read_limited(
            process.stdout,
            MAX_OUTPUT_LENGTH,
        )

        if not truncated:
            await process.wait()

        return output, truncated

    try:

        process = await asyncio.create_subprocess_exec(
            executable,
            *argv[1:],
            stdout=asyncio.subprocess.PIPE,
            stderr=asyncio.subprocess.STDOUT,
            start_new_session=True,
        )

        try:

            output, truncated = await asyncio.wait_for(
                collect_output(),
                timeout=TIMEOUT_SECONDS,
            )

        except asyncio.TimeoutError:

            stop_process_group(process)
            await process.wait()

            log_execution(
                user_id,
                command_text,
                "TIMEOUT",
            )

            return "Execution timed out after 45 seconds."

        if truncated:

            stop_process_group(process)
            await process.wait()

        result = output.decode(
            "utf-8",
            errors="replace",
        )

        if not result:
            result = "(No output)"

        if truncated:
            result += (
                "\n\n[Output limit reached; process stopped]"
            )

        log_execution(
            user_id,
            command_text,
            "OUTPUT_LIMIT" if truncated else "COMPLETED",
            process.returncode,
        )

        return (
            f"Command: {command_text}\n"
            f"Exit code: {process.returncode}\n\n"
            f"{result}"
        )

    except Exception as exc:

        if process and process.returncode is None:

            stop_process_group(process)
            await process.wait()

        log_execution(
            user_id,
            command_text,
            "ERROR",
        )

        return f"Execution error: {type(exc).__name__}"

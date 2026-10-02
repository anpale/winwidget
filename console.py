"""Command console for the browser agent.

  console.py                 interactive prompt (starts the agent if needed)
  console.py start | quit    start / stop the background agent
  console.py <command> ...   run one command, e.g.  console.py open example.com
"""
import base64
import json
import os
import shlex
import socket
import subprocess
import sys
import time
from datetime import datetime
from pathlib import Path

import common

HELP = """\
open <url>                         go to a page
screenshot [full] [--show]         save a PNG to the shots folder (--show opens it)
click <selector>                   click an element
type <selector> <text...>          fill an input
press <key>                        press a key, e.g. Enter
login <url> <user> <pass> <submit> log in with APP_USER / APP_PASS (selectors)
text [selector]                    print page text
url | title | back | reload
wait <selector|milliseconds>
start | ping | quit                quit stops the agent, exit leaves it running
"""


def send(cmd, args=(), timeout=90):
    try:
        token = common.TOKEN_FILE.read_text().strip()
        with socket.create_connection((common.HOST, common.PORT), timeout=timeout) as s:
            s.sendall((json.dumps({"token": token, "cmd": cmd, "args": list(args)}) + "\n").encode())
            line = s.makefile("rb").readline()
    except OSError as e:
        raise ConnectionError("agent is not running (type 'start')") from e
    return json.loads(line)


def is_running():
    try:
        return send("ping", timeout=3)["ok"]
    except (ConnectionError, ValueError, KeyError):
        return False


def start_agent():
    if is_running():
        return "agent already running"
    if getattr(sys, "frozen", False):
        cmd = [str(Path(sys.executable).with_name("agent.exe"))]
    else:
        exe = sys.executable
        if sys.platform == "win32" and Path(exe).with_name("pythonw.exe").exists():
            exe = str(Path(exe).with_name("pythonw.exe"))
        cmd = [exe, str(Path(__file__).with_name("agent.py"))]
    kwargs = {}
    if sys.platform == "win32":
        # DETACHED_PROCESS | CREATE_NEW_PROCESS_GROUP | CREATE_NO_WINDOW
        kwargs["creationflags"] = 0x00000008 | 0x00000200 | 0x08000000
    else:
        kwargs["start_new_session"] = True
    subprocess.Popen(cmd, stdin=subprocess.DEVNULL, stdout=subprocess.DEVNULL,
                     stderr=subprocess.DEVNULL, **kwargs)
    for _ in range(60):
        time.sleep(0.5)
        if is_running():
            return "agent started"
    return f"agent did not start in time - see {common.LOG_FILE}"


def show(path):
    if sys.platform == "win32":
        os.startfile(path)
    else:
        subprocess.run(["open" if sys.platform == "darwin" else "xdg-open", str(path)])


def run(cmd, args):
    if cmd == "start":
        print(start_agent())
        return
    open_after = "--show" in args
    args = [a for a in args if a != "--show"]
    reply = send(cmd, args)
    if not reply["ok"]:
        print("error:", reply["error"])
        return
    if "image_b64" in reply:
        common.SHOTS_DIR.mkdir(exist_ok=True)
        path = common.SHOTS_DIR / f"shot-{datetime.now():%Y%m%d-%H%M%S}.png"
        path.write_bytes(base64.b64decode(reply["image_b64"]))
        print(f"saved {path}")
        if open_after:
            show(path)
    else:
        print(reply["result"])


def repl():
    try:
        import readline  # noqa: F401  (line editing where available)
    except ImportError:
        pass
    if not is_running():
        print(start_agent())
    print("Type 'help' for commands, 'exit' to leave, 'quit' to stop the agent.")
    while True:
        try:
            line = input("agent> ").strip()
        except (EOFError, KeyboardInterrupt):
            print()
            return
        if not line:
            continue
        if line in ("exit", "q"):
            return
        if line in ("help", "?"):
            print(HELP)
            continue
        try:
            parts = shlex.split(line)
            run(parts[0], parts[1:])
            if parts[0] == "quit":
                return
        except (ConnectionError, ValueError) as e:
            print("error:", e)


def main(argv):
    if not argv:
        repl()
        return 0
    try:
        run(argv[0], argv[1:])
    except ConnectionError as e:
        if argv[0] == "quit":
            print("agent is not running")
            return 0
        print("error:", e)
        return 1
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))

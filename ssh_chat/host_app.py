from __future__ import annotations

import argparse
import getpass
import threading

from .paths import app_data_dir
from .server import run_server


def main() -> int:
    parser = argparse.ArgumentParser(description="Host do SSH Chat (servidor).")
    parser.add_argument("--host", default="0.0.0.0", help="Host para bind (default: 0.0.0.0).")
    parser.add_argument("--port", type=int, default=2222, help="Porta TCP (default: 2222).")
    parser.add_argument("--user", default="chat", help="Username (default: chat).")
    parser.add_argument(
        "--password",
        default=None,
        help="Password. Se omitido, pede no arranque (não mostra no ecrã).",
    )
    args = parser.parse_args()

    password = args.password
    if password is None:
        password = getpass.getpass("Password do chat: ")

    stop_event = threading.Event()
    data_dir = app_data_dir("ssh-chat")
    host_key_path = str(data_dir / "host_key")

    run_server(
        host=args.host,
        port=args.port,
        host_key_path=host_key_path,
        username=args.user,
        password=password,
        stop_event=stop_event,
        on_log=print,
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


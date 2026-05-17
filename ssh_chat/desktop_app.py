from __future__ import annotations

import argparse
import threading

import tkinter as tk

from .gui_client import GuiClient
from .paths import app_data_dir
from .server import run_server


def main() -> int:
    parser = argparse.ArgumentParser(description="App desktop: inicia servidor local e abre GUI.")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=2222)
    parser.add_argument("--user", default="chat")
    parser.add_argument("--password", default="chat123")
    args = parser.parse_args()

    stop_event = threading.Event()
    data_dir = app_data_dir("ssh-chat")
    host_key_path = str(data_dir / "host_key")

    server_thread = threading.Thread(
        target=run_server,
        kwargs={
            "host": args.host,
            "port": args.port,
            "host_key_path": host_key_path,
            "username": args.user,
            "password": args.password,
            "stop_event": stop_event,
            "on_log": None,
        },
        daemon=True,
    )
    server_thread.start()

    root = tk.Tk()
    try:
        root.call("tk", "scaling", 1.1)
    except Exception:
        pass

    app = GuiClient(root)
    app._host.set(args.host)
    app._port.set(args.port)
    app._user.set(args.user)
    app._password.set(args.password)

    # Auto-conecta
    root.after(200, app.connect)

    def _on_close() -> None:
        try:
            app.disconnect()
        finally:
            stop_event.set()
            root.destroy()

    root.protocol("WM_DELETE_WINDOW", _on_close)
    root.mainloop()
    stop_event.set()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


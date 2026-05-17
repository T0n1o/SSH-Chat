from __future__ import annotations

import argparse

import tkinter as tk

from .gui_client import GuiClient


def main() -> int:
    parser = argparse.ArgumentParser(description="UI do SSH Chat (cliente GUI).")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=2222)
    parser.add_argument("--user", default="chat")
    parser.add_argument("--password", default="chat123")
    args = parser.parse_args()

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
    root.mainloop()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


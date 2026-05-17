from __future__ import annotations

import argparse
import getpass
import sys
import threading

import paramiko


def _reader(chan: paramiko.Channel) -> None:
    try:
        while True:
            data = chan.recv(4096)
            if not data:
                break
            sys.stdout.write(data.decode("utf-8", errors="replace"))
            sys.stdout.flush()
    except Exception:
        pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Cliente simples para o SSH Chat (Paramiko).")
    parser.add_argument("--host", default="localhost")
    parser.add_argument("--port", type=int, default=2222)
    parser.add_argument("--user", default="chat")
    parser.add_argument("--password", default=None)
    parser.add_argument("--no-known-hosts", action="store_true", help="Não grava known_hosts.")
    args = parser.parse_args()

    password = args.password
    if password is None:
        password = getpass.getpass("Password: ")

    client = paramiko.SSHClient()
    if args.no_known_hosts:
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
    else:
        client.load_system_host_keys()
        client.set_missing_host_key_policy(paramiko.AutoAddPolicy())

    client.connect(args.host, port=args.port, username=args.user, password=password)
    chan = client.invoke_shell()

    t = threading.Thread(target=_reader, args=(chan,), daemon=True)
    t.start()

    try:
        while True:
            line = sys.stdin.readline()
            if not line:
                break
            chan.send(line)
    except KeyboardInterrupt:
        pass
    finally:
        try:
            chan.close()
        except Exception:
            pass
        client.close()
    return 0


if __name__ == "__main__":
    raise SystemExit(main())


from __future__ import annotations

import argparse
import os
import socket
import threading
import time
from typing import Callable

import paramiko

from .chatroom import ChatRoom


class _SSHChatServer(paramiko.ServerInterface):
    def __init__(self, *, username: str, password: str | None) -> None:
        super().__init__()
        self._username = username
        self._password = password
        self._shell_requested = threading.Event()

    def check_auth_password(self, username: str, password: str) -> int:
        if username != self._username:
            return paramiko.AUTH_FAILED
        if self._password is None:
            return paramiko.AUTH_FAILED
        return paramiko.AUTH_SUCCESSFUL if password == self._password else paramiko.AUTH_FAILED

    def get_allowed_auths(self, username: str) -> str:
        return "password"

    def check_channel_request(self, kind: str, chanid: int) -> int:
        if kind == "session":
            return paramiko.OPEN_SUCCEEDED
        return paramiko.OPEN_FAILED_ADMINISTRATIVELY_PROHIBITED

    def check_channel_pty_request(self, channel, term, width, height, pixelwidth, pixelheight, modes) -> bool:
        return True

    def check_channel_shell_request(self, channel) -> bool:
        self._shell_requested.set()
        return True

    @property
    def shell_requested(self) -> threading.Event:
        return self._shell_requested


def _load_or_create_host_key(path: str, bits: int = 2048) -> paramiko.PKey:
    if os.path.exists(path):
        return paramiko.RSAKey.from_private_key_file(path)
    key = paramiko.RSAKey.generate(bits)
    key.write_private_key_file(path)
    return key


def _send_line(chan: paramiko.Channel, text: str = "") -> None:
    chan.send((text + "\r\n").encode("utf-8", errors="replace"))


def _readline(chan: paramiko.Channel, *, max_bytes: int = 8192, timeout_s: float = 0.1) -> str | None:
    """
    Lê uma linha terminada em \\n (ou \\r\\n) do channel.
    Retorna None em EOF/desconexão.
    """
    buf = bytearray()
    while True:
        if chan.closed or chan.eof_received:
            return None
        if chan.recv_ready():
            chunk = chan.recv(1)
            if not chunk:
                return None
            b = chunk[0]
            if b == 10:  # \\n
                break
            if b == 13:  # \\r
                # Consome \\n se vier a seguir
                if chan.recv_ready():
                    nxt = chan.recv(1)
                    if nxt and nxt[0] != 10:
                        buf.extend(nxt)
                break
            buf.append(b)
            if len(buf) >= max_bytes:
                break
        else:
            time.sleep(timeout_s)
    return buf.decode("utf-8", errors="replace").strip()


def _unique_nickname(room: ChatRoom, desired: str) -> str:
    desired = (desired or "").strip()
    if not desired:
        desired = "anon"
    existing = set(room.list_nicknames())
    if desired not in existing:
        return desired
    i = 2
    while True:
        candidate = f"{desired}{i}"
        if candidate not in existing:
            return candidate
        i += 1


def _handle_connection(
    client_sock: socket.socket,
    addr: tuple[str, int],
    *,
    host_key: paramiko.PKey,
    username: str,
    password: str | None,
    room: ChatRoom,
) -> None:
    transport = None
    chan = None
    try:
        transport = paramiko.Transport(client_sock)
        transport.add_server_key(host_key)
        server = _SSHChatServer(username=username, password=password)
        transport.start_server(server=server)

        chan = transport.accept(20)
        if chan is None:
            return

        # Espera o cliente pedir "shell" (ssh normal faz isso)
        if not server.shell_requested.wait(20):
            return

        _send_line(chan, "Bem-vindo ao SSH Chat.")
        _send_line(chan, "Digite /help para comandos.")
        chan.send(b"Nickname: ")
        nick_line = _readline(chan)
        if nick_line is None:
            return
        nickname = _unique_nickname(room, nick_line)
        room.add(chan, nickname)
        room.broadcast(f"* {nickname} entrou no chat.\r\n", exclude=chan)
        _send_line(chan, f"Olá, {nickname}! (/quit para sair)")

        while True:
            chan.send(b"> ")
            line = _readline(chan)
            if line is None:
                break
            if not line:
                continue

            if line.startswith("/"):
                cmd = line.strip().split()[0].lower()
                if cmd in ("/quit", "/exit"):
                    _send_line(chan, "Tchau!")
                    break
                if cmd == "/help":
                    _send_line(chan, "Comandos:")
                    _send_line(chan, "  /help  mostra esta ajuda")
                    _send_line(chan, "  /who   lista utilizadores")
                    _send_line(chan, "  /quit  sai do chat")
                    continue
                if cmd == "/who":
                    users = ", ".join(room.list_nicknames()) or "(vazio)"
                    _send_line(chan, f"Online: {users}")
                    continue
                _send_line(chan, f"Comando desconhecido: {cmd}")
                continue

            room.broadcast(f"[{nickname}] {line}\r\n", exclude=chan)
            _send_line(chan, f"[eu] {line}")
    except Exception as e:
        try:
            if chan is not None and not chan.closed:
                _send_line(chan, f"Erro: {e}")
        except Exception:
            pass
    finally:
        try:
            if chan is not None:
                participant = room.remove(chan)
                if participant is not None:
                    room.broadcast(f"* {participant.nickname} saiu.\r\n", exclude=chan)
        finally:
            try:
                if transport is not None:
                    transport.close()
            except Exception:
                pass
            try:
                client_sock.close()
            except Exception:
                pass


def main() -> int:
    parser = argparse.ArgumentParser(description="Servidor de chat via SSH (Paramiko).")
    parser.add_argument("--host", default="127.0.0.1", help="Host para bind (default: 127.0.0.1).")
    parser.add_argument("--port", type=int, default=2222, help="Porta TCP (default: 2222).")
    parser.add_argument("--host-key", default="host_key", help="Caminho para host key (default: ./host_key).")
    parser.add_argument("--user", default="chat", help="Username (default: chat).")
    parser.add_argument(
        "--password",
        default=os.environ.get("SSH_CHAT_PASSWORD"),
        help="Password (ou env SSH_CHAT_PASSWORD). Se omitido, nenhum login é aceito.",
    )
    args = parser.parse_args()

    stop_event = threading.Event()

    def _on_log(msg: str) -> None:
        print(msg)

    try:
        run_server(
            host=args.host,
            port=args.port,
            host_key_path=args.host_key,
            username=args.user,
            password=args.password,
            stop_event=stop_event,
            on_log=_on_log,
        )
    except KeyboardInterrupt:
        print("\n[ssh-chat] Encerrando...")
        stop_event.set()
        return 0
    return 0


def run_server(
    *,
    host: str,
    port: int,
    host_key_path: str,
    username: str,
    password: str | None,
    stop_event: threading.Event,
    on_log: Callable[[str], None] | None = None,
) -> None:
    """
    Loop do servidor (bloqueante) com opção de stop_event.
    Útil para embutir o servidor dentro de uma app desktop.
    """
    host_key = _load_or_create_host_key(host_key_path)
    room = ChatRoom()

    sock = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    sock.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    sock.bind((host, port))
    sock.listen(100)
    sock.settimeout(0.5)

    if on_log:
        on_log(f"[ssh-chat] Escutando em {host}:{port} (user={username})")
        on_log(f"[ssh-chat] Host key: {os.path.abspath(host_key_path)}")

    try:
        while not stop_event.is_set():
            try:
                client, addr = sock.accept()
            except socket.timeout:
                continue
            t = threading.Thread(
                target=_handle_connection,
                args=(client, addr),
                kwargs={
                    "host_key": host_key,
                    "username": username,
                    "password": password,
                    "room": room,
                },
                daemon=True,
            )
            t.start()
    finally:
        try:
            sock.close()
        except Exception:
            pass


if __name__ == "__main__":
    raise SystemExit(main())

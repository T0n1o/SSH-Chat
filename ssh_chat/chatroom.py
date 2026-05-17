from __future__ import annotations

import threading
from dataclasses import dataclass


@dataclass(frozen=True)
class Participant:
    nickname: str
    channel: object  # paramiko.Channel-like


class ChatRoom:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._participants: dict[object, Participant] = {}

    def add(self, channel: object, nickname: str) -> Participant:
        with self._lock:
            participant = Participant(nickname=nickname, channel=channel)
            self._participants[channel] = participant
            return participant

    def remove(self, channel: object) -> Participant | None:
        with self._lock:
            return self._participants.pop(channel, None)

    def list_nicknames(self) -> list[str]:
        with self._lock:
            return sorted(p.nickname for p in self._participants.values())

    def broadcast(self, message: str, *, exclude: object | None = None) -> None:
        data = message.encode("utf-8", errors="replace")
        with self._lock:
            participants = list(self._participants.values())

        for p in participants:
            if exclude is not None and p.channel is exclude:
                continue
            try:
                p.channel.send(data)
            except Exception:
                # Ignora falhas de envio; o handler de conexão vai limpar depois.
                pass


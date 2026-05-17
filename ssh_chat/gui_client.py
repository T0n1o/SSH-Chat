from __future__ import annotations

import argparse
import queue
import threading
import tkinter as tk
from tkinter import messagebox, ttk

import paramiko


class GuiClient:
    def __init__(self, root: tk.Tk) -> None:
        self.root = root
        self.root.title("SSH Chat")

        self._events: queue.Queue[tuple[str, str]] = queue.Queue()
        self._ssh_client: paramiko.SSHClient | None = None
        self._chan: paramiko.Channel | None = None
        self._reader_thread: threading.Thread | None = None

        self._host = tk.StringVar(value="localhost")
        self._port = tk.IntVar(value=2222)
        self._user = tk.StringVar(value="chat")
        self._password = tk.StringVar(value="chat123")

        self._build_ui()
        self.root.protocol("WM_DELETE_WINDOW", self._on_close)
        self._poll_events()

    def _build_ui(self) -> None:
        frm = ttk.Frame(self.root, padding=10)
        frm.grid(row=0, column=0, sticky="nsew")

        self.root.columnconfigure(0, weight=1)
        self.root.rowconfigure(0, weight=1)
        frm.columnconfigure(1, weight=1)

        ttk.Label(frm, text="Host").grid(row=0, column=0, sticky="w")
        ttk.Entry(frm, textvariable=self._host, width=24).grid(row=0, column=1, sticky="ew", padx=(6, 6))
        ttk.Label(frm, text="Porta").grid(row=0, column=2, sticky="w")
        ttk.Entry(frm, textvariable=self._port, width=8).grid(row=0, column=3, sticky="w", padx=(6, 0))

        ttk.Label(frm, text="User").grid(row=1, column=0, sticky="w", pady=(6, 0))
        ttk.Entry(frm, textvariable=self._user, width=24).grid(row=1, column=1, sticky="ew", padx=(6, 6), pady=(6, 0))
        ttk.Label(frm, text="Senha").grid(row=1, column=2, sticky="w", pady=(6, 0))
        self._password_entry = ttk.Entry(frm, textvariable=self._password, show="*", width=16)
        self._password_entry.grid(row=1, column=3, sticky="w", padx=(6, 0), pady=(6, 0))

        self._btn_connect = ttk.Button(frm, text="Conectar", command=self.connect)
        self._btn_connect.grid(row=0, column=4, rowspan=2, sticky="ns", padx=(10, 0))

        self._btn_disconnect = ttk.Button(frm, text="Desconectar", command=self.disconnect, state="disabled")
        self._btn_disconnect.grid(row=0, column=5, rowspan=2, sticky="ns", padx=(6, 0))

        self._text = tk.Text(frm, height=20, wrap="word", state="disabled")
        self._text.grid(row=2, column=0, columnspan=6, sticky="nsew", pady=(10, 6))

        scroll = ttk.Scrollbar(frm, command=self._text.yview)
        scroll.grid(row=2, column=6, sticky="ns", pady=(10, 6))
        self._text.configure(yscrollcommand=scroll.set)

        frm.rowconfigure(2, weight=1)

        bottom = ttk.Frame(frm)
        bottom.grid(row=3, column=0, columnspan=7, sticky="ew")
        bottom.columnconfigure(0, weight=1)

        self._entry = ttk.Entry(bottom)
        self._entry.grid(row=0, column=0, sticky="ew")
        self._entry.bind("<Return>", lambda _e: self.send_message())

        self._btn_send = ttk.Button(bottom, text="Enviar", command=self.send_message, state="disabled")
        self._btn_send.grid(row=0, column=1, padx=(8, 0))

        self._append("Dica: rode o servidor e conecte (Host/Porta/User/Senha).\n")

    def _append(self, text: str) -> None:
        self._text.configure(state="normal")
        self._text.insert("end", text)
        self._text.see("end")
        self._text.configure(state="disabled")

    def _set_connected_ui(self, connected: bool) -> None:
        self._btn_connect.configure(state="disabled" if connected else "normal")
        self._btn_disconnect.configure(state="normal" if connected else "disabled")
        self._btn_send.configure(state="normal" if connected else "disabled")

    def _reader(self, chan: paramiko.Channel) -> None:
        try:
            while True:
                data = chan.recv(4096)
                if not data:
                    break
                self._events.put(("data", data.decode("utf-8", errors="replace")))
        except Exception as e:
            self._events.put(("error", str(e)))
        finally:
            self._events.put(("status", "disconnected"))

    def _poll_events(self) -> None:
        try:
            while True:
                kind, payload = self._events.get_nowait()
                if kind == "data":
                    self._append(payload)
                elif kind == "error":
                    self._append(f"\n[erro] {payload}\n")
                elif kind == "status" and payload == "disconnected":
                    self._append("\n[desconectado]\n")
                    self._set_connected_ui(False)
        except queue.Empty:
            pass
        self.root.after(50, self._poll_events)

    def connect(self) -> None:
        if self._ssh_client is not None:
            return
        host = self._host.get().strip()
        port = int(self._port.get())
        user = self._user.get().strip()
        password = self._password.get()

        if not host or not user:
            messagebox.showerror("SSH Chat", "Preencha Host e User.")
            return

        try:
            client = paramiko.SSHClient()
            client.set_missing_host_key_policy(paramiko.AutoAddPolicy())
            client.connect(host, port=port, username=user, password=password, look_for_keys=False, allow_agent=False)
            chan = client.invoke_shell()
        except Exception as e:
            messagebox.showerror("SSH Chat", f"Falha ao conectar:\n{e}")
            try:
                client.close()
            except Exception:
                pass
            return

        self._ssh_client = client
        self._chan = chan
        self._set_connected_ui(True)
        self._append("\n[conectado]\n")

        self._reader_thread = threading.Thread(target=self._reader, args=(chan,), daemon=True)
        self._reader_thread.start()
        self._entry.focus_set()

    def disconnect(self) -> None:
        chan, client = self._chan, self._ssh_client
        self._chan = None
        self._ssh_client = None

        try:
            if chan is not None:
                chan.close()
        except Exception:
            pass
        try:
            if client is not None:
                client.close()
        except Exception:
            pass
        self._set_connected_ui(False)

    def send_message(self) -> None:
        chan = self._chan
        if chan is None:
            return
        text = self._entry.get()
        if not text.strip():
            return
        try:
            chan.send(text + "\n")
            self._entry.delete(0, "end")
        except Exception as e:
            messagebox.showerror("SSH Chat", f"Falha ao enviar:\n{e}")
            self.disconnect()

    def _on_close(self) -> None:
        self.disconnect()
        self.root.destroy()


def main() -> int:
    parser = argparse.ArgumentParser(description="Cliente GUI (Tkinter) para o SSH Chat.")
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


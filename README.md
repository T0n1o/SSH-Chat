# SSH-Chat (Python, over SSH)

Single-room chat over the **SSH protocol**: you run an SSH chat server in Python and users connect either with a regular SSH client (e.g. `ssh`) or with the included GUI client (Tkinter).

> Educational project (not hardened for production).

## Features

- One shared room (broadcast to everyone)
- Nicknames (auto-unique)
- Commands:
  - `/help` show help
  - `/who` list online users
  - `/quit` leave
- GUI client (Tkinter)
- Windows-friendly packaging (prebuilt `.exe` via GitHub Releases)

## Quick start (GUI)

1) Start the host app on the server PC
2) Open the UI app on any PC and connect to the host IP/port

## Optional: run from source (terminal)

### Install

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

### Host the server

```powershell
python -m ssh_chat.server --host 0.0.0.0 --port 2222 --user chat --password chat123
```

### Connect with a regular SSH client

```powershell
ssh chat@<HOST_IP> -p 2222
```

### GUI client (Tkinter)

```powershell
python -m ssh_chat.gui_client --host <HOST_IP> --port 2222 --user chat --password chat123
```

## Windows `.exe`

This repo does **not** store `.exe` files in Git (they are large and change often). Instead, prebuilt executables are published in **GitHub Releases**.

- `ssh-chat-host.exe` (server/host)
- `ssh-chat-ui.exe` (GUI client)

Open the latest Release on GitHub and download them from the Assets section.

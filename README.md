# SSH-Chat (Python, via SSH)

Chat em “sala única” usando o **protocolo SSH**: você roda um servidor SSH em Python e os usuários conectam com um cliente SSH normal (ex.: `ssh`). Também inclui um cliente GUI (Tkinter) e uma forma de empacotar em `.exe` no Windows.

> Nota: exemplo educacional (não “hardened” para produção).

## Requisitos

- Python 3.10+
- Dependências: `paramiko`

Instalar (Windows PowerShell):

```powershell
python -m venv .venv
.\.venv\Scripts\Activate.ps1
pip install -r requirements.txt
```

## Rodar o servidor (terminal)

```powershell
python -m ssh_chat.server --host 0.0.0.0 --port 2222 --user chat --password chat123
```

Na primeira execução, o servidor cria automaticamente uma **host key** em `./host_key`.

## Conectar com SSH

```powershell
ssh chat@localhost -p 2222
```

- Ao entrar, escolha um nickname.
- Comandos:
  - `/help` ajuda
  - `/who` lista usuários
  - `/quit` sai

## Cliente Python (opcional)

```powershell
python -m ssh_chat.client --host localhost --port 2222 --user chat --password chat123
```

## Cliente com interface gráfica (GUI)

```powershell
python -m ssh_chat.gui_client --host localhost --port 2222 --user chat --password chat123
```

## Rodar via Docker (opcional)

### Com Docker Compose

```bash
docker compose up --build
```

Depois conecte:

```bash
ssh chat@localhost -p 2222
```

### Com `docker run`

```bash
docker build -t ssh-chat .
docker run --rm -p 2222:2222 -e SSH_CHAT_PASSWORD=chat123 -v "%cd%\\host_key:/app/host_key" ssh-chat
```

## Gerar `.exe` (Windows)

Gera 2 executáveis:
- `ssh-chat-host.exe` (servidor/host, com console e logs)
- `ssh-chat-ui.exe` (cliente GUI, sem console)

No PowerShell dentro da pasta do projeto:

```powershell
.\build_exe.ps1
```

Saída:

```text
.\dist\ssh-chat-host.exe
.\dist\ssh-chat-ui.exe
```

Uso:
- Abra `dist\ssh-chat-host.exe` (vai pedir uma senha e mostrar logs).
- Em qualquer PC da rede, abra `dist\ssh-chat-ui.exe` e conecte no IP do servidor (porta 2222).

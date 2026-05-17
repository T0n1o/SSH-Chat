from __future__ import annotations

import os
from pathlib import Path


def app_data_dir(app_name: str = "ssh-chat") -> Path:
    """
    Diretório de dados do utilizador para guardar ficheiros (ex.: host_key).
    - Windows: %APPDATA%\\<app_name>
    - Linux: ~/.local/share/<app_name>
    - macOS: ~/Library/Application Support/<app_name>
    """
    if os.name == "nt":
        base = os.environ.get("APPDATA") or str(Path.home() / "AppData" / "Roaming")
        path = Path(base) / app_name
    elif sys_platform() == "darwin":
        path = Path.home() / "Library" / "Application Support" / app_name
    else:
        xdg = os.environ.get("XDG_DATA_HOME")
        path = Path(xdg) / app_name if xdg else (Path.home() / ".local" / "share" / app_name)
    path.mkdir(parents=True, exist_ok=True)
    return path


def sys_platform() -> str:
    # Evita importar sys no topo em ambientes embebidos estranhos
    import sys

    return sys.platform


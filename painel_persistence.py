"""Persistência remota do estado publicado pelo Painel Comercial Afogados."""
from __future__ import annotations

import json
import os
from datetime import datetime, timezone
from urllib.error import HTTPError, URLError
from urllib.request import Request, urlopen


DEFAULT_SUPABASE_URL = "https://xljzpgzmrnkfydyfrlts.supabase.co"
DEFAULT_SUPABASE_PUBLISHABLE_KEY = "sb_publishable_rfcCXMYA2Nwl9RilpViHuQ_pEHESnrH"
TABLE_NAME = "painel_afogados_state"
STATE_KEY = "current"


class RemotePersistenceError(RuntimeError):
    """Falha ao ler ou gravar o estado permanente."""


_remote_config: dict[str, str] | None = None


def _streamlit_secret(st, name: str) -> str:
    if st is None:
        return ""
    try:
        return str(st.secrets.get(name, "") or "").strip()
    except Exception:
        return ""


def configure_remote_persistence(st=None) -> bool:
    """Configura a conexão usando ambiente/Secrets; retorna se ficou ativa."""
    global _remote_config
    url = (
        os.environ.get("SUPABASE_URL", "").strip()
        or _streamlit_secret(st, "SUPABASE_URL")
        or DEFAULT_SUPABASE_URL
    ).rstrip("/")
    publishable_key = (
        os.environ.get("SUPABASE_PUBLISHABLE_KEY", "").strip()
        or _streamlit_secret(st, "SUPABASE_PUBLISHABLE_KEY")
        or DEFAULT_SUPABASE_PUBLISHABLE_KEY
    )
    storage_token = (
        os.environ.get("PAINEL_STORAGE_TOKEN", "").strip()
        or _streamlit_secret(st, "PAINEL_STORAGE_TOKEN")
    )
    if not (url and publishable_key and storage_token):
        _remote_config = None
        return False
    _remote_config = {
        "url": url,
        "publishable_key": publishable_key,
        "storage_token": storage_token,
    }
    return True


def remote_persistence_enabled() -> bool:
    return _remote_config is not None


def _request(method: str, query: str, body=None, prefer: str = ""):
    if _remote_config is None:
        raise RemotePersistenceError("A persistência permanente não está configurada.")
    url = f'{_remote_config["url"]}/rest/v1/{TABLE_NAME}{query}'
    headers = {
        "apikey": _remote_config["publishable_key"],
        "Authorization": f'Bearer {_remote_config["publishable_key"]}',
        "x-panel-key": _remote_config["storage_token"],
        "Accept": "application/json",
    }
    data = None
    if body is not None:
        data = json.dumps(body, ensure_ascii=False, separators=(",", ":")).encode("utf-8")
        headers["Content-Type"] = "application/json"
    if prefer:
        headers["Prefer"] = prefer
    request = Request(url, data=data, headers=headers, method=method)
    try:
        with urlopen(request, timeout=15) as response:
            raw = response.read()
            return json.loads(raw.decode("utf-8")) if raw else None
    except HTTPError as exc:
        detail = exc.read(800).decode("utf-8", errors="replace")
        raise RemotePersistenceError(
            f"O Supabase recusou a operação (HTTP {exc.code}): {detail}"
        ) from exc
    except (URLError, TimeoutError, OSError) as exc:
        raise RemotePersistenceError(
            "Não foi possível acessar o armazenamento permanente. Tente novamente."
        ) from exc


def load_remote_payload() -> dict | None:
    if not remote_persistence_enabled():
        return None
    result = _request(
        "GET",
        f"?state_key=eq.{STATE_KEY}&select=payload&limit=1",
    )
    if not result:
        return None
    payload = result[0].get("payload")
    if not isinstance(payload, dict):
        raise RemotePersistenceError("O estado permanente retornado é inválido.")
    return payload


def save_remote_payload(payload: dict) -> None:
    if not remote_persistence_enabled():
        return
    record = {
        "state_key": STATE_KEY,
        "payload": payload,
        "updated_at": datetime.now(timezone.utc).isoformat(timespec="seconds"),
    }
    _request(
        "POST",
        "?on_conflict=state_key",
        [record],
        prefer="resolution=merge-duplicates,return=minimal",
    )

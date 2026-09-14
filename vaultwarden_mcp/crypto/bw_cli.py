"""``VaultCrypto`` backend that delegates key handling to the Bitwarden CLI.

Every instance drives its own private, throw-away Bitwarden CLI data directory
(``BITWARDENCLI_APPDATA_DIR``) rather than the invoking user's real ``bw`` login state, so
concurrent instances never collide and never touch anyone's personal vault session.
Credentials and the unlocked session key travel only through the child process
environment — never on argv, never in an exception message. Failures name the ``bw``
subcommand that failed, never vault contents.
"""

from __future__ import annotations

import base64
import json
import os
import shutil
import subprocess
import tempfile
from collections.abc import Callable
from pathlib import Path
from typing import Any

from .base import VaultRecord

#: ``bw`` subcommands this backend manages itself; :meth:`BwCliVaultCrypto.run` refuses them.
_MANAGED_COMMANDS = frozenset({"login", "logout", "unlock", "lock", "config", "serve"})

#: Environment variable name used with ``--passwordenv`` to unlock the vault.
_UNLOCK_ENV_NAME = "VAULTWARDEN_MCP_BW_MASTER_PASSWORD"


class BwCliError(RuntimeError):
    """A ``bw`` invocation failed or returned output that could not be parsed."""

    def __init__(self, command: str, message: str) -> None:
        self.command = command
        super().__init__(f"bw {command}: {message}")


class BwCliVaultCrypto:
    """Item-level vault access delegated to an installed Bitwarden CLI (``bw``)."""

    name = "bw_cli"

    def __init__(
        self,
        server_url: str,
        master_password: str | None,
        client_id: str | None,
        client_secret: str | None,
        ca_bundle_path: Path | str | None = None,
        *,
        bw_executable: str = "bw",
        runner: Callable[..., subprocess.CompletedProcess[str]] = subprocess.run,
        timeout_s: float = 120.0,
    ) -> None:
        if not server_url.startswith("https://"):
            raise ValueError("the bw_cli backend requires an https:// server_url")
        if not master_password:
            raise ValueError("the bw_cli backend needs the master_password credential")
        if not client_id:
            raise ValueError("the bw_cli backend needs the client_id credential")
        if not client_secret:
            raise ValueError("the bw_cli backend needs the client_secret credential")

        self._server_url = server_url
        self._master_password: str | None = master_password
        self._client_id: str | None = client_id
        self._client_secret: str | None = client_secret
        self._bw_executable = bw_executable
        self._runner = runner
        self._timeout_s = timeout_s
        self._session: str | None = None

        data_dir = Path(tempfile.mkdtemp(prefix="vaultwarden-mcp-bw-"))
        os.chmod(data_dir, 0o700)
        self._data_dir: Path | None = data_dir

        base_env = dict(os.environ)
        for key in ("BW_CLIENTID", "BW_CLIENTSECRET", "BW_SESSION", _UNLOCK_ENV_NAME):
            base_env.pop(key, None)
        base_env["BITWARDENCLI_APPDATA_DIR"] = str(data_dir)
        if ca_bundle_path:
            base_env["NODE_EXTRA_CA_CERTS"] = str(ca_bundle_path)
        self._base_env = base_env

    # -- process plumbing ------------------------------------------------------------

    def _sanitize(self, text: str | None) -> str:
        sanitized = text or ""
        for secret in (self._master_password, self._client_secret, self._session):
            if secret:
                sanitized = sanitized.replace(secret, "[REDACTED]")
        return sanitized[:300]

    def _execute(
        self,
        args: list[str],
        *,
        extra_env: dict[str, str] | None = None,
        use_session: bool = False,
    ) -> str:
        command = args[0] if args else self._bw_executable
        env = dict(self._base_env)
        if use_session and self._session:
            env["BW_SESSION"] = self._session
        if extra_env:
            env.update(extra_env)
        argv = [self._bw_executable, *args, "--nointeraction"]
        try:
            result = self._runner(
                argv, capture_output=True, text=True, env=env, timeout=self._timeout_s
            )
        except subprocess.TimeoutExpired as exc:
            raise BwCliError(command, self._sanitize(str(exc))) from exc
        if result.returncode != 0:
            raise BwCliError(command, self._sanitize(result.stderr))
        return result.stdout

    def _parse_json(self, command: str, text: str) -> Any:
        try:
            return json.loads(text)
        except json.JSONDecodeError as exc:
            raise BwCliError(command, self._sanitize(str(exc))) from exc

    @staticmethod
    def _encode(record: dict[str, Any]) -> str:
        return base64.b64encode(json.dumps(record).encode("utf-8")).decode("ascii")

    # -- session lifecycle -------------------------------------------------------------

    def _ensure_session(self) -> None:
        if self._session is not None:
            return
        if not (self._master_password and self._client_id and self._client_secret):
            raise BwCliError("unlock", "vault is locked; secrets were discarded")

        self._execute(["config", "server", self._server_url])
        status = self._parse_json("status", self._execute(["status"]))
        already_logged_in = (
            status.get("serverUrl") == self._server_url
            and status.get("status") != "unauthenticated"
        )
        if not already_logged_in:
            self._execute(
                ["login", "--apikey"],
                extra_env={
                    "BW_CLIENTID": self._client_id,
                    "BW_CLIENTSECRET": self._client_secret,
                },
            )
        session = self._execute(
            ["unlock", "--passwordenv", _UNLOCK_ENV_NAME, "--raw"],
            extra_env={_UNLOCK_ENV_NAME: self._master_password},
        )
        self._session = session.strip()
        self._execute(["sync"], use_session=True)

    # -- VaultCrypto ---------------------------------------------------------------------

    def account_email(self) -> str:
        self._ensure_session()
        status = self._parse_json("status", self._execute(["status"], use_session=True))
        email = status.get("userEmail")
        if not isinstance(email, str) or not email:
            raise BwCliError("status", "bw status did not report userEmail")
        return email

    def list_items(self, *, include_trash: bool = False) -> list[VaultRecord]:
        self._ensure_session()
        args = ["list", "items"]
        if include_trash:
            args.append("--trash")
        items = self._parse_json("list", self._execute(args, use_session=True))
        if not isinstance(items, list):
            raise BwCliError("list", "expected a JSON array of items")
        return items

    def get_item(self, item_id: str) -> VaultRecord:
        self._ensure_session()
        out = self._execute(["get", "item", item_id], use_session=True)
        return self._parse_json("get", out)

    def create_item(self, item: VaultRecord) -> VaultRecord:
        self._ensure_session()
        encoded = self._encode(item)
        out = self._execute(["create", "item", encoded], use_session=True)
        return self._parse_json("create", out)

    def edit_item(self, item_id: str, item: VaultRecord) -> VaultRecord:
        self._ensure_session()
        encoded = self._encode(item)
        out = self._execute(["edit", "item", item_id, encoded], use_session=True)
        return self._parse_json("edit", out)

    def list_folders(self) -> list[VaultRecord]:
        self._ensure_session()
        folders = self._parse_json(
            "list", self._execute(["list", "folders"], use_session=True)
        )
        if not isinstance(folders, list):
            raise BwCliError("list", "expected a JSON array of folders")
        return folders

    def create_folder(self, name: str) -> VaultRecord:
        self._ensure_session()
        encoded = self._encode({"name": name})
        out = self._execute(["create", "folder", encoded], use_session=True)
        return self._parse_json("create", out)

    def lock(self) -> None:
        try:
            self._execute(["lock"], use_session=True)
        except BwCliError:
            pass
        try:
            self._execute(["logout"], use_session=True)
        except BwCliError:
            pass
        self._session = None
        self._master_password = None
        self._client_id = None
        self._client_secret = None
        if self._data_dir is not None:
            shutil.rmtree(self._data_dir, ignore_errors=True)
            self._data_dir = None

    # -- full CLI coverage -----------------------------------------------------------

    def run(self, *args: str) -> str:
        """Run any ``bw`` command this class does not otherwise wrap."""
        if not args:
            raise BwCliError("run", "no command given")
        command = args[0]
        if command in _MANAGED_COMMANDS:
            raise BwCliError(
                command, f"{command!r} is managed by BwCliVaultCrypto directly"
            )
        secrets = {s for s in (self._master_password, self._client_secret) if s}
        for arg in args:
            if arg == "--session":
                raise BwCliError(command, "the --session flag is managed internally")
            if arg in secrets:
                raise BwCliError(command, "argument would place a secret on argv")
        self._ensure_session()
        return self._execute(list(args), use_session=True)

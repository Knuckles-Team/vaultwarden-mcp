"""BwCliVaultCrypto against a fake ``bw`` runner (never the real binary)."""

from __future__ import annotations

import base64
import json
import subprocess
from collections.abc import Callable
from pathlib import Path

import pytest

from vaultwarden_mcp.crypto.base import VaultCrypto
from vaultwarden_mcp.crypto.bw_cli import BwCliError, BwCliVaultCrypto

SERVER_URL = "https://vault.example.com"
CLIENT_ID = "user.client-id-1234"
CLIENT_SECRET = "example-client-credential"
MASTER_PASSWORD = "correct horse battery staple"

Predicate = Callable[[list[str]], bool]


class ScriptedRunner:
    """Fake ``subprocess.run`` replacement that records every invocation."""

    def __init__(self) -> None:
        self.calls: list[tuple[list[str], dict[str, str]]] = []
        self._handlers: list[tuple[Predicate, str, str, int]] = []

    def when(
        self,
        predicate: Predicate,
        *,
        stdout: str = "",
        stderr: str = "",
        returncode: int = 0,
    ) -> None:
        # Later registrations take priority, so a test can override one of the
        # default happy-path handlers (e.g. make "sync" fail).
        self._handlers.insert(0, (predicate, stdout, stderr, returncode))

    def __call__(
        self, argv: list[str], **kwargs: object
    ) -> subprocess.CompletedProcess[str]:
        env = kwargs.get("env")
        assert isinstance(env, dict)
        self.calls.append((list(argv), dict(env)))
        for predicate, stdout, stderr, returncode in self._handlers:
            if predicate(argv):
                return subprocess.CompletedProcess(argv, returncode, stdout, stderr)
        return subprocess.CompletedProcess(argv, 0, "", "")


def _is(command: str) -> Predicate:
    return lambda argv: len(argv) > 1 and argv[1] == command


def happy_runner(*, already_logged_in: bool = False) -> ScriptedRunner:
    """A runner that answers config/status/login/unlock/sync successfully."""
    runner = ScriptedRunner()
    status_body = json.dumps(
        {
            "serverUrl": SERVER_URL,
            "status": "unlocked" if already_logged_in else "unauthenticated",
            "userEmail": "owner@example.com",
        }
    )
    runner.when(_is("config"), stdout="")
    runner.when(_is("status"), stdout=status_body)
    runner.when(_is("login"), stdout="")
    runner.when(_is("unlock"), stdout="session-key-abc123\n")
    runner.when(_is("sync"), stdout="")
    return runner


def make_backend(runner: ScriptedRunner, **overrides: object) -> BwCliVaultCrypto:
    kwargs: dict[str, object] = {
        "server_url": SERVER_URL,
        "master_password": MASTER_PASSWORD,
        "client_id": CLIENT_ID,
        "client_secret": CLIENT_SECRET,
        "runner": runner,
    }
    kwargs.update(overrides)
    return BwCliVaultCrypto(**kwargs)  # type: ignore[arg-type]


# -- constructor validation -----------------------------------------------------------


def test_requires_master_password() -> None:
    with pytest.raises(ValueError, match="master_password"):
        make_backend(
            ScriptedRunner(),
            master_password=None,
            client_id=CLIENT_ID,
            client_secret=CLIENT_SECRET,
        )


def test_requires_client_id() -> None:
    with pytest.raises(ValueError, match="client_id"):
        make_backend(ScriptedRunner(), client_id=None)


def test_requires_client_secret() -> None:
    with pytest.raises(ValueError, match="client_secret"):
        make_backend(ScriptedRunner(), client_secret=None)


def test_requires_https_server_url() -> None:
    with pytest.raises(ValueError, match="https"):
        make_backend(ScriptedRunner(), server_url="http://vault.example.com")


def test_satisfies_vault_crypto_protocol() -> None:
    backend = make_backend(happy_runner())
    assert isinstance(backend, VaultCrypto)
    backend.lock()


# -- session establishment --------------------------------------------------------------


def test_first_use_runs_config_login_unlock_sync_in_order() -> None:
    runner = happy_runner()
    backend = make_backend(runner)

    backend.account_email()

    commands = [call[0][1] for call in runner.calls]
    assert commands.index("config") < commands.index("login")
    assert commands.index("login") < commands.index("unlock")
    assert commands.index("unlock") < commands.index("sync")
    backend.lock()


def test_login_skipped_when_already_logged_into_right_server() -> None:
    runner = happy_runner(already_logged_in=True)
    backend = make_backend(runner)

    backend.account_email()

    commands = [call[0][1] for call in runner.calls]
    assert "login" not in commands
    assert "config" in commands
    assert "unlock" in commands
    assert "sync" in commands
    backend.lock()


def test_session_established_once_across_multiple_calls() -> None:
    runner = happy_runner()
    runner.when(_is("list"), stdout="[]")
    backend = make_backend(runner)

    backend.list_items()
    backend.list_items()

    unlock_calls = [c for c in runner.calls if c[0][1] == "unlock"]
    assert len(unlock_calls) == 1
    backend.lock()


# -- secrecy: env only, never argv ----------------------------------------------------


def test_secrets_never_appear_on_argv() -> None:
    runner = happy_runner()
    runner.when(_is("list"), stdout="[]")
    backend = make_backend(runner)

    backend.list_items()

    for argv, _env in runner.calls:
        assert MASTER_PASSWORD not in argv
        assert CLIENT_ID not in argv
        assert CLIENT_SECRET not in argv
    backend.lock()


def test_secrets_and_session_travel_only_via_env() -> None:
    runner = happy_runner()
    backend = make_backend(runner)

    backend.account_email()

    login_env = next(env for argv, env in runner.calls if argv[1] == "login")
    assert login_env["BW_CLIENTID"] == CLIENT_ID
    assert login_env["BW_CLIENTSECRET"] == CLIENT_SECRET

    unlock_argv, unlock_env = next(
        (argv, env) for argv, env in runner.calls if argv[1] == "unlock"
    )
    assert "--passwordenv" in unlock_argv
    password_var = unlock_argv[unlock_argv.index("--passwordenv") + 1]
    assert unlock_env[password_var] == MASTER_PASSWORD

    sync_env = next(env for argv, env in runner.calls if argv[1] == "sync")
    assert sync_env.get("BW_SESSION") == "session-key-abc123"
    backend.lock()


def test_appdata_dir_is_private_and_removed_on_lock() -> None:
    runner = happy_runner()
    backend = make_backend(runner)

    backend.account_email()

    data_dir = runner.calls[0][1]["BITWARDENCLI_APPDATA_DIR"]
    path = Path(data_dir)
    assert path.is_dir()
    assert (path.stat().st_mode & 0o777) == 0o700
    for _argv, env in runner.calls:
        assert env["BITWARDENCLI_APPDATA_DIR"] == data_dir

    backend.lock()
    assert not path.exists()
    backend.lock()  # safe to call twice


def test_node_extra_ca_certs_set_from_ca_bundle_path(tmp_path: Path) -> None:
    ca_bundle = tmp_path / "ca.pem"
    ca_bundle.write_text("fake-ca")
    runner = happy_runner()
    backend = make_backend(runner, ca_bundle_path=ca_bundle)

    backend.account_email()

    for _argv, env in runner.calls:
        assert env["NODE_EXTRA_CA_CERTS"] == str(ca_bundle)
    backend.lock()


# -- item/folder operations -------------------------------------------------------------


def test_list_items_parses_json_and_adds_trash_flag() -> None:
    runner = happy_runner()
    runner.when(_is("list"), stdout=json.dumps([{"id": "1", "name": "n"}]))
    backend = make_backend(runner)

    items = backend.list_items(include_trash=True)

    assert items == [{"id": "1", "name": "n"}]
    list_call = next(argv for argv, _env in runner.calls if argv[1] == "list")
    assert "--trash" in list_call
    backend.lock()


def test_list_items_without_trash_omits_flag() -> None:
    runner = happy_runner()
    runner.when(_is("list"), stdout="[]")
    backend = make_backend(runner)

    backend.list_items()

    list_call = next(argv for argv, _env in runner.calls if argv[1] == "list")
    assert "--trash" not in list_call
    backend.lock()


def test_create_item_sends_base64_json_round_trip() -> None:
    runner = happy_runner()
    record = {"type": 1, "name": "Example", "login": {"username": "u"}}
    runner.when(_is("create"), stdout=json.dumps(record))
    backend = make_backend(runner)

    result = backend.create_item(record)

    assert result == record
    create_call = next(argv for argv, _env in runner.calls if argv[1] == "create")
    assert create_call[2] == "item"
    encoded = create_call[3]
    decoded = json.loads(base64.b64decode(encoded).decode("utf-8"))
    assert decoded == record
    backend.lock()


def test_edit_item_sends_base64_json_with_item_id() -> None:
    runner = happy_runner()
    record = {"type": 1, "name": "Renamed"}
    runner.when(_is("edit"), stdout=json.dumps(record))
    backend = make_backend(runner)

    result = backend.edit_item("item-id-1", record)

    assert result == record
    edit_call = next(argv for argv, _env in runner.calls if argv[1] == "edit")
    assert edit_call[2:4] == ["item", "item-id-1"]
    decoded = json.loads(base64.b64decode(edit_call[4]).decode("utf-8"))
    assert decoded == record
    backend.lock()


def test_get_item_returns_parsed_record() -> None:
    runner = happy_runner()
    record = {"id": "abc", "name": "Item"}
    runner.when(_is("get"), stdout=json.dumps(record))
    backend = make_backend(runner)

    assert backend.get_item("abc") == record
    backend.lock()


def test_list_folders_returns_parsed_records() -> None:
    runner = happy_runner()
    folders = [{"id": "f1", "name": "Personal"}]
    runner.when(_is("list"), stdout=json.dumps(folders))
    backend = make_backend(runner)

    assert backend.list_folders() == folders
    backend.lock()


def test_create_folder_encodes_name() -> None:
    runner = happy_runner()
    runner.when(_is("create"), stdout=json.dumps({"id": "f2", "name": "Work"}))
    backend = make_backend(runner)

    result = backend.create_folder("Work")

    assert result == {"id": "f2", "name": "Work"}
    create_call = next(argv for argv, _env in runner.calls if argv[1] == "create")
    decoded = json.loads(base64.b64decode(create_call[3]).decode("utf-8"))
    assert decoded == {"name": "Work"}
    backend.lock()


# -- run() passthrough -------------------------------------------------------------------


@pytest.mark.parametrize(
    "managed", ["login", "logout", "unlock", "lock", "config", "serve"]
)
def test_run_refuses_managed_commands(managed: str) -> None:
    backend = make_backend(happy_runner())

    with pytest.raises(BwCliError):
        backend.run(managed)


def test_run_refuses_session_flag() -> None:
    backend = make_backend(happy_runner())

    with pytest.raises(BwCliError):
        backend.run("get", "item", "id", "--session", "whatever")


def test_run_refuses_secret_bearing_argument() -> None:
    backend = make_backend(happy_runner())

    with pytest.raises(BwCliError):
        backend.run("generate", MASTER_PASSWORD)

    with pytest.raises(BwCliError):
        backend.run("generate", CLIENT_SECRET)


def test_run_passes_through_other_commands() -> None:
    runner = happy_runner()
    runner.when(_is("generate"), stdout="Xy9!aB2c\n")
    backend = make_backend(runner)

    output = backend.run("generate", "--length", "8")

    assert output == "Xy9!aB2c\n"
    generate_call = next(argv for argv, _env in runner.calls if argv[1] == "generate")
    assert generate_call[2:4] == ["--length", "8"]
    backend.lock()


# -- error handling -----------------------------------------------------------------------


def test_command_failure_raises_bw_cli_error_with_redacted_secrets() -> None:
    runner = happy_runner()
    runner.when(
        _is("sync"),
        stderr=f"sync failed for password {MASTER_PASSWORD} and secret {CLIENT_SECRET}",
        returncode=1,
    )
    backend = make_backend(runner)

    with pytest.raises(BwCliError) as excinfo:
        backend.account_email()

    assert excinfo.value.command == "sync"
    message = str(excinfo.value)
    assert MASTER_PASSWORD not in message
    assert CLIENT_SECRET not in message
    assert "[REDACTED]" in message


def test_invalid_json_raises_bw_cli_error() -> None:
    runner = happy_runner()
    runner.when(_is("list"), stdout="not json")
    backend = make_backend(runner)

    with pytest.raises(BwCliError):
        backend.list_items()
    backend.lock()


def test_session_key_redacted_from_later_failures() -> None:
    runner = happy_runner()
    runner.when(_is("list"), stderr="boom session-key-abc123 leaked", returncode=1)
    backend = make_backend(runner)

    with pytest.raises(BwCliError) as excinfo:
        backend.list_items()

    assert "session-key-abc123" not in str(excinfo.value)
    backend.lock()

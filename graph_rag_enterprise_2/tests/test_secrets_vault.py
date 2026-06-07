import sys
import types
import os

from infra.secrets import SecretsManager


def test_secrets_manager_reads_from_vault(monkeypatch, tmp_path):
    # Prepare fake hvac module with Client that returns expected structure
    hvac_mod = types.SimpleNamespace()

    class FakeKVV2:
        def read_secret_version(self, path):
            return {"data": {"data": {"NEO4J_PASSWORD": "vault-pass"}}}

    class FakeKV:
        def __init__(self):
            self.v2 = FakeKVV2()

    class FakeSecrets:
        def __init__(self):
            self.kv = FakeKV()

    class FakeClient:
        def __init__(self, url=None, token=None):
            self.secrets = FakeSecrets()

    hvac_mod.Client = FakeClient

    # Inject into sys.modules so SecretsManager lazy-import finds it
    monkeypatch.setitem(sys.modules, "hvac", hvac_mod)

    # Set Vault env vars to trigger Vault path
    monkeypatch.setenv("VAULT_ADDR", "http://vault:8200")
    monkeypatch.setenv("VAULT_TOKEN", "sometoken")
    monkeypatch.setenv("VAULT_SECRET_PATH", "secret/data/graph-rag")

    # Ensure no env var or file overrides exist
    monkeypatch.delenv("NEO4J_PASSWORD", raising=False)
    path = tmp_path / "varrun"
    path.mkdir()

    sm = SecretsManager()
    val = sm.get("NEO4J_PASSWORD", default=None)
    assert val == "vault-pass"

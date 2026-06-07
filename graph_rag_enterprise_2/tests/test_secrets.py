import os
import sys
import types
from infra.secrets import SecretsManager, get_secret


def test_get_secret_env(monkeypatch):
    monkeypatch.setenv('MYSECRET', 'envval')
    sm = SecretsManager()
    assert sm.get('MYSECRET') == 'envval'
    assert get_secret('MYSECRET') == 'envval'


def test_get_secret_file(monkeypatch, tmp_path):
    p = tmp_path / 'secret.txt'
    p.write_text('fileval')
    # unset any direct env
    monkeypatch.delenv('MYSECRET', raising=False)
    monkeypatch.setenv('MYSECRET_FILE', str(p))
    sm = SecretsManager()
    assert sm.get('MYSECRET') == 'fileval'


def test_get_secret_vault(monkeypatch):
    # ensure no direct env value
    monkeypatch.delenv('NEO4J_PASSWORD', raising=False)
    # set Vault env markers
    monkeypatch.setenv('VAULT_ADDR', 'http://fake-vault')
    monkeypatch.setenv('VAULT_TOKEN', 'fake-token')
    monkeypatch.setenv('VAULT_SECRET_PATH', 'secret/data/graph')

    # create a fake hvac module with Client returning the expected structure
    class FakeKVV2:
        @staticmethod
        def read_secret_version(path):
            return {'data': {'data': {'NEO4J_PASSWORD': 'vaultval'}}}

    class FakeKV:
        v2 = FakeKVV2()

    class FakeSecrets:
        kv = FakeKV()

    class FakeClient:
        def __init__(self, url, token):
            self.url = url
            self.token = token

        @property
        def secrets(self):
            return FakeSecrets()

    fake_hvac = types.SimpleNamespace(Client=FakeClient)
    monkeypatch.setitem(sys.modules, 'hvac', fake_hvac)

    sm = SecretsManager()
    assert sm.get('NEO4J_PASSWORD') == 'vaultval'

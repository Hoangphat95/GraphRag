"""Secrets helper: read from env, files (K8s), or Vault (optional).

This module provides a small `SecretsManager` abstraction used by the app to
retrieve secrets in a test-friendly way. It prefers environment variables,
then file-based secrets (mounted by k8s), and falls back to Vault when
configured and hvac is available.
"""
import os
import logging

logger = logging.getLogger(__name__)


class SecretsManager:
    def __init__(self, env_prefix: str = ""):
        self.env_prefix = env_prefix

    def _env_key(self, key: str) -> str:
        return f"{self.env_prefix}{key}"

    def get(self, key: str, default: str = None) -> str:
        """Get secret value from env, file path, or Vault.

        Order of resolution:
        1. Environment variable `env_prefix + key`
        2. File at `/var/run/secrets/{key}` or path specified by env var
           `<PREFIX><KEY>_FILE` (Kubernetes convention)
        3. Vault if `VAULT_ADDR` and `VAULT_TOKEN` and `VAULT_SECRET_PATH` set
        """
        # 1) environment
        env_key = self._env_key(key)
        val = os.environ.get(env_key)
        if val:
            return val

        # 2) file-based secret: either <ENV>_FILE or conventional path
        file_env = os.environ.get(env_key + "_FILE")
        if file_env and os.path.exists(file_env):
            try:
                return open(file_env, "r", encoding="utf-8").read().strip()
            except Exception:
                logger.exception("Failed reading secret file %s", file_env)

        # k8s-style mount path
        path = f"/var/run/secrets/{key}"
        if os.path.exists(path):
            try:
                return open(path, "r", encoding="utf-8").read().strip()
            except Exception:
                logger.exception("Failed reading secret file %s", path)

        # 3) optional Vault
        try:
            vault_addr = os.environ.get("VAULT_ADDR")
            vault_token = os.environ.get("VAULT_TOKEN")
            vault_path = os.environ.get("VAULT_SECRET_PATH")
            if vault_addr and vault_token and vault_path:
                # lazy import hvac to avoid hard dependency in test/CI
                try:
                    import hvac
                except Exception:
                    logger.warning("hvac not installed; skipping Vault secret fetch")
                    return default

                try:
                    client = hvac.Client(url=vault_addr, token=vault_token)
                    # read generic secret at specified path
                    secret = client.secrets.kv.v2.read_secret_version(path=vault_path)
                    data = secret.get("data", {}).get("data", {})
                    if key in data:
                        return data[key]
                except Exception:
                    logger.exception("Vault secret read failed")
        except Exception:
            logger.exception("Vault fetch setup failed")

        return default


# module-level convenience instance using no prefix
_default = SecretsManager()


def get_secret(key: str, default: str = None) -> str:
    return _default.get(key, default=default)
# end of module

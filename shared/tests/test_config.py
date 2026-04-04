"""shared/config.py 単体テスト"""

import importlib
import json
import logging
import tempfile

import pytest
import yaml


@pytest.fixture(autouse=True)
def _reset_config_cache(monkeypatch, tmp_path):
    """テストごとに config モジュールのキャッシュをリセットする。"""
    import config as cfg_module
    cfg_module._config = None
    yield
    cfg_module._config = None


@pytest.fixture()
def config_file(tmp_path, monkeypatch):
    """一時 YAML を作成し CONFIG_PATH を差し替えるヘルパー。"""
    def _create(data: dict):
        path = tmp_path / "application.yml"
        path.write_text(yaml.dump(data, allow_unicode=True), encoding="utf-8")
        import config as cfg_module
        cfg_module.CONFIG_PATH = path
        cfg_module._config = None  # キャッシュクリア
        return path
    return _create


# === load_config ===

class TestLoadConfig:
    def test_load_valid_yaml(self, config_file):
        config_file({"gcp": {"project_id": "test-project"}})
        from config import load_config
        cfg = load_config()
        assert cfg["gcp"]["project_id"] == "test-project"

    def test_load_missing_file_returns_empty(self, tmp_path):
        import config as cfg_module
        cfg_module.CONFIG_PATH = tmp_path / "nonexistent.yml"
        cfg_module._config = None
        cfg = cfg_module.load_config()
        assert cfg == {}

    def test_load_caches_result(self, config_file):
        config_file({"key": "value"})
        from config import load_config
        first = load_config()
        second = load_config()
        assert first is second


# === get ===

class TestGet:
    def test_dot_notation_access(self, config_file):
        config_file({"gcp": {"project_id": "my-proj", "region": "asia-northeast1"}})
        from config import get
        assert get("gcp.project_id") == "my-proj"
        assert get("gcp.region") == "asia-northeast1"

    def test_top_level_key(self, config_file):
        config_file({"debug": True})
        from config import get
        assert get("debug") is True

    def test_missing_key_returns_default(self, config_file):
        config_file({"gcp": {}})
        from config import get
        assert get("gcp.nonexistent") is None
        assert get("gcp.nonexistent", "fallback") == "fallback"

    def test_deeply_nested(self, config_file):
        config_file({"a": {"b": {"c": {"d": 42}}}})
        from config import get
        assert get("a.b.c.d") == 42

    def test_missing_intermediate_key(self, config_file):
        config_file({"a": {"b": 1}})
        from config import get
        assert get("a.x.y") is None


# === setup_logging ===

class TestSetupLogging:
    def test_returns_logger(self, config_file):
        config_file({})
        from config import setup_logging
        log = setup_logging("test-logger")
        assert isinstance(log, logging.Logger)
        assert log.name == "test-logger"
        assert log.level == logging.INFO

    def test_idempotent(self, config_file):
        config_file({})
        from config import setup_logging
        log1 = setup_logging("test-idempotent")
        handler_count = len(log1.handlers)
        log2 = setup_logging("test-idempotent")
        assert log1 is log2
        assert len(log2.handlers) == handler_count

import pytest

from core.config import load_config, ConfigError


def test_load_valid_config(monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "123:ABC")
    monkeypatch.setenv("TELEGRAM_USER_IDS", "111,222")
    cfg = load_config()
    assert cfg["telegram"]["token"] == "123:ABC"
    assert cfg["telegram"]["allowed_users"] == [111, 222]


def test_load_config_single_user(monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "123:ABC")
    monkeypatch.setenv("TELEGRAM_USER_IDS", "111")
    cfg = load_config()
    assert cfg["telegram"]["allowed_users"] == [111]


def test_load_config_missing_token(monkeypatch):
    monkeypatch.setenv("TELEGRAM_USER_IDS", "111")
    monkeypatch.delenv("TELEGRAM_TOKEN", raising=False)
    with pytest.raises(ConfigError, match="TELEGRAM_TOKEN"):
        load_config()


def test_load_config_missing_user_ids(monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "123:ABC")
    monkeypatch.delenv("TELEGRAM_USER_IDS", raising=False)
    with pytest.raises(ConfigError, match="TELEGRAM_USER_IDS"):
        load_config()


def test_load_config_invalid_user_ids(monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "123:ABC")
    monkeypatch.setenv("TELEGRAM_USER_IDS", "abc,def")
    with pytest.raises(ConfigError, match="integers"):
        load_config()


def test_load_config_strips_whitespace(monkeypatch):
    monkeypatch.setenv("TELEGRAM_TOKEN", "  123:ABC  ")
    monkeypatch.setenv("TELEGRAM_USER_IDS", " 111 , 222 ")
    cfg = load_config()
    assert cfg["telegram"]["token"] == "123:ABC"
    assert cfg["telegram"]["allowed_users"] == [111, 222]

import os


class ConfigError(Exception):
    pass


def load_config() -> dict:
    """Load config from environment variables.

    Required env vars:
        TELEGRAM_TOKEN      — Bot token from @BotFather
        TELEGRAM_USER_IDS   — Comma-separated allowed user IDs
    """
    token = os.environ.get("TELEGRAM_TOKEN", "").strip()
    user_ids_raw = os.environ.get("TELEGRAM_USER_IDS", "").strip()

    if not token:
        raise ConfigError(
            "TELEGRAM_TOKEN environment variable is required. "
            "Get one from @BotFather on Telegram."
        )
    if not user_ids_raw:
        raise ConfigError(
            "TELEGRAM_USER_IDS environment variable is required. "
            "Get your ID from @userinfobot on Telegram."
        )

    try:
        allowed_users = [int(uid.strip()) for uid in user_ids_raw.split(",") if uid.strip()]
    except ValueError:
        raise ConfigError("TELEGRAM_USER_IDS must be comma-separated integers")

    if not allowed_users:
        raise ConfigError("TELEGRAM_USER_IDS must contain at least one user ID")

    return {
        "telegram": {
            "token": token,
            "allowed_users": allowed_users,
        }
    }

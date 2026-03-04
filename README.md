# lobster-bot

A personal AI assistant on Telegram, powered by Claude Code.

Clone it, set two env vars, and you have a 24/7 AI assistant that can search the web, remember things about you, and run on a schedule.

## Quick Start

```bash
git clone https://github.com/aflekkas/lobster-bot.git
cd lobster-bot
pip install -r requirements.txt
```

Create a `.env` file:

```bash
TELEGRAM_TOKEN=your-bot-token-here
TELEGRAM_USER_IDS=your-user-id-here
```

Run:

```bash
set -a && source .env && set +a
python run.py
```

## Getting a Telegram Bot Token

1. Message [@BotFather](https://t.me/BotFather) on Telegram
2. Send `/newbot` and follow the prompts
3. Copy the token into your `.env`

## Finding Your Telegram User ID

Message [@userinfobot](https://t.me/userinfobot) on Telegram — it will reply with your user ID.

## Requirements

- Python 3.11+
- Claude Code CLI (`claude`) installed and authenticated
- Node.js (for Playwright MCP — web browsing)
- A Telegram bot token

## Deploy on Hostinger VPS

SSH into your VPS:

```bash
ssh root@your-server-ip
```

Install prerequisites:

```bash
apt update && apt install -y python3 python3-pip git
# Install Claude Code CLI: https://docs.anthropic.com/en/docs/claude-code
```

Clone and set up:

```bash
git clone https://github.com/aflekkas/lobster-bot.git ~/lobster-bot
cd ~/lobster-bot
pip install -r requirements.txt
```

Create your `.env`:

```bash
cat > ~/lobster-bot/.env << 'EOF'
TELEGRAM_TOKEN=your-bot-token-here
TELEGRAM_USER_IDS=your-user-id-here
EOF
```

Install the systemd service:

```bash
cp deploy/systemd/lobster-bot.service /etc/systemd/system/
systemctl daemon-reload
systemctl enable --now lobster-bot
```

Check it's running:

```bash
systemctl status lobster-bot
journalctl -u lobster-bot -f
```

Update to latest:

```bash
cd ~/lobster-bot && git pull && systemctl restart lobster-bot
```

## Commands

- `/new` — Start a new conversation
- `/usage` — Cost and token stats
- `/status` — Session info
- `/help` — Available commands

## How It Works

```
Telegram message → python-telegram-bot → claude -p --output-format json → Telegram response
```

- Messages are sent to Claude Code via subprocess (`claude -p`)
- SQLite tracks sessions (conversation continuity) and usage (cost/tokens)
- The bot auto-pulls updates from git every 5 minutes
- `.claude/settings.json` enforces a security boundary on what Claude can do

## Project Structure

```
lobster-bot/
├── core/
│   ├── bot.py         # Telegram handlers
│   ├── bridge.py      # Claude Code subprocess wrapper
│   ├── session.py     # SQLite session + usage tracking
│   └── config.py      # Env var config loader
├── .claude/
│   └── settings.json  # Permission boundary
├── deploy/
│   └── systemd/       # Service file
├── memory/            # Bot's memory (created at runtime)
├── CLAUDE.md          # Bot personality + instructions
├── run.py             # Entry point
└── .env               # Your secrets (gitignored)
```

## License

MIT

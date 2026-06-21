#!/bin/sh
set -e
uv run pytest test_discord_google_calendar_bot.py -q
touch /tmp/healthy
exec uv run python discord_google_calendar_bot.py

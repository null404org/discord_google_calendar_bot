#!/bin/bash -

cd /opt/discord_google_calendar_bot

source .venv/bin/activate

source docker_env.conf
export AWS_DEFAULT_REGION
export AWS_ACCESS_KEY_ID
export AWS_SECRET_ACCESS_KEY

python discord_google_calendar_bot.py

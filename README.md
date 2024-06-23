# discord_google_calendar_bot
Discord bot that pushes scheduled events to Google Calendar

This is a Python program that integrates a Discord bot with the Google Calendar
API. The bot listens for scheduled events created in a Discord server, and
automatically creates corresponding events in a Google Calendar.

The program uses the following key components:

- Discord API client: Handles the connection to the Discord API and listens for scheduled event updates.
- Google Calendar API client: Interacts with the Google Calendar API to create, update, and delete calendar events.
- AWS Secrets Manager: Securely stores the necessary credentials and API keys for the Discord and Google Calendar APIs.

The program is designed to run as a persistent service, rather than a
short-lived AWS Lambda function. It should be deployed as a systemctl service
on a Linux machine, so that it starts automatically at boot time.

Usage:
1. Set up the necessary AWS Secrets Manager secrets.
2. Run the program on a Linux machine with the required dependencies installed.
3. The bot will automatically connect to the Discord API and synchronize scheduled events with the Google Calendar.

# Requirements

You need to run this on a Debian-based Linux server, like Ubuntu. If you 
want to run it as a Docker container, you need to install 
[Docker Engine (Docker CE)](https://docs.docker.com/engine/install/ubuntu/) first.

# Installation

Clone the bot from this repo, go into the downloaded folder, and run the 
initial `setup.sh` script:

```bash
git clone https://github.com/null404org/discord_google_calendar_bot.git
cd discord_google_calendar_bot
/bin/bash setup.sh
```

To run this bot as a systemd service:

```bash
/bin/bash install_and_start_with_systemd.sh
```

To run this bot as a Docker container:

```bash
/bin/bash install_and_start_with_docker.sh
```

Take notice of the output of the installation scripts, where you will see
useful bot service management and monitoring commands.
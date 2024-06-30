# discord_google_calendar_bot

Discord bot that pushes scheduled events to Google Calendar

# Overview

This is a Python program that integrates a Discord bot with the Discord "Gateway" API, Google Calendar API, and AWS API. The bot listens for scheduled events created in a Discord server, and automatically creates corresponding events in a Google Calendar. All API keys and bot configuration are securely stored in and accessed from the AWS Secrets Manager service. 

Once the bot is properly set up and running, you should be able to simply create and manage your Discord scheduled events in Discord, where all of those immediately show up in your chosen Google Calendar, perfectly mirroring what you've set up in Discord. If you accidentally delete any managed calendar item from Google, simply restarting the bot will automatically recreate them all in your Google Calendar. You can also restore such a deleted Google Calendar item by doing a simple change to the corresponding Discord Scheduled Event.

The program uses the following key components:

- Discord API client: Handles the connection to the Discord API and persistenly listens for scheduled event updates
- Google Calendar API client: Interacts with the Google Calendar API to create, update, and delete calendar events
- AWS Secrets Manager: Securely stores the necessary credentials and API keys for the Discord and Google Calendar APIs

The bot program is designed to run as a persistent service, rather than a short-lived AWS Lambda function. It should be deployed on a persistent Linux instance either as a systemd service OR a Docker container, so that it starts automatically at boot time. 

NOTE: Only ONE instance of this bot should run at any time.

Usage:
1. Set up the necessary AWS Secrets Manager secrets
2. Run the program on a Linux machine with the required dependencies installed
3. The bot will automatically connect to the Discord API and synchronize any Discord Scheduled Events the user creates in Discord with the user's chosen Google Calendar

## Potential Future Development

- Sanitize Discord Scheduled Event user input by validating received Discord Scheduled Event objects against publicly available schema provided by Discord documentation
- Add unit tests

# Requirements

You need to run this on a Debian-based Linux server, like Ubuntu. If you want to run it as a Docker container, you need to install [Docker Engine (Docker CE)](https://docs.docker.com/engine/install/ubuntu/) first.

# Installation/Upgrade

## Create a Discord Bot Account

1. Follow these [Discord bot account creation instructions](https://discordpy.readthedocs.io/en/stable/discord.html)
2. Make sure you save the token (API Key) securely for future reference (ie. in Keepass)
3. Make sure to visit the Oauth2 Invite URL you created in your web browser and invite the bot to a Discord server you have admin rights on. This invite step is a one-time action.

## Create a Google API Service Account and Share Your Google Calendar With It

1. Follow these [Google API Service Account creation/setup instructions](https://medium.com/iceapple-tech-talks/integration-with-google-calendar-api-using-service-account-1471e6e102c8)
2. When following this procedure, make sure to skip everything after and including the "Enable Domain-wide delegation" part, as that is not needed to make this work. The one exception is that you do need to do the "Add Key in the Service Account", as this is where you get the actual API key JSON block
3. The "New Project" button is hidden the project selector drop down menu
4. Name the project: discord-google-calendar-bot
5. When enabling the Google Calendar API, go to Quick Access > APIs & Services > Filter > Google Calendar > Select "Google Calendar API" > Enable API
6. To get to "IAM & Admin" section, select the link for your newly created service account in the "Credentials" section
7. Make sure you save the service account email addresss (This is a fake email address used when sharing a calendar with the service account)
8. Go to your web version of your Google Calendar > Find the calendar you want to share on the left-hand side and hover your mouse over it > Click the three-dot menu right next to that calendar > Select "Settings and sharing" > Integrate Calendar
9. Make sure you save the email address listed right under "Calendar ID" (You will save this in AWS Secrets, later)
10. When adding a key to the service account, make sure you securely save the JSON block, as this is your Google API key

## AWS Secrets Setup

1. Either log into your existing AWS account or create a free-tier AWS account
2. Go to "Secrets Manager" and create a secret called "discord-google-calendar-bot"
3. Create three key-value secret pairs as follows:

| Key | Value description |
|---|---|
| DISCORD_TOKEN | This comes from the Discord Developer Application settings of your bot and is a long hex string |
| GOOGLE_CREDENTIALS_JSON | This comes from the Google API Services Account procedure and is a big JSON block |
| CALENDAR_ID | This comes from your Google Calendar sharing settings and looks like an email address |

NOTE: Make * sure * you either copy/paste the key names as they are or type them in UPPER CASE

## Bot Deployment/Upgrade

If you're doing an initial installation:

```bash
git clone https://github.com/null404org/discord_google_calendar_bot.git
cd discord_google_calendar_bot
```

If you're doing an upgrade:

```bash
cd discord_google_calendar_bot
git pull
```

Run the initial setup script. This prepares the needed Python virtual environment that allows the bot to use its own Python interpreter and Python dependencies, completely aside from whatever Python stuff you've installed at the user or system level:

```
/bin/bash setup.sh
```

Either run this bot as a systemd service:

```bash
/bin/bash install_and_start_with_systemd.sh
```

OR

Run this bot as a Docker container:

```bash
/bin/bash install_and_start_with_docker.sh
```

# Useful Bot Management/Monitoring/Uninstall Commands

## Systemd

| Desired effect          | Command                                            |
|-------------------------|----------------------------------------------------|
| Start the bot           | sudo systemctl start discord-google-calendar-bot   |
| Stop the bot            | sudo systemctl stop discord-google-calendar-bot    |
| Restart the bot         | sudo systemctl restart discord-google-calendar-bot |
| Get status of the bot   | sudo systemctl status discord-google-calendar-bot  |
| View the bot logs, live | sudo journalctl -fu discord-google-calendar-bot    |

To stop the bot and remove it completely from systemd:

```
sudo systemctl stop discord-google-calendar-bot
sudo systemctl disable discord-google-calendar-bot
sudo rm -rf /opt/discord_google_calendar_bot
sudo rm /etc/systemd/system/discord-google-calendar-bot.service
sudo userdel -r discord_google_calendar_bot
```

NOTE: Be * extremely * careful when running any command with "rm -rf" in it. Make sure to type it in * exactly * as you see here, or just copy/paste it, as-is.

## Docker

| Desired effect          | Command                                       |
|-------------------------|-----------------------------------------------|
| Start the bot           | docker start discord_google_calendar_bot      |
| Stop the bot            | docker stop discord_google_calendar_bot       |
| Restart the bot         | docker restart discord_google_calendar_bot    |
| Get status of the bot   | docker ps \| grep discord_google_calendar_bot |
| View the bot logs, live | docker logs discord_google_calendar_bot -f    |

To stop the running bot and remove all traces of it from Docker:

```
docker stop discord_google_calendar_bot
docker rm discord_google_calendar_bot
docker image rm discord_google_calendar_bot
```

#!/bin/bash
# This script installs the Discord bot as a systemd service.

# Variables
INSTALL_DIR=/opt/discord_google_calendar_bot
USERNAME="discord_google_calendar_bot"
GROUPNAME="discord_google_calendar_bot"

# Verify that the AWS CLI is installed and properly configured
if [ ! -d ~/.aws ]; then
  echo "Please install and properly configure the AWS CLI first."
  exit 1
fi

# Convert your AWS CLI credentials into a Docker environment variable file
cat ~/.aws/config ~/.aws/credentials | grep = | grep -v output | \
  sed -e 's/region/AWS_DEFAULT_REGION/' | tr -d ' ' | \
  awk -F= '{print toupper($1) "=" $2}' > ~/.aws/docker_env.conf
chmod 600 ~/.aws/docker_env.conf

# Create a non-root bot user to run the bot as
sudo groupadd $GROUPNAME
sudo useradd -r -m -g $GROUPNAME -s /usr/sbin/nologin $USERNAME
sudo passwd -l $USERNAME

sudo mkdir -p $INSTALL_DIR
sudo cp -rp .venv run_discord_google_calendar_bot.sh ~/.aws/docker_env.conf \
  discord_google_calendar_bot.py $INSTALL_DIR
sudo cp -p discord-google-calendar-bot.service /etc/systemd/system/
sudo chown -R $USERNAME:$GROUPNAME $INSTALL_DIR
sudo chmod 700 $INSTALL_DIR/
sudo chmod 700 $INSTALL_DIR/.venv
sudo chmod 400 $INSTALL_DIR/docker_env.conf
sudo chmod 400 $INSTALL_DIR/discord_google_calendar_bot.py
sudo chmod 700 $INSTALL_DIR/run_discord_google_calendar_bot.sh
sudo systemctl daemon-reload
sudo systemctl enable discord-google-calendar-bot
sudo systemctl start discord-google-calendar-bot

# Print instructions for manipulating the bot
echo ""
echo "The bot has been started as a systemd service:"
echo ""
SYSTEMD_PAGER=cat systemctl status discord-google-calendar-bot
echo ""
echo "Other operational things you can do with the container:"
echo ""
echo "sudo systemctl start discord-google-calendar-bot"
echo "sudo systemctl stop discord-google-calendar-bot"
echo "sudo systemctl restart discord-google-calendar-bot"
echo "sudo journalctl -fu discord-google-calendar-bot"
echo ""
echo "To stop the bot and remove it completely:"
echo ""
echo "sudo systemctl stop discord-google-calendar-bot"
echo "sudo systemctl disable discord-google-calendar-bot"
echo "sudo rm -rf /opt/discord_google_calendar_bot"
echo "sudo rm /etc/systemd/system/discord-google-calendar-bot.service"
echo "sudo userdel -r discord_google_calendar_bot"
echo ""

#!/bin/bash
# This script installs the Discord bot as a systemd service.

# Variables
SYSTEMD_SERVICE="discord_google_calendar_bot"
INSTALL_DIR=/opt/$SYSTEMD_SERVICE
USERNAME="$SYSTEMD_SERVICE"
GROUPNAME="$SYSTEMD_SERVICE"

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
sudo cp -rp .venv run_$SYSTEMD_SERVICE.sh ~/.aws/docker_env.conf \
  $SYSTEMD_SERVICE.py $INSTALL_DIR
sudo cp -p $SYSTEMD_SERVICE.service /etc/systemd/system/
sudo chown -R $USERNAME:$GROUPNAME $INSTALL_DIR
sudo chmod 700 $INSTALL_DIR/
sudo chmod 700 $INSTALL_DIR/.venv
sudo chmod 400 $INSTALL_DIR/docker_env.conf
sudo chmod 400 $INSTALL_DIR/$SYSTEMD_SERVICE.py
sudo chmod 700 $INSTALL_DIR/run_$SYSTEMD_SERVICE.sh
sudo systemctl daemon-reload
sudo systemctl enable $SYSTEMD_SERVICE

if systemctl is-active --quiet "$SYSTEMD_SERVICE"; then
  echo "Restart running service '$SYSTEMD_SERVICE'"
  sudo systemctl restart $SYSTEMD_SERVICE
else
  echo "Start service '$SYSTEMD_SERVICE'"
  sudo systemctl start $SYSTEMD_SERVICE
fi

# Print instructions for manipulating the bot
echo ""
echo "The bot is running as a systemd service:"
echo ""
SYSTEMD_PAGER=cat systemctl status $SYSTEMD_SERVICE
echo ""
echo "Other operational things you can do with the bot:"
echo ""
echo "sudo systemctl start $SYSTEMD_SERVICE"
echo "sudo systemctl stop $SYSTEMD_SERVICE"
echo "sudo systemctl restart $SYSTEMD_SERVICE"
echo "sudo systemctl status $SYSTEMD_SERVICE"
echo "sudo journalctl -fu $SYSTEMD_SERVICE"
echo ""
echo "To stop the bot and remove it completely:"
echo ""
echo "sudo systemctl stop $SYSTEMD_SERVICE"
echo "sudo systemctl disable $SYSTEMD_SERVICE"
echo "sudo rm -rf /opt/$SYSTEMD_SERVICE"
echo "sudo rm /etc/systemd/system/$SYSTEMD_SERVICE.service"
echo "sudo userdel -r $SYSTEMD_SERVICE"
echo ""

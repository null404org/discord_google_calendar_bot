#!/bin/bash
# This script installs the Discord bot as a Docker container. It expects
# that Docker is installed and configured correctly on the system.

# Verify that Docker is installed
if [ ! $(command -v docker) ]; then
  echo "Please install Docker first."
  exit 1
fi

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

# Build the Docker image
docker build -t discord_google_calendar_bot .

# Start the bot as a Docker container
docker run --name="discord_google_calendar_bot" \
  --env-file=$HOME/.aws/docker_env.conf -d discord_google_calendar_bot

# Print instructions for manipulating the bot
echo ""
echo "The bot has been started as a Docker container:"
echo ""
docker ps | grep discord_google_calendar_bot
echo ""
echo "Other operational things you can do with the container:"
echo ""
echo "docker start discord_google_calendar_bot"
echo "docker stop discord_google_calendar_bot"
echo "docker restart discord_google_calendar_bot"
echo "docker logs discord_google_calendar_bot -f"
echo ""
echo "To stop the bot and remove the docker container and image completely:"
echo ""
echo "docker stop discord_google_calendar_bot"
echo "docker rm discord_google_calendar_bot"
echo "docker image rm discord_google_calendar_bot"
echo ""

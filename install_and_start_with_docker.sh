#!/bin/bash
# This script installs the Discord bot as a Docker container. It expects
# that Docker is installed and configured correctly on the system.

CONTAINER_NAME="discord_google_calendar_bot"

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
docker build -t $CONTAINER_NAME .

# Start the bot as a Docker container
if docker inspect --format '{{.State.Running}}' "$CONTAINER_NAME" 2>/dev/null | grep -q 'true'; then
  printf "Restarting existing Docker bot $CONTAINER_NAME: "
  docker restart $CONTAINER_NAME
else
  printf "Starting $CONTAINER_NAME as a Docker container: "
  docker run --name="$CONTAINER_NAME" \
    --env-file=$HOME/.aws/docker_env.conf -d $CONTAINER_NAME
fi

# Print instructions for manipulating the bot
echo ""
echo "The bot is now running as a Docker container: "
echo ""
docker ps | grep $CONTAINER_NAME
echo ""
echo "Other operational things you can do with the bot:"
echo ""
echo "docker start $CONTAINER_NAME"
echo "docker stop $CONTAINER_NAME"
echo "docker restart $CONTAINER_NAME"
echo "docker ps | grep $CONTAINER_NAME"
echo "docker logs $CONTAINER_NAME -f"
echo ""
echo "To stop the bot, removing the docker container and image completely:"
echo ""
echo "docker stop $CONTAINER_NAME"
echo "docker rm $CONTAINER_NAME"
echo "docker image rm $CONTAINER_NAME"
echo ""

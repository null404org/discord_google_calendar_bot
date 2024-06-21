"""
discord_google_calendar_bot

This is a Python program that integrates a Discord bot with the Google Calendar
API. The bot listens for scheduled events created in a Discord server, and
automatically creates corresponding events in a Google Calendar.

The program uses the following key components:

- Discord API client: Handles the connection to the Discord API and listens for
  scheduled event updates.
- Google Calendar API client: Interacts with the Google Calendar API to create,
  update, and delete calendar events.
- AWS Secrets Manager: Securely stores the necessary credentials and API keys
  for the Discord and Google Calendar APIs.

The program is designed to run as a persistent service, rather than a
short-lived AWS Lambda function. It should be deployed as a systemctl service
on a Linux machine, so that it starts automatically at boot time.

Usage:
    1. Set up the necessary AWS Secrets Manager secrets.
    2. Run the program on a Linux machine with the required dependencies
       installed.
    3. The bot will automatically connect to the Discord API and synchronize
       scheduled events with the Google Calendar.

Dependencies:
    - Python 3.7+
    - discord.py
    - google-api-python-client
    - google-auth
    - boto3

Author:
    warelock (2024-06-15)
"""

import json
import logging
import os
from datetime import datetime, timezone

import boto3
import discord
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.errors import HttpError

logger = logging.getLogger(__name__)
logging.basicConfig(level=os.environ.get("LOGLEVEL", "INFO"))

AWS_DEFAULT_REGION = os.environ.get("AWS_DEFAULT_REGION")
AWS_ACCESS_KEY_ID = os.environ.get("AWS_ACCESS_KEY_ID")
AWS_SECRET_ACCESS_KEY = os.environ.get("AWS_SECRET_ACCESS_KEY")

# Set some Google event appearance customizations
GOOGLE_EVENT_CHANNEL_NAME_PREFIX = "🔉 "
GOOGLE_EVENT_LOCATION_PREFIX = "📍 "

# AWS Secrets Manager Client
aws_client = boto3.client("secretsmanager")


# Retrieve all secrets for a given AWS secrets name
def get_aws_secret(secret_name):
    """
    Retrieves all secrets for a given AWS secrets name.

    Args:
        secret_name (str): The name of the AWS secrets.

    Returns:
        dict: A dictionary containing all secrets.
    """
    response = aws_client.get_secret_value(SecretId=secret_name)
    aws_secret = json.loads(response["SecretString"])
    return aws_secret


# Fetch secrets from AWS Secrets Manager
aws_secrets = get_aws_secret("discord-google-calendar-bot")
DISCORD_TOKEN = aws_secrets["DISCORD_TOKEN"]
GOOGLE_CREDENTIALS_JSON = aws_secrets["GOOGLE_CREDENTIALS_JSON"]
CALENDAR_ID = aws_secrets["CALENDAR_ID"]

# Discord API client setup
intents = discord.Intents.default()
intents.guild_scheduled_events = True
discord_client = discord.Client(intents=intents)

# Google Calendar API client setup
google_credentials = service_account.Credentials.from_service_account_info(
    json.loads(GOOGLE_CREDENTIALS_JSON)
)
google_client = build("calendar", "v3", credentials=google_credentials)


def create_google_event(discord_event):
    """
    Creates a Google Calendar event from a Discord event.

    Args:
        discord_event (discord.Event): The Discord event to be converted to
        a Google Calendar event.

    Returns:
        dict: A dictionary containing the details of the Google Calendar
        event, including the event ID, summary, location, description,
        start time, and end time.

    This function takes a Discord event object and generates a corresponding
    Google Calendar event. It sets the event summary to include the Discord
    server name, the event name, and the event type (voice or text). The
    location is set based on the event type, using either the channel name
    or a custom location prefix. The event description, start time, and end
    time are also extracted from the Discord event object and included in
    the Google Calendar event details.
    """
    google_event_summary_prefix = "Discord (" + discord_client.guilds[0].name + "): "

    if discord_event.entity_type is discord.EntityType.voice:
        end_time = discord_event.start_time
        location = GOOGLE_EVENT_CHANNEL_NAME_PREFIX + discord_event.channel.name
    else:
        end_time = discord_event.end_time
        location = GOOGLE_EVENT_LOCATION_PREFIX + discord_event.location

    google_event_details = {
        "id": str(discord_event.id),
        "summary": google_event_summary_prefix + discord_event.name,
        "location": location,
        "description": discord_event.description,
        "start": {
            "dateTime": discord_event.start_time.isoformat(),
            "timeZone": "UTC",
        },
        "end": {
            "dateTime": end_time.isoformat(),
            "timeZone": "UTC",
        },
    }

    # Create the calendar event based on Discord event ID and announce it to
    # the console
    try:
        google_client.events().insert(
            calendarId=CALENDAR_ID, body=google_event_details
        ).execute()
    except HttpError as error:
        if error.status_code == 409:
            update_google_event(discord_event, discord_event)
    else:
        logger.info("Google Calendar event created for %s", discord_event.name)


def update_google_event(old_discord_event, new_discord_event):
    """
    Updates a Google Calendar event based on changes in a Discord event.

    Args:
        old_discord_event (discord.Event): The previous version of the
        Discord event.
        new_discord_event (discord.Event): The updated version of the
        Discord event.

    This function takes the old and new versions of a Discord event and
    updates the corresponding Google Calendar event. It generates the event
    details, including the summary, location, description, start time,
    and end time, based on the information in the new Discord event.

    The function then uses the Google Calendar API to update the existing
    event in the calendar, using the event ID from the old Discord event.
    Finally, it prints a message to the console indicating that the Google
    Calendar event has been updated successfully.
    """
    google_event_summary_prefix = "Discord (" + discord_client.guilds[0].name + "): "

    if new_discord_event.entity_type is discord.EntityType.voice:
        discord_end_time = new_discord_event.start_time
        discord_location = (
            GOOGLE_EVENT_CHANNEL_NAME_PREFIX + new_discord_event.channel.name
        )
    else:
        discord_end_time = new_discord_event.end_time
        discord_location = GOOGLE_EVENT_LOCATION_PREFIX + new_discord_event.location

    google_event_details = {
        "id": str(new_discord_event.id),
        "summary": google_event_summary_prefix + new_discord_event.name,
        "location": discord_location,
        "description": new_discord_event.description,
        "start": {
            "dateTime": new_discord_event.start_time.isoformat(),
            "timeZone": "UTC",
        },
        "end": {
            "dateTime": discord_end_time.isoformat(),
            "timeZone": "UTC",
        },
    }

    # Update the calendar event based on Discord event ID and announce it to
    # the console
    google_client.events().update(
        calendarId=CALENDAR_ID,
        eventId=str(old_discord_event.id),
        body=google_event_details,
    ).execute()
    logger.info("Google Calendar event created for %s", new_discord_event.name)


@discord_client.event
async def on_ready():
    """
    Event handler that is called when the Discord client is ready and logged
    in.

    This function performs the following tasks:

    1. Prints a message to the console indicating that the Discord client
    has logged in.
    2. Generates a prefix for the Google Calendar event summaries,
    which includes the name of the Discord server.
    3. Retrieves all scheduled events from the first Discord server the
    client is connected to.
    4. Retrieves the current events from the Google Calendar.
    5. Compares the scheduled Discord events to the existing Google Calendar
    events, and creates new Google Calendar events for any Discord events
    that don't have a matching Google Calendar event.

    This function is automatically called by the Discord client when the
    connection is established and the client is ready to receive and send
    messages.
    """
    # Announce ourselves to the console
    logger.info("We have logged in as %s", discord_client.user)

    google_event_summary_prefix = "Discord (" + discord_client.guilds[0].name + "): "

    # Do an initial push of all Discord scheduled events to Google Calendar,
    # matching based on event summary field
    discord_guild = discord_client.guilds[0]
    discord_scheduled_events = discord_guild.scheduled_events

    # Get the date and time as UTC
    now = datetime.now(timezone.utc).replace(tzinfo=None).isoformat() + "Z"
    google_events_result = (
        google_client.events()
        .list(
            calendarId=CALENDAR_ID,
            timeMin=now,
            maxResults=50,
            singleEvents=True,
            orderBy="startTime",
        )
        .execute()
    )
    google_events = google_events_result.get("items", [])
    google_event_summaries = [d["summary"] for d in google_events]

    for discord_event in discord_scheduled_events:
        if (
            google_event_summary_prefix + discord_event.name
            not in google_event_summaries
        ):
            create_google_event(discord_event)


@discord_client.event
async def on_scheduled_event_create(discord_event):
    """
    Event handler that is called when a new scheduled event is created in
    Discord.

    Args:
        discord_event (discord.ScheduledEvent): The newly created Discord
        scheduled event.

    This function is automatically called by the Discord client whenever a
    new scheduled event is created. It takes the newly created Discord event
    as input and calls the `create_google_event()` function to create a
    corresponding event in the Google Calendar.

    The `create_google_event()` function is responsible for generating the
    details of the Google Calendar event, including the event summary,
    location, description, start time, and end time, based on the
    information in the Discord event.
    """
    create_google_event(discord_event)


# When Discord sends us an update for an existing event, update the matching
# Google Calendar event
@discord_client.event
async def on_scheduled_event_update(old_discord_event, new_discord_event):
    """
    Event handler that is called when a scheduled event is updated in Discord.

    Args:
        old_discord_event (discord.ScheduledEvent): The previous version of the
            Discord scheduled event.
        new_discord_event (discord.ScheduledEvent): The updated version of the
            Discord scheduled event.

    This function is automatically called by the Discord client whenever a
    scheduled event is updated. It takes the old and new versions of the
    Discord event as input and calls the `update_google_event()` function to
    update the corresponding event in the Google Calendar.

    The `update_google_event()` function is responsible for modifying the
    details of the Google Calendar event, including the event summary,
    location, description, start time, and end time, based on the changes in
    the Discord event.
    """
    update_google_event(old_discord_event, new_discord_event)


# When a Discord tells us that an event was deleted, delete the matching
# Google Calendar event
@discord_client.event
async def on_scheduled_event_delete(discord_event):
    """
    Event handler that is called when a scheduled event is deleted in Discord.

    Args:
        discord_event (discord.ScheduledEvent): The Discord scheduled event
            that has been deleted.

    This function is automatically called by the Discord client whenever a
    scheduled event is deleted. It takes the deleted Discord event as input
    and uses the Google Calendar API to delete the corresponding event from
    the Google Calendar.

    After deleting the Google Calendar event, the function prints a message
    to the console indicating that the event has been deleted.
    """
    # Delete the calendar event based on Discord event ID and announce it to
    # the console
    google_client.events().delete(
        calendarId=CALENDAR_ID, eventId=str(discord_event.id)
    ).execute()
    logger.info("Google Calendar event deleted for %s", discord_event.name)


# Start the Discord bot service
discord_client.run(DISCORD_TOKEN)

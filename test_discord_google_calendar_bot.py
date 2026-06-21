"""Unit tests for discord_google_calendar_bot."""

import json
import unittest
from unittest.mock import MagicMock, patch

# ---------------------------------------------------------------------------
# Module-level patches — must be started BEFORE importing the bot module.
# The module runs side-effectful code at import time:
#   boto3.client("secretsmanager") → get_aws_secret() → sets DISCORD_TOKEN etc.
#   discord.Intents.default() / discord.Client(...)
#   service_account.Credentials.from_service_account_info(...)
#   googleapiclient.discovery.build(...)
#   discord_client.run(DISCORD_TOKEN)   ← last line, would block forever
# ---------------------------------------------------------------------------

MOCK_TOKEN = "test-discord-token"
MOCK_CREDS_JSON = json.dumps({
    "type": "service_account",
    "project_id": "test-project",
    "private_key_id": "key-id",
    "private_key": "fake-key",
    "client_email": "test@test.iam.gserviceaccount.com",
    "client_id": "123",
    "auth_uri": "https://accounts.google.com/o/oauth2/auth",
    "token_uri": "https://oauth2.googleapis.com/token",
})
MOCK_CALENDAR_ID = "test-cal-id"

_p_boto3 = patch("boto3.client")
_p_build = patch("googleapiclient.discovery.build")
_p_creds = patch("google.oauth2.service_account.Credentials.from_service_account_info")
_p_discord_client = patch("discord.Client")
_p_discord_intents = patch("discord.Intents")

_mock_boto3_fn = _p_boto3.start()
_mock_build_fn = _p_build.start()
_p_creds.start()
_mock_discord_cls = _p_discord_client.start()
_p_discord_intents.start()

_mock_secrets_client = MagicMock()
_mock_boto3_fn.return_value = _mock_secrets_client
_mock_secrets_client.get_secret_value.return_value = {
    "SecretString": json.dumps({
        "DISCORD_TOKEN": MOCK_TOKEN,
        "GOOGLE_CREDENTIALS_JSON": MOCK_CREDS_JSON,
        "CALENDAR_ID": MOCK_CALENDAR_ID,
    })
}
_mock_build_fn.return_value = MagicMock()

# The bot uses @discord_client.event as a decorator on each handler.
# If that decorator returns a MagicMock, the handlers become non-awaitable.
# Set event() to be an identity decorator so the original async functions
# are preserved on the bot module and can be awaited in tests.
_mock_discord_instance = MagicMock()
_mock_discord_instance.event = lambda f: f
_mock_discord_cls.return_value = _mock_discord_instance

import discord_google_calendar_bot as bot  # noqa: E402

import discord  # noqa: E402
import requests  # noqa: E402
from googleapiclient.errors import HttpError  # noqa: E402


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_http_error(status_code: int) -> HttpError:
    resp = MagicMock()
    resp.reason = "Error"
    resp.status = status_code               # HttpError.status_code returns resp.status as-is
    resp.__getitem__ = lambda _, k: str(status_code)
    return HttpError(resp=resp, content=b"error")


def _make_discord_event(**overrides):
    """Return a MagicMock that looks like a discord.ScheduledEvent.

    Use `event_id` to set the numeric event id (avoids shadowing the `id` builtin).
    """
    event = MagicMock()
    event.entity_type = discord.EntityType.external
    event.name = "Test Event"
    event.description = "A description"
    event.location = "Some Location"
    event.guild_id = 111
    event.id = overrides.pop("event_id", 222)
    event.channel = MagicMock()
    event.channel.name = "voice-channel"
    event.start_time = MagicMock()
    event.start_time.isoformat.return_value = "2024-06-01T10:00:00"
    event.end_time = MagicMock()
    event.end_time.isoformat.return_value = "2024-06-01T12:00:00"
    for k, v in overrides.items():
        setattr(event, k, v)
    return event


def _mock_discord_client(server_name="Test Server"):
    dc = MagicMock()
    dc.guilds = [MagicMock()]
    dc.guilds[0].name = server_name
    return dc


def _mock_google_client():
    return MagicMock()


# ---------------------------------------------------------------------------
# TestGetAwsSecret
# ---------------------------------------------------------------------------

class TestGetAwsSecret(unittest.TestCase):
    def test_returns_parsed_secret_dict(self):
        mock_client = MagicMock()
        mock_client.get_secret_value.return_value = {
            "SecretString": json.dumps({"KEY": "val", "NUM": 1})
        }
        with patch.object(bot, "aws_client", mock_client):
            result = bot.get_aws_secret("my-secret")
        mock_client.get_secret_value.assert_called_once_with(SecretId="my-secret")
        self.assertEqual(result, {"KEY": "val", "NUM": 1})


# ---------------------------------------------------------------------------
# TestGetScheduledEventRecurrenceRule
# ---------------------------------------------------------------------------

class TestGetScheduledEventRecurrenceRule(unittest.TestCase):
    def _response(self, recurrence_rule):
        resp = MagicMock()
        resp.json.return_value = {"recurrence_rule": recurrence_rule}
        return resp

    def test_returns_none_when_recurrence_rule_is_null(self):
        with patch("requests.get", return_value=self._response(None)):
            result = bot.get_scheduled_event_recurrence_rule(111, 222)
        self.assertIsNone(result)

    def test_builds_correct_discord_api_url(self):
        with patch("requests.get", return_value=self._response(None)) as mock_get:
            bot.get_scheduled_event_recurrence_rule(111, 222)
        mock_get.assert_called_once_with(
            "https://discord.com/api/v10/guilds/111/scheduled-events/222",
            headers={
                "Authorization": f"Bot {MOCK_TOKEN}",
                "Content-Type": "application/json",
            },
            timeout=60,
        )

    def test_yearly_recurrence_frequency_0(self):
        rule = {"frequency": 0, "interval": 1, "by_month": [6], "by_month_day": [15]}
        with patch("requests.get", return_value=self._response(rule)):
            result = bot.get_scheduled_event_recurrence_rule(111, 222)
        self.assertEqual(result["frequency"], 0)
        self.assertEqual(result["interval"], 1)
        self.assertEqual(result["by_month"], 6)
        self.assertEqual(result["by_month_day"], 15)
        self.assertIsNone(result["by_n_weekday_n"])
        self.assertIsNone(result["by_n_weekday_day"])

    def test_monthly_recurrence_frequency_1(self):
        rule = {"frequency": 1, "interval": 1, "by_n_weekday": [{"n": 2, "day": 4}]}
        with patch("requests.get", return_value=self._response(rule)):
            result = bot.get_scheduled_event_recurrence_rule(111, 222)
        self.assertEqual(result["frequency"], 1)
        self.assertEqual(result["by_n_weekday_n"], 2)
        self.assertEqual(result["by_n_weekday_day"], 4)
        self.assertIsNone(result["by_month"])
        self.assertIsNone(result["by_month_day"])

    def test_weekly_recurrence_frequency_2(self):
        rule = {"frequency": 2, "interval": 3}
        with patch("requests.get", return_value=self._response(rule)):
            result = bot.get_scheduled_event_recurrence_rule(111, 222)
        self.assertEqual(result["frequency"], 2)
        self.assertEqual(result["interval"], 3)
        self.assertIsNone(result["by_month"])

    def test_daily_recurrence_frequency_3(self):
        rule = {"frequency": 3, "interval": 1}
        with patch("requests.get", return_value=self._response(rule)):
            result = bot.get_scheduled_event_recurrence_rule(111, 222)
        self.assertEqual(result["frequency"], 3)
        self.assertEqual(result["interval"], 1)

    def test_timeout_exception_returns_none(self):
        with patch("requests.get", side_effect=requests.exceptions.Timeout()):
            result = bot.get_scheduled_event_recurrence_rule(111, 222)
        self.assertIsNone(result)

    def test_request_exception_returns_none(self):
        with patch("requests.get", side_effect=requests.exceptions.RequestException("oops")):
            result = bot.get_scheduled_event_recurrence_rule(111, 222)
        self.assertIsNone(result)


# ---------------------------------------------------------------------------
# TestCreateGoogleEvent
# ---------------------------------------------------------------------------

class TestCreateGoogleEvent(unittest.TestCase):
    def _run(self, discord_event, recurrence_rule=None):
        gc = _mock_google_client()
        dc = _mock_discord_client()
        with patch.object(bot, "google_client", gc), \
             patch.object(bot, "discord_client", dc), \
             patch.object(bot, "get_scheduled_event_recurrence_rule", return_value=recurrence_rule):
            bot.create_google_event(discord_event)
        return gc

    def _body(self, discord_event, recurrence_rule=None):
        gc = self._run(discord_event, recurrence_rule)
        return gc.events.return_value.insert.call_args.kwargs["body"]

    def test_voice_event_uses_start_time_as_end_time(self):
        event = _make_discord_event(entity_type=discord.EntityType.voice)
        body = self._body(event)
        self.assertEqual(body["end"]["dateTime"], event.start_time.isoformat())

    def test_voice_event_location_uses_channel_name(self):
        event = _make_discord_event(entity_type=discord.EntityType.voice)
        body = self._body(event)
        self.assertIn(event.channel.name, body["location"])

    def test_external_event_uses_end_time(self):
        event = _make_discord_event()
        body = self._body(event)
        self.assertEqual(body["end"]["dateTime"], event.end_time.isoformat())

    def test_external_event_location_uses_discord_location(self):
        event = _make_discord_event(location="Main Hall")
        body = self._body(event)
        self.assertIn("Main Hall", body["location"])

    def test_event_body_contains_correct_summary(self):
        event = _make_discord_event(name="Game Night")
        body = self._body(event)
        self.assertEqual(body["summary"], "Discord (Test Server): Game Night")

    def test_event_body_contains_description_and_id(self):
        event = _make_discord_event(description="Bring snacks", event_id=999)
        body = self._body(event)
        self.assertEqual(body["description"], "Bring snacks")
        self.assertEqual(body["id"], "999")

    def test_no_recurrence_rule_sets_recurrence_none(self):
        body = self._body(_make_discord_event(), recurrence_rule=None)
        self.assertIsNone(body["recurrence"])

    def test_recurrence_frequency_3_daily_weekdays(self):
        rule = {"frequency": 3, "interval": 1, "by_month": None, "by_month_day": None,
                "by_n_weekday_n": None, "by_n_weekday_day": None}
        body = self._body(_make_discord_event(), recurrence_rule=rule)
        self.assertEqual(body["recurrence"], ["RRULE:FREQ=WEEKLY;WKST=MO;BYDAY=MO,TU,WE,TH,FR"])

    def test_recurrence_frequency_2_weekly_with_interval(self):
        rule = {"frequency": 2, "interval": 2, "by_month": None, "by_month_day": None,
                "by_n_weekday_n": None, "by_n_weekday_day": None}
        body = self._body(_make_discord_event(), recurrence_rule=rule)
        self.assertEqual(body["recurrence"], ["RRULE:FREQ=WEEKLY;INTERVAL=2"])

    def test_recurrence_frequency_1_monthly_nth_weekday(self):
        rule = {"frequency": 1, "interval": 1, "by_month": None, "by_month_day": None,
                "by_n_weekday_n": 2, "by_n_weekday_day": 0}  # 0 → MO
        body = self._body(_make_discord_event(), recurrence_rule=rule)
        self.assertEqual(body["recurrence"], ["RRULE:FREQ=MONTHLY;WKST=MO;BYDAY=2MO"])

    def test_recurrence_frequency_0_yearly(self):
        rule = {"frequency": 0, "interval": 1, "by_month": 6, "by_month_day": 15,
                "by_n_weekday_n": None, "by_n_weekday_day": None}
        body = self._body(_make_discord_event(), recurrence_rule=rule)
        self.assertEqual(body["recurrence"], ["RRULE:FREQ=YEARLY;BYMONTH=6;BYMONTHDAY=15"])

    def test_409_conflict_calls_update_google_event(self):
        event = _make_discord_event()
        gc = _mock_google_client()
        dc = _mock_discord_client()
        gc.events.return_value.insert.return_value.execute.side_effect = _make_http_error(409)
        with patch.object(bot, "google_client", gc), \
             patch.object(bot, "discord_client", dc), \
             patch.object(bot, "get_scheduled_event_recurrence_rule", return_value=None), \
             patch.object(bot, "update_google_event") as mock_update:
            bot.create_google_event(event)
        mock_update.assert_called_once_with(event, event)

    def test_successful_insert_uses_correct_calendar_id(self):
        gc = _mock_google_client()
        dc = _mock_discord_client()
        with patch.object(bot, "google_client", gc), \
             patch.object(bot, "discord_client", dc), \
             patch.object(bot, "get_scheduled_event_recurrence_rule", return_value=None):
            bot.create_google_event(_make_discord_event())
        kwargs = gc.events.return_value.insert.call_args.kwargs
        self.assertEqual(kwargs["calendarId"], MOCK_CALENDAR_ID)


# ---------------------------------------------------------------------------
# TestUpdateGoogleEvent
# ---------------------------------------------------------------------------

class TestUpdateGoogleEvent(unittest.TestCase):
    def _run(self, new_event, old_event=None, recurrence_rule=None):
        if old_event is None:
            old_event = _make_discord_event(event_id=100)
        gc = _mock_google_client()
        dc = _mock_discord_client()
        with patch.object(bot, "google_client", gc), \
             patch.object(bot, "discord_client", dc), \
             patch.object(bot, "get_scheduled_event_recurrence_rule", return_value=recurrence_rule):
            bot.update_google_event(old_event, new_event)
        return gc

    def _body(self, new_event, **kw):
        gc = self._run(new_event, **kw)
        return gc.events.return_value.update.call_args.kwargs["body"]

    def test_voice_event_uses_start_time_as_end_time(self):
        event = _make_discord_event(entity_type=discord.EntityType.voice)
        body = self._body(event)
        self.assertEqual(body["end"]["dateTime"], event.start_time.isoformat())

    def test_voice_event_location_uses_channel_name(self):
        event = _make_discord_event(entity_type=discord.EntityType.voice)
        body = self._body(event)
        self.assertIn(event.channel.name, body["location"])

    def test_external_event_uses_end_time(self):
        event = _make_discord_event()
        body = self._body(event)
        self.assertEqual(body["end"]["dateTime"], event.end_time.isoformat())

    def test_no_recurrence_sets_recurrence_none(self):
        body = self._body(_make_discord_event())
        self.assertIsNone(body["recurrence"])

    def test_recurrence_frequency_3_daily_weekdays(self):
        rule = {"frequency": 3, "interval": 1, "by_month": None, "by_month_day": None,
                "by_n_weekday_n": None, "by_n_weekday_day": None}
        body = self._body(_make_discord_event(), recurrence_rule=rule)
        self.assertEqual(body["recurrence"], ["RRULE:FREQ=WEEKLY;WKST=MO;BYDAY=MO,TU,WE,TH,FR"])

    def test_recurrence_frequency_2_weekly_with_interval(self):
        rule = {"frequency": 2, "interval": 4, "by_month": None, "by_month_day": None,
                "by_n_weekday_n": None, "by_n_weekday_day": None}
        body = self._body(_make_discord_event(), recurrence_rule=rule)
        self.assertEqual(body["recurrence"], ["RRULE:FREQ=WEEKLY;INTERVAL=4"])

    def test_recurrence_frequency_1_monthly_nth_weekday(self):
        rule = {"frequency": 1, "interval": 1, "by_month": None, "by_month_day": None,
                "by_n_weekday_n": 1, "by_n_weekday_day": 2}  # 2 → WE
        body = self._body(_make_discord_event(), recurrence_rule=rule)
        self.assertEqual(body["recurrence"], ["RRULE:FREQ=MONTHLY;WKST=MO;BYDAY=1WE"])

    def test_recurrence_frequency_0_yearly(self):
        rule = {"frequency": 0, "interval": 1, "by_month": 12, "by_month_day": 25,
                "by_n_weekday_n": None, "by_n_weekday_day": None}
        body = self._body(_make_discord_event(), recurrence_rule=rule)
        self.assertEqual(body["recurrence"], ["RRULE:FREQ=YEARLY;BYMONTH=12;BYMONTHDAY=25"])

    def test_uses_old_event_id_as_event_id(self):
        old_event = _make_discord_event(event_id=999)
        new_event = _make_discord_event(event_id=888)
        gc = self._run(new_event, old_event=old_event)
        kwargs = gc.events.return_value.update.call_args.kwargs
        self.assertEqual(kwargs["eventId"], str(old_event.id))

    def test_uses_correct_calendar_id(self):
        gc = self._run(_make_discord_event())
        kwargs = gc.events.return_value.update.call_args.kwargs
        self.assertEqual(kwargs["calendarId"], MOCK_CALENDAR_ID)


# ---------------------------------------------------------------------------
# TestOnReady
# ---------------------------------------------------------------------------

class TestOnReady(unittest.IsolatedAsyncioTestCase):
    async def test_creates_missing_discord_events(self):
        dc = _mock_discord_client()
        dc.user = "TestBot#1234"
        new_event = _make_discord_event(name="Raid Night")
        dc.guilds[0].scheduled_events = [new_event]

        gc = _mock_google_client()
        gc.events.return_value.list.return_value.execute.return_value = {
            "items": [{"summary": "Discord (Test Server): Other Event"}]
        }

        with patch.object(bot, "discord_client", dc), \
             patch.object(bot, "google_client", gc), \
             patch.object(bot, "create_google_event") as mock_create:
            await bot.on_ready()

        mock_create.assert_called_once_with(new_event)

    async def test_skips_events_already_in_google_calendar(self):
        dc = _mock_discord_client()
        dc.user = "TestBot#1234"
        existing_event = _make_discord_event(name="Raid Night")
        dc.guilds[0].scheduled_events = [existing_event]

        gc = _mock_google_client()
        gc.events.return_value.list.return_value.execute.return_value = {
            "items": [{"summary": "Discord (Test Server): Raid Night"}]
        }

        with patch.object(bot, "discord_client", dc), \
             patch.object(bot, "google_client", gc), \
             patch.object(bot, "create_google_event") as mock_create:
            await bot.on_ready()

        mock_create.assert_not_called()

    async def test_creates_multiple_missing_events(self):
        dc = _mock_discord_client()
        dc.user = "TestBot#1234"
        event_a = _make_discord_event(name="Event A")
        event_b = _make_discord_event(name="Event B")
        dc.guilds[0].scheduled_events = [event_a, event_b]

        gc = _mock_google_client()
        gc.events.return_value.list.return_value.execute.return_value = {"items": []}

        with patch.object(bot, "discord_client", dc), \
             patch.object(bot, "google_client", gc), \
             patch.object(bot, "create_google_event") as mock_create:
            await bot.on_ready()

        self.assertEqual(mock_create.call_count, 2)


# ---------------------------------------------------------------------------
# TestEventHandlers
# ---------------------------------------------------------------------------

class TestEventHandlers(unittest.IsolatedAsyncioTestCase):
    async def test_on_scheduled_event_create_delegates_to_create(self):
        event = _make_discord_event()
        with patch.object(bot, "create_google_event") as mock_create:
            await bot.on_scheduled_event_create(event)
        mock_create.assert_called_once_with(event)

    async def test_on_scheduled_event_update_delegates_to_update(self):
        old_event = _make_discord_event(event_id=1)
        new_event = _make_discord_event(event_id=2)
        with patch.object(bot, "update_google_event") as mock_update:
            await bot.on_scheduled_event_update(old_event, new_event)
        mock_update.assert_called_once_with(old_event, new_event)

    async def test_on_scheduled_event_delete_calls_google_delete(self):
        event = _make_discord_event(event_id=555)
        gc = _mock_google_client()
        with patch.object(bot, "google_client", gc):
            await bot.on_scheduled_event_delete(event)
        gc.events.return_value.delete.assert_called_once_with(
            calendarId=MOCK_CALENDAR_ID,
            eventId=str(event.id),
        )

    async def test_on_scheduled_event_delete_executes_call(self):
        event = _make_discord_event(event_id=777)
        gc = _mock_google_client()
        with patch.object(bot, "google_client", gc):
            await bot.on_scheduled_event_delete(event)
        gc.events.return_value.delete.return_value.execute.assert_called_once()


if __name__ == "__main__":
    unittest.main()

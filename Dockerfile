# Use Python image as the base
#
# NOTE: This needs to stay at 3.12, as 3.13 has dependency issues
# with wheel
#
# "Use of deprecated module audioop"
# https://github.com/Rapptz/discord.py/issues/9477
#
FROM python:3.12-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory inside the container
WORKDIR /app

# Copy lock files first for layer caching
COPY pyproject.toml uv.lock /app/

# Install all dependencies including dev (pytest required for startup tests)
RUN uv sync --frozen --no-install-project

# Copy the application, tests, and entrypoint
COPY discord_google_calendar_bot.py test_discord_google_calendar_bot.py entrypoint.sh /app/
RUN chmod +x /app/entrypoint.sh

# Mark healthy once startup tests pass (written by entrypoint.sh)
HEALTHCHECK --interval=30s --timeout=10s --start-period=60s --retries=3 \
    CMD test -f /tmp/healthy || exit 1

ENTRYPOINT ["/app/entrypoint.sh"]

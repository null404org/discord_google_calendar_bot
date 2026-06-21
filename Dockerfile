# Use Python image as the base
#
# NOTE: This needs to stay at 3.12, as 3.13 has dependency issues
# with wheel
#
# "Use of deprecated module audioop"
# https://github.com/Rapptz/discord.py/issues/9477
#
FROM python:3.13.0b2-slim

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /uvx /bin/

# Set the working directory inside the container
WORKDIR /app

# Copy lock files first for layer caching
COPY pyproject.toml uv.lock /app/

# Install production dependencies (SHA-locked)
RUN uv sync --frozen --no-dev --no-install-project

# Copy the application
COPY discord_google_calendar_bot.py /app/

# Run the Python script continuously
CMD ["uv", "run", "python", "discord_google_calendar_bot.py"]

# Use Python image as the base
#
# NOTE: This needs to stay at 3.12, as 3.13 has dependency issues
# with wheel
#
# "Use of deprecated module audioop"
# https://github.com/Rapptz/discord.py/issues/9477
#
FROM python:3.12

# Set the working directory inside the container
WORKDIR /app

# Copy the Python script into the container
COPY discord_google_calendar_bot.py /app/

# Copy the Python script into the container
COPY requirements.txt /app/

# Install version-pinned dependencies
RUN pip install -r requirements.txt

# Run the Python script continuously
CMD ["python", "discord_google_calendar_bot.py"]

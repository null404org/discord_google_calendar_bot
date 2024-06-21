# Use Python 3.12 image as the base
FROM python:3.12-slim

# Set the working directory inside the container
WORKDIR /app

# Copy the Python script into the container
COPY discord_google_calendar_bot.py /app/

# Install dependencies
RUN pip install --no-cache-dir discord.py google-api-python-client google-auth boto3

# Run the Python script continuously
CMD ["python", "discord_google_calendar_bot.py"]

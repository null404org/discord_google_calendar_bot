# Use Python 3.12 image as the base
FROM python:3.13.0b1-slim

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

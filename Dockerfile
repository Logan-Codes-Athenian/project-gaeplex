# Use Python 3.11 slim image
FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy your source code and credentials
COPY src ./src

# Set working directory to src to run the bot
WORKDIR /app/src

# Run the bot
CMD ["python", "bot.py"]

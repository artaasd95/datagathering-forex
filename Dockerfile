FROM python:3.9-slim

# Set up working directory
WORKDIR /app

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy the fetcher scripts
COPY tick_fetcher.py .
COPY candle_fetcher.py .

# Default command (can be overridden)
CMD ["python", "tick_fetcher.py"] 
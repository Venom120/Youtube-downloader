FROM python:3.11-slim

# Set working directory
WORKDIR /app

# Install system dependencies for yt-dlp
RUN apt-get update && apt-get install -y \
    ffmpeg \
    curl \
    unzip \
    && rm -rf /var/lib/apt/lists/*

# Install Deno (recommended JavaScript runtime for yt-dlp EJS)
RUN curl -fsSL https://deno.land/install.sh | sh && \
    export PATH="/root/.deno/bin:$PATH"

# Add deno to PATH for subsequent commands
ENV PATH="/root/.deno/bin:${PATH}"

# Copy requirements and install Python dependencies
COPY requirements.txt .
RUN pip install --upgrade pip
RUN pip install --no-cache-dir -r requirements.txt
RUN pip install --no-cache-dir "yt-dlp[default]"

# Copy application code
COPY . .

# Create downloads and cookies directories
RUN mkdir -p /app/downloads
RUN mkdir -p /app/cookies

# Create yt-dlp config to enable Deno for JavaScript challenges
RUN mkdir -p /root/.config/yt-dlp && \
    echo "# yt-dlp configuration" > /root/.config/yt-dlp/config && \
    echo "# Enable Deno for EJS (JavaScript challenge solving)" >> /root/.config/yt-dlp/config && \
    echo "--js-runtimes deno" >> /root/.config/yt-dlp/config

# Expose port
EXPOSE 8000

# Run the application
CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000", "--reload"]

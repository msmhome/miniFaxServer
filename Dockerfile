FROM python:3.12.4-slim-bookworm

ENV PYTHONUNBUFFERED=1 \
    PYTHONPATH=/app

RUN apt-get update && \
    apt-get install -y wget ca-certificates && \
    wget -q https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb && \
    dpkg -i cloudflared-linux-amd64.deb && \
    rm -rf /var/lib/apt/lists/* && \
    apt-get remove wget && \
    rm cloudflared-linux-amd64.deb

# Create cloudflared directory for configuration
RUN mkdir -p /etc/cloudflared

# Set environment variables for cloudflared TODO: SecretsUsedInArgOrEnv: Do not use ARG or ENV instructions for sensitive data (ENV "TUNNEL_TOKEN") (line 16)
ENV TUNNEL_TOKEN=$TUNNEL_TOKEN

WORKDIR /app

COPY server.py .
COPY requirements.txt .
COPY entrypoint.sh /entrypoint.sh

RUN chmod +x /entrypoint.sh
RUN pip install --no-cache-dir -r requirements.txt 

ENTRYPOINT ["/entrypoint.sh"]
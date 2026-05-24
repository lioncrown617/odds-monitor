# ── Stage 1: Build Node dependencies ──────────────────────────────
FROM node:20-slim AS node-builder
WORKDIR /app
COPY hkjc-bridge/package*.json ./
RUN npm install --omit=dev
COPY hkjc-bridge/server.js ./

# ── Stage 2: Final image (Python + Chrome + Node) ─────────────────
FROM python:3.11-slim

# Install Chrome only (no nodejs via apt)
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl ca-certificates \
    && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub \
       | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] \
       http://dl.google.com/linux/chrome/deb/ stable main" \
       > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable \
    && rm -rf /var/lib/apt/lists/*

# Copy Node binary from builder
COPY --from=node-builder /usr/local/bin/node /usr/local/bin/node
COPY --from=node-builder /usr/local/lib/node_modules /usr/local/lib/node_modules

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=node-builder /app/node_modules ./node_modules
COPY --from=node-builder /app/server.js ./server.js

COPY . .

CMD ["sh", "-c", "node server.js & python odd.py"]

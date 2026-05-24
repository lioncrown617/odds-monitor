# ── Stage 1: Build Node dependencies ──────────────────────────────
FROM node:20-slim AS node-builder
WORKDIR /app
COPY package*.json ./
RUN npm install --omit=dev
COPY server.js ./

# ── Stage 2: Final image (Python + Chrome + Node) ─────────────────
FROM python:3.11-slim

# Install Chrome + Node.js
RUN apt-get update && apt-get install -y \
    wget gnupg unzip curl ca-certificates \
    && curl -fsSL https://dl.google.com/linux/linux_signing_key.pub \
       | gpg --dearmor -o /usr/share/keyrings/google-chrome.gpg \
    && echo "deb [arch=amd64 signed-by=/usr/share/keyrings/google-chrome.gpg] \
       http://dl.google.com/linux/chrome/deb/ stable main" \
       > /etc/apt/sources.list.d/google-chrome.list \
    && apt-get update && apt-get install -y google-chrome-stable nodejs \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY --from=node-builder /app/node_modules ./node_modules
COPY --from=node-builder /app/server.js ./server.js

COPY . .

CMD ["sh", "-c", "node server.js & python odd.py"]

FROM node:20-slim AS node-builder
WORKDIR /app
COPY hkjc-bridge/package*.json ./
RUN npm install --omit=dev
COPY hkjc-bridge/server.js ./

FROM python:3.11-slim
WORKDIR /app

COPY --from=node-builder /usr/local/bin/node /usr/local/bin/node
COPY --from=node-builder /usr/local/lib/node_modules /usr/local/lib/node_modules
COPY --from=node-builder /app/node_modules ./node_modules
COPY --from=node-builder /app/server.js ./server.js

COPY requirements.txt .
RUN pip install --no-cache-dir flask requests gunicorn

COPY . .

CMD node server.js & sleep 5 && gunicorn odd:app --bind 0.0.0.0:${PORT:-5000} --workers 1 --threads 4 --timeout 120

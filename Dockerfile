FROM node:20-slim AS node-builder
WORKDIR /app
COPY hkjc-bridge/package*.json ./
RUN npm install --omit=dev
COPY hkjc-bridge/server.js ./

FROM python:3.11-slim
WORKDIR /app

# 安裝 Node.js
COPY --from=node-builder /usr/local/bin/node /usr/local/bin/node
COPY --from=node-builder /usr/local/lib/node_modules /usr/local/lib/node_modules
RUN ln -s /usr/local/lib/node_modules/.bin/node /usr/local/bin/node 2>/dev/null || true

# 複製 Node bridge
COPY --from=node-builder /app/node_modules ./node_modules
COPY --from=node-builder /app/server.js ./server.js

# 安裝 Python 依賴
COPY requirements.txt .
RUN pip install --no-cache-dir flask requests gunicorn

# 複製所有程式
COPY . .

# 啟動：Node 橋接 + Gunicorn
CMD node server.js & sleep 3 && gunicorn odd:app --bind 0.0.0.0:$PORT --workers 1 --threads 4 --timeout 120

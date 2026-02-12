# --- Build stage ---
FROM node:20-slim AS build

WORKDIR /app

# Install dependencies first (layer caching)
COPY package.json package-lock.json ./
COPY client/package.json client/
COPY server/package.json server/
RUN npm ci

# Copy source and build
COPY client/ client/
COPY server/ server/
RUN npm run build

# --- Runtime stage ---
FROM node:20-slim

# Install Python + labelle CLI
# PyQt6 and darkdetect are GUI-only deps; we install labelle fully, then remove them
RUN apt-get update \
    && apt-get install -y --no-install-recommends \
       python3 python3-pip libusb-1.0-0 \
    && python3 -m pip install --no-cache-dir --break-system-packages labelle typing_extensions \
    && python3 -m pip uninstall -y --break-system-packages PyQt6 PyQt6-Qt6 PyQt6-sip 2>/dev/null || true \
    && apt-get purge -y --auto-remove python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /app

# Install only server production dependencies
COPY package.json package-lock.json ./
COPY server/package.json server/
RUN npm ci --workspace=server --omit=dev && npm cache clean --force

# Copy built artifacts from build stage
COPY --from=build /app/server/dist/ server/dist/
COPY --from=build /app/server/dist-client/ server/dist-client/

ENV NODE_ENV=production
EXPOSE 5000

CMD ["npm", "start"]

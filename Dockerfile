# --- Build stage: Node.js for client build only ---
FROM node:20-slim AS build

WORKDIR /app

# Install client dependencies
COPY package.json package-lock.json ./
COPY client/package.json client/
RUN npm ci

# Build client
COPY client/ client/
RUN npm run build

# --- Runtime stage: Python only ---
FROM python:3.12-slim

# Install libusb for DYMO USB access, uhubctl for per-port USB power control
# (printer power-save), then Python dependencies. PyQt6 is GUI-only; we keep
# darkdetect because labelle imports it at module load.
RUN apt-get update \
    && apt-get install -y --no-install-recommends libusb-1.0-0 uhubctl \
    && rm -rf /var/lib/apt/lists/*

COPY server/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --no-deps labelle \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

WORKDIR /app

# Copy Python server and package.json (used by /api/health for version)
COPY package.json .
COPY server/*.py server/

# Copy built client assets from build stage
COPY --from=build /app/server/dist-client/ server/dist-client/

# Build provenance: surfaced via /api/health so we can see what's deployed
ARG GIT_SHA=
ARG GIT_BRANCH=
ENV GIT_SHA=${GIT_SHA}
ENV GIT_BRANCH=${GIT_BRANCH}

EXPOSE 5000

CMD ["python", "server/app.py"]

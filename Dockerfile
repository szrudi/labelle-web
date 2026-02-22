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

# Install libusb for DYMO USB access, then Python dependencies
# PyQt6 is GUI-only; remove it to save space (darkdetect must stay — imported at load time)
RUN apt-get update \
    && apt-get install -y --no-install-recommends libusb-1.0-0 \
    && rm -rf /var/lib/apt/lists/*

COPY server/requirements.txt /tmp/requirements.txt
RUN pip install --no-cache-dir --no-deps labelle \
    && pip install --no-cache-dir -r /tmp/requirements.txt \
    && rm /tmp/requirements.txt

WORKDIR /app

# Copy Python server
COPY server/app.py server/label_builder.py server/config.py server/virtual_printer.py server/

# Copy built client assets from build stage
COPY --from=build /app/server/dist-client/ server/dist-client/

EXPOSE 5000

CMD ["python", "server/app.py"]

# WiFi AP Fallback Setup

## Current State

The Pi (`hector`, `10.10.10.63`) is back on home WiFi. AP fallback is configured and ready.

- AP SSID: `Labelle-Printer`
- AP password: `labelleprint`
- AP IP: `10.42.0.1`
- mDNS: `hector.local` (avahi-daemon was already installed)

## Everything done on the Pi (via SSH to 10.10.10.63)

### 1. Set WiFi autoconnect priority

```bash
sudo nmcli con modify "HakhorstEU-WiFi 1" connection.autoconnect-priority 10
sudo nmcli con modify "HakhorstEU-WiFi" connection.autoconnect-priority 10
```

There are two profiles for the same network — a stale one (`HakhorstEU-Wifi`, lowercase `f`, last used ~Feb 2025) and the active one (`HakhorstEU-WiFi 1`). The old one can be safely deleted:

```bash
sudo nmcli con delete "HakhorstEU-WiFi"
```

### 2. Created AP fallback connection profile

```bash
sudo nmcli con add type wifi ifname wlan0 con-name "Labelle-AP" \
  wifi.mode ap wifi.band bg wifi.channel 6 \
  wifi.ssid "Labelle-Printer" \
  wifi-sec.key-mgmt wpa-psk wifi-sec.psk "labelleprint" \
  ipv4.method shared \
  connection.autoconnect yes connection.autoconnect-priority 1
```

- `ipv4.method shared` — Pi runs DHCP + NAT for connected clients automatically
- `autoconnect-priority 1` — lower than the home WiFi (10), so NM only uses it as fallback

### 3. Tested AP activation

```bash
sudo nmcli con up "Labelle-AP"
```

Confirmed the Pi broadcasts `Labelle-Printer`, is reachable at `10.42.0.1`, and clients can connect.

Switched back with:

```bash
sudo nmcli con up "HakhorstEU-WiFi 1"
```

### 4. DNS redirect for captive portal

Created `/etc/NetworkManager/dnsmasq-shared.d/captive-portal.conf`:

```
address=/#/10.42.0.1
```

When NM runs in `shared` mode (AP), its built-in dnsmasq uses this config to resolve **all** domain lookups to the Pi's IP. This is what makes captive portal detection work — the OS thinks every domain points to the Pi.

### 5. Port 80/443 → 5000 iptables redirect

Created `/etc/NetworkManager/dispatcher.d/90-captive-portal` (chmod 755):

```bash
#!/bin/bash
IFACE="$1"
ACTION="$2"
CONNECTION_ID="$CONNECTION_ID"

if [ "$CONNECTION_ID" != "Labelle-AP" ]; then
    exit 0
fi

case "$ACTION" in
    up)
        iptables -t nat -A PREROUTING -i "$IFACE" -p tcp --dport 80 -j REDIRECT --to-port 5000
        iptables -t nat -A PREROUTING -i "$IFACE" -p tcp --dport 443 -j REDIRECT --to-port 5000
        ;;
    down)
        iptables -t nat -D PREROUTING -i "$IFACE" -p tcp --dport 80 -j REDIRECT --to-port 5000 2>/dev/null
        iptables -t nat -D PREROUTING -i "$IFACE" -p tcp --dport 443 -j REDIRECT --to-port 5000 2>/dev/null
        ;;
esac
```

NM dispatcher scripts run automatically when connections go up/down. This adds iptables rules only when `Labelle-AP` activates, and removes them when it deactivates. Needed because captive portal probes go to port 80, but Flask runs on 5000.

## What was done in the codebase

### 6. Captive portal detection routes (`server/app.py`)

Added routes that intercept well-known captive portal probe URLs and return 302 redirects to `http://10.42.0.1:5000/`:

- Apple iOS/macOS: `/hotspot-detect.html`, `/library/test/success.html`
- Android: `/generate_204`, `/gen_204`
- Windows: `/connecttest.txt`, `/ncsi.txt`
- Firefox: `/canonical.html`

When the OS gets a redirect instead of the expected "success" response, it opens a captive portal browser window pointing to the Labelle Web UI.

## How it all fits together

1. Pi can't find home WiFi → NM activates `Labelle-AP` (lower priority fallback)
2. Phone connects to `Labelle-Printer` WiFi, gets IP from dnsmasq DHCP
3. OS sends captive portal probe (e.g. `GET http://captive.apple.com/hotspot-detect.html`)
4. dnsmasq resolves `captive.apple.com` → `10.42.0.1` (the Pi)
5. iptables redirects port 80 → 5000 (Flask)
6. Flask returns 302 redirect to `http://10.42.0.1:5000/`
7. OS opens captive portal browser → Labelle Web UI appears

## Still TODO

- **Verify automatic fallback** — confirm NM switches to AP on its own when home WiFi disappears (we only tested manual `nmcli con up` so far)
- **Test captive portal flow end-to-end** — activate AP, connect from a phone, see if the browser auto-opens (requires deploying the updated `app.py`)
- **Deploy updated app** — rebuild Docker image with the new captive portal routes
- **Delete stale WiFi profile** — `sudo nmcli con delete "HakhorstEU-WiFi"` (the old one with lowercase `f`)
- **Change AP password** — `labelleprint` is a placeholder
- **Optional: periodic home WiFi retry timer** — deferred for now

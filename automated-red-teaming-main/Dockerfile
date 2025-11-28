# Latest Kali base
FROM kalilinux/kali-rolling:latest

ENV DEBIAN_FRONTEND=noninteractive \
    GO111MODULE=on

# Core tools, Chromium + runtime libs, GUI/VNC stack, Python, Go, VPN bits
# (single apt-get update; no duplicate libs)
RUN set -eux; \
  apt-get update; \
  apt-get install -y --no-install-recommends \
    kali-linux-headless \
    chromium \
    build-essential \
    # basics & helpers
    curl wget gnupg ca-certificates unzip xdg-utils dos2unix \
    # Python & VPN tooling
    python3-venv openvpn iproute2 \
    # Go for katana
    golang \
    # minimal fonts
    fonts-noto fonts-liberation \
    # GUI / VNC stack for headless UI
    xvfb x11vnc fluxbox novnc websockify \
    # Chromium runtime libs (deduped)
    libnss3 libxss1 libasound2t64 libgbm1 libatk-bridge2.0-0 \
    libcups2 libdrm2 libxdamage1 libxcomposite1 libgtk-3-0 \
    libappindicator3-1 \
  ; \
  rm -rf /var/lib/apt/lists/*

# katana (install straight into /usr/local/bin; no copy from ~/go/bin)
RUN set -eux; \
  GOBIN=/usr/local/bin CGO_ENABLED=1 go install github.com/projectdiscovery/katana/cmd/katana@latest

# NordVPN CLI (separate RUN because we add a new apt source)
RUN set -eux; \
  apt-get update; \
  apt-get install -y --no-install-recommends apt-transport-https; \
  wget -qO /etc/apt/trusted.gpg.d/nordvpn_public.asc https://repo.nordvpn.com/gpg/nordvpn_public.asc; \
  echo "deb https://repo.nordvpn.com/deb/nordvpn/debian stable main" > /etc/apt/sources.list.d/nordvpn.list; \
  apt-get update; \
  apt-get install -y --no-install-recommends nordvpn; \
  apt-get clean; \
  rm -rf /var/lib/apt/lists/*

# App workspace
WORKDIR /app
RUN mkdir -p /app/tmp

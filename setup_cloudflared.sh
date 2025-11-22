#!/bin/bash

# Setup script for Cloudflared tunnel
# This script helps set up a Cloudflare tunnel for the A2A server

set -e

echo "Setting up Cloudflared tunnel for MCU Green Agent..."

# Check if cloudflared is installed
if ! command -v cloudflared &> /dev/null; then
    echo "cloudflared is not installed. Installing..."
    
    # Detect OS and install cloudflared
    if [[ "$OSTYPE" == "darwin"* ]]; then
        # macOS
        brew install cloudflare/cloudflare/cloudflared
    elif [[ "$OSTYPE" == "linux-gnu"* ]]; then
        # Linux
        wget https://github.com/cloudflare/cloudflared/releases/latest/download/cloudflared-linux-amd64.deb
        sudo dpkg -i cloudflared-linux-amd64.deb
    else
        echo "Please install cloudflared manually from https://developers.cloudflare.com/cloudflare-one/connections/connect-apps/install-and-setup/installation"
        exit 1
    fi
fi

# Login to Cloudflare
echo "Please login to Cloudflare..."
cloudflared tunnel login

# Create tunnel
echo "Creating tunnel 'mcu-green-agent'..."
cloudflared tunnel create mcu-green-agent || echo "Tunnel may already exist"

# Create config directory
mkdir -p ~/.cloudflared

# Copy config file
if [ -f "cloudflared_config.yml" ]; then
    cp cloudflared_config.yml ~/.cloudflared/config.yml
    echo "Configuration file copied to ~/.cloudflared/config.yml"
    echo "Please edit ~/.cloudflared/config.yml and update the hostname with your domain"
else
    echo "Warning: cloudflared_config.yml not found"
fi

echo ""
echo "Setup complete! Next steps:"
echo "1. Edit ~/.cloudflared/config.yml and set your hostname"
echo "2. Run: cloudflared tunnel route dns mcu-green-agent your-subdomain.yourdomain.com"
echo "3. Start the tunnel: cloudflared tunnel run mcu-green-agent"
echo "4. Or run in background: nohup cloudflared tunnel run mcu-green-agent > cloudflared.log 2>&1 &"


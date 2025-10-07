#!/usr/bin/env bash
# Render build script to install LibreOffice and Python dependencies

set -o errexit  # Exit on error

echo "Installing system dependencies..."

# Update package list
apt-get update

# Install LibreOffice (headless version without GUI)
# This includes soffice command needed for PDF conversion
apt-get install -y libreoffice libreoffice-writer

# Install Python dependencies
echo "Installing Python dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

echo "Build completed successfully!"

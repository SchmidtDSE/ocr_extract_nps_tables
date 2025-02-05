# First, grab a Unix image with pixi installed
FROM ghcr.io/prefix-dev/pixi:0.39.5-bullseye-slim

# Install system dependencies
RUN apt-get update && apt-get install -y \
    tesseract-ocr \
    poppler-utils \
    && rm -rf /var/lib/apt/lists/*

# Set the working directory
WORKDIR /workspace
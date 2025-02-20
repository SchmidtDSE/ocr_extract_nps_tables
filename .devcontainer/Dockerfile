# First, grab a Unix image with pixi installed
FROM ghcr.io/prefix-dev/pixi:0.39.5-bullseye-slim

# Run on build scripts (system dependencies)
RUN .devcontainer/scripts/run_on_build.sh

# Set the working directory
WORKDIR /workspace
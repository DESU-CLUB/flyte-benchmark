FROM ubuntu:24.04

ENV DEBIAN_FRONTEND=noninteractive

# System dependencies
RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    python3-dev \
    curl \
    wget \
    git \
    build-essential \
    && apt-get clean \
    && rm -rf /var/lib/apt/lists/*

# Install Python packages
RUN pip3 install --break-system-packages flyte pandas numpy

# Create the project directory
RUN mkdir -p /home/user/flyte_project

WORKDIR /home/user/flyte_project

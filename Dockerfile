FROM node:11-alpine AS builder-node

# Build client
COPY client /app/client
WORKDIR /app/client
RUN npm install && npm run build

FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    curl \
    tzdata \
    ca-certificates \
    && rm -rf /var/lib/apt/lists/*

# Set timezone
RUN ln -snf /usr/share/zoneinfo/Europe/Berlin /etc/localtime && \
    echo "Europe/Berlin" > /etc/timezone

# Install uv
COPY --from=ghcr.io/astral-sh/uv:latest /uv /usr/local/bin/uv
ENV UV_COMPILE_BYTECODE=1 \
    UV_LINK_MODE=copy

# Add project
COPY . /app
WORKDIR /app

# Add dependencies
RUN uv sync \
    --frozen \
    --no-dev

# Add client application from node builder
COPY --from=builder-node /app/client/build /app/client/build

CMD [ "uv", "run", "server.py" ]

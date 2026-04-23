# syntax=docker/dockerfile:1
FROM nixos/nix:latest as builder

# Enable flakes
RUN echo "experimental-features = nix-command flakes" >> /etc/nix/nix.conf

WORKDIR /app
COPY . .

# 1. Mount a cache to /nix-cache
# 2. Tell Nix to treat /nix-cache as a binary cache (substituter)
# 3. After the build, copy the new paths into the cache
RUN --mount=type=cache,target=/nix-cache \
    nix build .#hiring-agent \
      --extra-substituters "file:///nix-cache?trusted=1" \
      --fallback && \
    nix copy --to "file:///nix-cache" .#hiring-agent && \
    mkdir -p /tmp/nix-store-closure && \
    xargs cp -R -t /tmp/nix-store-closure < <(nix-store -qR result)

# Final stage
FROM debian:bookworm-slim

# Install CA certificates (essential for OpenAI/GitHub API calls)
RUN apt-get update && apt-get install -y ca-certificates && rm -rf /var/lib/apt/lists/*

# Copy the nix store closure
COPY --from=builder /tmp/nix-store-closure /nix/store

# Copy the build result (which is a symlink in the builder, but COPY follows it)
COPY --from=builder /app/result /app

# Ensure we use the Nix-provided binary and environment
ENV PATH="/app/bin:${PATH}"
ENV PYTHONUNBUFFERED=1

WORKDIR /app
EXPOSE 8000

# Run the app
ENTRYPOINT ["hiring-agent"]
CMD ["--host", "0.0.0.0", "--port", "8000"]

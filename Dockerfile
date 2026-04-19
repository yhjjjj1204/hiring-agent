FROM nixos/nix:latest as builder

# Enable flakes
RUN echo "experimental-features = nix-command flakes" >> /etc/nix/nix.conf

WORKDIR /app
COPY . .

# Build the hiring-agent package
RUN nix build .#hiring-agent

# Extract the full closure to a directory
RUN mkdir -p /tmp/nix-store-closure
RUN xargs cp -R -t /tmp/nix-store-closure < <(nix-store -qR result)

# Use a slightly more complete base for runtime to ensure /bin/sh and basic libs are happy
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

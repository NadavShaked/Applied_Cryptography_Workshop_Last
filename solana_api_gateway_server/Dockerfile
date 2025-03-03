# Use the official Rust image for building
FROM rust:1.84.0 as builder

# Set the working directory inside the container
WORKDIR /app

# Copy your project into the container
COPY . /app/solana_api_gateway_server

# Set the working directory to the main project directory
WORKDIR /app/solana_api_gateway_server

# Build the project
RUN cargo build --release

# Use a newer base image for running the app (Ubuntu 22.04)
FROM ubuntu:22.04

# Set the working directory in the final image
WORKDIR /app

# Install required system dependencies including ca-certificates and libc6 (glibc)
RUN apt-get update && \
    apt-get install -y ca-certificates libc6 && \
    rm -rf /var/lib/apt/lists/*

# Copy the compiled Rust binary from the builder stage
COPY --from=builder /app/solana_api_gateway_server/target/release/solana-api-gateway-server /app/

# Expose the port your server runs on
EXPOSE 3030

# Command to run the application
CMD ["/app/solana-api-gateway-server"]

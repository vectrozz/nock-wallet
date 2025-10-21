FROM ubuntu:24.04

# Éviter les prompts interactifs
ENV DEBIAN_FRONTEND=noninteractive

# Installer dépendances de build
RUN apt-get update && apt-get install -y \
    curl git make clang llvm-dev libclang-dev protobuf-compiler pkg-config \
    build-essential ca-certificates \
 && rm -rf /var/lib/apt/lists/*

# Installer Rust (rustup)
RUN curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y
ENV PATH="/root/.cargo/bin:${PATH}"

COPY nockchain-wallet /usr/local/bin/nockchain-wallet
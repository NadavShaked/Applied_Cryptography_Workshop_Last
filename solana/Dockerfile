FROM ubuntu:noble


ENV LANG=en_US.UTF-8  
ENV LANGUAGE=en_US:en  
ENV LC_ALL=en_US.UTF-8
ENV PYVERSION=3.12
ENV TZ=America/New_York

RUN ln -snf /usr/share/zoneinfo/$TZ /etc/localtime && echo $TZ > /etc/timezone

# Install dependencies and some utility packages
RUN  apt-get update && \
     DEBIAN_FRONTEND=noninteractive apt-get install -y python3.12 git zip unzip tar sed openssl bind9-utils iproute2 file jq procps man curl net-tools  \
     locales \
     build-essential pkg-config \
     libudev-dev llvm libclang-dev \
     protobuf-compiler libssl-dev \
     screen nano vim bc && \
     locale-gen $LC_ALL
    
USER ubuntu

SHELL ["/bin/bash", "-c"]

# Install RUST    
RUN  curl --proto '=https' --tlsv1.2 -sSf https://sh.rustup.rs | sh -s -- -y

# Install patched Solana CLI
# RUN sh -c "$(curl -sSfL https://release.anza.xyz/stable/install)"
WORKDIR /home/ubuntu
RUN git clone --branch v2.1.11 https://github.com/anza-xyz/agave.git 

COPY max_limit.patch /tmp/

RUN export PATH=$HOME/.cargo/bin:$PATH && \
    mkdir -p $HOME/.local/share/solana/install/releases && \
    cd agave && \
    git apply /tmp/max_limit.patch && \
    ./scripts/cargo-install-all.sh $HOME/.local/share/solana/install/releases/patched 

RUN ln -s $HOME/.local/share/solana/install/releases/patched $HOME/.local/share/solana/install/releases/active_release && \
    echo export PATH=$HOME/.local/share/solana/install/releases/active_release/bin:$PATH >> $HOME/.bashrc

# Install Anchor CLI
RUN . "$HOME/.cargo/env" && cargo install --git https://github.com/coral-xyz/anchor avm --force && \
    avm install latest && \
    avm use latest
    
# Install Node and Yarn
RUN curl -o- https://raw.githubusercontent.com/nvm-sh/nvm/master/install.sh | bash 

RUN export NVM_DIR="$HOME/.nvm" && \
    [ -s "$NVM_DIR/nvm.sh" ] && . "$NVM_DIR/nvm.sh" && \
    nvm install node && \
    npm install --global yarn

WORKDIR /home/ubuntu

RUN rm -rf /home/ubuntu/.cargo/registry/*

RUN echo . "$HOME/.cargo/env" >> $HOME/.bashrc && echo export PATH="$HOME/.local/share/solana/install/releases/active_release/bin:$PATH" >> $HOME/.profile

USER root
RUN mkdir -p /home/ubuntu/test-ledger && chown ubuntu:ubuntu /home/ubuntu/test-ledger
USER ubuntu

CMD ["bash", "--login", "-c", "solana-test-validator --faucet-sol 1000000000 --compute-unit-limit 500000000"]


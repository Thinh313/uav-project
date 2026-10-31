FROM ubuntu@sha256:534baea6a22c03a63003dbc8dbe78fe34bc0d7e595d9a9dc9834884ff530eb55
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends gcc g++ libc6-dev binutils git python3 python3-empy python3-future python3-lxml python3-numpy pkg-config && rm -rf /var/lib/apt/lists/*
RUN apt-get update && DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends python3-pexpect python3-yaml python3-serial python3-pyparsing && rm -rf /var/lib/apt/lists/*

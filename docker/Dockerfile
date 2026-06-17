FROM ubuntu:22.04

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    python3 \
    python3-pip \
    iproute2 \
    iputils-ping \
    tcpdump \
    net-tools \
    && apt-get clean

WORKDIR /app

COPY . /app

CMD ["bash"]

RUN mkdir -p /app/data/input /app/data/output /app/data/logs
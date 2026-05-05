FROM ubuntu:24.04

LABEL org.opencontainers.image.title="flyte-end-to-end-ml-platform-workflow" \
      org.opencontainers.image.description="Flyte 2.0 environment for end_to_end_ml_platform_workflow Harbor task"

ENV DEBIAN_FRONTEND=noninteractive

RUN apt-get update && apt-get install -y \
    curl \
    ca-certificates \
    git \
    python3 \
    python3-pip \
    python3-pytest \
    bash \
    && rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages flyte pandas numpy

RUN mkdir -p /home/user/flyte_project && chmod 0755 /home/user/flyte_project

WORKDIR /home/user

CMD ["/bin/bash"]

FROM ubuntu:24.04

LABEL org.opencontainers.image.title="flyte-task-with-dynamic-parallelism" \
      org.opencontainers.image.description="Flyte 2.0 environment for task_with_dynamic_parallelism Harbor task"

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

RUN pip3 install --break-system-packages flyte

RUN mkdir -p /home/user/flyte_project && chmod 0755 /home/user/flyte_project

WORKDIR /home/user

CMD ["/bin/bash"]

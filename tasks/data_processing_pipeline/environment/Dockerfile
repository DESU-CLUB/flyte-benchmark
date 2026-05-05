FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git python3 python3-pip python3-pytest bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages flyte

RUN mkdir -p /home/user && chmod 0755 /home/user

RUN mkdir -p /home/user/flyte_project

LABEL Author="any-task-builder"
LABEL Description="Flyte 2.0 data processing pipeline task environment with project directory at /home/user/flyte_project."

# Container contents:
#   - ubuntu:24.04 base image
#   - python3, python3-pip, python3-pytest, curl, git, bash
#   - flyte (Flyte 2.0) installed via pip3 --break-system-packages
#   - /home/user/flyte_project  — empty project directory ready for the agent

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

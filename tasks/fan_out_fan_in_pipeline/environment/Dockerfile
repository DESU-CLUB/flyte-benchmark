FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git python3 python3-pip python3-pytest bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages flyte

RUN mkdir -p /home/user/flyte_project && chmod 0755 /home/user/flyte_project

WORKDIR /home/user

LABEL Author="any-task-builder"
LABEL Description="Flyte 2.0 environment for the fan_out_fan_in_pipeline Harbor task."

# Container contents:
#   - python3, pip3, pytest installed
#   - flyte pip package installed (Flyte 2.0)
#   - /home/user/flyte_project  — empty project directory ready for the agent's script

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

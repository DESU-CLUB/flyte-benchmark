FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git python3 python3-pip python3-pytest bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages flyte

RUN mkdir -p /home/user/flyte_project && chmod 0755 /home/user/flyte_project

LABEL Author="any-task-builder"
LABEL Description="Flyte 2.0 experiment tracking pipeline task environment with flyte installed."

# Container contents:
#   - flyte pip package installed (includes flyte.TaskEnvironment, flyte.Cache, flyte.Resources)
#   - /home/user/flyte_project  — project directory for the experiment tracking system
#   - python3, python3-pip, python3-pytest for running and testing the agent's script

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

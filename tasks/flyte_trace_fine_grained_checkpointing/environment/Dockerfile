FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git python3 python3-pip python3-pytest bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages flyte

RUN mkdir -p /home/user/flyte_project && chmod 0755 /home/user/flyte_project

RUN mkdir -p /home/user && chmod 0755 /home/user

LABEL Author="any-task-builder"
LABEL Description="Flyte 2.0 environment for flyte_trace_fine_grained_checkpointing — demonstrates @flyte.trace for granular LLM-call checkpointing."

# Container contents:
#   - ubuntu:24.04 base with curl, git, python3, python3-pip, python3-pytest, bash
#   - flyte package installed via pip3 (includes @flyte.trace decorator)
#   - /home/user/flyte_project  — project directory for the agent to write trace_pipeline.py

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

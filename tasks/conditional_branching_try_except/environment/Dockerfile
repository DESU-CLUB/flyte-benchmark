FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git python3 python3-pip python3-pytest bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages flyte

RUN mkdir -p /home/user/flyte_project && chmod 0755 /home/user/flyte_project

LABEL Author="any-task-builder"
LABEL Description="Flyte 2.0 environment for conditional_branching_try_except Harbor task — demonstrates Python if/elif/else conditional branching (flytekit.conditional is removed in Flyte 2.0)."

# Container contents:
#   - ubuntu:24.04 base with curl, ca-certificates, git, python3, python3-pip, python3-pytest, bash
#   - flyte (latest) installed via pip3 --break-system-packages
#   - /home/user/flyte_project  — empty project directory for the agent to populate

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

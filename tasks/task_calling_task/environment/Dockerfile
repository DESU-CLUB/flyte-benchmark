FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git python3 python3-pip python3-pytest bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages flyte

RUN mkdir -p /home/user/flyte_project && chmod 0755 /home/user/flyte_project

LABEL Author="any-task-builder"
LABEL Description="Flyte 2.0 environment for task_calling_task: sequential task composition demo."

# Container contents:
#   - python3, pip3, pytest installed
#   - flyte pip package installed
#   - /home/user/flyte_project  — working directory for the chained_tasks.py script

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

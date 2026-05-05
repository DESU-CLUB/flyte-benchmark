FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git python3 python3-pip python3-pytest bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

RUN pip3 install --break-system-packages flyte

RUN mkdir -p /home/user && chmod 0755 /home/user

LABEL Author="any-task-builder"
LABEL Description="Flyte 2.0 environment for task_with_file_io: CSV filter pipeline with pre-created input.csv."

RUN mkdir -p /home/user/flyte_project && \
    printf 'name,score\nalice,85\nbob,92\ncharlie,78\n' > /home/user/flyte_project/input.csv

# Container contents:
#   - python3, pip3, pytest installed
#   - flyte pip package installed
#   - /home/user/flyte_project  — working directory for the file_pipeline.py script
#   - /home/user/flyte_project/input.csv  — pre-created CSV with header name,score and 3 rows

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

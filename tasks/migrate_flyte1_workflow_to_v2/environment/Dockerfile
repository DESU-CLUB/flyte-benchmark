FROM ubuntu:24.04

RUN apt-get update -y && \
    DEBIAN_FRONTEND=noninteractive apt-get install -y --no-install-recommends \
        curl ca-certificates git python3 python3-pip python3-pytest bash && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Install both flyte (2.0) and flytekit (1.x) so the legacy file is syntactically
# importable for context, while the agent targets the new flyte package.
RUN pip3 install --break-system-packages flyte flytekit

RUN mkdir -p /home/user/flyte_project && chmod 0755 /home/user/flyte_project

# Pre-create the Flyte 1.0 legacy script that the agent must migrate.
RUN cat > /home/user/flyte_project/legacy_workflow.py << 'LEGACY_EOF'
import flytekit
from flytekit import task, workflow

@task
def square(n: int) -> int:
    return n ** 2

@task
def total(values: list) -> int:
    return sum(values)

@workflow
def compute_sum_of_squares(numbers: list) -> int:
    squared = flytekit.map_task(square)(n=numbers)
    return total(values=squared)

if __name__ == "__main__":
    result = compute_sum_of_squares(numbers=[1, 2, 3, 4, 5])
    print(f"Sum of squares: {result}")
LEGACY_EOF

WORKDIR /home/user

LABEL Author="any-task-builder"
LABEL Description="Flyte 2.0 migration environment: contains a pre-existing Flyte 1.0 legacy_workflow.py that the agent must migrate to Flyte 2.0 (modern_workflow.py)."

# Container contents:
#   - python3, pip3, pytest installed
#   - flyte pip package installed (Flyte 2.0)
#   - flytekit pip package installed (Flyte 1.x, for legacy file context only)
#   - /home/user/flyte_project/legacy_workflow.py  — pre-created Flyte 1.0 script
#   - /home/user/flyte_project/                    — agent writes modern_workflow.py here

CMD ["/bin/bash", "-c", "trap : TERM INT; sleep infinity & wait"]

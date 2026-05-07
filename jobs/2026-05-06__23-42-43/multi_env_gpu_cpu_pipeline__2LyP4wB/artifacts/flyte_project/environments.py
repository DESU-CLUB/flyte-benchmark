import flyte

# CPU environment for lightweight preprocessing tasks (4 CPUs, 8 GiB RAM)
cpu_env = flyte.TaskEnvironment(
    "cpu-preprocessing",
    resources=flyte.Resources(cpu=4, memory="8Gi"),
)

# GPU environment for heavy model training (8 CPUs, 32 GiB RAM)
gpu_env = flyte.TaskEnvironment(
    "gpu-training",
    resources=flyte.Resources(cpu=8, memory="32Gi"),
)

# CPU environment for lightweight evaluation tasks (2 CPUs, 4 GiB RAM)
eval_env = flyte.TaskEnvironment(
    "cpu-evaluation",
    resources=flyte.Resources(cpu=2, memory="4Gi"),
)

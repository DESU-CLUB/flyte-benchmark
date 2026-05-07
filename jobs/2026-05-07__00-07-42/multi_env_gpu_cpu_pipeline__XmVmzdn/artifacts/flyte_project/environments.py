import flyte

cpu_env = flyte.TaskEnvironment("cpu-preprocessing", resources=flyte.Resources(cpu=4, memory="8Gi"))
gpu_env = flyte.TaskEnvironment("gpu-training", resources=flyte.Resources(cpu=8, memory="32Gi"))
eval_env = flyte.TaskEnvironment("cpu-evaluation", resources=flyte.Resources(cpu=2, memory="4Gi"))
from parsl.executors import ThreadPoolExecutor, HighThroughputExecutor
from parsl.providers import LocalProvider
from parsl.launchers import SrunLauncher
from parsl.config import Config
from parsl.monitoring import MonitoringHub
from parsl.addresses import address_by_hostname
import json as js
import logging
import shutil
import os

logger = logging.getLogger()


def gen_config(threads=4, label="local", monitoring=True, slurm=False):
    monitor = None
    if monitoring:
        monitor = MonitoringHub(hub_address=address_by_hostname(),
                                workflow_name="ParslCodeML")
    if slurm == False:
        return Config(
            executors=[ThreadPoolExecutor(label=label,
                                          max_threads=threads)],
            strategy='simple',
            retries=0,
            monitoring=monitor
        )
    else:
        n_workers = os.getenv("SLURM_CPUS_ON_NODE")
        n_nodes = os.getenv("SLURM_NNODES")
        return Config(
            executors=[HighThroughputExecutor(label=label,
                                              address=address_by_hostname(),
                                              max_workers_per_node=int(
                                                  n_workers),
                                              provider=LocalProvider(
                                                  nodes_per_block=1,
                                                  init_blocks=1,
                                                  max_blocks=int(n_nodes),
                                                  min_blocks=0,
                                                  parallelism=1,
                                                  # TODO
                                                  # Change it from hardcoded
                                                  worker_init=f"module load mafft;module load anaconda3/2024.02_sequana;eval \"$(conda shell.bash hook)\";conda {os.getenv("CONDA_ENV")};export PYTHONPATH=$PYTHONPATH:{os.getcwd()}",
                                                  launcher=SrunLauncher(
                                                      overrides=f'-c {n_workers}')
                                              )
                                              )],
            monitoring=monitor
        )


def load_and_check_executables(filename):
    with open(filename, 'r') as f:
        executables_tmp = js.load(f)
        executables = dict()
        for app, info in executables_tmp.items():
            if (len(info["path"]) == 0):  # App is on path
                path = shutil.which(info["executable"])
                if path is None:
                    logger.error(f"Failed to find the {app} executable!")
                    exit(1)
                else:
                    executables[app] = info["executable"]
            else:
                if os.path.exists(os.path.join(info["path"], info["executable"])) == False:
                    logger.error(f"Failed to find the {
                                 app} executable on path {info["path"]}!")
                    exit(1)
                else:
                    executables[app] = os.path.join(
                        info["path"], info["executable"])
        return executables

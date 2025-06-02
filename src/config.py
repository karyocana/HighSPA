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


def gen_config(threads=4, label="local", monitoring=True, slurm=False, environment=None):
    monitor = None
    if monitoring:
        monitor = MonitoringHub(hub_address=address_by_hostname(),
                                workflow_name="HighSPA")
    if slurm == False:
        return Config(
            executors=[ThreadPoolExecutor(label=label,
                                          max_threads=threads)],
            strategy='simple',
            retries=0,
            monitoring=monitor
        )
    else:
        worker_init = ""
        if environment is not None:
            try:
                with open(environment, 'r') as env_:
                    text = env_.readlines()
                    worker_init = ";".join([line.strip() for line in text])
            except:
                worker_init = ""
            
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
                                                  worker_init=worker_init,
                                                  launcher=SrunLauncher(
                                                      overrides=f'-c {n_workers}')
                                              ),
                                              interchange_port_range=(65000,65500)
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

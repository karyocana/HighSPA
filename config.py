from parsl.executors import ThreadPoolExecutor
from parsl.config import Config
from parsl.monitoring import MonitoringHub
from parsl.addresses import address_by_hostname
import json as js
import logging, shutil, os

logger = logging.getLogger()

def gen_config(threads=4, label="local", monitoring = True):
    monitor = None
    if monitoring:
        monitor = MonitoringHub(hub_address=address_by_hostname(),
                                workflow_name="ParslCodeML")
    return Config(
        executors=[ThreadPoolExecutor(label=label,
                                      max_threads=threads)],
        strategy='simple',
        retries = 0,
        monitoring=monitor
    )

def load_and_check_executables(filename):
    executables_tmp = js.load(filename)
    executables = dict()
    for app, info in executables_tmp.items():
        if (len(info["path"]) == 0): #App is on path
            path = shutil.which(info["executable"])
            if path is None:
                logger.error(f"Failed to find the {app} executable!")
                exit(1)
            else:
                executables[app] = info["executable"]
        else:
            if os.path.exists(os.path.join(info["path"], info["executable"])) == False:
                logger.error(f"Failed to find the {app} executable on path {info["path"]}!")
                exit(1)
            else:
                executables[app] = os.path.join(info["path"], info["executable"])
    return executables


            

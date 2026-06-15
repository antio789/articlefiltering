import logging
import subprocess
import time
from datetime import datetime

time_hours = 6
time.sleep(time_hours*3600)

def setup_logger(run_name):
    log_filename = f"logs/{datetime.now().strftime('%m-%d_%H-%M')}_RUNSCRIPT_{run_name}.log"

    logger = logging.getLogger(run_name)
    logger.setLevel(logging.INFO)

    for handler in logger.handlers[:]:
        logger.removeHandler(handler)

    file_handler = logging.FileHandler(log_filename)
    file_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    logger.addHandler(file_handler)

    console_handler = logging.StreamHandler()
    console_handler.setFormatter(logging.Formatter('%(asctime)s %(message)s'))
    logger.addHandler(console_handler)

    return logger
"""
try:
    subprocess.run(['/media/bob-the-second/intelij/pycharmprojects/.venv/bin/python', "pretreatmentrun.py"], check=True)
except Exception as e:
    print(e)
"""
try:
    subprocess.run(['/media/bob-the-second/intelij/pycharmprojects/.venv/bin/python', "pretreatment_agentv2.py"], check=True)
except Exception as e:
    print(e)
try:
    subprocess.run(['/media/bob-the-second/intelij/pycharmprojects/.venv/bin/python', "pretreatment_agent_v3.py"], check=True)
except Exception as e:
    print(e)
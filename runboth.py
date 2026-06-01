import subprocess

# Run v2 first, wait for it to finish
subprocess.run(["/media/bob-the-second/ssd/intelij/pycharmprojects/.venv/bin/python", "pretreatment_agentv2.py"], check=True)

# Then run v1
subprocess.run(['/media/bob-the-second/ssd/intelij/pycharmprojects/.venv/bin/python', "pretreatmentrun.py"], check=True)
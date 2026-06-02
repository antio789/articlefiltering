import subprocess

# Run v2 first, wait for it to finish
subprocess.run(["/media/bob-the-second/ssd/intelij/pycharmprojects/.venv/bin/python", "pretreatment_agentv2.py"], check=True)

# Then run v3
subprocess.run(['/media/bob-the-second/ssd/intelij/pycharmprojects/.venv/bin/python', "pretreatment_agent_v3.py"], check=True)
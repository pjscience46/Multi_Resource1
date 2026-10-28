
import json
import csv
from pathlib import Path
from urllib.request import urlretrieve

# Download a real Montage workflow
url = (
    "https://raw.githubusercontent.com/wfcommons/"
    "WfInstances/main/pegasus/montage/"
    "montage-chameleon-2mass-10d-001.json"
)

filename = "montage.json"

if not Path(filename).exists():
    urlretrieve(url, filename)

# Load workflow
with open(filename, "r", encoding="utf-8") as f:
    data = json.load(f)

workflow = data["workflow"]

# DAG structure
spec_tasks = {
    task["id"]: task
    for task in workflow["specification"]["tasks"]
}

# Recorded executions
execution_tasks = workflow["execution"]["tasks"]

rows = []

for task in execution_tasks:
    task_id = task["id"]
    spec = spec_tasks[task_id]

    memory_bytes = task.get("memoryInBytes")

    rows.append({
        "task_id": task_id,
        "task_name": spec.get("name"),
        "parents": ";".join(spec.get("parents", [])),
        "children": ";".join(spec.get("children", [])),
        "runtime": task.get("runtimeInSeconds"),
        "cores": task.get("coreCount"),
        "memory_GiB": (
            memory_bytes / (1024 ** 3)
            if memory_bytes is not None else None
        ),
        "avg_cpu": task.get("avgCPU")
    })

# Save as CSV
with open("workflow_tasks.csv", "w", newline="") as f:
    writer = csv.DictWriter(
        f, fieldnames=rows[0].keys()
    )
    writer.writeheader()
    writer.writerows(rows)

print("Tasks extracted:", len(rows))
print("Saved to workflow_tasks.csv")

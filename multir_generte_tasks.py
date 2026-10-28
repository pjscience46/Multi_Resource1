
import csv
import random
from pathlib import Path

# Configuration
N_VALUES = [
    100, 200, 300, 400, 500,
    600, 700, 800, 900, 1000
]

NUM_INSTANCES = 100
NUM_RESOURCES = 2
OUTPUT_FOLDER = Path("tasks_multiresource")

# Reproducibility
rng = random.Random(46)


class gen_Task:
    def __init__(self, w, sigma, phi, q):
        self.w = w
        self.sigma = sigma
        self.phi = phi
        self.q = q

    def get_w(self):
        return self.w

    def get_sigma(self):
        return self.sigma

    def get_phi(self):
        return self.phi

    def get_q(self):
        return self.q


def generate_task():
    """Generate parameters for one task."""

    # Total workload: W = 10^X, X ~ U(2, 5)
    w = 10 ** rng.uniform(2, 5)

    # Sequential work fraction
    sigma = rng.uniform(0.05, 0.30)

    # Resource-dependent work fractions
    weights = [
        rng.gammavariate(1.0, 1.0)
        for _ in range(NUM_RESOURCES)
    ]

    total_weight = sum(weights)

    phi = [
        (1 - sigma) * weight / total_weight
        for weight in weights
    ]

    # Communication overhead coefficients
    # q = 10^X, X ~ U(-6, -2)
    q = [
        10 ** rng.uniform(-6, -2)
        for _ in range(NUM_RESOURCES)
    ]

    return gen_Task(w, sigma, phi, q)


def generate_n_tasks(n):
    """Generate n tasks."""
    return [generate_task() for _ in range(n)]


def save_nodes_in_csv(n, file_path):
    """Save task parameters to CSV."""

    nodes = generate_n_tasks(n)

    headers = (
        ["w", "sigma"]
        + [
            f"phi_{i + 1}"
            for i in range(NUM_RESOURCES)
        ]
        + [
            f"q_{i + 1}"
            for i in range(NUM_RESOURCES)
        ]
    )

    with open(
        file_path, "w", newline="", encoding="utf-8"
    ) as f:

        writer = csv.writer(f)
        writer.writerow(headers)

        for task in nodes:
            row = (
                [task.get_w(), task.get_sigma()]
                + task.get_phi()
                + task.get_q()
            )

            writer.writerow(row)


def main():

    OUTPUT_FOLDER.mkdir(
        parents=True, exist_ok=True
    )

    for n in N_VALUES:

        n_folder = OUTPUT_FOLDER / f"n={n}"
        n_folder.mkdir(parents=True, exist_ok=True)

        for i in range(1, NUM_INSTANCES + 1):

            file_path = n_folder / f"{i}.csv"
            save_nodes_in_csv(n, file_path)

        print(
            f"Generated {NUM_INSTANCES} "
            f"task files for n={n}"
        )

    print("Task generation completed successfully.")


if __name__ == "__main__":
    main()

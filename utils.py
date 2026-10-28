import time
import pandas as pd
from task import *
from random import uniform, gammavariate
import csv
import codecs
from numerics import *
from processors import *
from statistics import *
import matplotlib.pyplot as plt
from logging import log
from model import *

MODEL_LIST = [AmdahlMaxModel(), AmdahlSumModel(), PowerSumModel(), PowerMaxModel(), CommunicationSumModel(), CommunicationMaxModel()]


def generate_task(w_bounds=(2, 5), sigma_bounds=(0.05, 0.30), q_bounds=(-6, -2)):
    """Generate a task with the new multi-resource parameters."""
    w = 10 ** uniform(w_bounds[0], w_bounds[1])
    sigma = uniform(sigma_bounds[0], sigma_bounds[1])

    # The resource-dependent fractions sum to (1 - sigma).
    weight_1 = gammavariate(1.0, 1.0)
    weight_2 = gammavariate(1.0, 1.0)
    total_weight = weight_1 + weight_2
    phi_1 = (1 - sigma) * weight_1 / total_weight
    phi_2 = (1 - sigma) * weight_2 / total_weight

    q_1 = 10 ** uniform(q_bounds[0], q_bounds[1])
    q_2 = 10 ** uniform(q_bounds[0], q_bounds[1])
    return Task(w, sigma, phi_1, phi_2, q_1, q_2)


def generate_n_tasks(n, w_bounds=(2, 5), sigma_bounds=(0.05, 0.30), q_bounds=(-6, -2)):
    """Generate a list of n multi-resource tasks."""
    output = []
    for i in range(n):
        output += [generate_task(w_bounds, sigma_bounds, q_bounds)]
    return output


def extract_dependencies_from_csv(file, utf_code="utf-8"):
    """Extract dependencies from a DAGGEN output in CSV format."""
    edges = []
    f = codecs.open(file, "rb", utf_code)
    reader = csv.reader(f)
    for row in reader:
        if len(row) == 1 and row[0] and row[0][0] != '/' and row[0][0] != 'd' and row[0][0] != '}':
            element = row[0][2:]
            i = 0
            while element[i] != ' ':
                i += 1
            first_node = int(element[0:i]) - 1
            while element[i] == "-" or element[i] == ">" or element[i] == " ":
                i += 1
            j = i
            while element[j] != ' ':
                j += 1
            second_node = int(element[i:j]) - 1
            edges += [[first_node, second_node]]
    f.close()
    return edges


def generate_nodes_edges(n, dependency_file, w_bounds=(2, 5), sigma_bounds=(0.05, 0.30), q_bounds=(-6, -2)):
    nodes = generate_n_tasks(n, w_bounds, sigma_bounds, q_bounds)
    edges = extract_dependencies_from_csv(dependency_file)
    for edge in edges:  # Convert node indices to task objects
        edge[0] = nodes[edge[0]]
        edge[1] = nodes[edge[1]]
    return [nodes, edges]


def save_nodes_in_csv(n, file, w_bounds=(2, 5), sigma_bounds=(0.05, 0.30), q_bounds=(-6, -2)):
    """Save a set of generated multi-resource task parameters in a CSV file."""
    nodes = generate_n_tasks(n, w_bounds, sigma_bounds, q_bounds)
    with open(file, 'w', newline='', encoding='utf-8') as f:
        writer = csv.writer(f)
        writer.writerow(['w', 'sigma', 'phi_1', 'phi_2', 'q_1', 'q_2'])
        for task in nodes:
            writer.writerow([task.get_w(), task.get_sigma(), task.get_phi_1(), task.get_phi_2(),
                             task.get_q_1(), task.get_q_2()])


def load_nodes_from_csv(file):
    """Load pre-generated multi-resource task parameters from a CSV file."""
    nodes = []
    with open(file, 'r', newline='', encoding='utf-8') as f:
        reader = csv.DictReader(f)
        for row in reader:
            w = float(row['w'])
            sigma = float(row['sigma'])
            phi_1 = float(row['phi_1'])
            phi_2 = float(row['phi_2'])
            q_1 = float(row['q_1'])
            q_2 = float(row['q_2'])
            nodes.append(Task(w, sigma, phi_1, phi_2, q_1, q_2))
    return nodes


def compute_and_save(result_directory, model_name, mu, alpha, beta, gamma, version, writer, priority_num):

    if model_name == 'PowerSum':
        model = PowerSumModel()
    elif model_name == 'PowerMax':
        model = PowerMaxModel()
    elif model_name == 'CommunicationSum':
        model = CommunicationSumModel()
    elif model_name == 'CommunicationMax':
        model = CommunicationMaxModel()
    elif model_name == 'AmdahlSum':
        model = AmdahlSumModel()
    elif model_name == 'AmdahlMax':
        model = AmdahlMaxModel()
    else:
        raise ValueError(f"Unsupported model: {model_name}")

    # Read system configurations from combinations.csv
    combinations_df = pd.read_csv('combinations.csv')
    row_number = 0
    max_makespan_ratio = float('-inf')

    for index, row in combinations_df.iterrows():
        P = [int(row['P']), int(row['m'])]  # System resource-capacity vector
        d = len(P)
        n = int(row['n'])
        i = int(row['Index'])

        daggen_file = "GRAPHS/n=" + str(n) + "/daggen_output_" + str(i) + ".csv"
        node_file = "tasks_multiresource/n=" + str(n) + "/" + str(i) + ".csv"
        nodes = load_nodes_from_csv(node_file)
        edges = extract_dependencies_from_csv(daggen_file)
        task_graph = Graph(nodes, edges)
        adjacency = task_graph.get_adjacency()

        # Requires the multi-resource lower bound to be implemented in graph.py.
        time_opt = task_graph.get_T_opt(P, adjacency, speedup_model=model)
        processors = Processors(P)

        time_algo_1 = processors.online_scheduling_algorithm(task_graph, 1, alpha=alpha, beta=beta, gamma=gamma,
                                                             adjacency=adjacency, mu=mu, speedup_model=model, P=P, d=d,
                                                             version=version, priority_num=priority_num)

       
        min_time = processors.online_scheduling_algorithm(task_graph, 2, alpha=alpha, beta=beta, gamma=gamma,
                                                          adjacency=adjacency, mu=mu, speedup_model=model, P=P, d=d,
                                                          version=version, priority_num=priority_num)

        makespan_ratio = time_algo_1 / time_opt
        writer.writerow([str(P), str(n), str(time_algo_1), str(time_opt), str(makespan_ratio)])

        if makespan_ratio > max_makespan_ratio:
            max_makespan_ratio = makespan_ratio
        row_number += 1

        if alpha is not None:
            print(f"Completed computation for {row_number} (mu,alpha):{mu,alpha} model:{model_name} P:{P} n:{n}")
        elif beta is not None:
            print(f"Completed computation for {row_number} (mu,beta):{mu,beta} model:{model_name} P:{P} n:{n}")
        elif gamma is not None:
            print(f"Completed computation for {row_number} (mu,gamma):{mu,gamma} model:{model_name} P:{P} n:{n}")
        else:
            print(f"Completed computation for {row_number} mu:{mu} model:{model_name} P:{P} n:{n}")

    print(max_makespan_ratio)
    return max_makespan_ratio

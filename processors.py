from numerics import *
from graph import *
from task import Status
import csv
from math import *
from datetime import datetime
from models import *
from sortedcontainers import SortedList
import logging


class Processors:

    def __init__(self, P):
        # Total capacities of all resource types, e.g. [128, 512]
        self.P = list(P)
        self.available_resources = list(P)
        self.d = len(P)
        self.time = 0

    # Getters and Setters
    ############################################################

    def get_P(self):
        return self.P

    def get_available_resources(self):
        return self.available_resources

    def get_d(self):
        return self.d

    def get_time(self):
        return self.time

    def set_P(self, value):
        self.P = list(value)
        self.d = len(value)
        self.available_resources = list(value)

    def set_available_resources(self, value):
        self.available_resources = list(value)

    def set_time(self, value):
        self.time = value

    # Methods
    ############################################################

    def online_scheduling_algorithm(self, task_graph, allocation_function, alpha, beta, gamma,
        save_in_logs=False, adjacency=None,
        P=None, d=None, mu=None, speedup_model: Model = None,
        version=0, priority_num=0):
        """Online list scheduling with a vector of resource capacities.

        allocation_function:
            1 : allocate_processor_algo
            2 : allocate_processor_Min_time
            3 : allocate_processor_Min_area
        """

        # Use the resource-capacity vector from the class if not supplied.
        if speedup_model is None:
            raise ValueError("Speedup model must be provided from utils.py")
        if P is None:
            P = self.P
        P = list(P)

        if d is None:
            d = len(P)
        if d != len(P):
            raise ValueError("d must match the length of P")
        if mu is None:
            raise ValueError("Pass mu explicitly to online_scheduling_algorithm")

        if adjacency is None:
            adjacency = task_graph.get_adjacency()

        # Reset capacities/clock for each algorithm run on this graph.
        self.P = list(P)
        self.d = d
        self.available_resources = list(P)
        self.time = 0

        waiting_queue = []  # Initialize a waiting queue Q
        process_list = []   # List of tasks currently running
        nodes = task_graph.get_nodes()

        for task in nodes:  # Insert all tasks without parents in waiting queue
            if not task_graph.get_parents(nodes.index(task), adjacency):
                if allocation_function == 1:
                    task.allocate_processor_algo(P, d, mu, alpha, beta, gamma, speedup_model, version)
                elif allocation_function == 2:
                    task.allocate_processor_Min_time(P, d, mu, speedup_model)
                elif allocation_function == 3:
                    task.allocate_processor_Min_area(P, d, mu, speedup_model)
                else:
                    raise ValueError("Unknown allocation_function")

                task.set_needed_time(
                    task.get_execution_time(task.get_allocation(), speedup_model)
                )
                waiting_queue.append(task)
                task.set_status(Status.PROCESSING)

        while waiting_queue or process_list:
            # Cleaning of the resources after the next task finishes
            available_tasks = []
            if process_list:
                task = min(process_list)
                process_list.remove(task)
                task.set_status(Status.PROCESSED)

                # Release EACH resource type, instead of adding vectors.
                allocation = task.get_allocation()
                for i in range(d):
                    self.available_resources[i] += allocation[i]

                for child in task_graph.get_children(nodes.index(task), adjacency):
                    if nodes[child].get_status() == Status.BLOCKED:
                        parents = task_graph.get_parents(child, adjacency)
                        available = True
                        for parent in parents:
                            if nodes[parent].get_status() != Status.PROCESSED:
                                available = False
                                break
                        if available:
                            nodes[child].set_status(Status.AVAILABLE)
                            available_tasks.append(nodes[child])

            # Resource allocation for newly available tasks
            for task in available_tasks:
                if allocation_function == 1:
                    task.allocate_processor_algo(
                        P, d, mu, alpha, beta, gamma, speedup_model, version
                    )
                elif allocation_function == 2:
                    task.allocate_processor_Min_time(P, d, mu, speedup_model)
                elif allocation_function == 3:
                    task.allocate_processor_Min_area(P, d, mu, speedup_model)
                else:
                    raise ValueError("Unknown allocation_function")

                task.set_needed_time(
                    task.get_execution_time(task.get_allocation(), speedup_model)
                )
                waiting_queue.append(task)
                task.set_status(Status.PROCESSING)

            # FCFS, Allocation, Length, Area priorities
            if priority_num == 0:
                priority_name = "FCFS"
                sorted_tasks = list(waiting_queue)
            elif priority_num == 1:
                priority_name = "Allocation"
                # A vector cannot be meaningfully ranked as one count:
                # rank by total normalized allocated resource share.
                sorted_tasks = sorted(
                    waiting_queue,
                    key=lambda t: sum(
                        t.get_allocation()[i] / P[i] for i in range(d)
                    ),
                    reverse=True,
                )
            elif priority_num == 2:
                priority_name = "Length"
                sorted_tasks = sorted(
                    waiting_queue,
                    key=lambda t: t.get_needed_time(),
                    reverse=True,
                )
            elif priority_num == 3:
                priority_name = "Area"
                sorted_tasks = sorted(
                    waiting_queue,
                    key=lambda t: t.get_area(
                        t.get_allocation(), P, speedup_model
                    ),
                    reverse=True,
                )
            else:
                raise ValueError("Unknown priority_num")

            to_remove = []
            for task in sorted_tasks:
                allocation = task.get_allocation()

                # Task starts only when ALL resource types are available.
                if all(
                    self.available_resources[i] >= allocation[i]
                    for i in range(d)
                ):
                    process_list.append(task)
                    to_remove.append(task)
                    task.set_starting_time(self.get_time())
                    for i in range(d):
                        self.available_resources[i] -= allocation[i]

            # Remove scheduled tasks from waiting queue
            for task in to_remove:
                waiting_queue.remove(task)

            # Increment time to the next finishing task
            if process_list:
                next_task = min(process_list)
                self.time = (
                    next_task.get_needed_time() + next_task.get_starting_time()
                )
            elif waiting_queue:
                raise RuntimeError(
                    "Tasks remain in the queue but none can run; "
                    "check allocation vectors and resource capacities."
                )

        # Reset the graph, resource capacities, and simulation clock
        task_graph.init_status()
        final_time = self.get_time()
        logging.debug("Total execution time: %s seconds", final_time)
        self.available_resources = list(P)
        self.set_time(0)
        return final_time


# This class implements a DAG whose nodes are Task objects.

from task import Task, Status
import numpy as np
import logging


class Graph:

    def __init__(self, nodes=None, edges=None):
        self._nodes = nodes if nodes is not None else []
        self._edges = edges if edges is not None else []

    # Getters and Setters
    ############################################################

    def get_nodes(self):
        return self._nodes

    def get_edges(self):
        return self._edges

    def set_nodes(self, value):
        self._nodes = value

    def set_edges(self, value):
        self._edges = value

    # Methods
    ############################################################

    def add_node(self, node):
        """Nodes must contain only Task objects."""
        nodes = self.get_nodes()
        nodes += [node]
        self.set_nodes(nodes)

    def add_edge(self, edge):
        """Edges must be [int, int] pairs identifying parent and child task indices."""
        edges = self.get_edges()
        edges += [edge]
        self.set_edges(edges)

    def get_adjacency(self):
        """Return the adjacency matrix of the graph."""
        nodes = self.get_nodes()
        edges = self.get_edges()
        adjacency = np.zeros((len(nodes), len(nodes)))

        for [i, j] in edges:
            adjacency[i, j] = 1
        return adjacency

    def get_children(self, task, adjacency=None):
        """Return indices of the children of a given task."""
        children = []
        nodes = self.get_nodes()
        if adjacency is None:
            adjacency = self.get_adjacency()
        for i in range(len(nodes)):
            if adjacency[task, i] == 1:
                children += [i]
        return children

    def get_parents(self, task, adjacency=None):
        """Return indices of the parents of a given task."""
        parents = []
        nodes = self.get_nodes()
        if adjacency is None:
            adjacency = self.get_adjacency()
        for i in range(len(nodes)):
            if adjacency[i, task] == 1:
                parents += [i]
        return parents

    def get_A_min(self, P, speedup_model):
        """Sum of minimum average normalized areas of all tasks."""
        A_min = 0
        for task in self.get_nodes():
            A_min += task.get_minimum_area(P, speedup_model)[0]
        return A_min

    def get_C_min(self, P, adjacency, speedup_model):
        """Critical-path lower bound using each task's minimum execution time."""
        nodes = self.get_nodes()
        n = len(nodes)
        weights = [0] * n

        # Process a task only after all its parents have been processed.
        parents = [self.get_parents(i, adjacency) for i in range(n)]
        children = [self.get_children(i, adjacency) for i in range(n)]
        remaining_parents = [len(parents[i]) for i in range(n)]
        free_nodes = [i for i in range(n) if remaining_parents[i] == 0]

        idx = 0
        while idx < len(free_nodes):
            index_task = free_nodes[idx]
            idx += 1

            weight = nodes[index_task].get_minimum_execution_time(P, speedup_model)[0]
            p_weight = max((weights[parent] for parent in parents[index_task]), default=0)
            weights[index_task] = weight + p_weight

            for child in children[index_task]:
                remaining_parents[child] -= 1
                if remaining_parents[child] == 0:
                    free_nodes.append(child)

        if idx != n:
            raise ValueError("The graph contains a cycle; a DAG is required.")

        return max(weights, default=0)

    def get_T_opt(self, P, adjacency, speedup_model):
        """Lower bound on optimal makespan using normalized area and critical path."""
        output = max(self.get_A_min(P, speedup_model), self.get_C_min(P, adjacency, speedup_model))
        logging.debug("Lower bound on optimal makespan: %s", output)
        return output

    def init_status(self):
        """Reset the status of each task in the graph."""
        for task in self.get_nodes():
            task.set_status(Status.BLOCKED)

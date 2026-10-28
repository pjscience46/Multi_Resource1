from math import *
from model import Model
from enum import Enum


class Status(Enum):
    BLOCKED = 0
    AVAILABLE = 1
    PROCESSING = 2
    PROCESSED = 3


class Task:

    def __init__(self, w, sigma, phi_1, phi_2, q_1, q_2,
                 status: Status = Status.BLOCKED, allocation=None,
                 needed_time=None, starting_time=None):
        """Task parameters for a two-resource execution-time model."""
        self._w = w
        self._sigma = sigma
        self._phi_1 = phi_1
        self._phi_2 = phi_2
        self._q_1 = q_1
        self._q_2 = q_2
        self._status: Status = status
        self._allocation = allocation
        self._needed_time = needed_time
        self._starting_time = starting_time

    ## Getters and Setters
    ############################################################

    def get_w(self):
        return self._w

    def get_sigma(self):
        return self._sigma

    def get_phi_1(self):
        return self._phi_1

    def get_phi_2(self):
        return self._phi_2

    def get_q_1(self):
        return self._q_1

    def get_q_2(self):
        return self._q_2

    def get_status(self) -> Status:
        return self._status

    def get_allocation(self):
        return self._allocation

    def get_needed_time(self):
        return self._needed_time

    def get_starting_time(self):
        return self._starting_time

    def set_w(self, value):
        self._w = value

    def set_sigma(self, value):
        self._sigma = value

    def set_phi_1(self, value):
        self._phi_1 = value

    def set_phi_2(self, value):
        self._phi_2 = value

    def set_q_1(self, value):
        self._q_1 = value

    def set_q_2(self, value):
        self._q_2 = value

    def set_status(self, value: Status):
        self._status = value

    def set_allocation(self, value):
        # The task now receives an allocation vector [p, m].
        if len(value) != 2 or any(x < 1 for x in value):
            raise ValueError("Each of the two resource allocations must be at least 1")
        self._allocation = list(value)

    def set_needed_time(self, value):
        self._needed_time = value

    def set_starting_time(self, value):
        self._starting_time = value

    ## Methods
    ############################################################

    def __lt__(self, other):
        if self.get_needed_time() is None:
            return False
        if other.get_needed_time() is None:
            return True
        return (self.get_needed_time() + self.get_starting_time()
                < other.get_needed_time() + other.get_starting_time())

    def get_execution_time(self, nb_processors, speedup_model: Model):
        """Return the execution time for an allocation vector [p, m]."""
        if len(nb_processors) != 2 or any(x < 1 for x in nb_processors):
            raise ValueError("Each of the two resource allocations must be at least 1")
        return speedup_model.time(self, nb_processors)

    def get_area(self, nb_processors, P, speedup_model: Model):
        """Return average normalized area for allocation [p, m] and capacities P."""
        execution_time = self.get_execution_time(nb_processors, speedup_model)
        area_1 = nb_processors[0] * execution_time / P[0]
        area_2 = nb_processors[1] * execution_time / P[1]
        return (area_1 + area_2) / 2

    def get_p_max(self, P, speedup_model: Model):
        """With no task-specific maxima, use both system capacities."""
        return list(P)

    def allocate_processor_algo(self, P_num, d, mu, alpha, beta, gamma,
                                speedup_model: Model, version):

        # Step 1: Initial Allocation
        w = self.get_w()
        sigma = self.get_sigma()
        phi_1 = self.get_phi_1()
        phi_2 = self.get_phi_2()
        q_1 = self.get_q_1()
        q_2 = self.get_q_2()

        if d != 2 or len(P_num) != 2:
            raise ValueError("This Task class currently supports two resource types")

        # Max capacity for each resource type
        p_max = P_num[0]
        m_max = P_num[1]

        t_min = self.get_minimum_execution_time(P_num, speedup_model)
        a_min = self.get_minimum_area(P_num, speedup_model)
        final_nb_processors = None

        if version == 0:  # MAST
            Beta_min = inf
            for p in range(1, p_max + 1):
                for m in range(1, m_max + 1):
                    allocation = [p, m]
                    AR = self.get_area(allocation, P_num, speedup_model) / a_min[0]
                    TR = self.get_execution_time(allocation, speedup_model) / t_min[0]
                    if TR >= 1 and TR <= beta:
                        if AR < Beta_min:
                            Beta_min = AR
                            final_nb_processors = allocation

        elif version == 1:  # MTSA
            Alpha_min = inf
            for p in range(1, p_max + 1):
                for m in range(1, m_max + 1):
                    allocation = [p, m]
                    AR = self.get_area(allocation, P_num, speedup_model) / a_min[0]
                    TR = self.get_execution_time(allocation, speedup_model) / t_min[0]
                    if AR >= 1 and AR <= alpha:
                        if TR < Alpha_min:
                            Alpha_min = TR
                            final_nb_processors = allocation

        elif version == 2:  # MTPA
            min_value = inf
            for p in range(1, p_max + 1):
                for m in range(1, m_max + 1):
                    allocation = [p, m]
                    AR = self.get_area(allocation, P_num, speedup_model) / a_min[0]
                    TR = self.get_execution_time(allocation, speedup_model) / t_min[0]
                    total_value = (AR * gamma) + (TR * (1 - gamma))
                    if total_value < min_value:
                        min_value = total_value
                        final_nb_processors = allocation

        elif version == 3:  # FAIR
            R_min = inf
            for p in range(1, p_max + 1):
                for m in range(1, m_max + 1):
                    allocation = [p, m]
                    AR = self.get_area(allocation, P_num, speedup_model) / a_min[0]
                    TR = self.get_execution_time(allocation, speedup_model) / t_min[0]
                    R_j = max(TR, AR)
                    if R_j < R_min:
                        R_min = R_j
                        final_nb_processors = allocation

        else:
            raise ValueError("version must be 0 (MAST), 1 (MTSA), 2 (MTPA), or 3 (FAIR)")

        if final_nb_processors is None:
            raise ValueError("No feasible allocation found")

        # Preserve original behavior: cap versions 0, 1, 2; FAIR is uncapped.
        if version in (0, 1, 2):
            final_nb_processors = [
                min(final_nb_processors[0], ceil(mu * p_max)),
                min(final_nb_processors[1], ceil(mu * m_max))
            ]

        self.set_allocation(final_nb_processors)

    def get_minimum_execution_time(self, P, speedup_model: Model):
        """Return [minimum time, allocation] over all [p, m] combinations."""
        t_min = inf
        p_min = None

        p_max = P[0]
        m_max = P[1]

        for p in range(1, p_max + 1):
            for m in range(1, m_max + 1):
                allocation = [p, m]
                execution_time = self.get_execution_time(allocation, speedup_model)
                if execution_time < t_min:
                    t_min = execution_time
                    p_min = allocation

        return [t_min, p_min]

    def get_minimum_area(self, P, speedup_model: Model):
        """Return [minimum average normalized area, allocation]."""
        area_min = inf
        p_min = None

        p_max = P[0]
        m_max = P[1]

        for p in range(1, p_max + 1):
            for m in range(1, m_max + 1):
                allocation = [p, m]
                average_area = self.get_area(allocation, P, speedup_model)
                if average_area < area_min:
                    area_min = average_area
                    p_min = allocation

        return [area_min, p_min]

    def allocate_processor_Min_time(self, P, d, mu, speedup_model: Model):
        """Allocate the resource vector minimizing execution time."""
        self.set_allocation(self.get_minimum_execution_time(P, speedup_model)[1])

    def allocate_processor_Min_area(self, P, d, mu, speedup_model: Model):
        """Allocate the resource vector minimizing average area."""
        self.set_allocation(self.get_minimum_area(P, speedup_model)[1])

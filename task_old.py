
from math import *
from model import Model
from enum import Enum
from itertools import product


class Status(Enum):
    BLOCKED = 0
    AVAILABLE = 1
    PROCESSING = 2
    PROCESSED = 3


class Task:

    def __init__(self, w, sigma, phi_1, phi_2, q_1, q_2, status: Status = Status.BLOCKED, allocation=None, needed_time=None, starting_time=None, ):
        """
        :param w: The total parallelizable work of the task
        :param sigma: The sequential work fraction
        :param phi_1: The resource-dependent work fraction for resource 1
        :param phi_2: The resource-dependent work fraction for resource 2
        :param q_1: The communication overhead for resource 1
        :param q_2: The communication overhead for resource 2
        :param status: Can take the values 0 (non available), 1 (available), 2 (in the queue or being processed),
                       3 (processed).
        :param allocation: If None, the algorithm "allocate_processor" has not been run yet, else it's the number
                           of processor needed for the completion of the task.
        :param needed_time: The time needed by the task to be processed ( it depends on the allocation)
        :param starting_time: The time when the task start being processed.
        """
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

        if value < 1:

            raise ValueError("The number of allocated processors must be superior to 1")

        self._allocation = value

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
        return self.get_needed_time() + self.get_starting_time() < other.get_needed_time() + other.get_starting_time()

    def get_execution_time(self, nb_processors, speedup_model: Model):
        """
        Return the execution time for a given task,speedup model ( Amdahl, Communication, General, Roofline ).
        """
        # if self.get_p() == 0:
        #     raise ValueError("p must be different from 0")
       
        if nb_processors < 1:
            raise ValueError("The number of processors must be superior to 1")
        return speedup_model.time(self, nb_processors) 

    def get_area(self, number_of_processors, speedup_model: Model):
        """Return the area of a task depending on the number of processor allocated and the speedup model"""
        return self.get_execution_time(number_of_processors, speedup_model) * number_of_processors

    def get_p_max(self, P, speedup_model: Model):
        """"Allocating more than p_max processors to the task will no longer decrease its execution time"""
        return speedup_model.p_max(self, P)
 

    def allocate_processor_algo(self, P_num, d, mu, alpha,beta,gamma, speedup_model: Model,version):
        

        # Step 1 : Initial Allocation
        w = self.get_w()
        sigma = self.get_sigma()
        phi_1 = self.get_phi_1()
        phi_2 = self.get_phi_2()
        q_1 = self.get_q_1()
        q_2 = self.get_q_2()


        #p_num - number of avilable processors
       # p_max = self.get_p_max(P_num, speedup_model)
        p_max = P_num[0]
        m_max = P_num[1]
       
        t_min = self.get_minimum_execution_time(p_max, speedup_model)
        a_min = self.get_minimum_area(1, speedup_model)
        final_nb_processors = -1
        if version == 0:
            Beta_min = inf
            for i in range(1, p_max + 1):   
                AR = self.get_area(i, speedup_model) / a_min[0]  #ratio of area of task to minimum area
                TR = self.get_execution_time(i, speedup_model) / t_min[0] #ratio of time taken by task to minimum time
                if TR >=1 and TR <= beta:
                    if AR < Beta_min:
                        Beta_min = AR
                        final_nb_processors = i 

            if final_nb_processors > ceil(mu * P_num):
                self.set_allocation(ceil(mu * P_num))
            else:
                self.set_allocation(final_nb_processors) 

        elif version == 1:
            Alpha_min = inf
            for i in range(1, p_max + 1):
                AR = self.get_area(i, speedup_model)/ a_min[0]
                TR = self.get_execution_time(i, speedup_model) / t_min[0]
                if AR >=1 and AR <= alpha:
                    if TR < Alpha_min:
                        Alpha_min = TR
                        final_nb_processors = i 

            if final_nb_processors > ceil(mu * P_num):
                self.set_allocation(ceil(mu * P_num))
            else:
                self.set_allocation(final_nb_processors)  

        elif version == 2:
            min_value = float('inf')
            for i in range(1, p_max + 1):   
                AR = self.get_area(i, speedup_model) / a_min[0]
                TR = self.get_execution_time(i, speedup_model) / t_min[0]
                total_value = ((AR )* gamma ) + ((TR )* (1 - gamma))
                if total_value < min_value:
                    min_value = total_value
                    final_nb_processors = i 

            if final_nb_processors > ceil(mu * P_num):
                self.set_allocation(ceil(mu * P_num))
            else:
                self.set_allocation(final_nb_processors) 

        elif version == 3:
            R_min = inf   
            final_nb_processors = 1
            for i in range(1, p_max + 1):
                AR = self.get_area(i, speedup_model) / a_min[0]
                TR = self.get_execution_time(i, speedup_model) / t_min[0]
                R_j = max(TR, AR)

                if R_j < R_min:
                    R_min = R_j
                    final_nb_processors = i    #not storing global r as we are not using it to calculate adjusted allocation
            self.set_allocation(final_nb_processors)

            

    def get_minimum_execution_time(self, P, speedup_model: Model):
        """Return the minimum execution time"""
        t_min = inf
        p_min = -1
        for p in range(1, self.get_p_max(P, speedup_model) + 1):
            execution_time = self.get_execution_time(p, speedup_model)
            if execution_time < t_min:
                t_min = execution_time
                p_min = p
        return [t_min, p_min]

    # def get_minimum_area(self, P, speedup_model: Model):
    #     """Return the minimum area ( Processors needed x execution times )"""
    #     area_min = 100000000000
    #     p_min = -1
    #     for p in range(1, self.get_p_max(P, speedup_model) + 1):
    #         execution_time = self.get_execution_time(p, speedup_model)
    #         if execution_time * p < area_min:
    #             area_min = execution_time * p
    #             p_min = p
    #     return [area_min, p_min]


    def get_minimum_area(self, P, speedup_model: Model):
        """Return the minimum average normalized area
    and its corresponding resource allocation.

    P: Total resource capacities [P1, P2, ..., Pd]
    """

        d = len(P)

        area_min = float('inf')
        p_min = None

        # Maximum allocation for each resource type
        p_max = self.get_p_max(P, speedup_model)

        # Generate all possible resource allocation vectors
        resource_ranges = [
            range(1, p_max[i] + 1)
            for i in range(d)
        ]

        for p in product(*resource_ranges):

            # Execution time for the complete allocation vector
            execution_time = self.get_execution_time(
                p, speedup_model
            )

            # Calculate normalized area for each resource type
            total_area = 0

            for i in range(d):
                work_i = p[i] * execution_time
                area_i = work_i / P[i]
                total_area += area_i

            # Average area across all d resource types
            average_area = total_area / d

            if average_area < area_min:
                area_min = average_area
                p_min = p

        return [area_min, p_min]



    def allocate_processor_Min_time(self, P, mu, speedup_model: Model):
        """Allocate the processor to minimize the execution time of the task"""
        self.set_allocation(self.get_minimum_execution_time(P, speedup_model)[1])

    def allocate_processor_Min_area(self, P, mu, speedup_model: Model):
        """Allocate the processor to minimize the area of the task"""
        self.set_allocation(self.get_minimum_area(P, speedup_model)[1])

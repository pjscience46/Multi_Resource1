from math import sqrt, floor, ceil
from task import Task
from model import Model


# class AmdahlModel(Model):
#     name = "Amdahl"


#     def time(self, task: Task, nb_proc: int) -> float:
#         return task.get_w() * ((1/nb_proc) + task.get_d())

#     def p_max(self, task: Task, p: int) -> int:
#         return p


# class CommunicationModel(Model):
#     name = "Communication"

#     def time(self, task: Task, nb_proc: int) -> float:
#         w, c = task.get_w(), task.get_c()
#         return w * ((1/ nb_proc) + (c * (nb_proc - 1)))

#     def p_max(self, task: Task, p: int) -> int:
#         s = sqrt(task.get_w() / task.get_c())
#         if task.get_execution_time(floor(s), self) <= task.get_execution_time(ceil(s), self):
#             p_tild = floor(s)
#         else:
#             p_tild = ceil(s)

#         return round(min(p, task.get_p(), p_tild))


# class GeneralModel(Model):
#     name = "General"

 
#     def time(self, task: Task, nb_proc: int) -> float:
#         w, d, p, c = task.get_w(), task.get_d(), task.get_p(), task.get_c()
#         return w * ((1  / min(nb_proc, p)) + d + (c * (nb_proc - 1)))

#     def p_max(self, task: Task, p: int) -> int:
#         s = sqrt(task.get_w() / task.get_c())
#         if task.get_execution_time(floor(s), self) <= task.get_execution_time(ceil(s), self):
#             p_tild = floor(s)
#         else:
#             p_tild = ceil(s)

#         return round(min(p, task.get_p(), p_tild))


# class RooflineModel(Model):
#     name = "Roofline"


#     def time(self, task: Task, nb_proc: int) -> float:
#         w, d, p, c = task.get_w(), task.get_d(), task.get_p(), task.get_c()
#         return w / min(nb_proc, p)

#     def p_max(self, task: Task, p: int) -> int:
#         return min(ceil(task.get_p()), p) #max degree of parallelism, no.of proc





# Fixed exponent for Power models.
# Your current Task class does not contain alpha_1 or alpha_2.
POWER_EXPONENT = 0.8


# ==============================================
# 1. AMDAHL-SUM MODEL
# ==============================================

class AmdahlSumModel(Model):
    name = "AmdahlSum"

    def time(self, task: Task, nb_resources: list[int]) -> float:

        w = task.get_w()
        sigma = task.get_sigma()
        phi_1 = task.get_phi_1()
        phi_2 = task.get_phi_2()

        p1 = nb_resources[0]
        p2 = nb_resources[1]

        return w * (
            sigma
            + phi_1 / p1
            + phi_2 / p2
        )


# ==============================================
# 2. AMDAHL-MAX MODEL
# ==============================================

class AmdahlMaxModel(Model):
    name = "AmdahlMax"

    def time(self, task: Task, nb_resources: list[int]) -> float:

        w = task.get_w()
        sigma = task.get_sigma()
        phi_1 = task.get_phi_1()
        phi_2 = task.get_phi_2()

        p1 = nb_resources[0]
        p2 = nb_resources[1]

        return w * (
            sigma
            + max(
                phi_1 / p1,
                phi_2 / p2
            )
        )


# ==============================================
# 3. POWER-SUM MODEL
# ==============================================

class PowerSumModel(Model):
    name = "PowerSum"

    def time(self, task: Task, nb_resources: list[int]) -> float:

        w = task.get_w()
        phi_1 = task.get_phi_1()
        phi_2 = task.get_phi_2()

        p1 = nb_resources[0]
        p2 = nb_resources[1]

        return w * (
            phi_1 / (p1 ** POWER_EXPONENT)
            + phi_2 / (p2 ** POWER_EXPONENT)
        )


# ==============================================
# 4. POWER-MAX MODEL
# ==============================================

class PowerMaxModel(Model):
    name = "PowerMax"

    def time(self, task: Task, nb_resources: list[int]) -> float:

        w = task.get_w()
        phi_1 = task.get_phi_1()
        phi_2 = task.get_phi_2()

        p1 = nb_resources[0]
        p2 = nb_resources[1]

        return w * max(
            phi_1 / (p1 ** POWER_EXPONENT),
            phi_2 / (p2 ** POWER_EXPONENT)
        )


# ==============================================
# 5. COMMUNICATION-SUM MODEL
# ==============================================

class CommunicationSumModel(Model):
    name = "CommunicationSum"

    def time(self, task: Task, nb_resources: list[int]) -> float:

        w = task.get_w()
        phi_1 = task.get_phi_1()
        phi_2 = task.get_phi_2()
        q_1 = task.get_q_1()
        q_2 = task.get_q_2()

        p1 = nb_resources[0]
        p2 = nb_resources[1]

        return (
            (w * phi_1 / p1)
            + (q_1 * (p1 - 1))
            + (w * phi_2 / p2)
            + (q_2 * (p2 - 1))
        )


# ==============================================
# 6. COMMUNICATION-MAX MODEL
# ==============================================

class CommunicationMaxModel(Model):
    name = "CommunicationMax"

    def time(self, task: Task, nb_resources: list[int]) -> float:

        w = task.get_w()
        phi_1 = task.get_phi_1()
        phi_2 = task.get_phi_2()
        q_1 = task.get_q_1()
        q_2 = task.get_q_2()

        p1 = nb_resources[0]
        p2 = nb_resources[1]

        return max(
            (w * phi_1 / p1)
            + (q_1 * (p1 - 1)),

            (w * phi_2 / p2)
            + (q_2 * (p2 - 1))
        )

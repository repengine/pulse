from interfaces.simulation_interface import SimulationInterface
from interfaces.trust_interface import TrustInterface
from interfaces.symbolic_interface import SymbolicInterface
from interfaces.core_interface import CoreInterface

class ServiceRegistry:
    _services = {}

    @classmethod
    def register_simulation(cls, instance: SimulationInterface):
        cls._services['simulation'] = instance

    @classmethod
    def get_simulation(cls) -> SimulationInterface:
        return cls._services['simulation']

    @classmethod
    def register_trust(cls, instance: TrustInterface):
        cls._services['trust'] = instance

    @classmethod
    def get_trust(cls) -> TrustInterface:
        return cls._services['trust']

    @classmethod
    def register_symbolic(cls, instance: SymbolicInterface):
        cls._services['symbolic'] = instance

    @classmethod
    def get_symbolic(cls) -> SymbolicInterface:
        return cls._services['symbolic']

    @classmethod
    def register_core(cls, instance: CoreInterface):
        cls._services['core'] = instance

    @classmethod
    def get_core(cls) -> CoreInterface:
        return cls._services['core']
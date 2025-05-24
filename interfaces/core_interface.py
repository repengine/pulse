from abc import ABC, abstractmethod
from typing import Any, Optional


class CoreInterface(ABC):
    @abstractmethod
    def load_config(self, filename: str) -> Any:
        pass

    @abstractmethod
    def load_all_configs(self) -> Any:
        pass

    @abstractmethod
    def get_config_value(self, filename: str, key: str, default: Any = None) -> Any:
        pass

    @abstractmethod
    def reload_config(self, filename: str) -> Any:
        pass

    @abstractmethod
    def get_config(
        self, filename: str, key: Optional[str] = None, default: Any = None
    ) -> Any:
        pass

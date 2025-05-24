from interfaces.core_interface import CoreInterface
from core.pulse_config import ConfigLoader, get_config


class CoreAdapter(CoreInterface):
    def __init__(self, config_dir="config"):
        self.loader = ConfigLoader(config_dir)

    def load_config(self, filename):
        return self.loader.load_config(filename)

    def load_all_configs(self):
        return self.loader.load_all_configs()

    def get_config_value(self, filename, key, default=None):
        return self.loader.get_config_value(filename, key, default)

    def reload_config(self, filename):
        return self.loader.reload_config(filename)

    def get_config(self, filename, key=None, default=None):
        return get_config(filename, key, default)

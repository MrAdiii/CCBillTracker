from .dynamic_parser import DynamicParser

class ParserFactory:
    @staticmethod
    def get_parser(provider_config, global_config):
        return DynamicParser(provider_config, global_config)

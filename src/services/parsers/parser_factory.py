from .base_parser import BaseParser
from .credit_card_parser import CreditCardParser
from .airtel_parser import AirtelWifiParser, AirtelPostpaidParser
from .electricity_parser import ElectricityParser

class ParserFactory:
    @staticmethod
    def get_parser(provider_config):
        bill_type = provider_config.get('type', '')
        biller_name = provider_config.get('name', '')
        
        if bill_type == 'Credit Card':
            return CreditCardParser(provider_config)
        elif bill_type == 'Wifi' and 'Airtel' in biller_name:
            return AirtelWifiParser(provider_config)
        elif bill_type == 'Postpaid Cell' and 'Airtel' in biller_name:
            return AirtelPostpaidParser(provider_config)
        elif bill_type == 'Electricity':
            return ElectricityParser(provider_config)
        else:
            return BaseParser(provider_config)

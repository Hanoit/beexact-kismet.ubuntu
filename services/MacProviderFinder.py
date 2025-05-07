import json
import re
import threading
from sqlalchemy.exc import IntegrityError
from models.DBKismetModels import MACProviderTable, MACBaseProviderTable
from repository.RepositoryImpl import RepositoryImpl
from services.SentenceEmbeddings import find_provider
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()
db_lock = threading.Lock()


class MacProviderFinder:
    def __init__(self, session):
        self.__session = session

    def format_separator(self, mac_address, separator):
        formatted_mac = mac_address.replace(':', separator)
        return formatted_mac

    def format_mac_id(self, mac_address, position=None, separator=":"):
        parts = mac_address.split(':')
        if len(parts) > 1:
            formatted_mac = f'{separator}'.join(parts[:position] if position is not None else parts)
            if separator != ":":
                return self.format_separator(formatted_mac, separator)
            else:
                return formatted_mac
        else:
            raise ValueError("This is not a mac address")

    def get_provider_by_mac(self, mac_address):
        mac_id = self.format_mac_id(mac_address, position=5, separator="")
        provider_finder = RepositoryImpl(MACProviderTable, self.__session)
        with db_lock:
            existing_provider = provider_finder.search_by_id(mac_id)

        if existing_provider:
            base_provider = existing_provider.base_provider.provider_name
            return base_provider
        else:
            mac_id = self.format_mac_id(mac_address, position=4, separator="")
            with db_lock:
                existing_provider = provider_finder.search_sql_by_attr(f'{mac_id}', 'mac_sub_prefix')

            if existing_provider:
                base_provider = existing_provider.base_provider.provider_name
                return base_provider
            return None

    def get_provider(self, mac_address, ssid):
        # Try to find a provider based on the SSID
        base_provider = self.simple_match_provider_from_ssid(ssid)
        if not base_provider:
            base_provider = self.advance_match_provider_from_ssid(ssid)
            if not base_provider:
                return self.get_provider_by_mac(mac_address)

        if base_provider:
            mac_id = self.format_mac_id(mac_address, position=5, separator="")
            provider_finder = RepositoryImpl(MACProviderTable, self.__session)
            with db_lock:
                existing_provider = provider_finder.search_by_id(mac_id)
                if not existing_provider:
                    try:
                        mac_sub_prefix = self.format_mac_id(mac_address, position=4, separator="")
                        new_provider = MACProviderTable(id=mac_id, mac_sub_prefix=mac_sub_prefix,
                                                        base_provider_id=base_provider.id)
                        # print(f"{ssid} is {base_provider.provider_name}")
                        self.__session.add(new_provider)
                        self.__session.commit()
                    except IntegrityError:
                        self.__session.rollback()
                    except Exception as e:
                        self.__session.rollback()  # Rollback on general exceptions
                        raise e
                return base_provider.provider_name
        return None

    def simple_match_provider_from_ssid(self, ssid):
        base_providers = RepositoryImpl(MACBaseProviderTable, self.__session)
        list_base_providers = base_providers.search_all()

        for provider in list_base_providers:
            try:
                # Start with the provider's name
                search_terms = [re.escape(provider.provider_name)]

                # Add aliases to the search terms
                if provider.alias:
                    alias_data = json.loads(provider.alias)
                    search_terms.extend(re.escape(alias) for alias in alias_data)

                # Join all terms into a single regex pattern
                regex_pattern = '|'.join(search_terms)

                # Perform the regex search
                if re.search(regex_pattern, ssid, re.IGNORECASE):
                    return provider

            except Exception as e:
                raise ValueError(f"Error decoding JSON from alias provider \n {e}")

        return None

    def advance_match_provider_from_ssid(self, ssid):
        base_providers = RepositoryImpl(MACBaseProviderTable, self.__session)
        base_providers_result = base_providers.search_all()
        if base_providers_result:
            list_base_providers = [provider for provider in base_providers_result]
            provider, index_matching, max_similarity = find_provider(ssid, list_base_providers)
            # Find provider object by name
            if provider and base_providers_result[index_matching].provider_name == provider:
                return base_providers_result[index_matching]

        return None

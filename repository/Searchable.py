from abc import ABC, abstractmethod
from typing import List


class Searchable(ABC):
    @abstractmethod
    def search_by_id(self, id_value: str) -> object:
        """
        Search for a record by ID in the specified table class.

        param id_value: The ID of the record to search for.
        :return: The record if found, else None.
        """
        pass

    @abstractmethod
    def search_all(self) -> List[object]:
        """
        Search for a record by ID in the specified table class.

        :return: The records if found, else [None].
        """
        pass

    @abstractmethod
    def search_join_by_id(self, id_value, relationship_attr) -> object:
        """
        Search for a record by ID and join it with a specified relationship.

        :param id_value: The ID of the record to search for.
        :param relationship_attr: field relation attribute from table_relation_ship.
        :return: The records if found, else [None].
        """
        pass

    @abstractmethod
    def search_sql_by_attr(self, query, attribute) -> object:
        """
        Search for a record by ID and join it with a specified relationship.

        :param query: It is the sentence used into the query filter
        :param attribute: It is the field into he datatable used for running the query
        :return: The records if found, else [None].
        """
        pass
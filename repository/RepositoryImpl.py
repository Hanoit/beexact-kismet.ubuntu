from abc import ABC
from typing import List
from sqlalchemy.orm import joinedload
from repository.Searchable import Searchable


class RepositoryImpl(Searchable):
    def __init__(self, table_class, session):
        self.__table_class = table_class
        self.__session = session

    def search_by_id(self, id_value) -> object:
        """
        Search for a record by ID in the specified table class.
        """
        return self.__session.query(self.__table_class).filter_by(id=id_value).first()

    def search_all(self) -> List[object]:
        """
        Retrieve all records from the specified table class.
        """
        return self.__session.query(self.__table_class).all()

    def search_join_by_id(self, id_value, relationship_attr) -> object:
        """
        Search for a record by ID and join it with a specified relationship.
        """

        return self.__session.query(self.__table_class) \
            .options(joinedload(getattr(self.__table_class, relationship_attr))) \
            .filter_by(id=id_value).first()

    def search_sql_by_attr(self, query, attribute) -> object:
        if not hasattr(self.__table_class, attribute):
            raise ValueError(f"Attribute {attribute} not found in {self.__table_class.__tablename__}")
        return self.__session.query(self.__table_class).filter(
            getattr(self.__table_class, attribute).like(query)).first()


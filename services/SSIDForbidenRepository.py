from models.DBKismetModels import SSIDForbiddenTable
from repository.RepositoryImpl import RepositoryImpl


class SSIDForbiddenRepository:
    def __init__(self, session):
        self.__session = session

    def get_all(self):
        SSIDForbiddenQuery = RepositoryImpl(SSIDForbiddenTable, self.__session)
        return SSIDForbiddenQuery.search_all()


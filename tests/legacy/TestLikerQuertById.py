import unittest
from unittest.mock import MagicMock
from models.DBKismetModels import MACProviderTable
from repository.RepositoryImpl import RepositoryImpl


class TestRepositoryImpl(unittest.TestCase):

    def setUp(self):
        # Create a mock session
        self.Session = MagicMock()
        self.vendor_repository = RepositoryImpl(MACProviderTable, self.Session)

    def test_query_by_id(self):
        # Prepare the mock session to return a specific vendor
        mac_address = '78C57DC0'
        expected_vendor = 'XEROX CORPORATION'

        # Mock the behavior of the query
        mock_session = self.Session.return_value
        mock_query = mock_session.query.return_value
        mock_filter = mock_query.filter_by.return_value
        mock_filter.first.return_value = MagicMock(vendor_name=expected_vendor)

        # Call the method to test
        vendor_name = self.vendor_repository.search_sql_by_id(f"{mac_address}%").vendor_name

        # Verify the results
        self.assertEqual(vendor_name, expected_vendor)

        # Verify that the query method was called correctly
        mock_session.query.assert_called_with(MACProviderTable)
        mock_query.filter_by.assert_called_with(id=mac_address)



if __name__ == '__main__':
    unittest.main()

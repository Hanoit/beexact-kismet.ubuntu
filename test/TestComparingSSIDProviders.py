import unittest
from database.SessionKismetDB import get_session
from services.MacProviderFinder import MacProviderFinder


class TestMacProviderFinder(unittest.TestCase):
    @classmethod
    def setUpClass(cls):
        cls.session = get_session()
        cls.test_ssids = [
            'Gastnetwerk van Marcel',
            'tmobile',
            'Ziggo 4969358',
            'ZiggoAbels',
            'Ziggo 4969358',
            'Ziggo7642477',
            'Ziggo7642477',
            'Ziggo7642477',
            'Ziggo7642477',
            'ZiggoE9DEAA4',
            'ZiggoWes',
            'ZiggoWes',
            'ZiggoWes',
            'ZiggoWes',
            'ZiggoWes',
            'TMNL-9BE1F1',
            'TMNL-A2F7A1',
            'TMNL-ACE2C1',
            'TMNL-ADF111',
            'TMNL-D1DDE1',
            'TMNL-EA9481'
        ]

    def test_simple_match_provider_from_ssid(self):
        repo = MacProviderFinder(self.session)

        for ssid in self.test_ssids:
            print(f"Testing Simple Searching SSID: {ssid}")  # Opcional: para ver el SSID que se está probando
            result = repo.simple_match_provider_from_ssid(ssid)
            self.assertIsNotNone(result, f"Expected provider for SSID '{ssid}' not found.")
            self.assertIn(result.provider_name, ['Ziggo', 'TMNL', 'T-Mobile'],
                          f"Unexpected provider '{result.provider_name}' for SSID '{ssid}'")

        # Prueba con un SSID que no debe coincidir
        ssid = 'Nonexistent SSID'
        result = repo.simple_match_provider_from_ssid(ssid)
        self.assertIsNone(result, "Expected no provider for nonexistent SSID.")

    def test_advance_match_provider_from_ssid(self):
        repo = MacProviderFinder(self.session)

        for ssid in self.test_ssids:
            print(f"Testing Advance Searching SSID: {ssid}")  # Opcional: para ver el SSID que se está probando
            result = repo.advance_match_provider_from_ssid(ssid)
            self.assertIsNotNone(result, f"Expected provider for SSID '{ssid}' not found.")
            self.assertIn(result.provider_name, ['Ziggo', 'TMNL', 'T-Mobile'],
                          f"Unexpected provider '{result.provider_name}' for SSID '{ssid}'")

        # Prueba con un SSID que no debe coincidir
        ssid = 'Nonexistent SSID'
        result = repo.advance_match_provider_from_ssid(ssid)
        self.assertIsNone(result, "Expected no provider for nonexistent SSID.")


if __name__ == '__main__':
    unittest.main()

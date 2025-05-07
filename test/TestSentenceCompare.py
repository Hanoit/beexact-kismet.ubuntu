from services.SentenceEmbeddings import find_provider


def test_find_provider():
    providers_data = [
        "KPN",
        "Ziggo",
        "Vodafone",
        "Odido",
        "TMNL",
        "T-Mobile",
        "Trinet",
        "Delta",
        "Fibercop",
        "Fastweb",
        "Deutsche Glasfaser"
    ]

    # Casos de prueba SSID
    ssid_test_cases = [
        ("TMNL-9BACD1", "TMNL"),
        ("TMNL-EDFB21", "TMNL"),
        ("TMNL-AC11C1_guest1", "TMNL"),
        ("TMNL-CA08FA", "TMNL"),
        ("TMNL-CA08FA5G", "TMNL"),
        ("TMNL-B2B-243e5c", "TMNL"),
        ("TMNL-063B2D_5GEXT", "TMNL"),
        ("TMNL-0F3BC1", "TMNL"),
        ("TMNL-0F99B1", "TMNL"),
        ("TMNL-AECA11", "TMNL"),
        ("TMNL-6EE681_guest1", "TMNL"),
        ("TMNL-683F89-2.4ghz", "TMNL"),
        ("TMNL-BEDCC9", "TMNL"),
        ("TMNL-3590B1_guest1", "TMNL"),
        ("TMNL-356E51_guest1", "TMNL"),
        ("Vodafone-A1B2C3", "Vodafone"),
        ("Ziggo-D4E5F6", "Ziggo"),
        ("Random-SSID", None),  # No debería encontrar un proveedor
    ]

    for ssid, expected_provider in ssid_test_cases:
        provider, index, similarity = find_provider(ssid, providers_data, threshold=0.75)
        print(f"Testing SSID: {ssid}")
        print(f"Expected Provider: {expected_provider}, Found Provider: {provider}, Similarity: {similarity}")
        assert provider == expected_provider, f"Failed for SSID: {ssid}. Expected: {expected_provider}, Found: {provider}"


if __name__ == '__main__':
    # Ejecuta el caso de prueba
    test_find_provider()

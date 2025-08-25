import os
from kismetanalyzer import model, util
from kismetanalyzer.util import parse_networkname, parse_mac, parse_frequency, parse_channel, parse_manufacturer, \
    parse_type, parse_name, parse_commonname, parse_phyname, parse_encryption, parse_loc
from utils import util


class ExtDeviceModel(model.Device):
    """Extended device model that adds encryption, vendor, provider, RSSI, and accuracy."""

    def __init__(self, session=None, base=None, **kwargs):
        """
        Initialize the extended device model.

        :param session_factory: Database session factory.
        :param base: Base data dictionary for device information.
        :param kwargs: Additional attributes for the base Device class.
        """
        super().__init__(**kwargs)
        self.__accuracy_mt: float = 0.0
        self.__encryption: str = ""
        self.__vendor: str = ""
        self.__provider: str = ""
        self.__RSSI: int = 0
        self.__firstSeen: str = ""
        self.__session = session
        self.__base = base
        self.__ssid = ""
        self.__sequential_id = base.get('sequential_id', 'UNKNOWN') if base else 'UNKNOWN'

    @property
    def RSSI(self) -> int:
        """Get or set the RSSI value."""
        return self.__RSSI

    @RSSI.setter
    def RSSI(self, value: int):
        self.__RSSI = value

    @property
    def firstSeen(self) -> str:
        """Get or set the first seen time."""
        return self.__firstSeen

    @firstSeen.setter
    def firstSeen(self, value: str):
        self.__firstSeen = value

    @property
    def encryption(self) -> str:
        """Get or set the encryption type."""
        return self.__encryption

    @encryption.setter
    def encryption(self, value: str=""):
        self.__encryption = value

    @property
    def vendor(self) -> str:
        """Get or set the vendor name."""
        return self.__vendor

    @vendor.setter
    def vendor(self, value: str=""):
        self.__vendor = value

    @property
    def provider(self) -> str:
        """Get or set the provider name."""
        return self.__provider

    @provider.setter
    def provider(self, value: str=""):
        self.__provider = value

    @property
    def accuracy_mt(self) -> float:
        """Get or set the accuracy in meters."""
        return self.__accuracy_mt

    @accuracy_mt.setter
    def accuracy_mt(self, value: float=0.0):
        self.__accuracy_mt = value

    @property
    def ssid(self) -> str:
        """Get or set the accuracy in meters."""
        return self.__ssid

    @ssid.setter
    def ssid(self, value: str=""):
        self.__ssid = value

    @property
    def sequential_id(self) -> str:
        """Get the sequential ID for tracking."""
        return self.__sequential_id

    def from_json(self, dev: dict, flip_coord: bool=False, strongest: bool=False):
        """
        Create an ExtDeviceModel instance from JSON data.

        :param dev: JSON data representing the device.
        :param flip_coord: Whether to need flipping lat and log coordinates.
        :param strongest: Whether to use the strongest signal.
        :return: An instance of ExtDeviceModel.
        """

        lon, lat, alt = parse_loc(dev, strongest)
        if not flip_coord:
            loc = model.Location(lon, lat, alt)
        else:
            loc = model.Location(lat, lon, alt)

        self.location = loc
        self.ssid = parse_networkname(dev)
        self.mac = parse_mac(dev)
        self.frequency = parse_frequency(dev)
        self.channel = parse_channel(dev)
        self.manufacturer = parse_manufacturer(dev)
        self.type = parse_type(dev)
        self.name = parse_name(dev)
        self.commonname = parse_commonname(dev)
        self.phyname = parse_phyname(dev)
        self.encryption = parse_encryption(dev)
        self.vendor = util.parse_vendor(self.mac, self.__session, self.__sequential_id)
        self.provider = util.parse_provider(self.mac, self.ssid, self.__session)

    def from_json_no_vendor(self, dev: dict, flip_coord: bool=False, strongest: bool=False):
        """
        Create an ExtDeviceModel instance from JSON data WITHOUT vendor lookup (for batch processing)
        
        :param dev: JSON data representing the device.
        :param flip_coord: Whether to need flipping lat and log coordinates.
        :param strongest: Whether to use the strongest signal.
        :return: An instance of ExtDeviceModel.
        """
        
        lon, lat, alt = parse_loc(dev, strongest)
        if not flip_coord:
            loc = model.Location(lon, lat, alt)
        else:
            loc = model.Location(lat, lon, alt)

        self.location = loc
        self.ssid = parse_networkname(dev)
        self.mac = parse_mac(dev)
        self.frequency = parse_frequency(dev)
        self.channel = parse_channel(dev)
        self.manufacturer = parse_manufacturer(dev)
        self.type = parse_type(dev)
        self.name = parse_name(dev)
        self.commonname = parse_commonname(dev)
        self.phyname = parse_phyname(dev)
        self.encryption = parse_encryption(dev)
        
        # NO llamar vendor/provider - se harán en batch después
        self.vendor = None  # Se asignará después en batch
        self.provider = util.parse_provider(self.mac, self.ssid, self.__session)
        process_without_location = bool(int(os.getenv('PROCESS_WITHOUT_LOCATION', 1)))
        
        if self.location.lon != "0" and self.location.lat != "0":
            self.RSSI = self.__base.get('strongest_signal', 0)
            self.firstSeen = self.__base.get('first_time', 0)
        elif process_without_location:
            # Process devices without location data
            self.RSSI = self.__base.get('strongest_signal', 0)
            self.firstSeen = self.__base.get('first_time', 0)
        else:
            raise ValueError("Record does not have location info")

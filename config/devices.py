from dataclasses import dataclass

_IOS_USER_AGENT = "Mozilla/5.0 (iPhone; CPU iPhone OS 11_0 like Mac OS X) AppleWebKit/604.1.38 (KHTML, like Gecko) Version/11.0 Mobile/15A372 Safari/604.1"

@dataclass(frozen=True)
class DeviceProfile:
	
    """ profile for each device, used for emulation """
    name: str
    width: int = 393
    height: int = 851
    pixel_ratio: float = 2.75
    platform: str = "Android"
    user_agent: str | None = None  # set only when the user_agent cannot be inferred (for iOS devices)

    def as_dict(self) -> dict:
        """ return a dict representation of the device profile for use in Selenium mobile emulation 
        -> selenium.webdriver.chrome.options.Options.add_experimental_option("mobileEmulation", device_profile.as_dict())
        -> clientHints.platform NOT support iOS, so we need to set the userAgent for iOS devices, otherwise it will return invalid argument error
        """
        
        payload = {
            "deviceMetrics": {
                "width": self.width,
                "height": self.height,
                "pixelRatio": self.pixel_ratio,
            },
            "clientHints": {"platform": self.platform, "mobile": True},
        }
        if self.user_agent:
            payload["userAgent"] = self.user_agent
        return payload


DEVICES: dict[str, DeviceProfile] = {
    "Pixel 5": DeviceProfile("pixel_5", 393, 851, 2.75),
    "iPhone X": DeviceProfile("iphone_X", 390, 844, 3.0, platform="iOS", user_agent=_IOS_USER_AGENT),
}

DEFAULT_DEVICE = "Pixel 5"

def get_device_profile(device_name: str) -> DeviceProfile:
    try:
        return DEVICES[device_name]
    except KeyError:
        raise KeyError(f"Device '{device_name}' not found. Available devices: {list(DEVICES.keys())}")
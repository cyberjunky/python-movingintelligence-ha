# Python: Moving Intelligence

Home Assistant Python 3 API wrapper for Moving Intelligence asset and fleet management

## About

This package allows the Home Assistant integration 'moving_intelligence' to get get data from https://movingintelligence.com/en/.

NOTE: You need a login account together with an apikey to be able to use it.

## Installation

```bash
pip3 install pymovingintelligence_ha
```

## Example code

```python
#!/usr/bin/env python3

from pymovingintelligence_ha import MovingIntelligence
from pymovingintelligence_ha.utils import InvalidAuthError, InvalidPermissionsError
import asyncio
import logging

from aiohttp import ClientSession

logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.DEBUG)

async def async_main():
    api = MovingIntelligence(
        username="YOUR USERNAME",
        apikey="YOUR API-KEY"
    )
    try:
        devices = await api.get_devices()

        for device in devices:
            print(device.data)

    except InvalidPermissionsError:
        logger.error("No permission")
    except:
        logger.error("ConnectionError: Could not connect to MovingIntelligence")

asyncio.run(async_main())
```

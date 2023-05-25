import os
import requests
import json
import logging
from geopy.geocoders import Nominatim
from io import BytesIO

FORMAT = '%(asctime)s - [%(levelname)s] -  %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

GEO_API_KEY = "d6f6e475-5804-4aeb-af8a-076ce5fa06ca"


def get_map_by_coordinates(latitude: float, longitude: float):
    try:
        url = f"https://static-maps.yandex.ru/1.x/?ll={longitude},{latitude}&size=450,450&z=16&l=map"
        response = requests.get(url)
        image_bytes = BytesIO(response.content)
        return image_bytes
    except Exception as ex:
        logger.warning(ex)
        return None


def get_coordinates_by_address(address: str):
    with Nominatim(user_agent="EasyMeet") as geo_locator:
        try:
            location = geo_locator.geocode(address)
            return location.latitude, location.longitude
        except Exception as ex:
            logger.warning(ex)


def get_data_by_coordinates(departure: tuple, arrive: tuple, mode: str = "test"):
    if mode == "test":
        return 1319, 111287
    url = f'https://routing.api.2gis.com/get_dist_matrix?key={GEO_API_KEY}&version=2.0'
    headers = {'Content-type': 'application/json'}
    print(departure, arrive)
    data = {
        "points": [
            {
                "lat": departure[0],
                "lon": departure[1]
            },
            {
                "lat": arrive[0],
                "lon": arrive[1]
            }
        ],
        "sources": [0],
        "targets": [1],
        "type": 'jam',
        "mode": mode
    }
    print(data)
    request = requests.post(url, data=json.dumps(data), headers=headers)
    print(request)
    try:
        data = request.json()
        print(data)
        return data["routes"][0]["duration"], data["routes"][0]["distance"]
    except Exception as ex:
        logger.warning(ex)


def get_data_by_coordinates_public_transport(departure, arrive, start_time=None):
    url = f'https://routing.api.2gis.com/combo_routes/2.0?key={GEO_API_KEY}'
    headers = {'Content-type': 'application/json'}
    print(departure, arrive)
    data = {
        "locale": "ru",
        "source":
            {
                "name": "Point A",
                "point":
                    {
                        "lat": departure[0],
                        "lon": departure[1]
                    }
            },
        "target":
            {
                "name": "Point B",
                "point":
                    {
                        "lat": arrive[0],
                        "lon": arrive[1]
                    }
            },
        "transport": ["bus", "tram", "metro", "mcd", "mcc", "suburban_train", "aeroexpress"],
        # "start_time": start_time,
        # "enable_schedule": 'true'
    }
    print(data)
    request = requests.post(url, data=json.dumps(data), headers=headers)
    print(request)
    try:
        data = request.json()
        print(data)
        return data["routes"][0]["duration"], data["routes"][0]["distance"]
    except Exception as ex:
        logger.warning(ex)

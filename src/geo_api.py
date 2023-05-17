import os
import requests
import json
import logging
from geopy.geocoders import Nominatim
from io import BytesIO

FORMAT = '%(asctime)s - [%(levelname)s] -  %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

GEO_API_KEY = "ed7c0fbb-cd58-48b1-b23c-c44f91d321df"


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

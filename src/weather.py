import os
import requests
import logging

FORMAT = '%(asctime)s - [%(levelname)s] -  %(name)s - (%(filename)s).%(funcName)s(%(lineno)d) - %(message)s'
logging.basicConfig(format=FORMAT)
logger = logging.getLogger(__name__)

API_KEY = 'f362eec34c7a040a9b7c0d9e75e39f2b'


def get_weather_by_coordinates(coordinates):
    url = f"https://api.openweathermap.org/data/2.5/weather?" \
          f"lat={coordinates[0]}" \
          f"&lon={coordinates[1]}" \
          f"&appid={API_KEY}" \
          f"&units=metric" \
          f"&lang=ru"

    request = requests.get(url)
    if request.status_code != 200:
        logging.warning(request.status_code)
        logging.warning(request.text)
        return
    weather = request.json()
    result = f"Температура: {weather['main']['temp']}°C\n" \
             f"Ощущается как: {weather['main']['feels_like']}°C\n" \
             f"Вероятность осадков: {weather['main']['humidity']}%\n" \
             f"Давление: {weather['main']['pressure']}мм рт. ст.\n" \
             f"Скорость ветра: {weather['wind']['speed']}м/с\n" \
             f"На небе {weather['weather'][0]['description']}"
    return result

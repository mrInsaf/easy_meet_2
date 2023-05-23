from db_real import *
import aiogram_calendar
import requests

from weather import API_KEY

url = f"api.openweathermap.org/data/2.5/forecast?lat=44.34&lon=10.99&appid={API_KEY}"


request = requests.get(url)

weather = request.json()
print(weather)
# result = f"Температура: {weather['main']['temp']}°C\n" \
#          f"Ощущается как: {weather['main']['feels_like']}°C\n" \
#          f"Вероятность осадков: {weather['main']['humidity']}%\n" \
#          f"Давление: {weather['main']['pressure']}мм рт. ст.\n" \
#          f"Скорость ветра: {weather['wind']['speed']}м/с\n" \
#          f"На небе {weather['weather'][0]['description']}"
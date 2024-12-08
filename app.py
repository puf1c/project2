import requests

API_KEY = "zUbkkMW5KuUukUeAnMei0UyJIyy45eOD"

LATITUDE = "55.7558"
LONGITUDE = "37.6173"

def get_weather_parameters(api_key: str, lat: str, lon: str):
    weather_dict = {}
    try:
        # Получение ключа локации
        location_url = f"http://dataservice.accuweather.com/locations/v1/cities/geoposition/search"
        location_params = {
            "apikey": api_key,
            "q": f"{lat},{lon}"
        }

        location_response = requests.get(location_url, params=location_params)
        location_response.raise_for_status()  # Проверка на ошибки HTTP

        location_data = location_response.json()
        location_key = location_data["Key"]

        try:
            # Получение данных о погоде
            weather_url = f"http://dataservice.accuweather.com/currentconditions/v1/{location_key}"
            weather_params = {
                "apikey": api_key,
                "details": "true"
            }

            weather_response = requests.get(weather_url, params=weather_params)
            weather_response.raise_for_status()  # Проверка на ошибки HTTP

            weather_data = weather_response.json()[0]

            temperature = weather_data["Temperature"]["Metric"]["Value"]  # Температура в °C
            humidity = weather_data["RelativeHumidity"]  # Влажность в %
            wind_speed = weather_data["Wind"]["Speed"]["Metric"]["Value"]  # Скорость ветра в м/с
            rain_probability = weather_data.get("PrecipitationProbability", 0)  # Вероятность дождя в %

            weather_dict['temperature'] = temperature
            weather_dict['humidity'] = humidity
            weather_dict['wind_speed'] = wind_speed
            weather_dict['rain_probability'] = rain_probability

            return weather_dict

        except requests.exceptions.RequestException as e:
            print(f"Ошибка при запросе данных о погоде: {e}")
        except KeyError as e:
            print(f"Ошибка при обработке данных о погоде: {e}")

    except requests.exceptions.RequestException as e:
        print(f"Ошибка при запросе ключа локации: {e}")
    except KeyError as e:
        print(f"Ошибка при обработке данных локации: {e}")

def main():
    get_weather_parameters(API_KEY, LATITUDE, LONGITUDE)

    '''print(f"Температура: {temperature} °C")
    print(f"Влажность: {humidity} %")
    print(f"Скорость ветра: {wind_speed} м/с")
    print(f"Вероятность дождя: {rain_probability} %")'''

if __name__ == '__main__':
    main()
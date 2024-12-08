from weather_analyze import get_weather_parameters, check_bad_weather, get_location_key_by_name
from flask import Flask, request, render_template

API_KEY = "zUbkkMW5KuUukUeAnMei0UyJIyy45eOD"

LATITUDE = "55.7558"
LONGITUDE = "37.6173"

app = Flask(__name__)

# Главная страница с формой
@app.route('/')
def home():
    return render_template('form.html')

# Обработка данных формы
@app.route('/submit-route', methods=['POST'])
def submit_route():
    start_name = request.form.get('start')
    end_name = request.form.get('end')

    start_location_key = get_location_key_by_name(api_key=API_KEY, city_name=start_name)
    end_location_key = get_location_key_by_name(api_key=API_KEY, city_name=end_name)

    start_weather = get_weather_parameters(api_key=API_KEY, location_key=start_location_key)
    end_weather = get_weather_parameters(api_key=API_KEY, location_key=end_location_key)

    check_start_weather = check_bad_weather(start_weather)
    check_end_weather = check_bad_weather(end_weather)

    if check_start_weather == 'good' and check_end_weather == 'good':
        return 'В обеих точках приятная погода!'
    elif check_start_weather == 'bad' and check_end_weather == 'good':
        return f'В {start_name} сейчас погода не очень (('
    elif check_start_weather == 'good' and check_end_weather == 'bad':
        return f'В {end_name} сейчас погода не очень (('
    else:
        return 'В обеих точках ужасная погода!'

if __name__ == '__main__':
    app.run(debug=True)


from weather_analyze import get_weather_parameters, check_bad_weather, get_location_key_by_name,
from flask import Flask, request, render_template
from flask import Flask, render_template, request, redirect
import plotly.express as px
import pandas as pd
import dash
from dash import dcc, html

API_KEY = "nnYAI8k1VksWAqzZOQEebcG1eJ6Q1Nw0"

weather_data = {}
weather_comment = ""

app = Flask(__name__)

# Главная страница с формой
@app.route('/')
def home():
    return render_template('form.html')

# Обработка данных формы
@app.route('/submit-route', methods=['POST'])
def submit_route():
    try:
        start_name = request.form.get('start')
        end_name = request.form.get('end')

        start_location_key = get_location_key_by_name(api_key=API_KEY, city_name=start_name)
        end_location_key = get_location_key_by_name(api_key=API_KEY, city_name=end_name)

        if not start_location_key or not end_location_key:
            return 'Не удалось найти местоположение для указанных городов.'

        start_weather = get_weather_parameters(api_key=API_KEY, location_key=start_location_key)
        end_weather = get_weather_parameters(api_key=API_KEY, location_key=end_location_key)

        if not start_weather or not end_weather:
            return 'Не удалось получить данные о погоде для указанных городов.'

        global weather_data
        weather_data = {
            "start_city": start_name,
            "end_city": end_name,
            "start_weather": start_weather,
            "end_weather": end_weather
        }

        check_start_weather = check_bad_weather(start_weather)
        check_end_weather = check_bad_weather(end_weather)

        global weather_comment
        if check_start_weather == 'good' and check_end_weather == 'good':
            weather_comment = 'В обеих точках приятная погода!'
        elif check_start_weather == 'bad' and check_end_weather == 'good':
            weather_comment = f'В {start_name} сейчас погода не очень (('
        elif check_start_weather == 'good' and check_end_weather == 'bad':
            weather_comment = f'В {end_name} сейчас погода не очень (('
        else:
            weather_comment = 'В обеих точках ужасная погода!'

        return redirect('/weather-comparison')

    except Exception as e:
        return f'Произошла ошибка {e} при обработке данных.'

dash_app = dash.Dash(__name__, server=app, url_base_pathname='/weather-comparison/')

dash_app.layout = html.Div([
    html.H1("Сравнение погодных условий"),
    dcc.Graph(id='weather-histogram'),
    html.Div(id='weather-comment', style={'font-size': '20px', 'margin-top': '20px'}),
    html.A("Вернуться на главную", href="/", style={'display': 'block', 'margin-top': '20px'})
])

@dash_app.callback(
    dash.dependencies.Output('weather-histogram', 'figure'),
    dash.dependencies.Input('weather-histogram', 'id')
)
def update_histogram(_):
    if not weather_data:
        return px.bar()

    start_city = weather_data["start_city"]
    end_city = weather_data["end_city"]
    start_weather = weather_data["start_weather"]
    end_weather = weather_data["end_weather"]

    categories = ["Temperature", "Humidity", "Wind Speed", "Rain_probability"]
    start_values = [
        start_weather["temperature"],
        start_weather["humidity"],
        start_weather["wind_speed"],
        start_weather["rain_probability"]
    ]
    end_values = [
        end_weather["temperature"],
        end_weather["humidity"],
        end_weather["wind_speed"],
        end_weather["rain_probability"]
    ]

    data = pd.DataFrame({
        "Category": categories * 2,
        "Value": start_values + end_values,
        "City": [start_city] * 4 + [end_city] * 4
    })

    fig = px.bar(
        data,
        x="Category",
        y="Value",
        color="City",
        barmode="group",
        title="Сравнение погодных условий"
    )

    fig.update_layout(
        xaxis_title="Показатели",
        yaxis_title="Значения",
        legend_title="Города"
    )

    return fig


if __name__ == '__main__':
    app.run(debug=True)



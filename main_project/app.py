from weather_analyze import get_weather_parameters, check_bad_weather, get_location_key_by_name, get_weather_forecast, get_coordinates
from flask import Flask, render_template, request, redirect
from dash import Dash, dcc, html, Input, Output, callback_context, ALL, ctx
import dash_leaflet
import plotly.graph_objs as go

# ОБЯЗАТЕЛЬНО К ЗАПОЛНЕНИЮ
API_KEY = "ваш ключ для accuweather"

# глобальные переменные для хранения списка точек и погодных данных
cities = []
weather_data = {}

app = Flask(__name__)

# форма для ввода точек маршрута
@app.route('/')
def home():
    return render_template('form.html')

# обработка формы
@app.route('/submit-route', methods=['POST'])
def submit_route():
    try:
        start_name = request.form.get('start').strip()
        waypoints = [city.strip() for city in request.form.getlist('waypoints') if city.strip()]
        end_name = request.form.get('end').strip()

        # сохранение точек маршрута
        global cities, weather_data
        cities = [start_name] + waypoints + [end_name]
        weather_data = {}

        # получение прогноза погоды для каждой точки на 5 дней(берем максимальное число, потом обрежем по необходимости до нужного кол-ва дней)
        for city in cities:
            try:
                location_key = get_location_key_by_name(api_key=API_KEY, city_name=city)
                if not location_key:
                    return f"Не удалось найти местоположение для {city}."

                forecast = get_weather_forecast(api_key=API_KEY, location_key=location_key, days=5)
                if not forecast:
                    return f"Не удалось получить прогноз для {city}."

                weather_data[city] = forecast
            except Exception as e:
                return f"Ошибка обработки города {city}: {e}"

        return redirect('/weather-comparison')

    except Exception as e:
        return f'Произошла ошибка: {e}'


dash_app = Dash(__name__, server=app, url_base_pathname='/weather-comparison/')

# основной макет приложения Dash
dash_app.layout = html.Div([
    html.H1("Карта маршрута", style={'textAlign': 'center', 'color': '#000', 'marginBottom': '20px'}),
    html.P(
        "Чтобы поменять город, нажмите на иконку на карте.",
        style={'textAlign': 'center', 'color': '#000', 'marginBottom': '20px'}
    ),

    # Блок с картой маршрута и графиком
    html.Div([
        dash_leaflet.Map(center=[50, 50], zoom=4, children=[
            # добавление слоев для карты, маркеров и линии маршрута
            dash_leaflet.TileLayer(),
            dash_leaflet.LayerGroup(id="markers-layer"),
            dash_leaflet.Polyline(
                id="route-line", positions=[], color="#C71585", weight=4
            )
        ], id="map", style={'width': '50vw', 'height': '50vh', 'margin': '0 auto', 'marginBottom': '20px'}),
        # контейнер для графика (обновляется через callback)
        html.Div(id='weather-graph-container', style={
            'width': '50vw',
            'height': '50vh',
            'margin': '0 auto',
            'textAlign': 'center',
            'marginBottom': '20px'
        })
    ], style={'display': 'flex', 'flexDirection': 'column', 'alignItems': 'center'}),
    # блок выбора параметров через выпадающие списки
    html.Div([
        dcc.Dropdown(
            id='metric-dropdown',
            options=[
                {'label': 'Скорость ветра', 'value': 'windspeed'},
                {'label': 'Осадки', 'value': 'precipitation_sum'},
                {'label': 'Максимальная температура', 'value': 'max_temperature'},
                {'label': 'Минимальная температура', 'value': 'min_temperature'}
            ],
            clearable=False,
            style={'width': '50%', 'margin': '0 auto', 'marginBottom': '10px'}
        ),
        dcc.Dropdown(
            id='days-dropdown',
            options=[
                {'label': '3 дня', 'value': 3},
                {'label': '5 дней', 'value': 5}
            ],
            value=3,
            clearable=False,
            style={'width': '50%', 'margin': '0 auto', 'marginBottom': '20px'}
        )
    ], style={'width': '100%', 'marginTop': '10px', 'marginBottom': '20px'}),
    # возврат на главную
    html.Div([
        html.A("Назад", href="/", style={
            'display': 'inline-block',
            'padding': '10px 20px'
        })
    ], style={'textAlign': 'center', 'marginBottom': '20px'})
], style={'minHeight': '100vh', 'padding': '20px'})

# обновление маркеров и маршрута на карте
@dash_app.callback(
    [Output("markers-layer", "children"), Output("route-line", "positions")],
    Input('map', 'id')
)
def add_route_and_markers(_):
    markers = []
    route_positions = []

    for city in cities:
        try:
            coordinates = get_coordinates(city)

            if coordinates:
                route_positions.append(coordinates)
                marker = dash_leaflet.Marker(position=coordinates, children=[
                    dash_leaflet.Tooltip(city),
                    dash_leaflet.Popup([html.H3(city, style={'textAlign': 'center'}), html.P("")])
                ], id={'type': 'marker', 'index': city}, icon={
                    "iconUrl": "https://www.flaticon.com/free-icon/location-pin_3179068?term=location&page=1&position=4&origin=tag&related_id=3179068",
                    "iconSize": [25, 41],
                    "iconAnchor": [12, 41],
                    "popupAnchor": [1, -34]
                })
                markers.append(marker)
        except Exception as e:
            print(f"Ошибка с городом {city}: {e}")
    return markers, route_positions

# обновление графиков
@dash_app.callback(
    Output("weather-graph-container", "children"),
    [Input("metric-dropdown", "value"), Input("days-dropdown", "value")],
    Input({'type': 'marker', 'index': ALL}, 'n_clicks')
)
def update_graph(selected_metric, days, _):
    print(f"Triggered: {ctx.triggered_id}, Metric: {selected_metric}, Days: {days}")

    city_name = cities[0] if cities else None
    if ctx.triggered_id and isinstance(ctx.triggered_id, dict):
        city_name = ctx.triggered_id["index"]

    if city_name in weather_data:
        forecast = weather_data[city_name]
        try:
            dates = [day['date'] for day in forecast[:days]]
            values = [day[selected_metric] for day in forecast[:days]]

            print(f"Dates: {dates}, Values: {values}")

            fig = go.Figure()
            fig.add_trace(
                go.Scatter(x=dates, y=values, mode='lines+markers', name=selected_metric,
                           line=dict(color='green'))
            )
            fig.update_layout(
                title=f'{selected_metric} в {city_name} за {days} дней',
                xaxis_title='Дата',
                yaxis_title='Значение',
                template='plotly_white'
            )
            return dcc.Graph(figure=fig)
        except KeyError as e:
            return html.Div(f"Ошибка данных: {e}")

    return html.Div("Нет данных для отображения")

# запуск программы
if __name__ == '__main__':
    app.run(debug=True)



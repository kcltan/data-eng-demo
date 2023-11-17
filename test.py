import streamlit as st
import pandas as pd
import requests
import json
from plotly.subplots import make_subplots
import plotly.graph_objs as go
from datetime import datetime
from datetime import timezone as tmz
import pytz
from tzwhere import tzwhere
import folium
from streamlit_folium import folium_static
import yfinance as yf

tab1, tab2, tab3 = st.tabs(["News", "Weather","Stocks"])

NEWS_API_ENDPOINT = 'https://newsapi.org/v2/top-headlines'
with tab1:
    
    def fetch_news(country, category=None):
        params = {
            'country': country,
            'apiKey': st.secrets["NEWS_API_KEY"]
        }
        if category:
            params['category'] = category
        response = requests.get(NEWS_API_ENDPOINT, params=params)
        return response.json()

    st.title('News Aggregator')
  
    categories = ['All','Business', 'Entertainment', 'General', 'Health', 'Science', 'Sports', 'Technology']
    selected_category = st.selectbox('Select a category (optional)', categories)

    # Fetch the news
    if selected_category == 'All':
        news = fetch_news('GB')
    else:
        news = fetch_news('GB', category=selected_category)

    # Display the news articles
    for article in news['articles']:
        st.write(f"### [{article['title']}]({article['url']})")

with tab2:
    # Title and description for your app
    st.title("How's the weather? :sun_behind_rain_cloud:")

    st.subheader("Choose location")

    file = "worldcities.csv"
    data = pd.read_csv(file)


    country_set = set(data.loc[:,"country"])
    
    country_data = data.loc[data.loc[:,"country"] == 'United Kingdom',:]


    city_set = country_data.loc[:,"city_ascii"] 
    

    lat = float(country_data.loc[data.loc[:,"city_ascii"] == 'London', "lat"])
    lng = float(country_data.loc[data.loc[:,"city_ascii"] == 'London', "lng"])

    response_current = requests.get(f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&current_weather=true')

    st.subheader("Current weather")

    result_current = json.loads(response_current._content)

    current = result_current["current_weather"]
    temp = current["temperature"]
    speed = current["windspeed"]
    direction = current["winddirection"]

    # Increment added or substracted from degree values for wind direction
    ddeg = 11.25

    # Determine wind direction based on received degrees
    if direction >= (360-ddeg) or direction < (0+ddeg):
        common_dir = "N"
    elif direction >= (337.5-ddeg) and direction < (337.5+ddeg):
        common_dir = "N/NW"
    elif direction >= (315-ddeg) and direction < (315+ddeg):
        common_dir = "NW"
    elif direction >= (292.5-ddeg) and direction < (292.5+ddeg):
        common_dir = "W/NW"
    elif direction >= (270-ddeg) and direction < (270+ddeg):
        common_dir = "W"
    elif direction >= (247.5-ddeg) and direction < (247.5+ddeg):
        common_dir = "W/SW"
    elif direction >= (225-ddeg) and direction < (225+ddeg):
        common_dir = "SW"
    elif direction >= (202.5-ddeg) and direction < (202.5+ddeg):
        common_dir = "S/SW"
    elif direction >= (180-ddeg) and direction < (180+ddeg):
        common_dir = "S"
    elif direction >= (157.5-ddeg) and direction < (157.5+ddeg):
        common_dir = "S/SE"
    elif direction >= (135-ddeg) and direction < (135+ddeg):
        common_dir = "SE"
    elif direction >= (112.5-ddeg) and direction < (112.5+ddeg):
        common_dir = "E/SE"
    elif direction >= (90-ddeg) and direction < (90+ddeg):
        common_dir = "E"
    elif direction >= (67.5-ddeg) and direction < (67.5+ddeg):
        common_dir = "E/NE"
    elif direction >= (45-ddeg) and direction < (45+ddeg):
        common_dir = "NE"
    elif direction >= (22.5-ddeg) and direction < (22.5+ddeg):
        common_dir = "N/NE"


    st.info(f"The current temperature is {temp} °C. \n The wind speed is {speed} m/s. \n The wind is coming from {common_dir}.")

    st.subheader("Week ahead")

    st.write('Temperature and rain forecast one week ahead & city location on the map', unsafe_allow_html=True)

    with st.spinner('Loading...'):
        response_hourly = requests.get(f'https://api.open-meteo.com/v1/forecast?latitude={lat}&longitude={lng}&hourly=temperature_2m,precipitation')
        result_hourly = json.loads(response_hourly._content)
        hourly = result_hourly["hourly"]
        hourly_df = pd.DataFrame.from_dict(hourly)
        hourly_df.rename(columns = {'time':'Week ahead'}, inplace = True)
        hourly_df.rename(columns = {'temperature_2m':'Temperature °C'}, inplace = True)
        hourly_df.rename(columns = {'precipitation':'Precipitation mm'}, inplace = True)
        
        tz = tzwhere.tzwhere(forceTZ=True)
        timezone_str = tz.tzNameAt(lat, lng, forceTZ=True) # Seville coordinates
        
        timezone_loc = pytz.timezone(timezone_str)
        dt = datetime.now()
        tzoffset = timezone_loc.utcoffset(dt)#-timedelta(hours=1,minutes=0)
        
        
        # Create figure with secondary y axis
        fig = make_subplots(specs=[[{"secondary_y":True}]])
        
        
        week_ahead = pd.to_datetime(hourly_df['Week ahead'],format="%Y-%m-%dT%H:%M")
        
        # Add traces
        fig.add_trace(go.Scatter(x = week_ahead+tzoffset, 
                                y = hourly_df['Temperature °C'],
                                name = "Temperature °C"),
                    secondary_y = False,)
        
        fig.add_trace(go.Bar(x = week_ahead+tzoffset, 
                            y = hourly_df['Precipitation mm'],
                            name = "Precipitation mm"),
                    secondary_y = True,)
        
        time_now = datetime.now(tmz.utc)+tzoffset
        
        fig.add_vline(x = time_now, line_color="red", opacity=0.4)
        fig.add_annotation(x = time_now, y=max(hourly_df['Temperature °C'])+5,
                    text = time_now.strftime("%d %b %y, %H:%M"),
                    showarrow=False,
                    yshift=0)
        
        fig.update_yaxes(range=[min(hourly_df['Temperature °C'])-10,
                                max(hourly_df['Temperature °C'])+10],
                        title_text="Temperature °C",
                        secondary_y=False,
                        showgrid=False,
                        zeroline=False)
            
        fig.update_yaxes(range=[min(hourly_df['Precipitation mm'])-2,
                                max(hourly_df['Precipitation mm'])+8], 
                        title_text="Precipitation (rain/showers/snow) mm",
                        secondary_y=True,
                        showgrid=False)
        
        
        fig.update_layout(legend=dict(
            orientation="h",
            yanchor="bottom",
            y=1.02,
            xanchor="right",
            x=0.7
        ))
        
        # center on Liberty Bell, add marker
        m = folium.Map(location=[lat, lng], zoom_start=7)
        folium.Marker([lat, lng], 
                popup='London'+', '+'United Kingdom', 
                tooltip='London'+', '+'United Kingdom').add_to(m)
        
        # call to render Folium map in Streamlit
        
        # Make folium map responsive to adapt to smaller display size (
        # e.g., on smartphones and tablets)
        make_map_responsive= """
        <style>
        [title~="st.iframe"] { width: 100%}
        </style>
        """
        st.markdown(make_map_responsive, unsafe_allow_html=True)
        
        # Display chart
        st.plotly_chart(fig, use_container_width=True)
        
        # Display map
        st_data = folium_static(m, height = 370)
        
with tab3:
    # set the list of stock tickers to track
    tickers = ['AAPL', 'MSFT', 'AMZN', 'GOOGL']

    # get the daily performance of the stocks using the Yahoo Finance API
    stock_data = yf.download(tickers, period='2d')['Close']

    # create a Streamlit app
    st.title('Stocks Daily Performance')
    st.write('Daily performance of the selected stocks')

    # create a widget for each stock
    for ticker in tickers:
        # get the stock data for the current ticker
        data = stock_data[ticker]
        st.write(f'**{ticker}**')
        # create two columns for the stock values
        col1, col2, col3 = st.columns(3)

        # show the current value of the stock
        with col1:
            st.metric(label='Current value', value=f'{data.iloc[-1]:.2f}')
        
        # show the previous day's closing value of the stock
        with col2:
            st.metric(label='Previous day\'s closing value', value=f'{data.iloc[-2]:.2f}')
        
        # show the percentage change in the stock value
        change = (data.iloc[-1] - data.iloc[-2]) / data.iloc[-2] * 100
        with col3:
            if change >= 0:
                st.metric(label='Percentage change', value=f'{change:.2f}%' + ' 🟢')
            else:
                st.metric(label='Percentage change', value=f'{change:.2f}%' + ' 🔴')

        
        # add a separator between the stocks
        st.write('---')
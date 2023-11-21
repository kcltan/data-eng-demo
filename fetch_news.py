import requests
import streamlit as st

NEWS_API_ENDPOINT = "https://newsapi.org/v2/top-headlines"

def fetch_news(country, category=None):
    params = {
        'country': country,
        'apiKey': st.secrets["3e006bcd93584008af6febdd950ee322"]
    }
    if category:
        params['category'] = category
    response = requests.get(NEWS_API_ENDPOINT, params=params)
    return response.json()
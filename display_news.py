import streamlit as st
from fetch_news import fetch_news

st.title('News Aggregator 📰')

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
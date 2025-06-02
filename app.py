import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="המלצות מניות", layout="wide")

@st.cache_data
def load_sp500_tickers():
    url = "https://raw.githubusercontent.com/josericodata/SP500Forecaster/main/assets/data/sp500_tickers.csv"
    return pd.read_csv(url)['Symbol'].tolist()

def analyze_stock(ticker):
    data = yf.download(ticker, period="1y")
    data['MA50'] = data['Close'].rolling(50).mean()
    data['MA200'] = data['Close'].rolling(200).mean()
    return data

st.title("מערכת המלצות למניות S&P 500 🇮🇱")
selected_ticker = st.selectbox("בחר מנייה:", load_sp500_tickers())

if selected_ticker:
    st.subheader(f"ניתוח טכני עבור {selected_ticker}")
    data = analyze_stock(selected_ticker)
    st.line_chart(data[['Close', 'MA50', 'MA200']])
    
    current_price = data['Close'][-1]
    ma50 = data['MA50'][-1]
    
    if current_price > ma50:
        st.success("המלצה: קנייה (מחיר מעל ממוצע 50 יום)")
    else:
        st.error("המלצה: מכירה (מחיר מתחת לממוצע 50 יום)")
    
    st.write("נתונים אחרונים:")
    st.dataframe(data.tail(10))

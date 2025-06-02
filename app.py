import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="המלצות מניות", layout="wide")

@st.cache_data
def load_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    tables = pd.read_html(url)
    df = tables[0]
    return df['Symbol'].str.replace('.', '-').tolist()  # תיקון לטיקרים עם נקודות

def analyze_stock(ticker):
    try:
        data = yf.download(ticker, period="1y")
        if data.empty:
            return None
        
        # שטיחת עמודות MultiIndex (אם קיים)
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.map('_'.join).str.strip('_')
        
        # יצירת עמודות סטנדרטיות
        close_col = f'Close_{ticker}'  # שם עמודה לאחר שטיחה
        if close_col not in data.columns:
            return None
        
        data['Close'] = data[close_col]  # עמודה סטנדרטית
        data['MA50'] = data['Close'].rolling(50, min_periods=1).mean()
        data['MA200'] = data['Close'].rolling(200, min_periods=1).mean()
        
        return data[['Close', 'MA50', 'MA200']]  # החזרת עמודות סטנדרטיות בלבד
    except Exception as e:
        st.error(f"שגיאה בטעינת נתונים עבור {ticker}: {e}")
        return None

st.title("מערכת המלצות למניות S&P 500 🇮🇱")
tickers = load_sp500_tickers()

if not tickers:
    st.stop()

selected_ticker = st.selectbox("בחר מנייה:", tickers)

if selected_ticker:
    st.subheader(f"ניתוח טכני עבור {selected_ticker}")
    data = analyze_stock(selected_ticker)
    
    if data is None:
        st.warning("לא נמצאו נתונים עבור מניה זו.")
    else:
        st.line_chart(data[['Close', 'MA50', 'MA200']])
        current_price = data['Close'].iloc[-1]
        ma50 = data['MA50'].iloc[-1]
        
        if current_price > ma50:
            st.success("המלצה: קנייה (מחיר מעל ממוצע 50 יום)")
        else:
            st.error("המלצה: מכירה (מחיר מתחת לממוצע 50 יום)")
        
        st.write("נתונים אחרונים:")
        st.dataframe(data.tail(10))

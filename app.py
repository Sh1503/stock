# app.py
import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="המלצות מניות", layout="wide")

@st.cache_data
def load_sp500_tickers():
    try:
        # טען טיקרים מוויקיפדיה עם lxml
        url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
        tables = pd.read_html(url, flavor='lxml')
        df = tables[0]
        # החלף . ל- עבור טיקרים כמו BF.B -> BF-B
        return df['Symbol'].str.replace('.', '-').tolist()
    except Exception as e:
        st.error(f"שגיאה בטעינת רשימת המניות: {e}")
        return []

def analyze_stock(ticker):
    try:
        data = yf.download(ticker, period="1y")
        if data.empty:
            return None
        
        # שטיחת עמודות מרובות רמות
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.map('_'.join)
        
        # בדיקת עמודת Close
        close_col = f'Close_{ticker}' if f'Close_{ticker}' in data.columns else 'Close'
        if close_col not in data.columns:
            return None
        
        # חישוב ממוצעים
        data['MA50'] = data[close_col].rolling(50, min_periods=1).mean()
        data['MA200'] = data[close_col].rolling(200, min_periods=1).mean()
        
        # שינוי שם לעמודה אחידה
        data.rename(columns={close_col: 'Close'}, inplace=True)
        
        return data[['Close', 'MA50', 'MA200']]
    except Exception as e:
        st.error(f"שגיאה בעיבוד {ticker}: {str(e)}")
        return None

st.title("📈 מערכת המלצות למניות S&P 500")
tickers = load_sp500_tickers()

if not tickers:
    st.stop()

selected_ticker = st.selectbox("בחר מנייה:", tickers)

if selected_ticker:
    data = analyze_stock(selected_ticker)
    
    if data is None:
        st.warning("⚠️ לא נמצאו נתונים עבור מניה זו")
    else:
        st.subheader(f"ניתוח טכני עבור {selected_ticker}")
        st.line_chart(data)
        
        current_price = data['Close'].iloc[-1]
        ma50 = data['MA50'].iloc[-1]
        
        recommendation = "קנייה 🟢" if current_price > ma50 else "מכירה 🔴"
        st.markdown(f"**המלצה:** {recommendation} (מחיר נוכחי: ${current_price:.2f}, ממוצע 50 יום: ${ma50:.2f})")
        
        with st.expander("הצג נתונים היסטוריים"):
            st.dataframe(data.tail(10))

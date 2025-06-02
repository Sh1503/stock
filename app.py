import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="המלצות מניות", layout="wide")

@st.cache_data
def load_sp500_tickers():
    # טען את הטיקרים מוויקיפדיה
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    tables = pd.read_html(url)
    df = tables[0]
    tickers = df['Symbol'].tolist()
    # החלף נקודות במקף (כמו ש-yfinance דורש)
    tickers = [t.replace('.', '-') for t in tickers]
    return tickers

def analyze_stock(ticker):
    try:
        data = yf.download(ticker, period="1y")
        if data.empty:
            return None
        data['MA50'] = data['Close'].rolling(50, min_periods=1).mean()
        data['MA200'] = data['Close'].rolling(200, min_periods=1).mean()
        return data
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
        required_cols = ['Close', 'MA50', 'MA200']
        missing_cols = [col for col in required_cols if col not in data.columns]
        if missing_cols:
            st.error(f"חסרות עמודות: {', '.join(missing_cols)}")
            st.write("עמודות זמינות:", data.columns.tolist())
        else:
            st.line_chart(data[required_cols])
            current_price = data['Close'].iloc[-1]
            ma50 = data['MA50'].iloc[-1]
            if pd.isna(current_price) or pd.isna(ma50):
                st.warning("לא ניתן לחשב המלצה עקב נתונים חסרים.")
            elif current_price > ma50:
                st.success("המלצה: קנייה (מחיר מעל ממוצע 50 יום)")
            else:
                st.error("המלצה: מכירה (מחיר מתחת לממוצע 50 יום)")
            st.write("נתונים אחרונים:")
            st.dataframe(data.tail(10))

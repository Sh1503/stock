import streamlit as st
import yfinance as yf
import pandas as pd

st.set_page_config(page_title="המלצות מניות", layout="wide")

@st.cache_data
def load_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    tables = pd.read_html(url, flavor='lxml')
    df = tables[0]
    return df['Symbol'].str.replace('.', '-').tolist()

def analyze_stock(ticker):
    try:
        data = yf.download(ticker, period="1y")
        if data.empty:
            return None
        if isinstance(data.columns, pd.MultiIndex):
            data.columns = data.columns.map('_'.join)
        close_col = f'Close_{ticker}' if f'Close_{ticker}' in data.columns else 'Close'
        if close_col not in data.columns:
            return None
        data['MA50'] = data[close_col].rolling(50, min_periods=1).mean()
        data['MA200'] = data[close_col].rolling(200, min_periods=1).mean()
        data.rename(columns={close_col: 'Close'}, inplace=True)
        return data[['Close', 'MA50', 'MA200']]
    except Exception:
        return None

def is_pre_breakout(data):
    if data is None or data.shape[0] < 200:
        return False
    high_30d = data['Close'].tail(30).max()
    close = data['Close'].iloc[-1]
    ma50 = data['MA50'].iloc[-1]
    ma200 = data['MA200'].iloc[-1]
    return (
        close >= high_30d * 0.97 and
        ma50 > ma200
    )

def get_pre_breakout_stocks(tickers, n=5):
    breakout_candidates = []
    for ticker in tickers:
        data = analyze_stock(ticker)
        if is_pre_breakout(data):
            high_30d = data['Close'].tail(30).max()
            close = data['Close'].iloc[-1]
            distance = high_30d - close
            breakout_candidates.append({'Ticker': ticker, 'Price': close, '30d High': high_30d, 'Distance to High': distance})
        if len(breakout_candidates) >= 20:
            break
    df = pd.DataFrame(breakout_candidates)
    if not df.empty:
        df = df.sort_values('Distance to High').head(n)
    return df

@st.cache_data
def get_top_recommendations(tickers, n=5):
    results = []
    for ticker in tickers:
        data = analyze_stock(ticker)
        if data is None or data.isnull().values.any():
            continue
        current = data['Close'].iloc[-1]
        ma50 = data['MA50'].iloc[-1]
        ma200 = data['MA200'].iloc[-1]
        if current > ma50 and current > ma200:
            score = (current - ma50) + (current - ma200)
            results.append({'Ticker': ticker, 'Price': current, 'MA50': ma50, 'MA200': ma200, 'Score': score})
        if len(results) >= 20:
            break
    df = pd.DataFrame(results)
    if not df.empty:
        df = df.sort_values('Score', ascending=False).head(n)
    return df

st.title("📈 מערכת המלצות למניות S&P 500")

tickers = load_sp500_tickers()
if not tickers:
    st.stop()

# טבלת חמשת המומלצות של היום
with st.expander("🔥 חמשת המומלצות של היום"):
    st.info("הטבלה מתעדכנת אוטומטית לפי נתוני יום המסחר האחרון (קריטריון: מחיר מעל MA50 ו-MA200)")
    top_df = get_top_recommendations(tickers, n=5)
    if top_df is not None and not top_df.empty:
        st.table(top_df[['Ticker', 'Price', 'MA50', 'MA200']].set_index('Ticker'))
    else:
        st.warning("לא נמצאו מניות מומלצות היום לפי הקריטריונים.")

# טבלת חמשת ה־Pre Breakout
with st.expander("🚀 מניות קרובות לפריצה (Pre-Breakout)"):
    st.info("הטבלה מציגה מניות שמתקרבות ל-High של 30 יום, עם מגמת עלייה")
    breakout_df = get_pre_breakout_stocks(tickers, n=5)
    if breakout_df is not None and not breakout_df.empty:
        st.table(breakout_df.set_index('Ticker'))
    else:
        st.warning("לא נמצאו מניות מתאימות.")

# ניתוח מניה בודדת
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

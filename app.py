import streamlit as st
import yfinance as yf
import pandas as pd
from ta.momentum import RSIIndicator
from ta.volume import OnBalanceVolumeIndicator

st.set_page_config(page_title="מערכת ניתוח מניות", layout="wide", page_icon="💹")

# ------ פונקציות עזר ------
@st.cache_data
def load_sp500_tickers():
    url = 'https://en.wikipedia.org/wiki/List_of_S%26P_500_companies'
    tables = pd.read_html(url, flavor='lxml')
    df = tables[0]
    return df['Symbol'].str.replace('.', '-').tolist()

def analyze_stock(ticker):
    try:
        data = yf.download(ticker, period="6mo", progress=False)
        if data.empty or len(data) < 50:
            return None

        # חישוב ממוצעים נעים
        data['MA20'] = data['Close'].rolling(20).mean()
        data['MA50'] = data['Close'].rolling(50).mean()
        # חישוב RSI
        data['RSI'] = RSIIndicator(data['Close'], window=14).rsi()
        # חישוב OBV
        data['OBV'] = OnBalanceVolumeIndicator(data['Close'], data['Volume']).on_balance_volume()
        # שיא 3 חודשים
        data['3m_high'] = data['High'].rolling(63).max()
        distance_from_high = (data['3m_high'] - data['Close']) / data['3m_high']
        volume_spike = data['Volume'].iloc[-1] > 1.5 * data['Volume'].rolling(20).mean().iloc[-1]
        obv_trend = data['OBV'].iloc[-5:].pct_change().mean() > 0

        return {
            'data': data,
            'distance_from_high': distance_from_high.iloc[-1],
            'volume_spike': volume_spike,
            'rsi': data['RSI'].iloc[-1],
            'obv_trend': obv_trend
        }
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return None

@st.cache_data
def get_breakout_candidates(_tickers, max_stocks=100):
    candidates = []
    for ticker in _tickers[:max_stocks]:
        analysis = analyze_stock(ticker)
        if not analysis:
            continue
        
        if (analysis['distance_from_high'] <= 0.02 and 
            analysis['volume_spike'] and 
            40 < analysis['rsi'] < 70 and 
            analysis['obv_trend']):
            
            score = (1 - analysis['distance_from_high']) * 100 + analysis['rsi']
            candidates.append({
                'Ticker': ticker,
                'מחיר': analysis['data']['Close'].iloc[-1],
                'מרחק משיא (%)': round(analysis['distance_from_high']*100,2),
                'נפח יחסי': round(analysis['data']['Volume'].iloc[-1]/analysis['data']['Volume'].rolling(20).mean().iloc[-1],1),
                'RSI': round(analysis['rsi'],1),
                'ציון': round(score,1)
            })
    
    return pd.DataFrame(candidates).sort_values('ציון', ascending=False).head(10)

# ------ ממשק משתמש ------
st.title("📈 מערכת ניתוח מניות S&P 500")

if st.button("🔄 עדכן כל הנתונים"):
    st.cache_data.clear()

tickers = load_sp500_tickers()

# ------ חלק 1: סורק אוטומטי ------
st.header("🚀 סורק PRE-BREAKOUT אוטומטי")
with st.expander("📖 קריטריוני הזיהוי"):
    st.markdown("""
    - עד 2% משיא 3 חודשים
    - נפח מסחר גבוה ב-50%+ מממוצע 20 יום
    - RSI בין 40-70
    - מגמת OBV חיובית ב-5 ימים אחרונים
    """)

breakout_df = get_breakout_candidates(tickers)
if not breakout_df.empty:
    st.subheader("🔥 עשרת המובילות")
    st.dataframe(
        breakout_df.set_index('Ticker'),
        column_config={
            "מחיר": st.column_config.NumberColumn(format="$%.2f"),
            "ציון": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=150)
        }
    )
    
    # הצגת גרף למניה המובילה
    top_ticker = breakout_df.iloc[0]['Ticker']
    st.subheader(f"📊 ניתוח טכני עבור {top_ticker}")
    top_data = analyze_stock(top_ticker)['data']
    st.line_chart(top_data[['Close','MA20','MA50']])
    with st.expander("נתונים היסטוריים"):
        st.dataframe(top_data.tail(10))
else:
    st.warning("לא נמצאו מניות העומדות בקריטריונים היום")

# ------ חלק 2: בחירה ידנית ------
st.header("🔍 ניתוח מניה לפי בחירה")
selected_ticker = st.selectbox("בחר/י מניה:", tickers, index=0)
if selected_ticker:
    analysis = analyze_stock(selected_ticker)
    if not analysis:
        st.error("לא נמצאו נתונים עבור מניה זו")
    else:
        st.subheader(f"📉 ניתוח טכני עבור {selected_ticker}")
        col1, col2 = st.columns([2, 1])
        
        with col1:
            st.line_chart(analysis['data'][['Close','MA20','MA50']])
        
        with col2:
            st.metric("מחיר נוכחי", f"${analysis['data']['Close'].iloc[-1]:.2f}")
            st.metric("RSI", f"{analysis['rsi']:.1f}")
            st.metric("מרחק משיא", f"{analysis['distance_from_high']*100:.2f}%")
            st.metric("נפח יחסי", f"{analysis['data']['Volume'].iloc[-1]/analysis['data']['Volume'].rolling(20).mean().iloc[-1]:.1f}x")
        
        with st.expander("הצג אינדיקטורים מתקדמים"):
            st.write("**ממוצעים נעים**")
            st.line_chart(analysis['data'][['MA20','MA50']])
            st.write("**מדד OBV**")
            st.line_chart(analysis['data']['OBV'])

# ------ הוראות שימוש ------
st.sidebar.markdown("""
## 🛠️ הוראות שימוש
1. לחץ על כפתור העדכון לטעינת נתונים עדכניים
2. הטבלה העליונה מציגה מניות בסף פריצה לפי קריטריונים טכניים
3. השתמש בתפריט הבחירה לניתוח מניה ספציפית
4. נתונים מתעדכנים אוטומטית מדי הרצה

**הערה:**  
המערכת אינה תחליף לייעוץ השקעות מקצועי.
""")

# ------ הרצה ------
# שמור את הקוד כ-app.py והריץ עם:
# streamlit run app.py

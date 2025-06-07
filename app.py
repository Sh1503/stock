import streamlit as st
import yfinance as yf
import pandas as pd
import talib

st.set_page_config(page_title="מניות בסף פריצה", layout="wide", page_icon="💹")

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
        
        # חישוב אינדיקטורים
        data['MA20'] = data['Close'].rolling(20).mean()
        data['MA50'] = data['Close'].rolling(50).mean()
        data['RSI'] = talib.RSI(data['Close'], timeperiod=14)
        data['OBV'] = talib.OBV(data['Close'], data['Volume'])
        
        # זיהוי שיאי 3 חודשים
        data['3m_high'] = data['High'].rolling(63).max()
        distance_from_high = (data['3m_high'] - data['Close']) / data['3m_high']
        
        # זיהוי תבניות פריצה
        data['CUP_HANDLE'] = talib.CDLIDENTIFIED3LINES(data['Open'], data['High'], data['Low'], data['Close'])
        
        return {
            'data': data,
            'distance_from_high': distance_from_high.iloc[-1],
            'volume_spike': (data['Volume'][-1] > 1.5 * data['Volume'].rolling(20).mean()[-1]),
            'rsi': data['RSI'].iloc[-1],
            'obv_trend': (data['OBV'][-5:].pct_change().mean() > 0)
        }
    except Exception as e:
        print(f"Error analyzing {ticker}: {e}")
        return None

@st.cache_data
def get_breakout_candidates(_tickers, max_stocks=100):
    candidates = []
    for ticker in _tickers[:max_stocks]:  # מגביל לסריקה חלקית לשיפור ביצועים
        analysis = analyze_stock(ticker)
        if not analysis:
            continue
        
        # קריטריוני PRE-BREAKOUT
        if (analysis['distance_from_high'] <= 0.02 and 
            analysis['volume_spike'] and 
            40 < analysis['rsi'] < 70 and 
            analysis['obv_trend']):
            
            score = (1 - analysis['distance_from_high']) * 100 + analysis['rsi']
            candidates.append({
                'Ticker': ticker,
                'מחיר': analysis['data']['Close'].iloc[-1],
                'מרחק משיא (%)': round(analysis['distance_from_high']*100,2),
                'נפח יחסי': round(analysis['data']['Volume'][-1]/analysis['data']['Volume'].rolling(20).mean()[-1],1),
                'RSI': round(analysis['rsi'],1),
                'ציון': round(score,1)
            })
    
    return pd.DataFrame(candidates).sort_values('ציון', ascending=False).head(10)

# ------ ממשק משתמש ------
st.title("🚀 סורק מניות PRE-BREAKOUT מבוסס S&P 500")
with st.expander("📚 הסבר על המאפיינים הנסרקים"):
    st.markdown("""
    - **מרחק משיא 3 חודשים**: עד 2% משיא ה-3 חודשים האחרונים
    - **נפח מסחר**: נפח היום גבוה ב-50% מהממוצע 20 יום
    - **עוצמה (RSI)**: בין 40-70 (לא יתר-קנייה)
    - **עוצמת קונים (OBV)**: מגמה עולה ב-5 ימים אחרונים
    """)

if st.button("🔄 עדכן נתונים"):
    st.cache_data.clear()

tickers = load_sp500_tickers()
breakout_df = get_breakout_candidates(tickers)

if not breakout_df.empty:
    st.subheader("🔥 TOP 10 מניות בסף פריצה")
    st.dataframe(
        breakout_df.set_index('Ticker'),
        column_config={
            "מחיר": st.column_config.NumberColumn(format="$%.2f"),
            "ציון": st.column_config.ProgressColumn(format="%.1f", min_value=0, max_value=150)
        }
    )
    
    # הצגת גרף לדוגמה למניה המובילה
    st.subheader(f"ניתוח טכני עבור {breakout_df.iloc[0]['Ticker']}")
    fig_data = analyze_stock(breakout_df.iloc[0]['Ticker'])['data']
    st.line_chart(fig_data[['Close','MA20','MA50']])
else:
    st.warning("לא נמצאו מניות העומדות בקריטריונים היום")

# ------ הנחיות הרצה ------
st.sidebar.markdown("""
## 📌 הוראות שימוש
1. הלחיצה על כפתור העדכון תטען נתונים עדכניים
2. הטבלה ממוינת לפי 'ציון פריצה' משולב
3. השימוש בנתונים להחלטות השקעה - על אחריות המשתמש בלבד
""")

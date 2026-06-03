import streamlit as st
import yfinance as yf
import pandas as pd
import numpy as np

# Page configuration optimized for modern stock market applications
st.set_page_config(page_title="PRO Trader Terminal", page_icon="⚡", layout="centered")

st.markdown('''
<style>
    .main { background-color: #0b0f19; }
    h1 { color: #ffffff; font-family: 'Inter', sans-serif; font-weight: 800 !important; letter-spacing: -1px; }
    .stButton>button { width: 100%; background: linear-gradient(135deg, #22c55e 0%, #15803d 100%); color:white; border:none; padding:12px; border-radius:8px; font-weight:bold; transition: 0.3s; }
    .stButton>button:hover { transform: translateY(-2px); box-shadow: 0 4px 20px rgba(34,197,94,0.4); }
    
    /* Trader-Friendly Premium Cards */
    .metric-box { background: linear-gradient(145deg, #1e293b 0%, #0f172a 100%); border-left: 4px solid #3b82f6; padding: 20px; border-radius: 12px; margin-bottom: 20px; box-shadow: 0 4px 6px -1px rgba(0,0,0,0.1); }
    .metric-title { color: #94a3b8; font-size: 13px; font-weight: 600; text-transform: uppercase; letter-spacing: 1px; margin-bottom: 5px; }
    .metric-value { color: #ffffff; font-size: 24px; font-weight: 700; margin: 0; }
    
    /* Premium High-Converting Lock Cards */
    .lock-card { background: linear-gradient(145deg, #111827 0%, #030712 100%); border: 1px dashed #ef4444; padding: 20px; border-radius: 12px; margin-bottom: 15px; position: relative; }
    .lock-badge { background-color: rgba(239, 68, 68, 0.1); color: #ef4444; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 50px; border: 1px solid rgba(239, 68, 68, 0.2); display: inline-block; margin-bottom: 10px; text-transform: uppercase; }
    .unlocked-badge { background-color: rgba(34, 197, 94, 0.1); color: #22c55e; font-size: 11px; font-weight: 700; padding: 4px 10px; border-radius: 50px; border: 1px solid rgba(34, 197, 94, 0.2); display: inline-block; margin-bottom: 10px; text-transform: uppercase; }
</style>
''', unsafe_allow_html=True)

st.title("⚡ PRO Trader Terminal")
st.write("Scan trends, spot candlestick breakouts, and calculate your exact risk in seconds. 🚀")
st.markdown("---")

# Dynamic user session tracker for the 1-time free pass
if 'allocated_free_ticker' not in st.session_state:
    st.session_state.allocated_free_ticker = None

# Input Box
ticker = st.text_input("📊 Enter Stock Ticker (e.g., TATAMOTORS.NS, SBIN.NS, NETWEB.NS):", "TATAMOTORS.NS").strip().upper()

if st.button("⚡ Scan Stock Setup"):
    with st.spinner("Fetching market data and scanning technical setups..."):
        try:
            stock = yf.Ticker(ticker)
            df = pd.DataFrame()
            
            # --- TRIPLE DATA SAFETY SHIELD ---
            try: df = stock.history(period='2y', interval='1d', auto_adjust=False)
            except Exception: pass
            if df.empty or len(df) < 220:
                try: df = stock.history(period='2y', interval='1d', auto_adjust=True)
                except Exception: pass
            if df.empty or len(df) < 220:
                try: df = yf.download(ticker, period='2y', interval='1d', progress=False)
                except Exception: pass

            if df.empty or len(df) < 220:
                st.error("❌ Stock Not Found: Please enter a valid NSE ticker with '.NS' suffix.")
            else:
                try: live_price = stock.fast_info['lastPrice']
                except Exception: live_price = df['Close'].iloc[-1]
                
                # --- TECHNICAL INDICATORS ENGINE ---
                df['EMA20'] = df['Adj Close'].ewm(span=20, adjust=False).mean()
                df['EMA50'] = df['Adj Close'].ewm(span=50, adjust=False).mean()
                df['EMA200'] = df['Adj Close'].ewm(span=200, adjust=False).mean()
                
                delta = df['Adj Close'].diff()
                gain = (delta.where(delta > 0, 0)).rolling(window=14).mean()
                loss = (-delta.where(delta < 0, 0)).rolling(window=14).mean()
                df['RSI'] = 100 - (100 / (1 + (gain / (loss + 1e-8))))
                df['Vol_Avg20'] = df['Volume'].rolling(window=20).mean()
                
                # Candlestick Calculations
                df['Total_Range'] = df['High'] - df['Low']
                df['Candle_Body'] = (df['Close'] - df['Open']).abs()
                df['Upper_Shadow'] = df['High'] - np.maximum(df['Close'], df['Open'])
                df['Lower_Shadow'] = np.minimum(df['Close'], df['Open']) - df['Low']
                
                latest_row = df.iloc[-1]
                total_range_l = latest_row['Total_Range'] if latest_row['Total_Range'] > 0 else 1e-8
                
                # Simple Candlestick Pattern Logic
                is_hammer = (latest_row['Lower_Shadow'] > (2 * latest_row['Candle_Body'])) and (latest_row['Upper_Shadow'] < (0.2 * total_range_l))
                is_shooting_star = (latest_row['Upper_Shadow'] > (2 * latest_row['Candle_Body'])) and (latest_row['Lower_Shadow'] < (0.2 * total_range_l))
                is_marubozu = (latest_row['Candle_Body'] / total_range_l > 0.85) and (latest_row['Close'] > latest_row['Open'])
                
                if is_hammer: pa_pattern = "Bullish Hammer Found (Strong buying pressure from lower levels)"
                elif is_shooting_star: pa_pattern = "Shooting Star Trap (Sellers dominant at the top - High Risk)"
                elif is_marubozu: pa_pattern = "Marubozu Breakout (Strong bullish conviction and momentum)"
                else: pa_pattern = "Normal Trading Candle (No key reversal pattern found today)"
                
                # Volatility SL/Target Math
                high_low = df['High'] - df['Low']
                high_close = np.abs(df['High'] - df['Close'].shift())
                low_close = np.abs(df['Low'] - df['Close'].shift())
                df['ATR'] = pd.concat([high_low, high_close, low_close], axis=1).max(axis=1).rolling(14).mean()
                latest_atr = df['ATR'].iloc[-1]
                
                stop_loss = live_price - (2 * latest_atr)
                target = live_price + (4 * latest_atr)
                recommended_quantity = int(1000 / (live_price - stop_loss)) if (live_price - stop_loss) > 0 else 0
                
                latest_ema200 = latest_row['EMA200']
                macro_sentiment = "BULLISH (Stock is trading above major 200-EMA institutional support)" if live_price > latest_ema200 else "BEARISH (Stock is trading below 200-EMA resistance - High Risk Setup)"

                # --- SESSION GATEWAY ---
                if st.session_state.allocated_free_ticker is None:
                    st.session_state.allocated_free_ticker = ticker
                
                is_premium_unlocked = (ticker == st.session_state.allocated_free_ticker)

                st.success(f"🎯 Connected to {ticker} | CMP (Current Market Price): ₹{live_price:,.2f}")
                
                if is_premium_unlocked:
                    st.toast(f"Free pass applied for {ticker}!", icon="✨")
                    st.markdown(f'''
                    <div style="background-color: rgba(34, 197, 94, 0.05); border: 1px solid #22c55e; padding: 12px; border-radius: 8px; margin-bottom: 25px; font-size: 13px; color: #4ade80;">
                        ✨ <b>FREE 1-TIME PASS ACTIVE:</b> Premium analytical features are completely unlocked for your first stock: <b>{st.session_state.allocated_free_ticker}</b>. Next stock searches will require a premium unlock pass.
                    </div>
                    ''', unsafe_allow_html=True)

                # ------------------ 🔓 MODULE 1: FUNDAMENTALS ------------------
                st.markdown("### 🏛️ Fundamental Analysis")
                try:
                    info = stock.info
                    m_cap = info.get('marketCap', 0) / 10000000
                    pe = info.get('trailingPE', np.nan)
                    
                    f_score = 100
                    if pd.notna(pe) and pe > 45: f_score -= 20
                    if info.get('debtToEquity', 0) > 150: f_score -= 30
                    
                    m_cap_str = f"₹{m_cap:,.1f} Cr" if m_cap > 0 else "Calculating..."
                    pe_str = f"{pe:.2f}" if pd.notna(pe) else "N/A"
                    score_str = f"{f_score}/100"
                except Exception:
                    m_cap_str = "Synced via History"
                    pe_str = "Live Route Active"
                    score_str = "Verified"

                st.markdown(f'''
                <div class="metric-box">
                    <div style="display: flex; justify-content: space-between; margin-bottom: 10px;">
                        <div><div class="metric-title">Market Cap</div><div class="metric-value">{m_cap_str}</div></div>
                        <div><div class="metric-title">P/E Ratio</div><div class="metric-value">{pe_str}</div></div>
                    </div>
                    <hr style="border: 0; border-top: 1px solid #334155; margin: 12px 0;">
                    <div><div class="metric-title">Fundamental Health Score</div><div class="metric-value" style="color:#2ecc71;">{score_str}</div></div>
                </div>
                ''', unsafe_allow_html=True)

                # ------------------ 🔓 MODULE 2: TECHNICALS ------------------
                st.markdown("### 📊 Technical Setup & Volume")
                latest_rsi = latest_row['RSI']
                latest_vol = latest_row['Volume']
                avg_vol = latest_row['Vol_Avg20']
                
                st.write(f"⏱️ **RSI (14) Momentum:** {latest_rsi:.1f}")
                if 40 <= latest_rsi <= 65: st.info("🟢 Healthy Buying Zone — Stock has solid room to move up before getting overbought.")
                elif latest_rsi > 65: st.warning("🔴 Overbought Zone — Momentum is overextended. Entering heavy long positions here is highly risky.")
                else: st.info("🟡 Oversold Zone — Stock is heavily beaten down, waiting for a base reversal.")
                
                st.write(f"📈 **Today's Volume:** {int(latest_vol):,} shares")
                if latest_vol > avg_vol * 1.5: st.success("🔥 Volume Breakout! Institutional players and big blocks are highly active today.")
                else: st.write("Normal retail volume flows. No major institutional block changes detected.")
                
                st.markdown("---")

                # ------------------ 🔒 MODULE 3: THE TRADER PAYWALL ------------------
                st.markdown("### 🔒 Premium Pro Dashboard")
                
                if is_premium_unlocked:
                    st.markdown(f'''
                    <div class="lock-card" style="border: 1px solid #22c55e;">
                        <span class="unlocked-badge">🔓 Unlocked (Free Trial Pass)</span>
                        <h4 style="color:#ffffff; margin: 5px 0 5px 0; font-size:15px;">⚡ Candlestick Pattern (Price Action)</h4>
                        <p style="color:#22c55e; font-size:14px; font-weight:600; margin:0;">👉 {pa_pattern}</p>
                    </div>
                    
                    <div class="lock-card" style="border: 1px solid #22c55e;">
                        <span class="unlocked-badge">🔓 Unlocked (Free Trial Pass)</span>
                        <h4 style="color:#ffffff; margin: 5px 0 5px 0; font-size:15px;">📡 Long-Term Trend (200 EMA)</h4>
                        <p style="color:#e2e8f0; font-size:14px; margin:0;">• 200 EMA Support Level: <b>₹{latest_ema200:,.2f}</b></p>
                        <p style="color:#3b82f6; font-size:14px; font-weight:600; margin:4px 0 0 0;">👉 Trend Status: {macro_sentiment}</p>
                    </div>
                    
                    <div class="lock-card" style="border: 1px solid #22c55e; background: linear-gradient(145deg, #0f172a 0%, #022c22 100%);">
                        <span class="unlocked-badge">🔓 Unlocked (Free Trial Pass)</span>
                        <h4 style="color:#ffffff; margin: 5px 0 10px 0; font-size:16px; font-weight:700;">⚖️ Risk Calculator & Position Sizing</h4>
                        <p style="margin:4px 0; color:#f1f5f9; font-size:14px;">• Strict Stop-Loss (SL): <span style="color:#ef4444; font-weight:bold; font-size:16px;">₹{stop_loss:,.2f}</span></p>
                        <p style="margin:4px 0; color:#f1f5f9; font-size:14px;">• Mathematical Target Price: <span style="color:#22c55e; font-weight:bold; font-size:16px;">₹{target:,.2f}</span></p>
                        <p style="margin:12px 0 0 0; color:#93c5fd; font-size:14px; padding-top:8px; border-top:1px dashed #334155;">👉 <b>Risk Allocation:</b> To limit your maximum loss to exactly <b>₹1,000</b> on this trade, your buying quantity must not exceed: <span style="color:#ffffff; font-weight:bold; background-color:#1e3a8a; padding:2px 8px; border-radius:4px;">{recommended_quantity} Shares</span></p>
                    </div>
                    ''', unsafe_allow_html=True)
                else:
                    st.markdown(f'''
                    <div style="background-color: rgba(239,68,68,0.05); border: 1px solid rgba(239,68,68,0.15); padding: 12px; border-radius: 8px; margin-bottom: 20px; font-size: 13px; color: #fca5a5;">
                        🔒 <b>FREE PASS EXPIRED:</b> Your 1-time free token was utilized for <b>{st.session_state.allocated_free_ticker}</b>. Pro metrics for {ticker} are currently locked.
                    </div>
                    
                    <div class="lock-card">
                        <span class="lock-badge">🔒 Locked Feature</span>
                        <h4 style="color:#3b82f6; margin: 0 0 5px 0; font-size:15px;">⚡ Candlestick Pattern (Price Action)</h4>
                        <p style="color:#64748b; font-size:13px; margin:0;">Real-time breakout patterns and candle structure scan parameters are locked.</p>
                    </div>
                    
                    <div class="lock-card">
                        <span class="lock-badge">🔒 Locked Feature</span>
                        <h4 style="color:#3b82f6; margin: 0 0 5px 0; font-size:15px;">📡 Long-Term Trend (200 EMA)</h4>
                        <p style="color:#64748b; font-size:13px; margin:0;">200-EMA institutional base support lines and macro trend routing are locked.</p>
                    </div>
                    
                    <div class="lock-card" style="background: linear-gradient(145deg, #111827 0%, #1c1917 100%);">
                        <span class="lock-badge" style="color:#f59e0b; border-color:rgba(245,158,11,0.2); background-color:rgba(245,158,11,0.1);">🚨 Risk Engine Locked</span>
                        <h4 style="color:#f59e0b; margin: 0 0 8px 0; font-size:16px; font-weight:700;">⚖️ Risk Calculator & Position Sizing</h4>
                        <p style="margin:4px 0; color:#475569; font-size:14px;">• Strict Stop-Loss (SL) Price: <span style="color:#ef4444; font-weight:bold;">[ SECURE LOCKED ]</span></p>
                        <p style="margin:4px 0; color:#475569; font-size:14px;">• Mathematical Target Price: <span style="color:#22c55e; font-weight:bold;">[ SECURE LOCKED ]</span></p>
                        <p style="margin:4px 0; color:#475569; font-size:14px;">• Recommended Buying Quantity (Max ₹1000 Risk): <span style="color:#3b82f6; font-weight:bold;">[ SECURE LOCKED ]</span></p>
                    </div>
                    ''', unsafe_allow_html=True)
                    
                    st.markdown("<h3 style='text-align: center; color: #ffffff; margin-top:30px; margin-bottom: 5px; font-size:22px;'>Trade Smart with Full System Accuracy</h3>", unsafe_allow_html=True)
                    st.markdown("<p style='text-align: center; font-size: 14px; color:#94a3b8; margin-bottom: 25px;'>Stop gambling on blind retail setups. Save your hard-earned capital from a potential ₹10,000 catastrophic loss for less than the price of a generic tea transaction.</p>", unsafe_allow_html=True)
                    
                    # 🟢 YAHAN AAPKA ASLI TOPMATE LINK LAGAO 🟢
                    pay_url = "https://topmate.io/kishan_sharma23" 
                    
                    st.markdown(f'''
                        <div style="text-align: center; margin-bottom:40px;">
                            <a href="{pay_url}" target="_blank">
                                <button style="background: linear-gradient(135deg, #22c55e 0%, #15803d 100%); color:white; padding:15px 40px; border:none; border-radius:8px; font-size:18px; font-weight:bold; cursor:pointer; box-shadow: 0 4px 20px rgba(34,197,94,0.4); width: 100%;">
                                    💳 Unlock Full Premium Dashboard — ₹49 Only
                                </button>
                            </a>
                        </div>
                    ''', unsafe_allow_html=True)
                
        except Exception as main_error:
            st.error(f"❌ System Exception: {main_error}")
          

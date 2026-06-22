import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="バフェットプロ v3.5", layout="wide")
st.title("🛡️ バフェットプロ v3.5")
st.subheader("安定版・最終調整済み")
st.caption(f"更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

st.sidebar.header("スクリーニング条件")
per_max = st.sidebar.slider("PERの上限", 5, 30, 15)
market_cap_max = st.sidebar.slider("時価総額上限 (億円)", 30, 1000, 500)
netcash_min = st.sidebar.slider("ネットキャッシュ比率下限", 0.3, 3.0, 0.5, 0.05)

if st.sidebar.button("🚀 自動スクリーニング実行", type="primary", use_container_width=True):
    candidates = ['8152.T', '7427.T', '5280.T', '8141.T', '7868.T', '7980.T', '7857.T', 
                  '6444.T', '7482.T', '5946.T', '6659.T', '7746.T', '7776.T', '6417.T',
                  '6908.T', '6298.T', '7780.T']

    results = []
    debug = []

    for code in candidates:
        try:
            ticker = yf.Ticker(code)
            info = ticker.info
            market_cap = info.get('marketCap', 0) / 1e8
            price = info.get('currentPrice', 0)
            name = info.get('longName', 'Unknown').replace('株式会社', '').replace(' Inc.', '').strip()[:22]
            per = info.get('trailingPE') or info.get('forwardPE', 999)

            if market_cap < 15 or market_cap > market_cap_max:
                debug.append(f"{code}: 時価総額 {market_cap:.1f}億 → 範囲外")
                continue

            bs = ticker.balance_sheet
            if bs is None or bs.empty:
                bs = ticker.quarterly_balance_sheet

            current_assets = 0
            investments = 0
            total_liab = 0

            if bs is not None and not bs.empty:
                bs = bs.fillna(0)
                for idx in bs.index:
                    idx_str = str(idx).lower()
                    if 'current asset' in idx_str or 'total current assets' in idx_str:
                        current_assets = bs.loc[idx].iloc[0]
                    if any(k in idx_str for k in ['investment', 'marketable', 'securities', 'short term invest']):
                        investments = bs.loc[idx].iloc[0]
                    if 'total liab' in idx_str or 'total liabilities' in idx_str:
                        total_liab = bs.loc[idx].iloc[0]

            net_cash = current_assets + (investments * 0.7) - total_liab
            ncr = round(net_cash / (market_cap * 1e8), 3) if market_cap > 0 else 0.0

            debug.append(f"{code}: {name} | PER={per:.1f} | NCR={ncr:.3f} | 時価総額={market_cap:.1f}億")

            if per <= per_max and ncr >= netcash_min:
                results.append({
                    'コード': code.replace('.T',''),
                    '銘柄名': name,
                    '株価': round(price,1),
                    '時価総額': round(market_cap,1),
                    'PER': round(per,2),
                    'ネットキャッシュ比率': ncr
                })
        except Exception as e:
            debug.append(f"{code}: エラー - {str(e)[:30]}")
            continue

    if results:
        df = pd.DataFrame(results).sort_values('ネットキャッシュ比率', ascending=False).reset_index(drop=True)
        st.success(f"✅ {len(df)}銘柄が条件を満たしました！")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.subheader("📊 自動ポートフォリオ提案")
        top_n = min(3, len(df))
        top = df.head(top_n).copy()
        
        if top_n == 1:
            weights = [100]
        elif top_n == 2:
            weights = [60, 40]
        else:
            weights = [45, 35, 20]
            
        top['推奨比率(%)'] = weights[:top_n]
        st.dataframe(top, use_container_width=True, hide_index=True)
        
    else:
        st.error("❌ 条件に合う銘柄がありませんでした。条件を緩めて再度実行してください。")

    with st.expander("📋 詳細デバッグログ", expanded=True):
        for line in debug:
            st.text(line)

    st.info("デバッグログを見て、NCR（ネットキャッシュ比率）が0.5以上になる銘柄があるか確認してください。")

else:
    st.info("左側のサイドバーで条件を設定し、「自動スクリーニング実行」を押してください。")
    st.markdown("**推奨**: PER上限=15、ネットキャッシュ比率下限=0.5、時価総額上限=500億円")

st.caption("🛡️ Buffett Pro v3.5 | 最終安定版 | 世界一有能な株式分析官")

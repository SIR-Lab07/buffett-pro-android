import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="バフェットプロ v5.1", layout="wide")
st.title("🛡️ バフェットプロ v5.1")
st.subheader("Yahoo Finance版 - 調整済み最終版")
st.caption(f"更新: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")

st.sidebar.header("スクリーニング条件")
per_max = st.sidebar.slider("PERの上限", 5, 30, 15)
market_cap_max = st.sidebar.slider("時価総額上限 (億円)", 30, 1000, 500)
min_ncr = st.sidebar.slider("最低ネットキャッシュ比率", 0.0, 2.0, 0.0, 0.05)

if st.sidebar.button("🚀 自動スクリーニング実行", type="primary", use_container_width=True):
    candidates = ['8152.T', '7427.T', '5280.T', '7980.T', '7857.T', '7868.T', '8141.T',
                  '7482.T', '6444.T', '6659.T', '7746.T', '7776.T', '6298.T', '6196.T']

    results = []
    debug = []

    for code in candidates:
        try:
            ticker = yf.Ticker(code)
            info = ticker.info
            market_cap = info.get('marketCap', 0) / 1e8
            if market_cap < 15 or market_cap > market_cap_max:
                debug.append(f"{code}: 時価総額 {market_cap:.1f}億 → 範囲外")
                continue

            per = info.get('trailingPE') or info.get('forwardPE', 999)
            name = info.get('longName', 'Unknown').replace('株式会社', '').strip()[:22]

            bs = ticker.balance_sheet
            if bs is None or bs.empty:
                bs = ticker.quarterly_balance_sheet

            current_assets = 0
            investments = 0
            total_liab = 0

            if bs is not None and not bs.empty:
                for idx in bs.index:
                    idx_lower = str(idx).lower()
                    value = float(bs.loc[idx].iloc[0]) if len(bs.loc[idx]) > 0 else 0
                    if 'current asset' in idx_lower:
                        current_assets = value
                    if any(k in idx_lower for k in ['investment', 'marketable', 'securities']):
                        investments = value
                    if 'total liab' in idx_lower or 'total liabilities' in idx_lower:
                        total_liab = value

            net_cash = current_assets + investments * 0.7 - total_liab
            ncr = round(net_cash / (market_cap * 1e8), 3) if market_cap > 0 else 0.0

            debug.append(f"{code}: {name} | PER={per:.1f} | NCR={ncr:.3f} | 時価総額={market_cap:.1f}億")

            if per <= per_max and ncr >= min_ncr:
                results.append({
                    'コード': code.replace('.T',''),
                    '銘柄名': name,
                    '株価': round(info.get('currentPrice', 0), 1),
                    '時価総額': round(market_cap, 1),
                    'PER': round(per, 2),
                    'ネットキャッシュ比率': ncr
                })
        except:
            debug.append(f"{code}: データ取得失敗")
            continue

    if results:
        df = pd.DataFrame(results).sort_values('ネットキャッシュ比率', ascending=False).reset_index(drop=True)
        st.success(f"✅ {len(df)}銘柄が条件を満たしました！")
        st.dataframe(df, use_container_width=True, hide_index=True)
        
        st.subheader("📊 推奨ポートフォリオ")
        top_n = min(3, len(df))
        top = df.head(top_n).copy()
        weights = [50, 30, 20] if top_n == 3 else [60, 40] if top_n == 2 else [100]
        top['推奨比率(%)'] = weights
        st.dataframe(top, use_container_width=True, hide_index=True)
    else:
        st.warning("条件に合う銘柄がありませんでした。")
        st.info("最低ネットキャッシュ比率を0.0に設定して再度実行してください。")

    with st.expander("📋 詳細デバッグログ", expanded=True):
        for line in debug:
            st.text(line)

else:
    st.info("左側のサイドバーで条件を設定し、「自動スクリーニング実行」を押してください。")
    st.markdown("**推奨設定**: PER上限=15、ネットキャッシュ比率下限=0.0")

st.caption("🛡️ Buffett Pro v5.1 | Yahoo Finance最終調整版")

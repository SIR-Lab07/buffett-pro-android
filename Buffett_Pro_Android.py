import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="バフェットプロ v3.3", layout="wide")
st.title("🛡️ バフェットプロ v3.3")
st.subheader("エラー修正版・安定動作")
st.caption(f"更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

st.sidebar.header("スクリーニング条件")
per_max = st.sidebar.slider("PERの上限", 5, 30, 12)
market_cap_max = st.sidebar.slider("時価総額上限 (億円)", 100, 2000, 600)
netcash_min = st.sidebar.slider("ネットキャッシュ比率下限", 0.3, 2.0, 0.6, 0.1)

if st.sidebar.button("🚀 全銘柄診断実行", type="primary", use_container_width=True):
    candidates = ['8152.T','7427.T','5280.T','8141.T','7868.T','3209.T','8278.T','7857.T',
                  '7980.T','6444.T','5946.T','7482.T','6659.T','7746.T','6196.T','7776.T',
                  '6417.T','6908.T','7995.T','6298.T','7780.T','6976.T']

    results = []
    debug = []

    for code in candidates:
        try:
            ticker = yf.Ticker(code)
            info = ticker.info
            market_cap = info.get('marketCap', 0) / 1e8
            price = info.get('currentPrice', 0)
            name = info.get('longName', 'Unknown').replace('株式会社', '').strip()[:22]

            if market_cap > market_cap_max or market_cap < 15:
                debug.append(f"{code}: 時価総額 {market_cap:.1f}億 → 範囲外")
                continue

            bs = ticker.get_balance_sheet()
            if bs is None or bs.empty:
                debug.append(f"{code}: 財務諸表取得失敗")
                continue

            # 安全なデータ取得方法に変更
            current_assets = bs.get('Current Assets', pd.Series([0]))[0] if 'Current Assets' in bs.index else 0
            total_liab = bs.get('Total Liabilities Net Minority Interest', pd.Series([0]))[0] if 'Total Liabilities Net Minority Interest' in bs.index else 0
            investments = 0
            for key in ['Investments', 'Investment Securities', 'Marketable Securities', 'Short Term Investments']:
                if key in bs.index:
                    investments = bs.get(key, pd.Series([0]))[0]
                    break

            net_cash = (current_assets + investments * 0.7) - total_liab
            ncr = net_cash / (market_cap * 1e8) if market_cap > 0 else 0
            per = info.get('trailingPE') or info.get('forwardPE', 999)

            debug.append(f"{code}: PER={per:.1f} | NCR={ncr:.2f} | 時価総額={market_cap:.1f}億")

            if per <= per_max and ncr >= netcash_min:
                results.append({
                    'コード': code.replace('.T',''),
                    '銘柄名': name,
                    '株価': round(price,1),
                    '時価総額': round(market_cap,1),
                    'PER': round(per,2),
                    'ネットキャッシュ比率': round(ncr,2)
                })
        except Exception as e:
            debug.append(f"{code}: エラー - {str(e)[:35]}")
            continue

    if results:
        df = pd.DataFrame(results).sort_values('ネットキャッシュ比率', ascending=False)
        st.success(f"✅ {len(df)}銘柄が見つかりました！")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.error("❌ 条件に合う銘柄がありませんでした。条件をさらに緩めてください。")

    with st.expander("📋 詳細デバッグログ", expanded=True):
        for line in debug:
            st.text(line)

    st.info("デバッグログを確認しながら、PER上限やネットキャッシュ比率の下限を調整してください。")

else:
    st.info("左のサイドバーで条件を設定して「全銘柄診断実行」を押してください。")
    st.markdown("**推奨設定**: PER上限 = 15、ネットキャッシュ比率下限 = 0.5")

st.caption("🛡️ Buffett Pro v3.3 | エラー修正・安全取得版")

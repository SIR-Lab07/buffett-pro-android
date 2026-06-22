import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="バフェットプロ診断版", layout="wide")
st.title("🛡️ バフェットプロ v3.2")
st.subheader("診断・デバッグ強化版")
st.caption(f"更新: {datetime.now().strftime('%Y-%m-%d %H:%M')}")

st.warning("現在デバッグ中です。どの銘柄が除外されているかを詳細に表示します。")

# 条件
st.sidebar.header("条件設定（診断用）")
per_max = st.sidebar.slider("PERの上限", 5, 30, 15)
market_cap_max = st.sidebar.slider("時価総額上限 (億円)", 100, 2000, 800)
netcash_min = st.sidebar.slider("ネットキャッシュ比率下限", 0.3, 2.0, 0.5, 0.1)

if st.sidebar.button("🔍 全銘柄診断実行", type="primary"):
    candidates = ['8152.T', '7427.T', '5280.T', '8141.T', '7868.T', '3209.T', '8278.T', 
                  '7857.T', '7980.T', '6444.T', '5946.T', '7482.T', '6659.T', '7746.T',
                  '6196.T', '7776.T', '6417.T', '6908.T', '7995.T', '6298.T']

    results = []
    debug = []

    for code in candidates:
        status = f"{code} : "
        try:
            ticker = yf.Ticker(code)
            info = ticker.info
            market_cap = info.get('marketCap', 0) / 1e8
            price = info.get('currentPrice', 0)
            name = info.get('longName', 'Unknown')[:25]

            status += f"時価総額={market_cap:.1f}億, "

            if market_cap > market_cap_max:
                debug.append(status + "時価総額が大きすぎる")
                continue

            bs = ticker.balance_sheet
            if bs.empty:
                debug.append(status + "財務諸表取得失敗")
                continue

            current = bs.loc['Current Assets'].iloc[0] if 'Current Assets' in bs.index else 0
            liab = bs.loc.get('Total Liabilities Net Minority Interest', pd.Series([0])).iloc[0]
            invest = 0
            for k in ['Investments','Investment Securities','Marketable Securities']:
                if k in bs.index:
                    invest = bs.loc[k].iloc[0]
                    break

            netcash = (current + invest * 0.7) - liab
            ncr = netcash / (market_cap * 1e8) if market_cap > 0 else 0
            per = info.get('trailingPE') or 999

            status += f"PER={per:.1f}, NCR={ncr:.2f}"

            if per <= per_max and ncr >= netcash_min:
                results.append({
                    'コード': code.replace('.T',''),
                    '銘柄名': name.replace('株式会社','').strip(),
                    '株価': round(price,1),
                    '時価総額': round(market_cap,1),
                    'PER': round(per,2),
                    'ネットキャッシュ比率': round(ncr,2)
                })
            else:
                debug.append(status + " → 条件不適合")
        except Exception as e:
            debug.append(f"{code} : エラー発生 - {str(e)[:40]}")

    if results:
        df = pd.DataFrame(results).sort_values('ネットキャッシュ比率', ascending=False)
        st.success(f"✅ {len(df)}銘柄がヒットしました！")
        st.dataframe(df, use_container_width=True, hide_index=True)
    else:
        st.error("❌ 条件に合う銘柄が1つも見つかりませんでした。")

    with st.expander("📋 詳細デバッグログ（全銘柄の処理結果）", expanded=True):
        for line in debug:
            st.text(line)

    st.info("上記のデバッグログを見て、条件を調整してください。特に「財務諸表取得失敗」が多い場合はyfinanceの制限が考えられます。")

else:
    st.info("左側のサイドバーで条件を調整し、「全銘柄診断実行」ボタンを押してください。")
    st.markdown("""
    ### 現在の診断版の目的
    - どの銘柄がなぜ除外されたのかを明確に表示
    - PER上限を15、ネットキャッシュ比率下限を0.5に設定して開始することを推奨
    """)

st.caption("🛡️ Buffett Pro v3.2 Diagnosis Mode | 世界一有能な株式分析官")

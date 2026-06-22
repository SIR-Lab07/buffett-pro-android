import streamlit as st
import pandas as pd
import yfinance as yf
from datetime import datetime
import warnings
warnings.filterwarnings('ignore')

st.set_page_config(page_title="バフェットプロ v5.0", layout="wide")
st.title("🛡️ バフェットプロ v5.0")
st.subheader("Yahoo Finance版 - 実用最終版")
st.caption(f"最終更新: {datetime.now().strftime('%Y年%m月%d日 %H:%M')}")

st.markdown("**Yahoo Financeからデータを取得してネットキャッシュ比率を計算**")

# サイドバー
st.sidebar.header("スクリーニング条件")
per_max = st.sidebar.slider("PERの上限", 5, 25, 12)
market_cap_max = st.sidebar.slider("時価総額上限 (億円)", 50, 1000, 500)
min_ncr = st.sidebar.slider("最低ネットキャッシュ比率", 0.0, 2.0, 0.5, 0.1)

run_button = st.sidebar.button("🚀 Yahoo Financeでスクリーニング実行", type="primary", use_container_width=True)

# 対象銘柄（小型株・財務が比較的取得しやすい銘柄を中心に）
candidates = [
    '8152.T', '7427.T', '5280.T', '7980.T', '7857.T', '7868.T', '8141.T',
    '7482.T', '5946.T', '6444.T', '6659.T', '7746.T', '7776.T', '6298.T',
    '7780.T', '6196.T', '6417.T', '6908.T', '7995.T'
]

if run_button:
    with st.spinner("Yahoo Financeから財務データを取得中...（約40〜70秒かかります）"):
        results = []
        debug = []

        for code in candidates:
            try:
                ticker = yf.Ticker(code)
                info = ticker.info
                
                market_cap = info.get('marketCap', 0) / 1e8
                if market_cap < 20 or market_cap > market_cap_max:
                    debug.append(f"{code}: 時価総額 {market_cap:.1f}億 → 範囲外")
                    continue

                per = info.get('trailingPE') or info.get('forwardPE', 999)
                name = info.get('longName', '---').replace('株式会社', '').strip()[:20]

                # 財務諸表取得（複数方法でフォールバック）
                bs = ticker.balance_sheet
                if bs is None or bs.empty:
                    bs = ticker.quarterly_balance_sheet

                current_assets = 0
                investments = 0
                total_liab = 0
                cash = 0

                if bs is not None and not bs.empty:
                    for idx in bs.index:
                        idx_lower = str(idx).lower()
                        value = bs.loc[idx].iloc[0] if len(bs.loc[idx]) > 0 else 0
                        
                        if 'current asset' in idx_lower or 'total current assets' in idx_lower:
                            current_assets = value
                        if 'cash' in idx_lower and 'equivalents' in idx_lower:
                            cash = value
                        if any(k in idx_lower for k in ['investment', 'marketable', 'securities']):
                            investments = value
                        if any(k in idx_lower for k in ['total liabilities', 'total liab']):
                            total_liab = value

                # 保守的なネットキャッシュ計算
                liquid = current_assets if current_assets > cash else cash + investments
                net_cash = liquid - total_liab
                ncr = round(net_cash / (market_cap * 1e8), 3) if market_cap > 0 else 0.0

                debug.append(f"{code}: {name} | PER={per:.1f} | NCR={ncr:.3f} | 時価総額={market_cap:.1f}億")

                if per <= per_max and ncr >= min_ncr:
                    results.append({
                        'コード': code.replace('.T', ''),
                        '銘柄名': name,
                        '株価': round(info.get('currentPrice', 0), 1),
                        '時価総額': round(market_cap, 1),
                        'PER': round(per, 2),
                        'ネットキャッシュ比率': ncr,
                        '優待': 'あり' if code in ['7427.T'] else 'なし'
                    })
            except Exception as e:
                debug.append(f"{code}: 取得エラー")
                continue

        if results:
            df = pd.DataFrame(results).sort_values('ネットキャッシュ比率', ascending=False).reset_index(drop=True)
            st.success(f"✅ {len(df)}銘柄が条件を満たしました")
            st.dataframe(df, use_container_width=True, hide_index=True)

            st.subheader("📊 推奨ポートフォリオ")
            top3 = df.head(3).copy()
            weights = [45, 35, 20][:len(top3)]
            top3['推奨比率(%)'] = weights
            st.dataframe(top3[['コード','銘柄名','ネットキャッシュ比率','推奨比率(%)']], 
                        use_container_width=True, hide_index=True)
        else:
            st.error("条件に合う銘柄が見つかりませんでした。")
            st.info("ネットキャッシュ比率下限を0.0に下げて試してください。")

    with st.expander("📋 デバッグログ", expanded=True):
        for line in debug:
            st.text(line)

else:
    st.info("左のサイドバーで条件を設定して「スクリーニング実行」ボタンを押してください。")
    st.markdown("""
    ### このアプリの特徴
    - Yahoo Financeからリアルタイムデータ取得
    - 複数の取得方法で安定化
    - ネットキャッシュ比率を保守的に計算
    """)

st.caption("🛡️ Buffett Pro v5.0 | Yahoo Finance版最終版 | 世界一有能な株式分析官")

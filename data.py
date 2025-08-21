import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO

# ページ設定
st.set_page_config(
    page_title="日本の高齢化社会分析",
    page_icon="📊",
    layout="wide"
)

# タイトル
st.title("🏥 日本の高齢化社会分析ダッシュボード")
st.markdown("---")

# データアップロード機能
st.sidebar.header("📁 データアップロード")
uploaded_file = st.sidebar.file_uploader(
    "Excelファイルをアップロード",
    type=['xlsx', 'xls'],
    help="census_2020.xlsxファイルをアップロードしてください"
)

@st.cache_data
def load_excel_data(file):
    """Excelファイルの読み込み"""
    try:
        # シート確認
        excel_file = pd.ExcelFile(file)
        st.sidebar.success(f"シート: {excel_file.sheet_names}")
        
        # メインシートの読み込み
        df = pd.read_excel(file, sheet_name='census_2020', header=None)
        return df
    except Exception as e:
        st.error(f"ファイル読み込みエラー: {e}")
        return None

def analyze_data_structure(df):
    """データ構造の分析"""
    st.header("📋 データ構造分析")
    
    col1, col2 = st.columns(2)
    
    with col1:
        st.subheader("基本情報")
        st.write(f"**行数**: {df.shape[0]:,}")
        st.write(f"**列数**: {df.shape[1]:,}")
        st.write(f"**データサイズ**: {df.memory_usage(deep=True).sum() / 1024**2:.1f} MB")
    
    with col2:
        st.subheader("データサンプル")
        st.dataframe(df.head(10))
    
    # 都道府県データの特定
    st.subheader("🗾 都道府県データの特定")
    
    prefectures = ['北海道', '青森', '岩手', '宮城', '秋田', '山形', '福島', 
                  '茨城', '栃木', '群馬', '埼玉', '千葉', '東京', '神奈川']
    
    found_data = []
    for idx, row in df.iterrows():
        for col in row:
            if pd.notna(col) and any(pref in str(col) for pref in prefectures):
                found_data.append({
                    '行番号': idx + 1,
                    'データ': str(col)[:50] + "..." if len(str(col)) > 50 else str(col)
                })
                if len(found_data) >= 10:  # 最初の10件のみ表示
                    break
        if len(found_data) >= 10:
            break
    
    if found_data:
        st.write("**都道府県データが見つかった行:**")
        st.dataframe(pd.DataFrame(found_data))
    else:
        st.warning("都道府県データが見つかりませんでした")

def create_sample_analysis():
    """サンプル分析の作成"""
    st.header("📊 サンプル分析（デモデータ）")
    
    # デモデータの作成
    years = list(range(1980, 2021, 5))
    prefectures = ['東京都', '大阪府', '愛知県', '北海道', '沖縄県', '秋田県']
    
    np.random.seed(42)  # 再現性のため
    
    demo_data = []
    for pref in prefectures:
        base_aging_rate = np.random.uniform(15, 25)  # 1980年の基本高齢化率
        for i, year in enumerate(years):
            # 年を追うごとに高齢化率が増加（実際のトレンドを模擬）
            aging_rate = base_aging_rate + (i * np.random.uniform(2, 4))
            population = np.random.randint(800000, 13000000)  # 人口
            
            demo_data.append({
                '年': year,
                '都道府県': pref,
                '高齢化率': round(aging_rate, 1),
                '総人口': population,
                '高齢者人口': int(population * aging_rate / 100)
            })
    
    demo_df = pd.DataFrame(demo_data)
    
    # 分析1: 高齢化率推移
    st.subheader("📈 高齢化率推移（1980-2020年）")
    
    fig, ax = plt.subplots(figsize=(12, 6))
    
    for pref in prefectures:
        pref_data = demo_df[demo_df['都道府県'] == pref]
        ax.plot(pref_data['年'], pref_data['高齢化率'], 
               marker='o', linewidth=2, label=pref)
    
    ax.set_xlabel('年')
    ax.set_ylabel('高齢化率 (%)')
    ax.set_title('都道府県別高齢化率推移')
    ax.legend()
    ax.grid(True, alpha=0.3)
    
    st.pyplot(fig)
    
    # 分析2: 2020年高齢化率ランキング
    st.subheader("🏆 2020年高齢化率ランキング")
    
    latest_data = demo_df[demo_df['年'] == 2020].sort_values('高齢化率', ascending=False)
    
    col1, col2 = st.columns(2)
    
    with col1:
        fig, ax = plt.subplots(figsize=(8, 6))
        bars = ax.barh(latest_data['都道府県'], latest_data['高齢化率'])
        ax.set_xlabel('高齢化率 (%)')
        ax.set_title('2020年 都道府県別高齢化率')
        
        # カラーマップ
        colors = plt.cm.Reds(np.linspace(0.4, 0.8, len(bars)))
        for bar, color in zip(bars, colors):
            bar.set_color(color)
        
        st.pyplot(fig)
    
    with col2:
        st.write("**ランキング表**")
        ranking_df = latest_data[['都道府県', '高齢化率', '総人口', '高齢者人口']].reset_index(drop=True)
        ranking_df.index += 1
        st.dataframe(ranking_df)
    
    # 分析3: 相関分析
    st.subheader("🔍 相関分析")
    
    # 2020年データでの相関
    latest_year_data = demo_df[demo_df['年'] == 2020]
    
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(15, 5))
    
    # 散布図1: 総人口 vs 高齢化率
    ax1.scatter(latest_year_data['総人口'], latest_year_data['高齢化率'], 
               alpha=0.7, s=100, c='blue')
    for idx, row in latest_year_data.iterrows():
        ax1.annotate(row['都道府県'], 
                    (row['総人口'], row['高齢化率']),
                    xytext=(5, 5), textcoords='offset points',
                    fontsize=8)
    ax1.set_xlabel('総人口')
    ax1.set_ylabel('高齢化率 (%)')
    ax1.set_title('総人口 vs 高齢化率')
    ax1.grid(True, alpha=0.3)
    
    # 散布図2: 高齢者人口の絶対数
    ax2.scatter(latest_year_data['都道府県'], latest_year_data['高齢者人口'], 
               alpha=0.7, s=100, c='red')
    ax2.set_xlabel('都道府県')
    ax2.set_ylabel('高齢者人口')
    ax2.set_title('都道府県別高齢者人口')
    ax2.tick_params(axis='x', rotation=45)
    ax2.grid(True, alpha=0.3)
    
    plt.tight_layout()
    st.pyplot(fig)
    
    return demo_df

def show_insights(demo_df):
    """重要な洞察の表示"""
    st.header("💡 データから見える洞察")
    
    # 最新データ
    latest_data = demo_df[demo_df['年'] == 2020]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        max_aging = latest_data.loc[latest_data['高齢化率'].idxmax()]
        st.metric(
            label="🔴 最高高齢化率",
            value=f"{max_aging['高齢化率']}%",
            delta=f"{max_aging['都道府県']}"
        )
    
    with col2:
        min_aging = latest_data.loc[latest_data['高齢化率'].idxmin()]
        st.metric(
            label="🔵 最低高齢化率", 
            value=f"{min_aging['高齢化率']}%",
            delta=f"{min_aging['都道府県']}"
        )
    
    with col3:
        avg_aging = latest_data['高齢化率'].mean()
        st.metric(
            label="📊 全国平均",
            value=f"{avg_aging:.1f}%",
            delta="高齢化率"
        )
    
    # トレンド分析
    st.subheader("📈 トレンド分析")
    
    # 各都道府県の高齢化率増加速度
    trend_analysis = []
    for pref in demo_df['都道府県'].unique():
        pref_data = demo_df[demo_df['都道府県'] == pref].sort_values('年')
        if len(pref_data) >= 2:
            rate_1980 = pref_data.iloc[0]['高齢化率']
            rate_2020 = pref_data.iloc[-1]['高齢化率']
            increase_rate = ((rate_2020 - rate_1980) / rate_1980) * 100
            
            trend_analysis.append({
                '都道府県': pref,
                '1980年高齢化率': f"{rate_1980:.1f}%",
                '2020年高齢化率': f"{rate_2020:.1f}%",
                '増加率': f"{increase_rate:.1f}%"
            })
    
    trend_df = pd.DataFrame(trend_analysis)
    st.dataframe(trend_df)

def main():
    """メイン関数"""
    
    # サイドバーメニュー
    st.sidebar.header("🎛️ 分析メニュー")
    analysis_mode = st.sidebar.radio(
        "分析モードを選択",
        ["📁 データアップロード", "📊 サンプル分析", "📋 使い方ガイド"]
    )
    
    if analysis_mode == "📁 データアップロード":
        if uploaded_file is not None:
            df = load_excel_data(uploaded_file)
            if df is not None:
                analyze_data_structure(df)
        else:
            st.info("👆 サイドバーからExcelファイルをアップロードしてください")
            st.markdown("""
            ### 📋 必要なファイル
            - **ファイル名**: census_2020.xlsx
            - **形式**: Excel形式
            - **内容**: 国勢調査時系列データ
            """)
    
    elif analysis_mode == "📊 サンプル分析":
        demo_df = create_sample_analysis()
        show_insights(demo_df)
        
        # データダウンロード
        st.subheader("💾 分析結果のダウンロード")
        
        # CSVダウンロード
        csv = demo_df.to_csv(index=False, encoding='utf-8')
        st.download_button(
            label="📥 分析データをCSVダウンロード",
            data=csv,
            file_name="aging_analysis_demo.csv",
            mime="text/csv"
        )
    
    elif analysis_mode == "📋 使い方ガイド":
        st.header("📖 使い方ガイド")
        
        st.markdown("""
        ### 🎯 このアプリについて
        
        日本の高齢化社会の進行を分析するためのStreamlitダッシュボードです。
        
        ### 📊 主な機能
        
        1. **データアップロード**: Excelファイルの構造分析
        2. **高齢化率推移**: 時系列でのトレンド分析
        3. **地域比較**: 都道府県別の比較分析
        4. **相関分析**: 人口と高齢化率の関係性
        
        ### 🔧 技術スタック
        
        - **Python**: データ処理・分析
        - **Streamlit**: Webアプリケーション
        - **Pandas**: データ操作
        - **Matplotlib/Seaborn**: データ可視化
        
        ### 📈 転職ポートフォリオとして
        
        このプロジェクトは以下のスキルを証明します:
        
        - **データクリーニング**: 複雑なExcel構造の処理
        - **探索的データ分析**: トレンド発見・仮説検証
        - **データ可視化**: 効果的なグラフ作成
        - **Webアプリ開発**: ユーザーフレンドリーなUI
        - **医療・社会課題**: ドメイン知識の活用
        """)
        
        st.subheader("🚀 次のステップ")
        st.markdown("""
        1. **実データでの分析**: 国勢調査データで実際の分析
        2. **予測モデル**: 機械学習による将来予測
        3. **医療需要**: 高齢化と医療費の相関分析
        4. **政策提言**: データに基づく施策提案
        """)

    # フッター
    st.markdown("---")
    st.markdown("""
    **📊 日本の高齢化社会分析ダッシュボード**  
    作成者: 医療従事者（作業療法士）によるデータ分析プロジェクト  
    目的: 転職用ポートフォリオ・社会課題の可視化
    """)

if __name__ == "__main__":
    main()

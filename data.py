import streamlit as st
import pandas as pd
import numpy as np
import plotly.express as px
import plotly.graph_objects as go
from plotly.subplots import make_subplots
import seaborn as sns
import matplotlib.pyplot as plt
from datetime import datetime

# ページ設定
st.set_page_config(
    page_title="日本の人口動態100年史 - 高齢化社会分析ダッシュボード",
    page_icon="📊",
    layout="wide",
    initial_sidebar_state="expanded"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 2.5rem;
        font-weight: bold;
        color: #1f77b4;
        text-align: center;
        margin-bottom: 1rem;
    }
    .sub-header {
        font-size: 1.5rem;
        color: #ff7f0e;
        margin-top: 2rem;
        margin-bottom: 1rem;
    }
    .metric-card {
        background-color: #f0f2f6;
        padding: 1rem;
        border-radius: 0.5rem;
        margin: 0.5rem 0;
    }
    .insight-box {
        background-color: #e1f5fe;
        padding: 1rem;
        border-left: 4px solid #2196f3;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

@st.cache_data
def load_data():
    """データの読み込み（キャッシュ付き）"""
    try:
        # 前処理済みデータの読み込み
        df_analysis = pd.read_csv('census_analysis_data.csv')
        aging_indicators = pd.read_csv('aging_indicators.csv')
        return df_analysis, aging_indicators
    except FileNotFoundError:
        st.error("データファイルが見つかりません。事前にデータ前処理を実行してください。")
        return None, None

def create_aging_trend_chart(aging_indicators):
    """高齢化率推移チャート"""
    # 全国平均を計算
    national_avg = aging_indicators.groupby('年')['高齢化率'].mean().reset_index()
    
    fig = go.Figure()
    
    # 主要都道府県の高齢化率推移
    major_prefs = ['東京都', '大阪府', '愛知県', '北海道', '沖縄県', '秋田県']
    colors = px.colors.qualitative.Set1
    
    for i, pref in enumerate(major_prefs):
        pref_data = aging_indicators[aging_indicators['都道府県名'] == pref]
        if not pref_data.empty:
            fig.add_trace(go.Scatter(
                x=pref_data['年'],
                y=pref_data['高齢化率'],
                mode='lines+markers',
                name=pref,
                line=dict(color=colors[i], width=2),
                marker=dict(size=6)
            ))
    
    # 全国平均
    fig.add_trace(go.Scatter(
        x=national_avg['年'],
        y=national_avg['高齢化率'],
        mode='lines+markers',
        name='全国平均',
        line=dict(color='black', width=3, dash='dash'),
        marker=dict(size=8)
    ))
    
    # 重要な社会節目を追加
    milestones = [
        (1970, "高齢化社会(7%)"),
        (1994, "高齢社会(14%)"),
        (2007, "超高齢社会(21%)")
    ]
    
    for year, label in milestones:
        fig.add_vline(x=year, line_dash="dot", line_color="red", 
                     annotation_text=label, annotation_position="top")
    
    fig.update_layout(
        title="日本の高齢化率推移（1920-2020年）",
        xaxis_title="年",
        yaxis_title="高齢化率（%）",
        hovermode='x unified',
        height=500
    )
    
    return fig

def create_population_pyramid(df_analysis, selected_year, selected_pref):
    """人口ピラミッド作成"""
    # 特定年・都道府県のデータを抽出
    data = df_analysis[
        (df_analysis['年'] == selected_year) & 
        (df_analysis['都道府県名'] == selected_pref)
    ].copy()
    
    # 年齢区分を整理
    age_groups = ['0～4歳', '5～9歳', '10～14歳', '15～19歳', '20～24歳', 
                  '25～29歳', '30～34歳', '35～39歳', '40～44歳', '45～49歳',
                  '50～54歳', '55～59歳', '60～64歳', '65～69歳', '70～74歳',
                  '75～79歳', '80～84歳', '85歳以上']
    
    data = data[data['年齢区分'].isin(age_groups)]
    
    if data.empty:
        return go.Figure().add_annotation(text="データがありません", 
                                        xref="paper", yref="paper",
                                        x=0.5, y=0.5, showarrow=False)
    
    # 男女別データの準備
    male_pop = -data['男性人口'].fillna(0)  # 左側（負の値）
    female_pop = data['女性人口'].fillna(0)  # 右側（正の値）
    
    fig = go.Figure()
    
    # 男性（左側）
    fig.add_trace(go.Bar(
        y=data['年齢区分'],
        x=male_pop,
        name='男性',
        orientation='h',
        marker=dict(color='lightblue'),
        text=data['男性人口'].fillna(0),
        textposition='inside'
    ))
    
    # 女性（右側）
    fig.add_trace(go.Bar(
        y=data['年齢区分'],
        x=female_pop,
        name='女性',
        orientation='h',
        marker=dict(color='pink'),
        text=data['女性人口'].fillna(0),
        textposition='inside'
    ))
    
    fig.update_layout(
        title=f"{selected_pref} - {selected_year}年 人口ピラミッド",
        xaxis_title="人口（人）",
        yaxis_title="年齢階級",
        barmode='relative',
        height=600,
        yaxis=dict(categoryorder='array', categoryarray=age_groups[::-1])
    )
    
    return fig

def create_regional_heatmap(aging_indicators, selected_year):
    """地域別高齢化率ヒートマップ"""
    year_data = aging_indicators[aging_indicators['年'] == selected_year]
    
    fig = px.choropleth(
        year_data,
        locations='都道府県名',
        color='高齢化率',
        locationmode='geojson-id',
        color_continuous_scale='Reds',
        title=f"{selected_year}年 都道府県別高齢化率"
    )
    
    # 日本地図のジオメトリは実際の実装では外部ファイルを使用
    fig.update_layout(height=500)
    
    return fig

def display_key_insights(aging_indicators):
    """重要な洞察の表示"""
    st.markdown('<div class="sub-header">🔍 データから見える重要な洞察</div>', 
                unsafe_allow_html=True)
    
    # 最新年のデータ
    latest_year = aging_indicators['年'].max()
    latest_data = aging_indicators[aging_indicators['年'] == latest_year]
    
    # 最高・最低高齢化率
    max_aging = latest_data.loc[latest_data['高齢化率'].idxmax()]
    min_aging = latest_data.loc[latest_data['高齢化率'].idxmin()]
    
    col1, col2, col3 = st.columns(3)
    
    with col1:
        st.markdown(f"""
        <div class="insight-box">
        <h4>🔴 最高高齢化率</h4>
        <p><strong>{max_aging['都道府県名']}</strong></p>
        <p>{max_aging['高齢化率']:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col2:
        st.markdown(f"""
        <div class="insight-box">
        <h4>🔵 最低高齢化率</h4>
        <p><strong>{min_aging['都道府県名']}</strong></p>
        <p>{min_aging['高齢化率']:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)
    
    with col3:
        national_avg = latest_data['高齢化率'].mean()
        st.markdown(f"""
        <div class="insight-box">
        <h4>📊 全国平均</h4>
        <p><strong>高齢化率</strong></p>
        <p>{national_avg:.1f}%</p>
        </div>
        """, unsafe_allow_html=True)

def main():
    """メイン関数"""
    st.markdown('<div class="main-header">🏥 日本の人口動態100年史</div>', 
                unsafe_allow_html=True)
    st.markdown('<div class="main-header">高齢化社会における医療需要予測ダッシュボード</div>', 
                unsafe_allow_html=True)
    
    # データ読み込み
    df_analysis, aging_indicators = load_data()
    
    if df_analysis is None:
        st.stop()
    
    # サイドバー
    st.sidebar.header("📋 分析設定")
    
    # 年選択
    available_years = sorted(aging_indicators['年'].unique())
    selected_year = st.sidebar.selectbox(
        "分析年を選択",
        available_years,
        index=len(available_years)-1  # 最新年をデフォルト
    )
    
    # 都道府県選択
    available_prefs = sorted(df_analysis['都道府県名'].unique())
    selected_pref = st.sidebar.selectbox(
        "都道府県を選択",
        available_prefs,
        index=available_prefs.index('東京都') if '東京都' in available_prefs else 0
    )
    
    # 分析タイプ選択
    analysis_type = st.sidebar.radio(
        "分析タイプ",
        ["📈 高齢化推移分析", "👥 人口ピラミッド", "🗾 地域比較", "🔮 将来予測"]
    )
    
    # メインコンテンツ
    if analysis_type == "📈 高齢化推移分析":
        st.plotly_chart(create_aging_trend_chart(aging_indicators), 
                       use_container_width=True)
        
        # 重要な洞察
        display_key_insights(aging_indicators)
        
        # 詳細データテーブル
        with st.expander("📊 詳細データを見る"):
            st.dataframe(aging_indicators[aging_indicators['年'] == selected_year])
    
    elif analysis_type == "👥 人口ピラミッド":
        st.plotly_chart(create_population_pyramid(df_analysis, selected_year, selected_pref), 
                       use_container_width=True)
        
        # 比較年の追加
        st.markdown("### 📊 時代比較")
        comparison_years = st.multiselect(
            "比較する年を選択",
            available_years,
            default=[1980, 2000, 2020] if all(y in available_years for y in [1980, 2000, 2020]) else available_years[-3:]
        )
        
        if len(comparison_years) > 1:
            cols = st.columns(len(comparison_years))
            for i, year in enumerate(comparison_years):
                with cols[i]:
                    mini_fig = create_population_pyramid(df_analysis, year, selected_pref)
                    mini_fig.update_layout(height=400, title=f"{year}年")
                    st.plotly_chart(mini_fig, use_container_width=True)
    
    elif analysis_type == "🗾 地域比較":
        # 都道府県ランキング
        year_data = aging_indicators[aging_indicators['年'] == selected_year].copy()
        year_data = year_data.sort_values('高齢化率', ascending=False)
        
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown("### 🔴 高齢化率 TOP10")
            top10 = year_data.head(10)
            fig_top = px.bar(
                top10,
                x='高齢化率',
                y='都道府県名',
                orientation='h',
                color='高齢化率',
                color_continuous_scale='Reds'
            )
            fig_top.update_layout(height=400)
            st.plotly_chart(fig_top, use_container_width=True)
        
        with col2:
            st.markdown("### 🔵 高齢化率 BOTTOM10")
            bottom10 = year_data.tail(10)
            fig_bottom = px.bar(
                bottom10,
                x='高齢化率',
                y='都道府県名',
                orientation='h',
                color='高齢化率',
                color_continuous_scale='Blues'
            )
            fig_bottom.update_layout(height=400)
            st.plotly_chart(fig_bottom, use_container_width=True)
    
    elif analysis_type == "🔮 将来予測":
        st.markdown("### 🔮 2040年医療需要予測")
        
        # 簡単な線形予測モデル
        recent_data = aging_indicators[aging_indicators['年'] >= 2000]
        
        # 都道府県別の高齢化率トレンド
        projection_data = []
        for pref in recent_data['都道府県名'].unique():
            pref_data = recent_data[recent_data['都道府県名'] == pref]
            if len(pref_data) >= 3:  # 最低3データポイント必要
                # 線形回帰で2040年を予測
                x = pref_data['年'].values
                y = pref_data['高齢化率'].values
                
                # 簡単な線形予測
                trend = np.polyfit(x, y, 1)
                predicted_2040 = np.polyval(trend, 2040)
                
                projection_data.append({
                    '都道府県名': pref,
                    '2020年高齢化率': pref_data[pref_data['年'] == 2020]['高齢化率'].iloc[0] if len(pref_data[pref_data['年'] == 2020]) > 0 else None,
                    '2040年予測高齢化率': max(0, min(100, predicted_2040)),  # 0-100%の範囲に制限
                    '医療需要増加率': max(0, min(100, predicted_2040)) / pref_data[pref_data['年'] == 2020]['高齢化率'].iloc[0] * 100 - 100 if len(pref_data[pref_data['年'] == 2020]) > 0 else 0
                })
        
        projection_df = pd.DataFrame(projection_data)
        
        if not projection_df.empty:
            # 予測結果の可視化
            fig_projection = px.scatter(
                projection_df,
                x='2020年高齢化率',
                y='2040年予測高齢化率',
                hover_data=['都道府県名'],
                title="2040年高齢化率予測 vs 2020年実績",
                labels={'2020年高齢化率': '2020年高齢化率（%）', '2040年予測高齢化率': '2040年予測高齢化率（%）'}
            )
            
            # 対角線を追加（変化なしライン）
            fig_projection.add_shape(
                type="line",
                x0=0, y0=0, x1=50, y1=50,
                line=dict(dash="dash", color="red"),
                name="変化なしライン"
            )
            
            st.plotly_chart(fig_projection, use_container_width=True)
            
            # 医療需要が最も増加する地域
            top_increase = projection_df.nlargest(5, '医療需要増加率')
            
            st.markdown("### 🚨 医療需要増加率 TOP5")
            for idx, row in top_increase.iterrows():
                st.markdown(f"""
                **{row['都道府県名']}**: {row['医療需要増加率']:.1f}%増加予測  
                （{row['2020年高齢化率']:.1f}% → {row['2040年予測高齢化率']:.1f}%）
                """)
    
    # フッター
    st.markdown("---")
    st.markdown("""
    **データソース**: 国勢調査（総務省統計局）時系列データ  
    **分析期間**: 1920年（大正9年）～2020年（令和2年）  
    **作成者**: 医療従事者（作業療法士）によるデータ分析
    """)

if __name__ == "__main__":
    main()

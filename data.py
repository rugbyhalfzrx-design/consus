import streamlit as st
import pandas as pd
import numpy as np
import matplotlib.pyplot as plt
import seaborn as sns
from io import BytesIO
import base64

# ページ設定
st.set_page_config(
    page_title="Excel自動可視化ツール",
    page_icon="📊",
    layout="wide"
)

# カスタムCSS
st.markdown("""
<style>
    .main-header {
        font-size: 3rem;
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
        background-color: #e8f5e8;
        padding: 1rem;
        border-left: 4px solid #4caf50;
        margin: 1rem 0;
    }
</style>
""", unsafe_allow_html=True)

def detect_data_types(df):
    """データ型を自動検出"""
    numeric_cols = df.select_dtypes(include=[np.number]).columns.tolist()
    categorical_cols = df.select_dtypes(include=['object']).columns.tolist()
    datetime_cols = df.select_dtypes(include=['datetime64']).columns.tolist()
    
    # 文字列から日付に変換可能な列を検出
    for col in categorical_cols[:]:
        if df[col].dtype == 'object':
            try:
                pd.to_datetime(df[col].dropna().head(100))
                datetime_cols.append(col)
                categorical_cols.remove(col)
            except:
                pass
    
    return numeric_cols, categorical_cols, datetime_cols

def auto_clean_data(df):
    """データの自動クリーニング"""
    original_shape = df.shape
    
    # 1. 完全に空の行・列を削除
    df = df.dropna(how='all').dropna(axis=1, how='all')
    
    # 2. 数値列の文字列を数値に変換
    for col in df.columns:
        if df[col].dtype == 'object':
            # カンマ区切りの数値を変換
            try:
                df[col] = pd.to_numeric(df[col].astype(str).str.replace(',', ''), errors='ignore')
            except:
                pass
    
    # 3. 日付列の変換
    for col in df.columns:
        if df[col].dtype == 'object':
            try:
                df[col] = pd.to_datetime(df[col], errors='ignore')
            except:
                pass
    
    cleaned_shape = df.shape
    
    return df, original_shape, cleaned_shape

def create_summary_stats(df):
    """基本統計量の表示"""
    st.subheader("📋 データの基本情報")
    
    col1, col2, col3, col4 = st.columns(4)
    
    with col1:
        st.metric("行数", f"{df.shape[0]:,}")
    with col2:
        st.metric("列数", f"{df.shape[1]:,}")
    with col3:
        st.metric("欠損値", f"{df.isnull().sum().sum():,}")
    with col4:
        memory_usage = df.memory_usage(deep=True).sum() / 1024**2
        st.metric("データサイズ", f"{memory_usage:.1f} MB")
    
    # データ型の分布
    st.subheader("📊 データ型の分布")
    
    numeric_cols, categorical_cols, datetime_cols = detect_data_types(df)
    
    col1, col2, col3 = st.columns(3)
    with col1:
        st.write(f"**数値列**: {len(numeric_cols)}列")
        if numeric_cols:
            st.write(", ".join(numeric_cols[:5]) + ("..." if len(numeric_cols) > 5 else ""))
    
    with col2:
        st.write(f"**カテゴリ列**: {len(categorical_cols)}列")
        if categorical_cols:
            st.write(", ".join(categorical_cols[:5]) + ("..." if len(categorical_cols) > 5 else ""))
    
    with col3:
        st.write(f"**日付列**: {len(datetime_cols)}列")
        if datetime_cols:
            st.write(", ".join(datetime_cols[:5]) + ("..." if len(datetime_cols) > 5 else ""))

def auto_visualize_numeric(df, numeric_cols):
    """数値データの自動可視化"""
    if not numeric_cols:
        return
    
    st.subheader("📈 数値データの可視化")
    
    # 1. 基本統計量
    st.write("**基本統計量**")
    st.dataframe(df[numeric_cols].describe())
    
    # 2. ヒストグラム（最大6列まで）
    if len(numeric_cols) > 0:
        st.write("**分布の確認（ヒストグラム）**")
        
        # 表示する列数を調整
        cols_to_plot = numeric_cols[:6]  # 最大6列
        n_cols = min(3, len(cols_to_plot))
        n_rows = (len(cols_to_plot) + n_cols - 1) // n_cols
        
        fig, axes = plt.subplots(n_rows, n_cols, figsize=(15, 5*n_rows))
        if n_rows == 1:
            axes = [axes] if n_cols == 1 else axes
        else:
            axes = axes.flatten()
        
        for i, col in enumerate(cols_to_plot):
            axes[i].hist(df[col].dropna(), bins=30, alpha=0.7, color='skyblue', edgecolor='black')
            axes[i].set_title(f'{col}の分布')
            axes[i].set_xlabel(col)
            axes[i].set_ylabel('頻度')
            axes[i].grid(True, alpha=0.3)
        
        # 余ったサブプロットを非表示
        for i in range(len(cols_to_plot), len(axes)):
            axes[i].set_visible(False)
        
        plt.tight_layout()
        st.pyplot(fig)
    
    # 3. 相関分析（数値列が2つ以上ある場合）
    if len(numeric_cols) >= 2:
        st.write("**相関分析**")
        
        # 相関行列
        corr_matrix = df[numeric_cols].corr()
        
        fig, ax = plt.subplots(figsize=(10, 8))
        sns.heatmap(corr_matrix, annot=True, cmap='coolwarm', center=0,
                   square=True, linewidths=0.5, ax=ax)
        ax.set_title('相関行列')
        st.pyplot(fig)
        
        # 最も相関の高いペア
        corr_pairs = []
        for i in range(len(corr_matrix.columns)):
            for j in range(i+1, len(corr_matrix.columns)):
                corr_value = corr_matrix.iloc[i, j]
                if abs(corr_value) > 0.5:  # 相関係数の絶対値が0.5以上
                    corr_pairs.append({
                        '変数1': corr_matrix.columns[i],
                        '変数2': corr_matrix.columns[j],
                        '相関係数': round(corr_value, 3)
                    })
        
        if corr_pairs:
            st.write("**強い相関を持つ変数ペア**")
            corr_df = pd.DataFrame(corr_pairs)
            corr_df = corr_df.sort_values('相関係数', key=abs, ascending=False)
            st.dataframe(corr_df)

def auto_visualize_categorical(df, categorical_cols):
    """カテゴリデータの自動可視化"""
    if not categorical_cols:
        return
    
    st.subheader("📊 カテゴリデータの可視化")
    
    # カテゴリごとの分析（最大4列まで）
    cols_to_analyze = categorical_cols[:4]
    
    for col in cols_to_analyze:
        st.write(f"**{col} の分析**")
        
        # 値のカウント
        value_counts = df[col].value_counts().head(10)  # 上位10件
        
        if len(value_counts) > 0:
            col1, col2 = st.columns(2)
            
            with col1:
                # 棒グラフ
                fig, ax = plt.subplots(figsize=(8, 6))
                value_counts.plot(kind='bar', ax=ax, color='lightcoral')
                ax.set_title(f'{col} の分布')
                ax.set_xlabel(col)
                ax.set_ylabel('件数')
                ax.tick_params(axis='x', rotation=45)
                plt.tight_layout()
                st.pyplot(fig)
            
            with col2:
                # 円グラフ（カテゴリが少ない場合）
                if len(value_counts) <= 8:
                    fig, ax = plt.subplots(figsize=(8, 6))
                    ax.pie(value_counts.values, labels=value_counts.index, autopct='%1.1f%%')
                    ax.set_title(f'{col} の構成比')
                    st.pyplot(fig)
                else:
                    # テーブル表示
                    st.write("**上位10件の詳細**")
                    summary_df = pd.DataFrame({
                        col: value_counts.index,
                        '件数': value_counts.values,
                        '割合(%)': (value_counts.values / len(df) * 100).round(1)
                    })
                    st.dataframe(summary_df)

def auto_visualize_time_series(df, datetime_cols, numeric_cols):
    """時系列データの自動可視化"""
    if not datetime_cols or not numeric_cols:
        return
    
    st.subheader("📅 時系列データの可視化")
    
    # 日付列を選択（最初の日付列を使用）
    date_col = datetime_cols[0]
    
    st.write(f"**{date_col} を基準とした時系列分析**")
    
    # 数値列から選択可能なものを表示
    selected_numeric_cols = st.multiselect(
        "可視化する数値列を選択してください",
        numeric_cols,
        default=numeric_cols[:3]  # 最大3列をデフォルト選択
    )
    
    if selected_numeric_cols:
        # 日付でソート
        df_sorted = df.sort_values(date_col)
        
        fig, ax = plt.subplots(figsize=(12, 6))
        
        for col in selected_numeric_cols:
            ax.plot(df_sorted[date_col], df_sorted[col], 
                   marker='o', linewidth=2, label=col, alpha=0.8)
        
        ax.set_xlabel(date_col)
        ax.set_ylabel('値')
        ax.set_title('時系列推移')
        ax.legend()
        ax.grid(True, alpha=0.3)
        
        # x軸の日付表示を調整
        plt.xticks(rotation=45)
        plt.tight_layout()
        st.pyplot(fig)

def suggest_analysis_insights(df, numeric_cols, categorical_cols, datetime_cols):
    """分析の洞察と提案"""
    st.subheader("💡 分析の洞察と提案")
    
    insights = []
    
    # データ品質の評価
    missing_rate = (df.isnull().sum().sum() / (df.shape[0] * df.shape[1])) * 100
    if missing_rate > 10:
        insights.append(f"⚠️ データの欠損率が{missing_rate:.1f}%と高いです。データクリーニングを検討してください。")
    elif missing_rate < 1:
        insights.append(f"✅ データの品質は良好です（欠損率: {missing_rate:.1f}%）。")
    
    # 数値データの分析提案
    if len(numeric_cols) >= 2:
        insights.append(f"📊 {len(numeric_cols)}個の数値列があります。相関分析や回帰分析が可能です。")
        
        # 分散の大きい列を特定
        high_variance_cols = []
        for col in numeric_cols:
            if df[col].std() / df[col].mean() > 1:  # 変動係数が1以上
                high_variance_cols.append(col)
        
        if high_variance_cols:
            insights.append(f"📈 {', '.join(high_variance_cols[:3])} は変動が大きいです。外れ値の確認を推奨します。")
    
    # カテゴリデータの分析提案
    if len(categorical_cols) >= 1:
        insights.append(f"🏷️ {len(categorical_cols)}個のカテゴリ列があります。グループ別分析が可能です。")
        
        # ユニーク値が少ないカテゴリ列を特定
        low_cardinality_cols = []
        for col in categorical_cols:
            unique_rate = df[col].nunique() / len(df)
            if unique_rate < 0.1:  # ユニーク率が10%未満
                low_cardinality_cols.append(col)
        
        if low_cardinality_cols:
            insights.append(f"📂 {', '.join(low_cardinality_cols[:3])} はカテゴリ数が少なく、グループ分析に適しています。")
    
    # 時系列データの分析提案
    if datetime_cols:
        insights.append(f"📅 時系列データが検出されました。トレンド分析や予測分析が可能です。")
    
    # 洞察の表示
    for insight in insights:
        st.markdown(f"""
        <div class="insight-box">
        {insight}
        </div>
        """, unsafe_allow_html=True)

def create_download_section(df):
    """分析結果のダウンロード機能"""
    st.subheader("💾 分析結果のダウンロード")
    
    col1, col2 = st.columns(2)
    
    with col1:
        # クリーニング済みデータのダウンロード
        csv = df.to_csv(index=False, encoding='utf-8')
        st.download_button(
            label="📥 クリーニング済みデータ（CSV）",
            data=csv,
            file_name="cleaned_data.csv",
            mime="text/csv"
        )
    
    with col2:
        # 基本統計量のダウンロード
        numeric_cols, _, _ = detect_data_types(df)
        if numeric_cols:
            stats = df[numeric_cols].describe()
            stats_csv = stats.to_csv(encoding='utf-8')
            st.download_button(
                label="📊 基本統計量（CSV）",
                data=stats_csv,
                file_name="basic_statistics.csv",
                mime="text/csv"
            )

def main():
    """メイン関数"""
    
    # タイトル
    st.markdown('<div class="main-header">📊 Excel自動可視化ツール</div>', 
                unsafe_allow_html=True)
    
    st.markdown("""
    <div style="text-align: center; font-size: 1.2rem; margin-bottom: 2rem; color: #666;">
    Excelファイルをアップロードするだけで、自動的にデータを分析・可視化します
    </div>
    """, unsafe_allow_html=True)
    
    # サイドバー
    st.sidebar.header("🎛️ 設定")
    
    # ファイルアップロード
    uploaded_file = st.sidebar.file_uploader(
        "📁 Excelファイルをアップロード",
        type=['xlsx', 'xls'],
        help="Excel形式のファイルをアップロードしてください"
    )
    
    # シート選択（ファイルがアップロードされた場合）
    sheet_name = None
    if uploaded_file is not None:
        try:
            excel_file = pd.ExcelFile(uploaded_file)
            sheet_names = excel_file.sheet_names
            
            if len(sheet_names) > 1:
                sheet_name = st.sidebar.selectbox(
                    "📋 分析するシートを選択",
                    sheet_names
                )
            else:
                sheet_name = sheet_names[0]
                
        except Exception as e:
            st.error(f"ファイル読み込みエラー: {e}")
            return
    
    # 可視化オプション
    st.sidebar.subheader("📊 可視化オプション")
    
    show_data_summary = st.sidebar.checkbox("データサマリー表示", value=True)
    show_numeric_viz = st.sidebar.checkbox("数値データ可視化", value=True)
    show_categorical_viz = st.sidebar.checkbox("カテゴリデータ可視化", value=True)
    show_time_series_viz = st.sidebar.checkbox("時系列データ可視化", value=True)
    show_insights = st.sidebar.checkbox("分析の洞察表示", value=True)
    
    # メインコンテンツ
    if uploaded_file is not None:
        try:
            # データ読み込み
            with st.spinner("📊 データを読み込んでいます..."):
                df = pd.read_excel(uploaded_file, sheet_name=sheet_name)
                
                # データクリーニング
                df, original_shape, cleaned_shape = auto_clean_data(df)
            
            st.success(f"✅ データ読み込み完了！（{original_shape[0]}→{cleaned_shape[0]}行, {original_shape[1]}→{cleaned_shape[1]}列）")
            
            # データの型検出
            numeric_cols, categorical_cols, datetime_cols = detect_data_types(df)
            
            # データプレビュー
            with st.expander("👀 データプレビュー", expanded=False):
                st.dataframe(df.head(100))
            
            # 分析実行
            if show_data_summary:
                create_summary_stats(df)
            
            if show_numeric_viz and numeric_cols:
                auto_visualize_numeric(df, numeric_cols)
            
            if show_categorical_viz and categorical_cols:
                auto_visualize_categorical(df, categorical_cols)
            
            if show_time_series_viz and datetime_cols and numeric_cols:
                auto_visualize_time_series(df, datetime_cols, numeric_cols)
            
            if show_insights:
                suggest_analysis_insights(df, numeric_cols, categorical_cols, datetime_cols)
            
            # ダウンロードセクション
            create_download_section(df)
            
        except Exception as e:
            st.error(f"❌ エラーが発生しました: {e}")
            st.info("ファイル形式やデータ構造を確認してください。")
    
    else:
        # サンプルデータでのデモ
        st.info("👆 サイドバーからExcelファイルをアップロードして分析を開始してください")
        
        # デモボタン
        if st.button("🎯 サンプルデータでデモを見る"):
            # サンプルデータ作成
            np.random.seed(42)
            sample_data = {
                '日付': pd.date_range('2020-01-01', periods=100, freq='D'),
                '売上金額': np.random.normal(100000, 20000, 100),
                '訪問者数': np.random.poisson(50, 100),
                '地域': np.random.choice(['東京', '大阪', '名古屋', '福岡'], 100),
                '商品カテゴリ': np.random.choice(['A', 'B', 'C', 'D'], 100),
                '評価': np.random.uniform(1, 5, 100)
            }
            
            df = pd.DataFrame(sample_data)
            
            st.success("✅ サンプルデータで分析を実行中...")
            
            # サンプルデータの分析
            numeric_cols, categorical_cols, datetime_cols = detect_data_types(df)
            
            create_summary_stats(df)
            auto_visualize_numeric(df, numeric_cols)
            auto_visualize_categorical(df, categorical_cols)
            auto_visualize_time_series(df, datetime_cols, numeric_cols)
            suggest_analysis_insights(df, numeric_cols, categorical_cols, datetime_cols)
        
        # 使い方ガイド
        with st.expander("📖 使い方ガイド", expanded=False):
            st.markdown("""
            ### 🎯 このツールについて
            
            Excel自動可視化ツールは、アップロードされたExcelファイルを自動的に分析し、
            適切なグラフや統計情報を生成するWebアプリケーションです。
            
            ### 📊 自動生成される分析
            
            1. **データサマリー**: 行数、列数、欠損値の状況
            2. **数値データ可視化**: ヒストグラム、相関分析
            3. **カテゴリデータ可視化**: 棒グラフ、円グラフ
            4. **時系列分析**: トレンドグラフ
            5. **分析の洞察**: データの特徴と改善提案
            
            ### 🔧 対応データ形式
            
            - Excel形式（.xlsx, .xls）
            - 複数シート対応
            - 自動データクリーニング
            - 日本語データ対応
            
            ### 💡 活用例
            
            - **売上データ分析**: 月次売上、地域別分析
            - **顧客データ分析**: 年齢分布、購入履歴
            - **在庫データ分析**: 商品別在庫推移
            - **アンケート分析**: 回答分布、満足度分析
            """)
    
    # フッター
    st.markdown("---")
    st.markdown("""
    <div style="text-align: center; color: #666; font-size: 0.9rem;">
    📊 <strong>Excel自動可視化ツール</strong><br>
    データ分析を誰でも簡単に | 作成: データサイエンティスト候補
    </div>
    """, unsafe_allow_html=True)

if __name__ == "__main__":
    main()

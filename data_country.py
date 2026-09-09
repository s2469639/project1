import base64
from pathlib import Path
import matplotlib.font_manager as fm
import numpy as np
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import streamlit as st

# ==========================================
# 0. 페이지 설정 (문서 아이콘 적용)
# ==========================================
st.set_page_config(
    page_title="무역 분석 대시보드",
    page_icon="📄",
    layout="wide",
)

# 현재 스크립트 기준 상대 경로 설정
BASE_DIR = Path(__file__).resolve().parent
BACI_FILE = BASE_DIR / "baci_85_sample.csv"
COUNTRY_FILE = BASE_DIR / "country_codes_sample.csv"
ATOZ_FONT = BASE_DIR / "에이투지체-7Bold.ttf"
NANUM_FONT = BASE_DIR / "NanumGothic.ttf"
BG_IMAGE = BASE_DIR / "wave.jpg"
CURSOR_IMAGE = BASE_DIR / "2.png"

# ==========================================
# 1. 리소스(폰트, 배경 이미지, 커서) Base64 변환
# ==========================================
# 1-1. 제목 폰트 인코딩
title_font_css = ""
if ATOZ_FONT.exists():
    with open(ATOZ_FONT, "rb") as f:
        font_b64 = base64.b64encode(f.read()).decode("utf-8")
    title_font_css = f"""
    @font-face {{
        font-family: 'AtoZBold';
        src: url(data:font/truetype;charset=utf-8;base64,{font_b64}) format('truetype');
        font-weight: bold;
        font-style: normal;
    }}
    """
    fm.fontManager.addfont(str(ATOZ_FONT))
else:
    title_font_css = """
    @font-face {
        font-family: 'AtoZBold';
        src: local('에이투지체-7Bold'), local('에이투지체'), local('AtoZ-7Bold');
    }
    """

# 본문 폰트 설정
if NANUM_FONT.exists():
    fm.fontManager.addfont(str(NANUM_FONT))
    plt.rcParams["font.family"] = "NanumGothic"
else:
    plt.rcParams["font.family"] = "Malgun Gothic"

plt.rcParams["axes.unicode_minus"] = False

# 1-2. 배경화면 wave.jpg (투명도 50%)
bg_css = ""
if BG_IMAGE.exists():
    with open(BG_IMAGE, "rb") as f:
        bg_b64 = base64.b64encode(f.read()).decode("utf-8")
    bg_css = f"""
    /* 배경 이미지를 가상 요소로 본문 뒤에 깔고 투명도 0.5 적용 */
    .stApp::before {{
        content: "";
        position: fixed;
        top: 0;
        left: 0;
        width: 100vw;
        height: 100vh;
        background-image: url('data:image/jpeg;base64,{bg_b64}');
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        opacity: 0.5;
        z-index: -1;
        pointer-events: none;
    }}
    /* 기본 배경색 투명화 */
    .stApp {{
        background-color: transparent !important;
    }}
    """

# 1-3. 마우스 커서 2.png
cursor_css = ""
if CURSOR_IMAGE.exists():
    with open(CURSOR_IMAGE, "rb") as f:
        cursor_b64 = base64.b64encode(f.read()).decode("utf-8")
    cursor_url = f"data:image/png;base64,{cursor_b64}"
    cursor_css = f"""
    /* 전체 화면 및 주요 클릭 요소에 커서 강제 적용 */
    html, body, .stApp, * {{
        cursor: url('{cursor_url}'), auto !important;
    }}
    button, a, select, input, [role="button"], .stSelectbox, .stMultiSelect {{
        cursor: url('{cursor_url}'), pointer !important;
    }}
    """

# 스타일 CSS 통합 주입
st.markdown(
    f"""
    <style>
    {title_font_css}
    {bg_css}
    {cursor_css}
    
    /* 기본 본문 */
    html, body, [class*="css"], div, p, span, label {{
        font-family: 'NanumGothic', 'Malgun Gothic', sans-serif;
        color: #2F3E35;
    }}
    
    /* 제목 전용 클래스 (에이투지체-7Bold) */
    .atoz-title {{
        font-family: 'AtoZBold', sans-serif !important;
        color: #244F3A !important;
        font-size: 2.7rem !important;
        font-weight: bold !important;
        line-height: 1.3 !important;
        margin: 0 !important;
        padding-top: 8px !important;
        padding-bottom: 4px !important;
        display: block !important;
        letter-spacing: -0.5px;
    }}
    
    h2, h3 {{
        color: #38644D !important;
        font-weight: 600;
    }}
    
    /* 사이드바 파스텔 반투명 배경 */
    [data-testid="stSidebar"] {{
        background-color: rgba(242, 247, 244, 0.9) !important;
    }}
    
    /* 지표(Metric) 스타일 */
    [data-testid="stMetricValue"] {{
        color: #244F3A !important;
        font-weight: 700;
    }}
    </style>
    """,
    unsafe_allow_html=True,
)


# ==========================================
# 2. 데이터 불러오기 및 전처리
# ==========================================
@st.cache_data
def load_data():
    baci_df = pd.read_csv(BACI_FILE)
    country_df = pd.read_csv(COUNTRY_FILE)

    # 수입국(j) 코드 매핑
    merged_df = pd.merge(
        baci_df, country_df[["j", "country_name"]], on="j", how="left"
    )
    merged_df["country_name"] = merged_df["country_name"].fillna("Unknown")

    # 무역액(v) 분위수 기준 등급(소, 중, 대) 구분
    q_low = merged_df["v"].quantile(0.33)
    q_high = merged_df["v"].quantile(0.66)

    conditions = [
        merged_df["v"] <= q_low,
        (merged_df["v"] > q_low) & (merged_df["v"] <= q_high),
        merged_df["v"] > q_high,
    ]
    choices = ["소", "중", "대"]
    merged_df["trade_grade"] = np.select(conditions, choices, default="중")

    return baci_df, merged_df


baci_raw, df = load_data()

# ==========================================
# 3. 사이드바 필터 (국가 다중 필터 & 무역액 등급)
# ==========================================
st.sidebar.header("🔍 필터 옵션")

# 국가 다중 선택 필터
country_options = sorted(df["country_name"].dropna().unique().tolist())
selected_countries = st.sidebar.multiselect(
    "국가 선택 (다중 필터)",
    options=country_options,
    default=country_options,
    placeholder="분석할 국가를 선택하세요",
)

# 무역액 등급 선택 (대, 중, 소)
grade_options = ["대", "중", "소"]
selected_grades = st.sidebar.multiselect(
    "무역액 등급 선택",
    options=grade_options,
    default=grade_options,
    placeholder="무역액 등급을 선택하세요",
)

# 필터링 적용
filtered_df = df.copy()

if selected_grades:
    filtered_df = filtered_df[filtered_df["trade_grade"].isin(selected_grades)]
else:
    filtered_df = filtered_df.iloc[0:0]

if selected_countries:
    filtered_df = filtered_df[
        filtered_df["country_name"].isin(selected_countries)
    ]
else:
    filtered_df = filtered_df.iloc[0:0]

# ==========================================
# 4. 메인 화면 구성
# ==========================================

# 1. 화면 타이틀
st.markdown(
    '<div class="atoz-title">무역 분석 대시보드</div>', unsafe_allow_html=True
)

if len(selected_countries) == len(country_options):
    country_display = "전체 국가"
elif len(selected_countries) > 3:
    country_display = f"{selected_countries[0]} 외 {len(selected_countries)-1}개국"
elif selected_countries:
    country_display = ", ".join(selected_countries)
else:
    country_display = "선택 없음"

st.caption(
    f"📍 현재 필터: **국가: {country_display}** | **무역액 등급: {', '.join(selected_grades) if selected_grades else '선택 없음'}** (조회 건수: {len(filtered_df):,}건)"
)
st.write("---")

# 2. 결측치 현황
st.subheader("1. 데이터 결측치 현황 (baci_85_sample.csv)")
null_counts = baci_raw.isnull().sum()
null_df = pd.DataFrame(
    {
        "컬럼": null_counts.index,
        "결측치 수": null_counts.values,
        "결측률(%)": (null_counts.values / len(baci_raw) * 100).round(2),
    }
)
st.dataframe(null_df, use_container_width=True, hide_index=True)

# 3. 주요 거래 지표
st.subheader("2. 주요 거래 지표")
col_m1, col_m2 = st.columns(2)

total_trades = len(filtered_df)
total_export_value = filtered_df["v"].sum() if not filtered_df.empty else 0.0

with col_m1:
    st.metric(label="총 거래 건수", value=f"{total_trades:,} 건")
with col_m2:
    st.metric(
        label="총 수출액 (USD)",
        value=f"${total_export_value:,.2f}",
    )

st.write("---")

# 4. 반응형 시각화 분석 (Plotly 기반)
st.subheader("3. 무역 시각화 분석")
c_col1, c_col2 = st.columns([1.3, 0.7])

with c_col1:
    st.markdown("**국가 × 연도 수출액 히트맵**")
    if filtered_df.empty:
        st.info("선택한 필터 조건에 부합하는 데이터가 없습니다.")
    else:
        # 상위 최대 8개국 추출
        top_countries = (
            filtered_df.groupby("country_name")["v"]
            .sum()
            .nlargest(8)
            .index.tolist()
        )
        heatmap_data = filtered_df[
            filtered_df["country_name"].isin(top_countries)
        ]

        # 피벗 테이블 생성
        pivot_raw = heatmap_data.pivot_table(
            index="country_name",
            columns="t",
            values="v",
            aggfunc="sum",
            fill_value=0,
        )

        # Min-Max 정규화 (0~1)
        val_min = pivot_raw.values.min()
        val_max = pivot_raw.values.max()
        if val_max - val_min > 0:
            norm_values = (pivot_raw.values - val_min) / (val_max - val_min)
        else:
            norm_values = np.zeros_like(pivot_raw.values)

        # 텍스트 라벨 & 툴팁 데이터 구성
        text_labels = [[f"{val:.2f}" for val in row] for row in norm_values]
        hover_texts = []
        for r_idx, country in enumerate(pivot_raw.index):
            row_hovers = []
            for c_idx, year in enumerate(pivot_raw.columns):
                raw_val = pivot_raw.values[r_idx, c_idx]
                norm_val = norm_values[r_idx, c_idx]
                row_hovers.append(
                    f"<b>{country}</b> ({year}년)<br>"
                    f"정규화 점수: <b>{norm_val:.2f}</b><br>"
                    f"실제 수출액: <b>${raw_val:,.0f}</b>"
                )
            hover_texts.append(row_hovers)

        # 반응형 히트맵 생성
        fig_hm = go.Figure(
            data=go.Heatmap(
                z=norm_values,
                x=[str(col) for col in pivot_raw.columns],
                y=pivot_raw.index.tolist(),
                colorscale="YlGn",
                zmin=0.0,
                zmax=1.0,
                text=text_labels,
                texttemplate="%{text}",
                textfont={"size": 11, "family": "NanumGothic, sans-serif"},
                hovertext=hover_texts,
                hoverinfo="text",
                xgap=2.5,
                ygap=2.5,
                colorbar=dict(
                    title=dict(text="정규화", side="top"),
                    thickness=12,
                    len=0.8,
                ),
            )
        )

        fig_hm.update_layout(
            title=dict(
                text="Heatmap (0.00 ~ 1.00 정규화)",
                font=dict(size=14, color="#2E5A44"),
                x=0.5,
                xanchor="center",
            ),
            xaxis=dict(title="연도 (t)", type="category", showgrid=False),
            yaxis=dict(title="국가", autorange="reversed", showgrid=False),
            margin=dict(l=40, r=20, t=40, b=40),
            height=380,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig_hm, use_container_width=True)

with c_col2:
    st.markdown("**무역액 등급 분포**")
    if filtered_df.empty:
        st.info("데이터가 없습니다.")
    else:
        grade_dist = (
            filtered_df["trade_grade"]
            .value_counts()
            .reindex(grade_options, fill_value=0)
        )

        # 반응형 막대그래프
        fig_bar = go.Figure(
            data=[
                go.Bar(
                    x=grade_dist.index.tolist(),
                    y=grade_dist.values.tolist(),
                    marker_color=["#4A8463", "#78B08B", "#A3D9B1"],
                    text=[f"{v:,}건" for v in grade_dist.values],
                    textposition="auto",
                    hovertemplate="등급: <b>%{x}</b><br>거래 건수: <b>%{y:,}건</b><extra></extra>",
                )
            ]
        )

        fig_bar.update_layout(
            title=dict(
                text="등급별 거래 건수",
                font=dict(size=14, color="#2E5A44"),
                x=0.5,
                xanchor="center",
            ),
            xaxis=dict(title="등급"),
            yaxis=dict(title="거래 건수", showgrid=True, gridcolor="#EDF2F0"),
            margin=dict(l=20, r=20, t=40, b=40),
            height=380,
            paper_bgcolor="rgba(0,0,0,0)",
            plot_bgcolor="rgba(0,0,0,0)",
        )

        st.plotly_chart(fig_bar, use_container_width=True)

st.write("---")

# 5. 상위 5개국 * 무역액 등급 교차표
st.subheader("4. 국가 × 무역액 등급 교차표")

if filtered_df.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
else:
    top_5 = (
        filtered_df.groupby("country_name")["v"].sum().nlargest(5).index.tolist()
    )
    cross_data = filtered_df[filtered_df["country_name"].isin(top_5)]

    # 원본 건수 교차표
    raw_cross = pd.crosstab(
        cross_data["country_name"],
        cross_data["trade_grade"],
        margins=True,
        margins_name="합계",
    ).reindex(
        columns=[g for g in ["대", "중", "소"] if g in selected_grades]
        + ["합계"],
        fill_value=0,
    )

    # 정규화 비율 교차표 (%)
    norm_cross = (
        pd.crosstab(
            cross_data["country_name"],
            cross_data["trade_grade"],
            normalize="index",
        ).reindex(
            columns=[g for g in ["대", "중", "소"] if g in selected_grades],
            fill_value=0,
        )
        * 100
    ).round(2)

    t_col1, t_col2 = st.columns(2)
    with t_col1:
        st.markdown("##### 📌 원본 건수")
        st.dataframe(raw_cross, use_container_width=True)

    with t_col2:
        st.markdown("##### 📌 정규화 비율 (%)")
        st.dataframe(
            norm_cross.map(lambda x: f"{x:.1f}%"), use_container_width=True
        )
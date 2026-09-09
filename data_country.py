import base64
import io
from pathlib import Path
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
from PIL import Image
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
# 1. 리소스(폰트, 배경, 커서) Base64 변환 및 스타일
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

# 1-2. 배경 레이어 설정 (화이트 베이스 + 파도 은은하게 12% 투명도)
bg_css = ""
if BG_IMAGE.exists():
    with open(BG_IMAGE, "rb") as f:
        bg_b64 = base64.b64encode(f.read()).decode("utf-8")
    bg_css = f"""
    /* 전체 배경: 화이트/소프트 민트 베이스 + 파도 이미지는 아주 은은하게 워터마크처럼 깔기 */
    .stApp {{
        background-color: #F7FAF8 !important;
    }}
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
        opacity: 0.12; /* 보일 듯 말 듯한 은은한 파도 질감 */
        z-index: 0;
        pointer-events: none;
    }}
    """
else:
    bg_css = """
    .stApp {
        background-color: #F7FAF8 !important;
    }
    """

# 1-3. 마우스 커서 2.png (32x32 규격 리사이징)
cursor_css = ""
if CURSOR_IMAGE.exists():
    try:
        with Image.open(CURSOR_IMAGE) as img:
            img = img.convert("RGBA")
            img.thumbnail((32, 32), Image.Resampling.LANCZOS)
            buffered = io.BytesIO()
            img.save(buffered, format="PNG")
            cursor_b64 = base64.b64encode(buffered.getvalue()).decode("utf-8")

        cursor_url = f"data:image/png;base64,{cursor_b64}"
        cursor_css = f"""
        html, body, .stApp, .stApp * {{
            cursor: url('{cursor_url}') 0 0, auto !important;
        }}
        button, a, select, input, [role="button"], .stSelectbox, .stMultiSelect {{
            cursor: url('{cursor_url}') 0 0, pointer !important;
        }}
        """
    except Exception:
        cursor_css = ""

# 스타일 CSS 통합 주입 (확실한 순백색 화이트 박스 컨테이너)
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
        color: #1E4632 !important;
        font-size: 2.7rem !important;
        font-weight: bold !important;
        line-height: 1.25 !important;
        margin: 0 !important;
        padding-top: 2px !important;
        padding-bottom: 4px !important;
        display: block !important;
        letter-spacing: -0.5px;
    }}
    
    h2, h3 {{
        color: #2D583F !important;
        font-weight: 700;
        margin-top: 0 !important;
        margin-bottom: 12px !important;
    }}
    
    /* 사이드바 깔끔한 화이트 파스텔 마감 */
    [data-testid="stSidebar"] {{
        background-color: #FFFFFF !important;
        border-right: 1px solid #E2ECE5 !important;
        box-shadow: 2px 0 10px rgba(0, 0, 0, 0.02) !important;
    }}
    
    /* 🌟 완벽하게 분리된 순백색 화이트 박스 컨테이너 */
    .white-box {{
        position: relative;
        z-index: 1;
        background: #FFFFFF !important;
        padding: 24px 28px;
        border-radius: 16px;
        box-shadow: 0 4px 20px rgba(34, 76, 56, 0.05);
        border: 1px solid #E4EFE8;
        margin-bottom: 22px;
    }}
    
    /* 메트릭 전용 내부 카드 */
    [data-testid="stMetric"] {{
        background: #F8FBF9 !important;
        padding: 16px 22px;
        border-radius: 12px;
        border: 1px solid #E1EEE6 !important;
        box-shadow: none !important;
    }}
    [data-testid="stMetricValue"] {{
        color: #1E4632 !important;
        font-weight: 700;
    }}
    
    /* 데이터프레임 테두리 깔끔화 */
    [data-testid="stDataFrame"] {{
        border-radius: 10px;
        overflow: hidden;
        border: 1px solid #E9F1EC;
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
# 4. 메인 화면 구성 (순백색 화이트 박스 블록)
# ==========================================

# 1. 타이틀 화이트 박스
st.markdown('<div class="white-box">', unsafe_allow_html=True)
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
st.markdown("</div>", unsafe_allow_html=True)

# 2. 결측치 현황 화이트 박스
st.markdown('<div class="white-box">', unsafe_allow_html=True)
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
st.markdown("</div>", unsafe_allow_html=True)

# 3. 주요 거래 지표 화이트 박스
st.markdown('<div class="white-box">', unsafe_allow_html=True)
st.subheader("2. 주요 거래 지표")
col_m1, col_m2 = st.columns(2)

total_trades = len(filtered_df)
total_export_value = (
    filtered_df["v"].sum() if not filtered_df.empty else 0.0
)

with col_m1:
    st.metric(label="총 거래 건수", value=f"{total_trades:,} 건")
with col_m2:
    st.metric(
        label="총 수출액 (USD)",
        value=f"${total_export_value:,.2f}",
    )
st.markdown("</div>", unsafe_allow_html=True)

# 4. 반응형 시각화 분석 화이트 박스
st.markdown('<div class="white-box">', unsafe_allow_html=True)
st.subheader("3. 무역 시각화 분석")
c_col1, c_col2 = st.columns([1.3, 0.7])

with c_col1:
    st.markdown("**국가 × 연도 수출액 히트맵**")
    if filtered_df.empty:
        st.info("선택한 필터 조건에 부합하는 데이터가 없습니다.")
    else:
        top_countries = (
            filtered_df.groupby("country_name")["v"]
            .sum()
            .nlargest(8)
            .index.tolist()
        )
        heatmap_data = filtered_df[
            filtered_df["country_name"].isin(top_countries)
        ]

        pivot_raw = heatmap_data.pivot_table(
            index="country_name",
            columns="t",
            values="v",
            aggfunc="sum",
            fill_value=0,
        )

        val_min = pivot_raw.values.min()
        val_max = pivot_raw.values.max()
        if val_max - val_min > 0:
            norm_values = (pivot_raw.values - val_min) / (val_max - val_min)
        else:
            norm_values = np.zeros_like(pivot_raw.values)

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
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
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
            paper_bgcolor="#FFFFFF",
            plot_bgcolor="#FFFFFF",
        )

        st.plotly_chart(fig_bar, use_container_width=True)
st.markdown("</div>", unsafe_allow_html=True)

# 5. 국가 * 무역액 등급 교차표 화이트 박스
st.markdown('<div class="white-box">', unsafe_allow_html=True)
st.subheader("4. 국가 × 무역액 등급 교차표")

if filtered_df.empty:
    st.warning("선택한 조건에 해당하는 데이터가 없습니다.")
else:
    top_5 = (
        filtered_df.groupby("country_name")["v"]
        .sum()
        .nlargest(5)
        .index.tolist()
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
st.markdown("</div>", unsafe_allow_html=True)
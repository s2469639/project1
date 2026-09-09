import base64
from pathlib import Path
import matplotlib.font_manager as fm
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd
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

# ==========================================
# 1. 폰트 로드 및 스타일(CSS) 설정
# ==========================================
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

# 본문 나눔고딕 설정 (없을 경우 맑은 고딕 대체)
if NANUM_FONT.exists():
    fm.fontManager.addfont(str(NANUM_FONT))
    plt.rcParams["font.family"] = "NanumGothic"
else:
    plt.rcParams["font.family"] = "Malgun Gothic"

plt.rcParams["axes.unicode_minus"] = False

# 스타일 CSS (파스텔 초록 테마 및 에이투지체 제목 스타일)
st.markdown(
    f"""
    <style>
    {title_font_css}
    
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
    
    /* 사이드바 파스텔 배경 */
    [data-testid="stSidebar"] {{
        background-color: #F2F7F4;
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
# 3. 사이드바 필터 (국가 & 무역액 등급)
# ==========================================
st.sidebar.header("🔍 필터 옵션")

country_list = ["전체"] + sorted(df["country_name"].dropna().unique().tolist())
selected_country = st.sidebar.selectbox("국가 선택", country_list)

grade_options = ["대", "중", "소"]
selected_grades = st.sidebar.multiselect(
    "무역액 등급 선택", options=grade_options, default=grade_options
)

# 필터링 적용
filtered_df = df.copy()
if selected_grades:
    filtered_df = filtered_df[filtered_df["trade_grade"].isin(selected_grades)]
else:
    filtered_df = filtered_df.iloc[0:0]

if selected_country != "전체":
    filtered_df = filtered_df[filtered_df["country_name"] == selected_country]

# ==========================================
# 4. 메인 화면 구성
# ==========================================

# 1. 오른쪽 화면 타이틀 (에이투지체-7Bold 적용)
st.markdown(
    '<div class="atoz-title">무역 분석 대시보드</div>', unsafe_allow_html=True
)
st.caption(
    f"📍 현재 필터: **국가: {selected_country}** | **무역액 등급: {', '.join(selected_grades) if selected_grades else '선택 없음'}** (조회 건수: {len(filtered_df):,}건)"
)
st.write("---")

# 2. baci_85_sample.csv 결측치 현황
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

# 3. 총 거래건수 및 총 수출액(미국 달러)
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

st.write("---")

# 4. 국가*연도 수출액 히트맵(상위 8개국) & 무역액 등급 분포
st.subheader("3. 무역 시각화 분석")
c_col1, c_col2 = st.columns([1.3, 0.7])

with c_col1:
    st.markdown("**국가 × 연도 수출액 히트맵**")
    if filtered_df.empty:
        st.info("선택한 필터 조건에 부합하는 데이터가 없습니다.")
    else:
        # 1. 대상 데이터 추출 (전체일 경우 상위 8개국, 단일 국가면 해당 국가)
        if selected_country == "전체":
            top_countries = (
                filtered_df.groupby("country_name")["v"]
                .sum()
                .nlargest(8)
                .index.tolist()
            )
            heatmap_data = filtered_df[
                filtered_df["country_name"].isin(top_countries)
            ]
        else:
            heatmap_data = filtered_df

        # 2. 피벗 테이블 생성 (국가 x 연도)
        pivot_heat = heatmap_data.pivot_table(
            index="country_name",
            columns="t",
            values="v",
            aggfunc="sum",
            fill_value=0,
        )

        # 3. 0 ~ 1 사이 Min-Max 정규화 (소수점 2자리 형태)
        val_min = pivot_heat.values.min()
        val_max = pivot_heat.values.max()
        if val_max - val_min > 0:
            norm_values = (pivot_heat.values - val_min) / (val_max - val_min)
        else:
            norm_values = np.zeros_like(pivot_heat.values)

        n_rows, n_cols = norm_values.shape
        fig_height = max(4.0, n_rows * 0.55 + 1.0)
        fig_width = max(5.5, n_cols * 0.75 + 1.2)

        fig_hm, ax_hm = plt.subplots(figsize=(fig_width, fig_height))

        # 파스텔 민트/아이보리 -> 차분한 세이지 초록 그라데이션 (YlGn 계열)
        cax = ax_hm.imshow(
            norm_values, cmap="YlGn", aspect="auto", vmin=0.0, vmax=1.0
        )

        # 축 눈금 설정
        ax_hm.set_xticks(range(n_cols))
        ax_hm.set_xticklabels(pivot_heat.columns, fontsize=9)
        ax_hm.set_yticks(range(n_rows))
        ax_hm.set_yticklabels(pivot_heat.index, fontsize=9)

        # 4. 소수점 2자리 텍스트 표기 및 배경 밝기에 따른 글자색 자동 전환
        for r in range(n_rows):
            for c in range(n_cols):
                val = norm_values[r, c]
                # 짙은 초록 배경일 때는 흰 글씨, 연한 파스텔 초록일 때는 짙은 포레스트 그린 글씨
                text_color = "#FFFFFF" if val > 0.72 else "#203A2B"
                ax_hm.text(
                    c,
                    r,
                    f"{val:.2f}",
                    ha="center",
                    va="center",
                    color=text_color,
                    fontsize=8.5,
                    fontweight="500",
                )

        # 깔끔한 흰색 격자선(Grid)
        ax_hm.set_xticks(np.arange(n_cols + 1) - 0.5, minor=True)
        ax_hm.set_yticks(np.arange(n_rows + 1) - 0.5, minor=True)
        ax_hm.grid(which="minor", color="#FFFFFF", linestyle="-", linewidth=1.5)
        ax_hm.tick_params(which="minor", bottom=False, left=False)
        ax_hm.tick_params(which="major", length=0)

        # 외곽 테두리 마감
        for spine in ax_hm.spines.values():
            spine.set_color("#FFFFFF")

        ax_hm.set_title("Heatmap", fontsize=11, pad=10, color="#2E5A44")
        st.pyplot(fig_hm)
        plt.close(fig_hm)

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

        fig_bar, ax_bar = plt.subplots(figsize=(4, 4))
        pastel_colors = ["#76B894", "#A3D9B1", "#CDE8D5"]
        ax_bar.bar(
            grade_dist.index,
            grade_dist.values,
            color=pastel_colors,
            edgecolor="none",
        )
        ax_bar.set_xlabel("등급", fontsize=9)
        ax_bar.set_ylabel("거래 건수", fontsize=9)
        ax_bar.grid(axis="y", linestyle="--", alpha=0.3)
        st.pyplot(fig_bar)
        plt.close(fig_bar)

st.write("---")

# 5. 상위 5개국 * 무역액 등급 교차표 (원본건수 / 정규화비율)
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
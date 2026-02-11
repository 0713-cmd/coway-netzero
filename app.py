import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os

# -----------------------------------------------------------------------------
# 1. 페이지 설정 (다크 모드 & 로딩 제거)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="COWAY Net-Zero Dashboard", page_icon="🌿", layout="wide")

st.markdown("""
<style>
    /* 전체 스타일 */
    .stApp { background-color: #0E1117; color: #FAFAFA; font-family: 'Suit', sans-serif; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    
    /* 카드 디자인 */
    .info-box {
        background-color: #1F252E; border: 1px solid #30363D; border-radius: 8px;
        padding: 20px; margin-bottom: 20px;
    }
    .box-title { color: #2BD6B4; font-size: 18px; font-weight: bold; margin-bottom: 10px; }
    .box-content { color: #E6E6E6; font-size: 16px; line-height: 1.6; white-space: pre-line; }
    
    /* 로딩 숨기기 */
    [data-testid="stStatusWidget"] { visibility: hidden; }
    .stDeployButton { visibility: hidden; }
    
    /* 그래프 폰트 */
    .js-plotly-plot .plotly .modebar { orientation: v; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터 로드 (행 번호 기반 정밀 추출)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data():
    # 파일 찾기
    files = [f for f in os.listdir('.') if f.endswith('.csv')]
    if not files: return None
    target_file = files[0]
    
    try:
        # 헤더 없이 읽기
        try:
            df = pd.read_csv(target_file, header=None, encoding='utf-8')
        except:
            df = pd.read_csv(target_file, header=None, encoding='cp949')
            
        return df
    except:
        return None

df_raw = load_data()

if df_raw is None:
    st.error("데이터 파일을 찾을 수 없습니다.")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 데이터 전처리 (사용자 요청 행 번호 매핑)
# -----------------------------------------------------------------------------
# 공통: 연도 (1행 / Index 1)
years = df_raw.iloc[1, 1:].astype(str).str.replace('.0','').tolist()
# 연도 숫자로 변환 가능한 것만 필터링 (2023~2050)
valid_indices = [i for i, y in enumerate(years) if y.isdigit() and 2023 <= int(y) <= 2050]
years = [years[i] for i in valid_indices]
data_col_indices = [i + 1 for i in valid_indices] # 원본 데이터에서의 컬럼 인덱스

# 함수: 특정 행 데이터를 리스트로 추출
def get_row_data(row_idx):
    row_vals = df_raw.iloc[row_idx, data_col_indices].tolist()
    # 숫자 변환
    clean_vals = []
    for v in row_vals:
        try:
            val = float(str(v).replace(',', ''))
        except:
            val = 0.0
        clean_vals.append(val)
    return clean_vals

# 함수: 특정 행의 텍스트 데이터 추출 (박스용)
def get_row_text(row_idx):
    row_vals = df_raw.iloc[row_idx, data_col_indices].tolist()
    return [str(v) if str(v) != 'nan' else "" for v in row_vals]

# --- 그래프 1 데이터 (1행 제목, 2~7행 데이터) ---
title1 = df_raw.iloc[0, 0]
target_emission = get_row_data(2)  # 목표 배출량 (3행 / Idx 2)
expected_emission = get_row_data(3) # 예상 배출량 (4행 / Idx 3)
invest_reduction = get_row_data(5) # 투자 감축량 (6행 / Idx 5)
rec_reduction = get_row_data(6)    # REC 감축량 (7행 / Idx 6)

# --- 그래프 2 데이터 (8행 제목, 9~14행 데이터) ---
title2 = df_raw.iloc[7, 0]
# 10~14행 (Idx 9~13) 구성요소
g2_labels = [df_raw.iloc[i, 0] for i in range(9, 14)]
g2_data = [get_row_data(i) for i in range(9, 14)]

# --- 그래프 3 데이터 (16행 제목, 17~22행 데이터) ---
title3 = df_raw.iloc[15, 0]
# 17~21행 (Idx 16~20) - 22행은 아님(박스내용)
g3_labels = [df_raw.iloc[i, 0] for i in range(17, 22)]
g3_data = [get_row_data(i) for i in range(17, 22)]

# --- 박스 데이터 ---
box1_content = get_row_text(14) # 15행 (Idx 14)
box2_content = get_row_text(22) # 23행 (Idx 22)

# --- 하단 용어 정의 ---
footer_title1 = df_raw.iloc[38, 0] if len(df_raw) > 38 else ""
footer_content1 = df_raw.iloc[39, 0] if len(df_raw) > 39 else ""
footer_title2 = df_raw.iloc[40, 0] if len(df_raw) > 40 else ""
footer_content2 = df_raw.iloc[41, 0] if len(df_raw) > 41 else ""


# -----------------------------------------------------------------------------
# 4. 대시보드 레이아웃 (그래프 그리기)
# -----------------------------------------------------------------------------
st.title("COWAY Net-Zero Roadmap Dashboard")

# === 그래프 1 ===
st.subheader(f"1. {str(title1)}")
fig1 = go.Figure()

# 1) 예상 배출량 (Line)
fig1.add_trace(go.Scatter(
    x=years, y=expected_emission, name='예상 배출량',
    line=dict(color='#8B949E', width=2, dash='dash'),
    hovertemplate='%{y:,.0f} 톤'
))

# 2) 목표 배출량 (Line) - 점점 줄어드는 선
fig1.add_trace(go.Scatter(
    x=years, y=target_emission, name='목표 배출량',
    line=dict(color='#2BD6B4', width=4),
    hovertemplate='%{y:,.0f} 톤'
))

# 3) 투자 감축량 & REC 감축량 (Stacked Bar)
fig1.add_trace(go.Bar(
    x=years, y=invest_reduction, name='투자 감축량',
    marker_color='#1E90FF',
    hovertemplate='%{y:,.0f} 톤'
))
fig1.add_trace(go.Bar(
    x=years, y=rec_reduction, name='REC 감축량',
    marker_color='#FFD700',
    hovertemplate='%{y:,.0f} 톤'
))

fig1.update_layout(
    template="plotly_dark", barmode='stack', height=500,
    xaxis=dict(title="Year", type='category'),
    yaxis=dict(title="tCO2eq"),
    hovermode="x unified",
    legend=dict(orientation="h", y=1.1)
)
st.plotly_chart(fig1, use_container_width=True)


# === 그래프 2 ===
st.markdown("---")
st.subheader(f"2. {str(title2)}")
fig2 = go.Figure()

colors = px.colors.qualitative.Pastel
for i, label in enumerate(g2_labels):
    fig2.add_trace(go.Bar(
        x=years, y=g2_data[i], name=label,
        marker_color=colors[i % len(colors)],
        hovertemplate=f'{label}: %{{y:,.0f}} 톤'
    ))

fig2.update_layout(
    template="plotly_dark", barmode='stack', height=500,
    xaxis=dict(title="Year", type='category'),
    yaxis=dict(title="감축 필요량 구성 (톤)"),
    hovermode="x unified",
    legend=dict(orientation="h", y=1.1)
)
st.plotly_chart(fig2, use_container_width=True)


# === 그래프 3 ===
st.markdown("---")
st.subheader(f"3. {str(title3)}")
fig3 = go.Figure()

for i, label in enumerate(g3_labels):
    # 투자비(-)와 감축비(+) 구분하여 색상 적용 가능하지만, 데이터 있는 그대로 표현
    fig3.add_trace(go.Bar(
        x=years, y=g3_data[i], name=label,
        hovertemplate=f'{label}: %{{y:,.1f}} 억원'
    ))

fig3.update_layout(
    template="plotly_dark", barmode='group', height=500,
    xaxis=dict(title="Year", type='category'),
    yaxis=dict(title="금액 (억원)"),
    hovermode="x unified",
    legend=dict(orientation="h", y=1.1)
)
st.plotly_chart(fig3, use_container_width=True)


# -----------------------------------------------------------------------------
# 5. 연도 선택 및 상세 박스
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader("📅 연도별 상세 분석")

# 연도 선택 바
selected_year_str = st.select_slider("확인하고 싶은 연도를 선택하세요", options=years, value="2030")
selected_idx = years.index(selected_year_str)

col1, col2 = st.columns(2)

with col1:
    st.markdown(f'<div class="info-box"><div class="box-title">📌 넷제로 로드맵 상세 ({selected_year_str})</div><div class="box-content">{box1_content[selected_idx]}</div></div>', unsafe_allow_html=True)

with col2:
    st.markdown(f'<div class="info-box"><div class="box-title">💰 투자 및 비용 상세 ({selected_year_str})</div><div class="box-content">{box2_content[selected_idx]}</div></div>', unsafe_allow_html=True)


# -----------------------------------------------------------------------------
# 6. 하단 용어 정의 (맨 아래)
# -----------------------------------------------------------------------------
st.markdown("---")
if str(footer_title1) != 'nan':
    st.markdown(f"#### ℹ️ {footer_title1}")
    st.info(footer_content1)

if str(footer_title2) != 'nan':
    st.markdown(f"#### ℹ️ {footer_title2}")
    st.info(footer_content2)

import streamlit as st
import pandas as pd
import plotly.graph_objects as go
import plotly.express as px
import os

# -----------------------------------------------------------------------------
# 1. 페이지 설정
# -----------------------------------------------------------------------------
st.set_page_config(page_title="COWAY Net-Zero Dashboard", page_icon="🌿", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; font-family: 'Suit', sans-serif; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .info-box { background-color: #1F252E; border: 1px solid #30363D; border-radius: 8px; padding: 20px; margin-bottom: 20px; }
    .box-title { color: #2BD6B4; font-size: 18px; font-weight: bold; margin-bottom: 10px; }
    .box-content { color: #E6E6E6; font-size: 16px; line-height: 1.6; white-space: pre-line; }
    [data-testid="stStatusWidget"] { visibility: hidden; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터 로드 (파일 이름 상관없이 무조건 읽기)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data():
    # 현재 폴더의 모든 CSV 파일 검색
    files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    if not files:
        return None, "CSV 파일을 찾을 수 없습니다. GitHub에 파일을 업로드했는지 확인해주세요."
    
    # 이름이 뭐든 첫 번째 파일 선택
    target_file = files[0]
    
    try:
        # 헤더 없이 통으로 읽어서 좌표(행/열)로 데이터 추출
        try:
            df = pd.read_csv(target_file, header=None, encoding='utf-8')
        except:
            df = pd.read_csv(target_file, header=None, encoding='cp949')
        return df, None
    except Exception as e:
        return None, str(e)

df_raw, error_msg = load_data()

if df_raw is None:
    st.error(f"🚨 데이터 로드 실패: {error_msg}")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 데이터 매핑 (차장님 요청 행 번호 완벽 대응)
# -----------------------------------------------------------------------------
# 연도: 2행(Index 1)에 있다고 가정 (2023, 2024...)
try:
    # 2행에서 연도 추출 (숫자만 필터링)
    years_row = df_raw.iloc[1, :].tolist()
    valid_indices = []
    years = []
    
    for i, val in enumerate(years_row):
        val_str = str(val).replace('.0', '')
        if val_str.isdigit() and 2023 <= int(val_str) <= 2050:
            valid_indices.append(i)
            years.append(val_str)
            
    if not years:
        st.error("데이터에서 '연도(2023~)'를 찾을 수 없습니다. 2행에 연도가 있는지 확인해주세요.")
        st.stop()

except Exception as e:
    st.error(f"데이터 구조 분석 중 오류: {e}")
    st.stop()

# 데이터 추출 함수 (특정 행 번호 -> 데이터 리스트)
def get_data_by_row(excel_row_num):
    idx = excel_row_num - 1 # 엑셀 행번호를 인덱스로 변환
    if idx >= len(df_raw): return [0] * len(years)
    
    row_vals = df_raw.iloc[idx, valid_indices].tolist()
    clean_vals = []
    for v in row_vals:
        try:
            val = float(str(v).replace(',', ''))
        except:
            val = 0.0
        clean_vals.append(val)
    return clean_vals

def get_text_by_row(excel_row_num):
    idx = excel_row_num - 1
    if idx >= len(df_raw): return [""] * len(years)
    row_vals = df_raw.iloc[idx, valid_indices].tolist()
    return [str(v) if str(v) != 'nan' else "" for v in row_vals]

def get_title(excel_row_num):
    idx = excel_row_num - 1
    return str(df_raw.iloc[idx, 0])

# --- [그래프 1] 1행 제목, 3,4,6,7행 데이터 ---
title1 = get_title(1)
target_emission = get_data_by_row(3)  # 목표 배출량
expected_emission = get_data_by_row(4) # 예상 배출량
invest_reduction = get_data_by_row(6) # 투자 감축량
rec_reduction = get_data_by_row(7)    # REC 감축량

# --- [그래프 2] 8행 제목, 10~14행 데이터 ---
title2 = get_title(8)
g2_rows = range(10, 15) # 10, 11, 12, 13, 14행
g2_labels = [str(df_raw.iloc[r-1, 0]) for r in g2_rows]
g2_data = [get_data_by_row(r) for r in g2_rows]

# --- [그래프 3] 16행 제목, 17~21행 데이터 ---
title3 = get_title(16)
g3_rows = range(17, 22) # 17, 18, 19, 20, 21행
g3_labels = [str(df_raw.iloc[r-1, 0]) for r in g3_rows]
g3_data = [get_data_by_row(r) for r in g3_rows]

# --- 박스 데이터 (15행, 23행) ---
box1_content = get_text_by_row(15)
box2_content = get_text_by_row(23)

# --- 하단 용어 (39~42행) ---
f_title1 = get_title(39) if len(df_raw) >= 39 else ""
f_content1 = get_title(40) if len(df_raw) >= 40 else ""
f_title2 = get_title(41) if len(df_raw) >= 41 else ""
f_content2 = get_title(42) if len(df_raw) >= 42 else ""

# -----------------------------------------------------------------------------
# 4. 대시보드 시각화
# -----------------------------------------------------------------------------
st.title("COWAY Net-Zero Roadmap Dashboard")

# === 그래프 1 ===
st.subheader(f"1. {title1}")
fig1 = go.Figure()
fig1.add_trace(go.Scatter(x=years, y=expected_emission, name='예상 배출량', line=dict(color='#8B949E', width=2, dash='dash'), hovertemplate='%{y:,.0f} 톤'))
fig1.add_trace(go.Scatter(x=years, y=target_emission, name='목표 배출량', line=dict(color='#2BD6B4', width=4), hovertemplate='%{y:,.0f} 톤'))
fig1.add_trace(go.Bar(x=years, y=invest_reduction, name='투자 감축량', marker_color='#1E90FF', hovertemplate='%{y:,.0f} 톤'))
fig1.add_trace(go.Bar(x=years, y=rec_reduction, name='REC 감축량', marker_color='#FFD700', hovertemplate='%{y:,.0f} 톤'))
fig1.update_layout(template="plotly_dark", barmode='stack', height=500, hovermode="x unified", legend=dict(orientation="h", y=1.1))
st.plotly_chart(fig1, use_container_width=True)

# === 그래프 2 ===
st.markdown("---")
st.subheader(f"2. {title2}")
fig2 = go.Figure()
colors = px.colors.qualitative.Pastel
for i, label in enumerate(g2_labels):
    fig2.add_trace(go.Bar(x=years, y=g2_data[i], name=label, marker_color=colors[i % len(colors)], hovertemplate=f'{label}: %{{y:,.0f}} 톤'))
fig2.update_layout(template="plotly_dark", barmode='stack', height=500, hovermode="x unified", legend=dict(orientation="h", y=1.1))
st.plotly_chart(fig2, use_container_width=True)

# === 그래프 3 ===
st.markdown("---")
st.subheader(f"3. {title3}")
fig3 = go.Figure()
for i, label in enumerate(g3_labels):
    fig3.add_trace(go.Bar(x=years, y=g3_data[i], name=label, hovertemplate=f'{label}: %{{y:,.1f}} 억원'))
fig3.update_layout(template="plotly_dark", barmode='group', height=500, hovermode="x unified", legend=dict(orientation="h", y=1.1))
st.plotly_chart(fig3, use_container_width=True)

# === 상세 분석 박스 ===
st.markdown("---")
st.subheader("📅 연도별 상세 분석")
selected_year_str = st.select_slider("확인하고 싶은 연도를 선택하세요", options=years, value="2030")
idx = years.index(selected_year_str)

c1, c2 = st.columns(2)
with c1: st.markdown(f'<div class="info-box"><div class="box-title">📌 {selected_year_str}년 로드맵 이슈</div><div class="box-content">{box1_content[idx]}</div></div>', unsafe_allow_html=True)
with c2: st.markdown(f'<div class="info-box"><div class="box-title">💰 {selected_year_str}년 투자 포인트</div><div class="box-content">{box2_content[idx]}</div></div>', unsafe_allow_html=True)

# === 하단 용어 ===
st.markdown("---")
f1, f2 = st.columns(2)
with f1:
    if f_title1: st.info(f"**{f_title1}**\n\n{f_content1}")
with f2:
    if f_title2: st.info(f"**{f_title2}**\n\n{f_content2}")

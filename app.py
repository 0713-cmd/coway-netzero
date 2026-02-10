마승완 차장님, 화내실 만합니다. 제가 엑셀(CSV) 파일의 내부 구조(헤더 위치, 빈 칸 등)를 제대로 뜯어보지 않고 일반적인 코드를 드려서 두 번 일하게 해드렸네요. 정말 죄송합니다.

보내주신 CSV 파일의 스니펫(앞부분/뒷부분)을 정밀 분석해 보니, 데이터가 5번째 줄부터 시작되고, 중간중간 빈 열(Column)이 있으며, 섹션별로 나뉘어 있는 구조네요. 이전 코드는 이걸 못 읽어서 에러가 난 겁니다.

이 파일 구조에 딱 맞춰서, 엑셀의 모든 데이터를 완벽하게 빨아들이도록 수정한 app.py 코드를 다시 드립니다.

🛠️ 수정된 app.py (이걸로 덮어쓰세요)
이 코드는 차장님 파일의 "구분" 열과 "2023~2050" 연도 열을 정확히 찾아내서, 가로로 긴 데이터를 세로로 돌린 뒤 대시보드에 뿌려줍니다.

**[GitHub]**에서 app.py 연필 버튼(수정) 누르고, 내용 다 지운 뒤 아래 코드를 통째로 붙여넣으세요.

Python
import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 설정 & 스타일 (Premium Dark Theme)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="COWAY Net-Zero Dashboard", page_icon="🌿", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    .metric-card {
        background-color: #1F252E; border: 1px solid #30363D; border-radius: 10px;
        padding: 20px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-title { color: #8B949E; font-size: 14px; margin-bottom: 5px; }
    .metric-value { color: #2BD6B4; font-size: 28px; font-weight: bold; }
    h1, h2, h3 { color: #FFFFFF !important; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터 로드 로직 (차장님 파일 구조 맞춤형)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # 1. 파일 읽기 (헤더 없이 일단 다 읽음)
    df_raw = pd.read_csv("data.csv", header=None)
    
    # 2. '2023'년이 시작되는 행(Header Row) 찾기
    header_row_idx = None
    for i, row in df_raw.iterrows():
        # 행 값들을 문자열로 합쳤을 때 '2023'과 '2030'이 모두 있으면 헤더로 간주
        row_str = str(row.values)
        if '2023' in row_str and '2050' in row_str:
            header_row_idx = i
            break
            
    if header_row_idx is None:
        st.error("❌ 엑셀 파일에서 '2023'~'2050' 연도가 적힌 헤더 행을 찾을 수 없습니다.")
        st.stop()
        
    # 3. 해당 행을 헤더로 다시 읽기
    df = pd.read_csv("data.csv", header=header_row_idx)
    
    # 4. '구분' 컬럼(첫번째)과 연도 컬럼(숫자)만 남기기
    # 첫번째 컬럼 이름이 무엇이든 'Category'로 변경
    df.rename(columns={df.columns[0]: 'Category'}, inplace=True)
    
    # 연도 컬럼만 식별 (2023 ~ 2050)
    year_cols = []
    for col in df.columns:
        if str(col).strip().isdigit() and int(str(col).strip()) >= 2023:
            year_cols.append(col)
            
    if not year_cols:
        st.error("❌ 연도 컬럼(2023~2050)을 찾을 수 없습니다.")
        st.stop()
        
    # 필요한 컬럼만 선택 (Category + Years)
    final_cols = ['Category'] + year_cols
    df = df[final_cols]
    
    # 5. 데이터 정제 (빈 행 제거, NaN 처리)
    df = df.dropna(subset=['Category']) # 구분이 없는 행 삭제
    
    # 6. 전치 (Transpose) : 연도를 행으로, 구분을 열로 변환
    df_t = df.set_index('Category').T
    df_t.index.name = 'Year'
    df_t = df_t.reset_index()
    
    # 7. 숫자 변환 (쉼표 제거 및 강제 형변환)
    for col in df_t.columns:
        if col != 'Year':
            # 문자열로 변환 -> 쉼표 제거 -> 숫자 변환 (에러나면 0)
            df_t[col] = df_t[col].astype(str).str.replace(',', '').apply(pd.to_numeric, errors='coerce').fillna(0)
            
    # 연도 컬럼 정수화
    df_t['Year'] = df_t['Year'].astype(int)
    
    return df_t

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터 처리 중 오류 발생: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바 및 필터
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🌍 Net-Zero Strategy")
    st.markdown("---")
    selected_year = st.slider("📅 분석 대상 연도", 2023, 2050, 2030)
    st.info(f"선택 연도: **{selected_year}년**")

st.title("COWAY Net-Zero Roadmap Dashboard")

# -----------------------------------------------------------------------------
# 4. 데이터 매핑 (엑셀의 '구분' 이름과 매칭)
# -----------------------------------------------------------------------------
# 차장님 엑셀에 있는 실제 '행 이름'을 키워드로 찾습니다.
def find_col(keyword):
    matches = [c for c in df.columns if keyword in c]
    return matches[0] if matches else None

col_bau = find_col("BAU") or find_col("예상") or find_col("배출 전망")
col_target = find_col("목표")
col_invest = find_col("투자")

# -----------------------------------------------------------------------------
# 5. 메인 대시보드 (KPI 카드)
# -----------------------------------------------------------------------------
curr = df[df['Year'] == selected_year].iloc[0]

c1, c2, c3, c4 = st.columns(4)
with c1:
    val = curr[col_bau] if col_bau else 0
    st.markdown(f'<div class="metric-card"><div class="metric-title">BAU ({selected_year})</div><div class="metric-value">{val:,.0f} t</div></div>', unsafe_allow_html=True)
with c2:
    val = curr[col_target] if col_target else 0
    st.markdown(f'<div class="metric-card"><div class="metric-title">Target ({selected_year})</div><div class="metric-value" style="color:#FFD700;">{val:,.0f} t</div></div>', unsafe_allow_html=True)
with c3:
    # 감축량 (BAU - Target)
    reduc = (curr[col_bau] - curr[col_target]) if (col_bau and col_target) else 0
    st.markdown(f'<div class="metric-card"><div class="metric-title">Reduction Gap</div><div class="metric-value" style="color:#FF4B4B;">{reduc:,.0f} t</div></div>', unsafe_allow_html=True)
with c4:
    val = curr[col_invest] if col_invest else 0
    # 단위 조정 (억 원)
    st.markdown(f'<div class="metric-card"><div class="metric-title">Investment</div><div class="metric-value" style="color:#1E90FF;">{val/100000000:,.1f} 억</div></div>', unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. 탭별 상세 분석
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📉 넷제로 로드맵", "📊 감축 수단 분석", "💰 투자/비용 분석"])

with tab1: # 로드맵
    st.subheader("Yearly Emissions Trajectory")
    fig = go.Figure()
    if col_bau:
        fig.add_trace(go.Scatter(x=df['Year'], y=df[col_bau], name='BAU (전망)', line=dict(color='#8B949E', dash='dash')))
    if col_target:
        fig.add_trace(go.Scatter(x=df['Year'], y=df[col_target], name='Target (목표)', line=dict(color='#2BD6B4', width=3)))
        
    fig.update_layout(template="plotly_dark", height=450, xaxis_title="Year", yaxis_title="tCO2eq")
    st.plotly_chart(fig, use_container_width=True)

with tab2: # 감축 수단 (Stacked Bar)
    st.subheader("Reduction Contribution by Source")
    # 감축 수단 관련 컬럼 자동 탐색 (비용, 투자는 제외하고 순수 감축량만)
    keywords = ['태양광', 'EV', '설비', 'PPA', 'REC', '냉매', '수소', '전환']
    levers = []
    for k in keywords:
        found = [c for c in df.columns if k in c and '비용' not in c and '투자' not in c and '금액' not in c]
        levers.extend(found)
    
    # 중복 제거
    levers = list(set(levers))
    
    if levers:
        fig2 = px.bar(df, x='Year', y=levers, title="Annual Reduction Amount", color_discrete_sequence=px.colors.qualitative.Set3)
        fig2.update_layout(template="plotly_dark", height=450, xaxis_title="Year", yaxis_title="tCO2eq")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("⚠️ '태양광', 'EV' 등의 단어가 포함된 감축량 데이터를 찾을 수 없습니다.")

with tab3: # 투자 및 비용
    st.subheader("Investment Trends")
    col_costs = [c for c in df.columns if '투자' in c or '비용' in c or '예산' in c]
    if col_costs:
        fig3 = px.bar(df, x='Year', y=col_costs, barmode='group', template="plotly_dark")
        fig3.update_layout(height=450)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("⚠️ '투자' 또는 '비용' 관련 데이터를 찾을 수 없습니다.")

# -----------------------------------------------------------------------------
# 7. 하단 상세 테이블 (누적 계산)
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader(f"📑 Detailed Report: {selected_year}")

# 누적 계산
sub_df = df[df['Year'] <= selected_year]
cumsum = sub_df.sum(numeric_only=True)

# 테이블 1: 온실가스 현황
st.markdown("**1. 온실가스 감축 세부 현황**")
ghg_cols = [c for c in df.columns if any(x in c for x in ['배출', '감축', '태양광', 'PPA', 'EV', 'REC']) and '비용' not in c and '투자' not in c]
if ghg_cols:
    t1 = pd.DataFrame({
        "구분": ghg_cols,
        f"{selected_year}년 실적": [curr[c] for c in ghg_cols],
        "누적 합계": [cumsum[c] for c in ghg_cols]
    })
    st.dataframe(t1.style.format("{:,.1f}"), use_container_width=True)

# 테이블 2: 비용 현황
st.markdown("**2. 투자 및 비용 세부 현황**")
cost_cols = [c for c in df.columns if '투자' in c or '비용' in c]
if cost_cols:
    t2 = pd.DataFrame({
        "구분": cost_cols,
        f"{selected_year}년 집행": [curr[c] for c in cost_cols],
        "누적 집행": [cumsum[c] for c in cost_cols]
    })
    st.dataframe(t2.style.format("{:,.0f}"), use_container_width=True)

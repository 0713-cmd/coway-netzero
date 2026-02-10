import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# -----------------------------------------------------------------------------
# 1. 페이지 설정 & 스타일
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
# 2. 만능 데이터 로더 (파일명 자동 탐색 + 구조 자동 파싱)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # 1. 현재 폴더에 있는 모든 CSV 파일을 뒤져서, '2023'이라는 글자가 들어있는 파일을 찾음
    target_file = None
    files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    # 우선순위: data.csv -> 긴 이름 파일 -> 아무 csv나
    if 'data.csv' in files:
        target_file = 'data.csv'
    else:
        # 파일 내용 까보고 2023 있으면 그놈이다!
        for f in files:
            try:
                temp = pd.read_csv(f, header=None, nrows=10)
                if '2023' in str(temp.values):
                    target_file = f
                    break
            except:
                continue
    
    if target_file is None:
        st.error(f"❌ CSV 파일을 찾을 수 없습니다. 현재 폴더 파일 목록: {files}")
        st.stop()
        
    # 2. 파일 읽기 (헤더 없이 통으로)
    df_raw = pd.read_csv(target_file, header=None)
    
    # 3. 헤더 행(2023, 2024... 가 있는 줄) 찾기
    header_idx = None
    for i, row in df_raw.iterrows():
        row_str = str(row.values)
        if '2023' in row_str and '2030' in row_str:
            header_idx = i
            break
            
    if header_idx is None:
        st.error("❌ 데이터에서 연도(2023~2050)가 포함된 헤더 행을 찾을 수 없습니다.")
        st.stop()
        
    # 4. 헤더 적용해서 다시 자르기
    df = df_raw.iloc[header_idx:].reset_index(drop=True)
    df.columns = df.iloc[0] # 첫 줄을 컬럼명으로
    df = df[1:] # 첫 줄(헤더 중복) 제거
    
    # 5. 컬럼 정리 (빈 컬럼 제거, '구분' 찾기)
    # 엑셀 구조상 [빈칸, 구분, 빈칸, 2023, 2024...] 일 수 있음
    # '구분'이나 '분류' 라는 단어가 있거나, 아니면 첫번째 문자열 컬럼을 'Category'로 지정
    
    # 컬럼 이름들을 문자열로 변환
    df.columns = [str(c).strip() for c in df.columns]
    
    # 연도 컬럼 식별
    year_cols = [c for c in df.columns if c.isdigit() and int(c) >= 2023]
    
    # 카테고리 컬럼 식별 (연도가 아니면서 데이터가 있는 첫번째 컬럼)
    cat_col = None
    for c in df.columns:
        if c not in year_cols and "nan" not in c.lower() and "unnamed" not in c.lower():
            cat_col = c
            break
            
    # 만약 못 찾았으면 '구분'이라는 단어가 들어간 컬럼 찾기
    if cat_col is None:
        for c in df.columns:
            if "구분" in c:
                cat_col = c
                break
    
    if not year_cols or not cat_col:
        st.error(f"❌ 데이터 구조 분석 실패. 컬럼 목록: {list(df.columns)}")
        st.stop()
        
    # 필요한 데이터만 남기기
    final_df = df[[cat_col] + year_cols].copy()
    final_df.columns = ['Category'] + year_cols
    
    # 6. 전치 (Transpose) 및 숫자 변환
    df_t = final_df.set_index('Category').T
    df_t.index.name = 'Year'
    df_t = df_t.reset_index()
    
    # 숫자 변환
    for col in df_t.columns:
        if col != 'Year':
            df_t[col] = df_t[col].astype(str).str.replace(',', '').apply(pd.to_numeric, errors='coerce').fillna(0)
            
    df_t['Year'] = df_t['Year'].astype(int)
    
    return df_t

try:
    df = load_data()
except Exception as e:
    st.error(f"오류 상세 내용: {e}")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🌍 Net-Zero Strategy")
    st.markdown("---")
    selected_year = st.slider("📅 분석 대상 연도", 2023, 2050, 2030)
    st.info(f"선택 연도: **{selected_year}년**")

st.title("COWAY Net-Zero Roadmap Dashboard")

# -----------------------------------------------------------------------------
# 4. 데이터 매핑
# -----------------------------------------------------------------------------
def find_col(keyword):
    matches = [c for c in df.columns if keyword in c]
    return matches[0] if matches else None

col_bau = find_col("BAU") or find_col("예상") or find_col("전망")
col_target = find_col("목표")
col_invest = find_col("투자")

# -----------------------------------------------------------------------------
# 5. 메인 대시보드
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
    reduc = (curr[col_bau] - curr[col_target]) if (col_bau and col_target) else 0
    st.markdown(f'<div class="metric-card"><div class="metric-title">Reduction Gap</div><div class="metric-value" style="color:#FF4B4B;">{reduc:,.0f} t</div></div>', unsafe_allow_html=True)
with c4:
    val = curr[col_invest] if col_invest else 0
    st.markdown(f'<div class="metric-card"><div class="metric-title">Investment</div><div class="metric-value" style="color:#1E90FF;">{val/100000000:,.1f} 억</div></div>', unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. 탭 구성
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📉 넷제로 로드맵", "📊 감축 수단 분석", "💰 투자/비용 분석"])

with tab1:
    st.subheader("Yearly Emissions Trajectory")
    fig = go.Figure()
    if col_bau:
        fig.add_trace(go.Scatter(x=df['Year'], y=df[col_bau], name='BAU', line=dict(color='#8B949E', dash='dash')))
    if col_target:
        fig.add_trace(go.Scatter(x=df['Year'], y=df[col_target], name='Target', line=dict(color='#2BD6B4', width=3)))
    fig.update_layout(template="plotly_dark", height=450, xaxis_title="Year", yaxis_title="tCO2eq")
    st.plotly_chart(fig, use_container_width=True)

with tab2:
    st.subheader("Reduction Contribution")
    # 감축 수단 키워드 (투자, 비용 제외)
    keywords = ['태양광', 'EV', '설비', 'PPA', 'REC', '냉매', '수소', '전환', '효율']
    levers = []
    for k in keywords:
        found = [c for c in df.columns if k in c and '비용' not in c and '투자' not in c and '금액' not in c]
        levers.extend(found)
    levers = list(set(levers))
    
    if levers:
        fig2 = px.bar(df, x='Year', y=levers, template="plotly_dark", title="Annual Reduction Amount")
        fig2.update_layout(height=450, barmode='stack')
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("ℹ️ 감축 수단 데이터('태양광', 'PPA' 등)가 식별되지 않았습니다.")

with tab3:
    st.subheader("Investment Trends")
    col_costs = [c for c in df.columns if '투자' in c or '비용' in c]
    if col_costs:
        fig3 = px.bar(df, x='Year', y=col_costs, template="plotly_dark")
        fig3.update_layout(height=450)
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("ℹ️ 투자/비용 데이터가 식별되지 않았습니다.")

# -----------------------------------------------------------------------------
# 7. 하단 테이블
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader(f"📑 Analysis Report: {selected_year}")
sub_df = df[df['Year'] <= selected_year]
cumsum = sub_df.sum(numeric_only=True)

col1, col2 = st.columns(2)
with col1:
    st.markdown("**1. 온실가스 감축 현황**")
    if levers:
        t1 = pd.DataFrame({
            "구분": levers,
            f"{selected_year}년": [curr[c] for c in levers],
            "누적": [cumsum[c] for c in levers]
        })
        st.dataframe(t1.style.format("{:,.1f}"), use_container_width=True)

with col2:
    st.markdown("**2. 투자 집행 현황**")
    if col_costs:
        t2 = pd.DataFrame({
            "구분": col_costs,
            f"{selected_year}년": [curr[c] for c in col_costs],
            "누적": [cumsum[c] for c in col_costs]
        })
        st.dataframe(t2.style.format("{:,.0f}"), use_container_width=True)

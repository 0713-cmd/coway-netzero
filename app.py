import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# -----------------------------------------------------------------------------
# 1. 디자인 및 페이지 설정 (Premium Dark Theme & 로딩 제거)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="COWAY Net-Zero Dashboard", page_icon="🌿", layout="wide")

st.markdown("""
<style>
    /* 전체 배경 및 폰트 */
    .stApp { background-color: #0E1117; color: #FAFAFA; font-family: 'Suit', sans-serif; }
    
    /* 사이드바 */
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    
    /* KPI 카드 디자인 */
    .metric-card {
        background-color: #1F252E; border: 1px solid #30363D; border-radius: 12px;
        padding: 24px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-title { color: #8B949E; font-size: 15px; margin-bottom: 8px; font-weight: 500; }
    .metric-value { color: #2BD6B4; font-size: 32px; font-weight: 700; }
    .metric-unit { color: #8B949E; font-size: 14px; margin-left: 4px; }
    
    /* 헤더 및 텍스트 */
    h1, h2, h3 { color: #FFFFFF !important; font-weight: 700; }
    
    /* 로딩 애니메이션 숨기기 (쾌적한 환경) */
    [data-testid="stStatusWidget"] { visibility: hidden; }
    .stDeployButton { visibility: hidden; }
    
    /* 테이블 스타일 */
    .dataframe { font-size: 14px !important; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 지능형 데이터 로드 함수 (엑셀 서식 자동 파파괴)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data():
    # 1. 폴더 내의 아무 CSV 파일이나 찾음
    target_file = None
    files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    if not files:
        return None, "CSV 파일을 찾을 수 없습니다."
    
    # 우선순위: data.csv -> 그 외 아무거나
    target_file = 'data.csv' if 'data.csv' in files else files[0]
    
    try:
        # 인코딩 자동 감지 시도 (한글 깨짐 방지)
        try:
            df_raw = pd.read_csv(target_file, header=None, encoding='utf-8')
        except UnicodeDecodeError:
            df_raw = pd.read_csv(target_file, header=None, encoding='cp949')
            
        # 2. 헤더 행(2023, 2024... 가 있는 줄) 찾기
        header_idx = None
        for i, row in df_raw.iterrows():
            row_str = str(row.values)
            # 2023과 2030이 동시에 있는 줄을 헤더로 간주
            if '2023' in row_str and '2030' in row_str:
                header_idx = i
                break
        
        if header_idx is None:
            return None, "데이터에서 연도(2023~2050)를 찾을 수 없습니다."
            
        # 3. 데이터프레임 재설정
        df = df_raw.iloc[header_idx:].reset_index(drop=True)
        df.columns = df.iloc[0] # 첫 줄을 컬럼명으로
        df = df[1:] # 헤더 중복 제거
        
        # 4. 컬럼 정리
        # 첫 번째 유효한 문자열 컬럼을 'Category'로 지정
        df.columns = [str(c).strip() for c in df.columns]
        
        year_cols = []
        cat_col = None
        
        # 연도 컬럼 식별
        for c in df.columns:
            if c.replace('.0','').isdigit() and int(float(c)) >= 2023:
                year_cols.append(c)
        
        # 카테고리 컬럼 식별 (연도가 아니면서 데이터가 있는 첫번째 컬럼)
        for c in df.columns:
            if c not in year_cols and "nan" not in c.lower() and "unnamed" not in c.lower():
                cat_col = c
                break
        if cat_col is None: cat_col = df.columns[0] # 못 찾으면 무조건 첫번째
        
        # 5. 최종 데이터프레임 구축
        df_clean = df[[cat_col] + year_cols].copy()
        df_clean.columns = ['Category'] + [str(int(float(y))) for y in year_cols] # 컬럼명 깔끔하게(2023)
        
        # 6. 전치 (Transpose)
        df_t = df_clean.set_index('Category').T
        df_t.index.name = 'Year'
        df_t = df_t.reset_index()
        
        # 7. 숫자 변환 (쉼표, 공백 제거)
        for col in df_t.columns:
            if col != 'Year':
                df_t[col] = df_t[col].astype(str).str.replace(',', '').str.replace(' ', '').apply(pd.to_numeric, errors='coerce').fillna(0)
        
        df_t['Year'] = df_t['Year'].astype(int)
        
        return df_t, None
        
    except Exception as e:
        return None, str(e)

# 데이터 로드 실행
df, error_msg = load_data()

if df is None:
    st.error(f"🚨 데이터 로드 실패: {error_msg}")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바 (연도 선택)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🌍 Net-Zero Strategy")
    st.markdown("---")
    selected_year = st.slider("📅 분석 대상 연도", 2023, 2050, 2030)
    st.caption(f"Analysis Target: {selected_year} Year")
    
    st.markdown("---")
    st.markdown("### 🔍 Dashboard Info")
    st.info("코웨이 넷제로 달성을 위한\n연도별 로드맵 및 감축 수단 분석")

# 메인 타이틀
st.title("COWAY Net-Zero Roadmap Dashboard")
st.markdown(f"#### 🚀 Vision 2050: Towards Carbon Neutrality (Base: {selected_year})")

# -----------------------------------------------------------------------------
# 4. 데이터 매핑 (키워드로 자동 찾기)
# -----------------------------------------------------------------------------
def get_col(keywords):
    for col in df.columns:
        for k in keywords:
            if k in col:
                return col
    return None

col_bau = get_col(["BAU", "예상", "전망", "Business"])
col_target = get_col(["목표", "Target"])
col_invest = get_col(["투자", "Investment"])

# -----------------------------------------------------------------------------
# 5. KPI 메트릭 (상단 카드)
# -----------------------------------------------------------------------------
curr = df[df['Year'] == selected_year].iloc[0]

c1, c2, c3, c4 = st.columns(4)

with c1:
    val = curr[col_bau] if col_bau else 0
    st.markdown(f'''<div class="metric-card"><div class="metric-title">BAU ({selected_year})</div>
    <div class="metric-value">{val:,.0f} <span class="metric-unit">t</span></div></div>''', unsafe_allow_html=True)

with c2:
    val = curr[col_target] if col_target else 0
    st.markdown(f'''<div class="metric-card"><div class="metric-title">Target ({selected_year})</div>
    <div class="metric-value" style="color:#FFD700;">{val:,.0f} <span class="metric-unit">t</span></div></div>''', unsafe_allow_html=True)

with c3:
    reduc = (curr[col_bau] - curr[col_target]) if (col_bau and col_target) else 0
    st.markdown(f'''<div class="metric-card"><div class="metric-title">Reduction Gap</div>
    <div class="metric-value" style="color:#FF4B4B;">{reduc:,.0f} <span class="metric-unit">t</span></div></div>''', unsafe_allow_html=True)

with c4:
    val = curr[col_invest] if col_invest else 0
    st.markdown(f'''<div class="metric-card"><div class="metric-title">Investment</div>
    <div class="metric-value" style="color:#1E90FF;">{val/100000000:,.1f} <span class="metric-unit">억</span></div></div>''', unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 6. 메인 차트 탭
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📉 1. 넷제로 로드맵 분석", "📊 2. 넷제로 감축 수단", "💰 3. 연도별 투자 및 비용"])

# --- TAB 1: 로드맵 분석 ---
with tab1:
    st.subheader("연도별 온실가스 배출량 전망 (BAU vs Target)")
    fig = go.Figure()
    
    if col_bau:
        fig.add_trace(go.Scatter(x=df['Year'], y=df[col_bau], name='BAU (전망)', 
                                line=dict(color='#8B949E', dash='dash')))
    if col_target:
        fig.add_trace(go.Scatter(x=df['Year'], y=df[col_target], name='Target (목표)', 
                                line=dict(color='#2BD6B4', width=4)))
        
    # 감축 영역 색칠
    if col_bau and col_target:
        fig.add_trace(go.Scatter(x=df['Year'], y=df[col_target], fill='tonexty', 
                                fillcolor='rgba(43, 214, 180, 0.1)', line=dict(width=0), 
                                showlegend=False, hoverinfo='skip'))

    fig.update_layout(template="plotly_dark", height=500, xaxis_title="Year", yaxis_title="tCO2eq", 
                      hovermode="x unified", legend=dict(orientation="h", y=1.1))
    st.plotly_chart(fig, use_container_width=True)

# --- TAB 2: 감축 수단 (구성성분 그래프) ---
with tab2:
    st.subheader("감축 수단별 기여도 분석 (Stacked Chart)")
    
    # 감축 수단 키워드 (여기에 포함된 단어가 있는 행만 그래프로 그림)
    # 비용, 투자, 배출량 같은 단어가 들어간 건 제외
    lever_keywords = ['태양광', 'EV', '설비', 'PPA', 'REC', '냉매', '수소', '전환', '효율', '상쇄', '감축']
    exclude_keywords = ['비용', '투자', '금액', '배출량', 'BAU', '목표']
    
    levers = []
    for col in df.columns:
        # 1. 감축 키워드가 포함되어 있고
        if any(k in col for k in lever_keywords):
            # 2. 제외 키워드는 없어야 함
            if not any(ex in col for ex in exclude_keywords):
                levers.append(col)
    
    # 중복 제거
    levers = list(set(levers))
    
    if levers:
        fig2 = px.bar(df, x='Year', y=levers, title="연도별 감축 수단 구성",
                      color_discrete_sequence=px.colors.qualitative.Set3)
        fig2.update_layout(template="plotly_dark", height=500, barmode='stack', 
                           xaxis_title="Year", yaxis_title="Reduction (tCO2eq)",
                           hovermode="x unified", legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.warning("⚠️ 감축 수단 데이터(태양광, PPA 등)를 식별하지 못했습니다. 엑셀의 '구분' 열 이름을 확인해주세요.")

# --- TAB 3: 투자 및 비용 ---
with tab3:
    st.subheader("연도별 투자 및 감축 비용 추이")
    
    cost_cols = [c for c in df.columns if ('투자' in c or '비용' in c or '예산' in c) and '단가' not in c]
    
    if cost_cols:
        fig3 = px.bar(df, x='Year', y=cost_cols, title="투자 및 비용 집행 현황",
                      template="plotly_dark", barmode='group')
        fig3.update_layout(height=500, xaxis_title="Year", yaxis_title="Amount (KRW)",
                           hovermode="x unified", legend=dict(orientation="h", y=1.1))
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.warning("⚠️ 투자 또는 비용 관련 데이터를 찾을 수 없습니다.")

# -----------------------------------------------------------------------------
# 7. 하단 상세 테이블 (누적 자동 계산)
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader(f"📑 상세 분석 보고서 ({selected_year}년 기준)")

# 선택 연도까지의 데이터 필터링
sub_df = df[df['Year'] <= selected_year]
# 누적 합계 계산
cumsum = sub_df.sum(numeric_only=True)

col_t1, col_t2 = st.columns(2)

# 테이블 1: 온실가스 감축 현황
with col_t1:
    st.markdown("#### 1. 온실가스 세부 현황")
    if levers:
        t1_data = []
        for l in levers:
            t1_data.append({
                "구분": l,
                f"{selected_year}년 실적 (t)": curr[l],
                f"누적 (2023~{selected_year}) (t)": cumsum[l]
            })
        t1_df = pd.DataFrame(t1_data)
        # 표 그리기 (숫자 포맷팅)
        st.dataframe(t1_df.style.format({
            f"{selected_year}년 실적 (t)": "{:,.1f}",
            f"누적 (2023~{selected_year}) (t)": "{:,.1f}"
        }), use_container_width=True, hide_index=True)
    else:
        st.info("표시할 감축 데이터가 없습니다.")

# 테이블 2: 투자 및 비용 현황
with col_t2:
    st.markdown("#### 2. 투자 및 감축비용 세부 현황")
    if cost_cols:
        t2_data = []
        for c in cost_cols:
            t2_data.append({
                "구분": c,
                f"{selected_year}년 집행 (원)": curr[c],
                f"누적 (2023~{selected_year}) (원)": cumsum[c]
            })
        t2_df = pd.DataFrame(t2_data)
        st.dataframe(t2_df.style.format({
            f"{selected_year}년 집행 (원)": "{:,.0f}",
            f"누적 (2023~{selected_year}) (원)": "{:,.0f}"
        }), use_container_width=True, hide_index=True)
    else:
        st.info("표시할 비용 데이터가 없습니다.")

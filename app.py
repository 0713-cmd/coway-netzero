import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go
import os

# -----------------------------------------------------------------------------
# 1. 디자인 및 설정 (로딩 제거 & 다크 테마)
# -----------------------------------------------------------------------------
st.set_page_config(page_title="COWAY Net-Zero Dashboard", page_icon="🌿", layout="wide")

st.markdown("""
<style>
    .stApp { background-color: #0E1117; color: #FAFAFA; font-family: 'Suit', sans-serif; }
    [data-testid="stSidebar"] { background-color: #161B22; border-right: 1px solid #30363D; }
    
    /* KPI 카드 스타일 */
    .metric-card {
        background-color: #1F252E; border: 1px solid #30363D; border-radius: 12px;
        padding: 24px; text-align: center; box-shadow: 0 4px 6px rgba(0,0,0,0.3);
    }
    .metric-title { color: #8B949E; font-size: 15px; margin-bottom: 8px; }
    .metric-value { color: #2BD6B4; font-size: 32px; font-weight: 700; }
    .metric-unit { color: #8B949E; font-size: 14px; margin-left: 4px; }
    
    /* 로딩 숨기기 */
    [data-testid="stStatusWidget"] { visibility: hidden; }
    .stDeployButton { visibility: hidden; }
    
    /* 폰트 및 헤더 */
    h1, h2, h3 { color: #FFFFFF !important; font-weight: 700; }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 강력한 데이터 로더 (파일 구조 자동 파괴 기능 탑재)
# -----------------------------------------------------------------------------
@st.cache_data(show_spinner=False)
def load_data():
    # 1. 폴더 내의 아무 CSV 파일이나 찾음
    target_file = None
    files = [f for f in os.listdir('.') if f.endswith('.csv')]
    
    if not files: return None, "CSV 파일을 찾을 수 없습니다."
    target_file = files[0] # 아무거나 잡히는 대로 읽음
    
    try:
        # 헤더 없이 일단 통으로 읽기
        try:
            df_raw = pd.read_csv(target_file, header=None, encoding='utf-8')
        except:
            df_raw = pd.read_csv(target_file, header=None, encoding='cp949')
            
        # 2. "2023"이라는 숫자가 있는 행(Row)을 헤더로 찾기
        header_idx = None
        year_start_col = None
        
        for r_idx, row in df_raw.iterrows():
            row_vals = [str(v).replace('.0','') for v in row.values] # 2023.0 -> 2023 처리
            if '2023' in row_vals and '2030' in row_vals:
                header_idx = r_idx
                # 2023이 시작되는 열(Column) 위치 찾기
                for c_idx, val in enumerate(row_vals):
                    if val == '2023':
                        year_start_col = c_idx
                        break
                break
        
        if header_idx is None: return None, "데이터에서 연도(2023)를 찾을 수 없습니다."
        
        # 3. 데이터 추출 (헤더 행부터 끝까지)
        # 구분 컬럼은 보통 '2023'보다 앞에 있음. (차장님 파일은 Column 1이 '구분'임)
        category_col_idx = 1 
        
        # 헤더 설정
        years = df_raw.iloc[header_idx, year_start_col:].astype(str).str.replace('.0','').tolist()
        
        # 데이터 정제
        data_rows = []
        for r_idx in range(header_idx + 1, len(df_raw)):
            row = df_raw.iloc[r_idx]
            cat_name = row[category_col_idx]
            
            # 구분이 비어있으면 건너뜀
            if pd.isna(cat_name) or str(cat_name).strip() == '': continue
            
            # 값 추출
            vals = row[year_start_col:].tolist()
            
            # 딕셔너리 생성
            entry = {'Category': str(cat_name).strip()}
            for y, v in zip(years, vals):
                # 숫자 변환 (쉼표 제거)
                try:
                    entry[y] = float(str(v).replace(',', ''))
                except:
                    entry[y] = 0.0
            data_rows.append(entry)
            
        df_clean = pd.DataFrame(data_rows)
        
        # 전치 (그래프 그리기 좋게 변환)
        df_t = df_clean.set_index('Category').T
        df_t.index.name = 'Year'
        df_t = df_t.reset_index()
        
        # 연도 정수화 (2023 ~ 2050)
        df_t = df_t[df_t['Year'].apply(lambda x: str(x).isdigit() and int(x) >= 2023)]
        df_t['Year'] = df_t['Year'].astype(int)
        
        return df_t, None
        
    except Exception as e:
        return None, str(e)

# 데이터 로드
df, error_msg = load_data()

if df is None:
    st.error(f"🚨 오류 발생: {error_msg}")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 대시보드 UI
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🌍 Net-Zero Strategy")
    st.markdown("---")
    selected_year = st.slider("📅 분석 대상 연도", 2023, 2050, 2030)
    st.info(f"Target Year: **{selected_year}**")

st.title("COWAY Net-Zero Roadmap Dashboard")
st.markdown(f"##### Vision 2050: 탄소중립 달성을 위한 여정 (Base: {selected_year})")

# 데이터 매핑 함수
def find_col(keywords):
    for col in df.columns:
        for k in keywords:
            if k in col: return col
    return None

col_bau = find_col(["BAU", "예상", "전망"])
col_target = find_col(["목표"])
col_invest = find_col(["투자", "Investment"]) # 투자 비용

# -----------------------------------------------------------------------------
# 4. KPI 카드
# -----------------------------------------------------------------------------
curr = df[df['Year'] == selected_year].iloc[0]

c1, c2, c3, c4 = st.columns(4)
with c1:
    val = curr[col_bau] if col_bau else 0
    st.markdown(f'''<div class="metric-card"><div class="metric-title">BAU (전망)</div>
    <div class="metric-value">{val:,.0f}<span class="metric-unit">t</span></div></div>''', unsafe_allow_html=True)
with c2:
    val = curr[col_target] if col_target else 0
    st.markdown(f'''<div class="metric-card"><div class="metric-title">Target (목표)</div>
    <div class="metric-value" style="color:#FFD700;">{val:,.0f}<span class="metric-unit">t</span></div></div>''', unsafe_allow_html=True)
with c3:
    gap = (curr[col_bau] - curr[col_target]) if (col_bau and col_target) else 0
    st.markdown(f'''<div class="metric-card"><div class="metric-title">Reduction Gap</div>
    <div class="metric-value" style="color:#FF4B4B;">{gap:,.0f}<span class="metric-unit">t</span></div></div>''', unsafe_allow_html=True)
with c4:
    # 투자비가 보통 원 단위라 억 단위로 변환
    inv = 0
    for c in df.columns:
        if '투자' in c and '비용' in c: inv += curr[c]
    st.markdown(f'''<div class="metric-card"><div class="metric-title">Est. Investment</div>
    <div class="metric-value" style="color:#1E90FF;">{inv/100000000:,.1f}<span class="metric-unit">억</span></div></div>''', unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. 탭 구성 (그래프)
# -----------------------------------------------------------------------------
tab1, tab2, tab3 = st.tabs(["📉 1. 넷제로 로드맵", "📊 2. 감축 수단 분석", "💰 3. 투자 비용"])

# TAB 1: 로드맵
with tab1:
    fig = go.Figure()
    if col_bau:
        fig.add_trace(go.Scatter(x=df['Year'], y=df[col_bau], name='BAU (전망)', line=dict(color='#8B949E', dash='dash')))
    if col_target:
        fig.add_trace(go.Scatter(x=df['Year'], y=df[col_target], name='Target (목표)', line=dict(color='#2BD6B4', width=4)))
    
    if col_bau and col_target:
        fig.add_trace(go.Scatter(x=df['Year'], y=df[col_target], fill='tonexty', fillcolor='rgba(43, 214, 180, 0.1)', line=dict(width=0), showlegend=False))
        
    fig.update_layout(template="plotly_dark", height=450, xaxis_title="Year", yaxis_title="Emissions (tCO2eq)", hovermode="x unified")
    st.plotly_chart(fig, use_container_width=True)

# TAB 2: 감축 수단 (구성요소)
with tab2:
    # 감축 수단 키워드 (여기에 해당하는 행만 그래프로 그림)
    # 태양광, EV, PPA, REC, 설비, 냉매 등등
    redu_keywords = ['태양광', 'EV', '설비', 'PPA', 'REC', '냉매', '수소', '감축']
    # 제외할 키워드 (비용, 투자, 배출량 등)
    exclude = ['비용', '투자', '금액', '배출량', '필요량']
    
    levers = []
    for col in df.columns:
        if any(k in col for k in redu_keywords) and not any(e in col for e in exclude):
            levers.append(col)
            
    if levers:
        fig2 = px.bar(df, x='Year', y=levers, title="연도별 감축 수단 구성 (Stacked)", template="plotly_dark",
                      color_discrete_sequence=px.colors.qualitative.Pastel)
        fig2.update_layout(barmode='stack', height=450, hovermode="x unified")
        st.plotly_chart(fig2, use_container_width=True)
    else:
        st.info("ℹ️ 감축 수단 데이터(태양광, PPA 등)를 찾을 수 없습니다. 엑셀의 '구분' 이름을 확인해주세요.")

# TAB 3: 투자 비용
with tab3:
    cost_cols = [c for c in df.columns if ('투자' in c or '비용' in c or '예산' in c) and '단가' not in c]
    if cost_cols:
        fig3 = px.bar(df, x='Year', y=cost_cols, title="연도별 투자 집행 계획", template="plotly_dark")
        fig3.update_layout(height=450, hovermode="x unified")
        st.plotly_chart(fig3, use_container_width=True)
    else:
        st.info("ℹ️ 투자 비용 데이터를 찾을 수 없습니다.")

# -----------------------------------------------------------------------------
# 6. 하단 상세 테이블 (누적 자동 계산)
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader(f"📑 상세 데이터 보고서 ({selected_year}년 기준)")

sub_df = df[df['Year'] <= selected_year]
cumsum = sub_df.sum(numeric_only=True)

c1, c2 = st.columns(2)
with c1:
    st.markdown("**1. 온실가스 감축 상세**")
    if levers:
        t1 = pd.DataFrame({
            "구분": levers,
            f"{selected_year}년 실적": [curr[l] for l in levers],
            f"누적 (2023~{selected_year})": [cumsum[l] for l in levers]
        })
        st.dataframe(t1.style.format("{:,.1f}"), use_container_width=True, hide_index=True)

with c2:
    st.markdown("**2. 투자 및 비용 상세**")
    if cost_cols:
        t2 = pd.DataFrame({
            "구분": cost_cols,
            f"{selected_year}년 집행": [curr[c] for c in cost_cols],
            f"누적 (2023~{selected_year})": [cumsum[c] for c in cost_cols]
        })
        st.dataframe(t2.style.format("{:,.0f}"), use_container_width=True, hide_index=True)

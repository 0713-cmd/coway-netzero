import streamlit as st
import pandas as pd
import plotly.express as px
import plotly.graph_objects as go

# -----------------------------------------------------------------------------
# 1. 페이지 설정 및 프리미엄 디자인 (Dark & Gold Theme)
# -----------------------------------------------------------------------------
st.set_page_config(
    page_title="COWAY Net-Zero Dashboard",
    page_icon="🌿",
    layout="wide",
    initial_sidebar_state="expanded"
)

# Custom CSS for Premium Look
st.markdown("""
<style>
    /* 전체 배경 및 폰트 */
    .stApp {
        background-color: #0E1117;
        color: #FAFAFA;
        font-family: 'Helvetica Neue', sans-serif;
    }
    /* 사이드바 스타일 */
    [data-testid="stSidebar"] {
        background-color: #161B22;
        border-right: 1px solid #30363D;
    }
    /* 카드형 컨테이너 스타일 */
    .metric-card {
        background-color: #1F252E;
        border: 1px solid #30363D;
        border-radius: 10px;
        padding: 20px;
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.3);
        text-align: center;
    }
    .metric-title {
        color: #8B949E;
        font-size: 14px;
        margin-bottom: 5px;
    }
    .metric-value {
        color: #2BD6B4; /* 민트색 포인트 */
        font-size: 28px;
        font-weight: bold;
    }
    /* 헤더 스타일 */
    h1, h2, h3 {
        color: #FFFFFF !important;
        font-weight: 700;
    }
    /* 표 스타일 */
    .dataframe {
        font-size: 14px !important;
        background-color: #1F252E !important;
    }
</style>
""", unsafe_allow_html=True)

# -----------------------------------------------------------------------------
# 2. 데이터 로드 및 전처리 (Transpose Logic)
# -----------------------------------------------------------------------------
@st.cache_data
def load_data():
    # CSV 파일 로드 (헤더가 여러 줄일 수 있으므로 넉넉히 읽고 처리)
    df_raw = pd.read_csv("data.csv", header=None)
    
    # '2023'년이 시작되는 행 찾기 (데이터 구조에 따라 유동적 대응)
    start_row = 0
    for idx, row in df_raw.iterrows():
        if "2023" in str(row.values):
            start_row = idx
            break
            
    # 해당 행을 헤더로 설정
    df = pd.read_csv("data.csv", header=start_row)
    
    # 첫 번째 컬럼(구분)을 인덱스로 설정하고 전치(Transpose)
    # 엑셀이 가로로 길기 때문에 세로(DB형태)로 바꿔야 그래프를 그리기 쉬움
    df = df.set_index(df.columns[0]).T
    
    # 인덱스 이름 정리 (연도)
    df.index.name = 'Year'
    df = df.reset_index()
    
    # 데이터 정제 (숫자 변환, 결측치 처리)
    # 실제 CSV의 Row Name(구분)을 정확히 매핑해야 합니다.
    # 사용자가 업로드한 파일의 일반적인 용어 매칭
    
    cols = df.columns
    # 숫자로 변환 (쉼표 제거)
    for col in cols:
        if col != 'Year':
            try:
                df[col] = df[col].astype(str).str.replace(',', '').apply(pd.to_numeric, errors='coerce').fillna(0)
            except:
                pass
                
    # Year 컬럼도 숫자로
    df['Year'] = pd.to_numeric(df['Year'], errors='coerce')
    df = df.dropna(subset=['Year']) # 연도가 없는 행 삭제
    df['Year'] = df['Year'].astype(int)
    
    return df

try:
    df = load_data()
except Exception as e:
    st.error(f"데이터를 불러오는 중 오류가 발생했습니다: {e}")
    st.info("CSV 파일 형식이 '구분' 행에 연도(2023, 2024...)가 있는 가로형 데이터인지 확인해주세요.")
    st.stop()

# -----------------------------------------------------------------------------
# 3. 사이드바 (필터 및 로고)
# -----------------------------------------------------------------------------
with st.sidebar:
    st.title("🌍 Net-Zero Strategy")
    st.markdown("---")
    
    # 분석 연도 선택
    selected_year = st.slider("📅 분석 대상 연도", 2023, 2050, 2030)
    
    st.markdown("---")
    st.markdown("### ⚙️ Dashboard Settings")
    show_data = st.checkbox("Show Raw Data", value=False)
    
    st.info(f"현재 **{selected_year}년** 기준 분석 중입니다.")

# -----------------------------------------------------------------------------
# 4. 메인 대시보드
# -----------------------------------------------------------------------------
st.title("COWAY Net-Zero Roadmap Dashboard")
st.markdown(f"##### Vision 2050: Sustainable Future & Carbon Neutrality")

# (1) 핵심 KPI 카드 (선택된 연도 기준)
current_data = df[df['Year'] == selected_year].iloc[0]

# 컬럼 매핑 (CSV 파일의 '구분' 열 이름과 일치해야 함 - 유동적으로 찾기)
def get_col_val(keyword):
    matches = [c for c in df.columns if keyword in c]
    return matches[0] if matches else None

col_bau = get_col_val("예상") or get_col_val("BAU")
col_target = get_col_val("목표")
col_invest = get_col_val("투자")

c1, c2, c3, c4 = st.columns(4)
with c1:
    val = current_data[col_bau] if col_bau else 0
    st.markdown(f"""<div class="metric-card"><div class="metric-title">BAU Emissions ({selected_year})</div><div class="metric-value">{val:,.0f} t</div></div>""", unsafe_allow_html=True)
with c2:
    val = current_data[col_target] if col_target else 0
    st.markdown(f"""<div class="metric-card"><div class="metric-title">Target Emissions ({selected_year})</div><div class="metric-value" style="color:#FFD700;">{val:,.0f} t</div></div>""", unsafe_allow_html=True)
with c3:
    # 감축량 계산 (BAU - Target)
    bau_val = current_data[col_bau] if col_bau else 0
    target_val = current_data[col_target] if col_target else 0
    reduction = bau_val - target_val
    st.markdown(f"""<div class="metric-card"><div class="metric-title">Total Reduction</div><div class="metric-value" style="color:#FF4B4B;">{reduction:,.0f} t</div></div>""", unsafe_allow_html=True)
with c4:
    val = current_data[col_invest] if col_invest else 0
    st.markdown(f"""<div class="metric-card"><div class="metric-title">Est. Investment</div><div class="metric-value" style="color:#1E90FF;">{val/100000000:,.1f} 억</div></div>""", unsafe_allow_html=True)

st.markdown("---")

# -----------------------------------------------------------------------------
# 5. 그래프 섹션
# -----------------------------------------------------------------------------

# Tab 구성
tab1, tab2, tab3 = st.tabs(["📉 넷제로 로드맵", "📊 감축 수단 분석", "💰 투자 및 비용 분석"])

with tab1:
    st.subheader("Yearly Emissions Trajectory (2023-2050)")
    
    # BAU vs Target 라인 차트
    fig_roadmap = go.Figure()
    
    if col_bau:
        fig_roadmap.add_trace(go.Scatter(x=df['Year'], y=df[col_bau], mode='lines+markers', name='BAU (예상 배출량)', line=dict(color='#8B949E', dash='dash')))
    if col_target:
        fig_roadmap.add_trace(go.Scatter(x=df['Year'], y=df[col_target], mode='lines+markers', name='Target (목표 배출량)', line=dict(color='#2BD6B4', width=3)))
        
    # 영역 채우기 (감축량)
    if col_bau and col_target:
        fig_roadmap.add_trace(go.Scatter(
            x=df['Year'], y=df[col_bau],
            fill=None, mode='lines', line_color='rgba(0,0,0,0)', showlegend=False, hoverinfo='skip'
        ))
        fig_roadmap.add_trace(go.Scatter(
            x=df['Year'], y=df[col_target],
            fill='tonexty', mode='lines', fillcolor='rgba(43, 214, 180, 0.2)', line_color='rgba(0,0,0,0)',
            name='Reduction Area'
        ))

    fig_roadmap.update_layout(
        template="plotly_dark",
        xaxis_title="Year",
        yaxis_title="Emissions (tCO2eq)",
        height=500,
        hovermode="x unified"
    )
    st.plotly_chart(fig_roadmap, use_container_width=True)

with tab2:
    st.subheader("Reduction Contribution by Levers")
    
    # 감축 수단 컬럼 찾기 (키워드로 자동 매핑)
    levers = ['태양광', 'EV', '설비', 'PPA', 'REC', '냉매']
    found_levers = []
    for l in levers:
        matches = [c for c in df.columns if l in c and "비용" not in c and "투자" not in c] # 비용이나 투자가 아닌 순수 감축량 컬럼
        found_levers.extend(matches)
    
    if found_levers:
        # Stacked Bar Chart
        fig_levers = px.bar(
            df, 
            x='Year', 
            y=found_levers, 
            title="Annual GHG Reduction by Source",
            color_discrete_sequence=px.colors.qualitative.Pastel
        )
        fig_levers.update_layout(
            template="plotly_dark",
            barmode='stack',
            height=500,
            xaxis_title="Year",
            yaxis_title="Reduction Amount (tCO2eq)"
        )
        st.plotly_chart(fig_levers, use_container_width=True)
    else:
        st.warning("감축 수단(태양광, EV, PPA 등)과 관련된 데이터 컬럼을 CSV에서 찾을 수 없습니다. 컬럼명에 해당 단어가 포함되어 있는지 확인해주세요.")

with tab3:
    st.subheader("Investment & Abatement Cost Analysis")
    
    # 비용 관련 컬럼
    col_inv = get_col_val("투자")
    col_cost = get_col_val("비용") or get_col_val("단가")
    
    if col_inv:
        fig_cost = go.Figure()
        
        # 막대: 투자비
        fig_cost.add_trace(go.Bar(
            x=df['Year'], y=df[col_inv], 
            name='Investment (투자비)',
            marker_color='#1E90FF',
            yaxis='y1'
        ))
        
        # 선: 감축 비용 (있다면)
        if col_cost:
            fig_cost.add_trace(go.Scatter(
                x=df['Year'], y=df[col_cost],
                name='Abatement Cost (감축단가)',
                mode='lines+markers',
                marker_color='#FFD700',
                yaxis='y2'
            ))

        fig_cost.update_layout(
            template="plotly_dark",
            height=500,
            xaxis_title="Year",
            yaxis=dict(title="Investment (KRW)", side="left"),
            yaxis2=dict(title="Cost per Ton", side="right", overlaying="y", showgrid=False),
            legend=dict(x=0.01, y=0.99)
        )
        st.plotly_chart(fig_cost, use_container_width=True)
    else:
        st.warning("투자비 관련 데이터를 찾을 수 없습니다.")

# -----------------------------------------------------------------------------
# 6. 상세 현황 테이블 (누적 포함)
# -----------------------------------------------------------------------------
st.markdown("---")
st.subheader(f"📑 Detailed Analysis Report: {selected_year}")

# 누적 데이터 계산 (2023 ~ 선택 연도)
df_filtered = df[df['Year'] <= selected_year]
cumulative_sum = df_filtered.sum(numeric_only=True)
cumulative_sum['Year'] = "Cumulative (2023~)" # 라벨링

# 현재 연도 데이터
current_year_row = df[df['Year'] == selected_year].iloc[0]

# (1) 온실가스 세부 현황
st.markdown("#### 1. 온실가스 감축 세부 현황")
cols_ghg = [c for c in df.columns if any(x in c for x in ['배출', '감축', '태양광', 'PPA', 'EV', 'REC'])]
if cols_ghg:
    # 표 데이터 구성
    table_ghg = pd.DataFrame({
        "구분": cols_ghg,
        f"{selected_year}년 실적": [current_year_row[c] for c in cols_ghg],
        f"누적 (2023~{selected_year})": [cumulative_sum[c] for c in cols_ghg]
    })
    # 포맷팅 (소수점)
    st.dataframe(
        table_ghg.style.format({f"{selected_year}년 실적": "{:,.1f}", f"누적 (2023~{selected_year})": "{:,.1f}"})
        .background_gradient(cmap="Greens", subset=[f"{selected_year}년 실적"]),
        use_container_width=True
    )

# (2) 투자 및 비용 세부 현황
st.markdown("#### 2. 투자 및 감축비용 세부 현황")
cols_money = [c for c in df.columns if any(x in c for x in ['투자', '비용', '금액', '예산'])]
if cols_money:
    table_money = pd.DataFrame({
        "구분": cols_money,
        f"{selected_year}년 집행": [current_year_row[c] for c in cols_money],
        f"누적 (2023~{selected_year})": [cumulative_sum[c] for c in cols_money]
    })
    st.dataframe(
        table_money.style.format({f"{selected_year}년 집행": "{:,.0f}", f"누적 (2023~{selected_year})": "{:,.0f}"})
        .background_gradient(cmap="Blues", subset=[f"{selected_year}년 집행"]),
        use_container_width=True
    )

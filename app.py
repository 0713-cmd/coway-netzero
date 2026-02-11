import streamlit as st
import os

st.set_page_config(page_title="파일 확인 모드", layout="wide")

st.title("📂 파일 시스템 정밀 진단")

# 현재 폴더에 있는 모든 파일 가져오기
files = os.listdir('.')

st.write("### 현재 GitHub 저장소에 있는 파일 목록:")

# 파일 목록 출력
found_csv = False
for f in files:
    if f == 'data.csv':
        st.success(f"✅ {f} (정상! 이 파일이 있어야 합니다)")
        found_csv = True
    elif f.endswith('.csv'):
        st.warning(f"⚠️ {f} (CSV긴 한데 이름이 'data.csv'가 아닙니다)")
    else:
        st.info(f"ℹ️ {f} (기타 파일)")

st.markdown("---")

if found_csv:
    st.balloons()
    st.success("데이터 파일(data.csv)이 정확히 있습니다! 코드가 왜 못 읽는지 확인해보겠습니다.")
else:
    st.error("🚨 'data.csv' 파일이 없습니다!")
    st.markdown("""
    **해결 방법:**
    1. GitHub 파일 목록으로 가세요.
    2. 이상한 이름의 파일(예: `data.csv.xlsx` 등)을 클릭하세요.
    3. 연필 아이콘(✏️)을 눌러 이름을 정확히 **`data.csv`** 로 수정하세요.
    4. **Commit changes**를 누르세요.
    """)

import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------
# 1. 과목 및 설정 (수정 시 이 부분만 확인하세요)
# ---------------------------------------------------------
SUBJECT_NAME = "소비자재무설계2_001 퀴즈"
CURRENT_WEEK = "11주차"
ADMIN_PASSWORD = "3383"

# 퀴즈 데이터 (수정 가능)
QUIZ_DATA = [
    {"q": "1. 현재가치는 미래가치를 기간에 따른 (___________)로 할인하여 구한다.", "a": "할인율"},
    {"q": "2. 정해진 기간 동안 현금흐름 금액이나 간격 둘 중에 하나라도 동일하게 발생하지 않는 불규칙적인 현금흐름이라면 (_____________)방식으로 현재가치나 미래가치를 구할 수 있다.", "a": "cash flow"},
    {"q": "3. 보유한 기간에 원금 대비 얻은 수익의 비율은?", "a": "보유기간수익률"},
    {"q": "4. 세부기간의 수익률을 곱하여 보유기간의 제곱근(n제곱근)을 취한(적용한) 수익률은?", "a": "기하평균 수익률"},
    {"q": "5. 기대수익률은 예상수익률을 확률로 가중평균한 값으로, 예상수익률에 (_____)을 곱한 기댓값의 합계이다.", "a": "확률"},
    {"q": "6. 빈 칸에 들어갈 적당한 말은? 요구수익률 = 실질무위험수익률 + (_____________) + 위험보상률", "a": "물가상승률"},
    {"q": "7.기대수익률이 요구수익률보다 높은 자산은 투자자들의 선호(투자)가 높아져 가격이 (_____)한다.", "a": "상승"},
]


NUM_QUESTIONS = len(QUIZ_DATA)

# 페이지 설정
st.set_page_config(page_title=f"{SUBJECT_NAME}", layout="wide")

# Supabase 연결 설정
@st.cache_resource
def init_connection() -> Client:
    url = st.secrets["SUPABASE_URL"]
    key = st.secrets["SUPABASE_KEY"]
    return create_client(url, key)

try:
    supabase = init_connection()
except Exception as e:
    st.error("수파베이스 연결 설정(Secrets)이 필요합니다.")

if "submitted_on_this_device" not in st.session_state:
    st.session_state.submitted_on_this_device = False

st.title(f"📊 {SUBJECT_NAME}")

tab1, tab2, tab3 = st.tabs(["✍️ 퀴즈 제출", "🖥️ 제출자 명단 확인", "🔐 성적 분석(교수용)"])

# --- [TAB 1] 학생 제출 화면 ---
with tab1:
    st.header("답안지")
    
    if st.session_state.submitted_on_this_device:
        st.warning("⚠️ 이 기기에서 제출이 완료되었습니다.")
    else:
        with st.form("quiz_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("이름", placeholder="이름")
            with col2:
                student_id = st.text_input("학번", placeholder="학번")
            
            st.divider()
            
            user_responses = []
            for i, item in enumerate(QUIZ_DATA):
                st.markdown(f"**{item['q']}**")
                ans = st.text_input(f"{i+1}번 답안", key=f"q{i}")
                user_responses.append(ans)

            submitted = st.form_submit_button("답안 제출하기")

            if submitted:
                if not name or not student_id:
                    st.error("이름과 학번을 입력해 주세요.")
                else:
                    try:
                        # 수파베이스에서 이번 주차, 해당 학번의 데이터가 있는지 조회
                        existing_data = supabase.table("sm001_quiz_results").select("*").eq("주차", CURRENT_WEEK).eq("학번", student_id).execute()

                        if existing_data.data: # 이미 제출한 기록이 있다면
                            st.error(f"❌ {name} 학생은 이미 제출했습니다.")
                        else:
                            kst = timezone(timedelta(hours=9))
                            now_time = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S")
                            row_dict = {"주차": CURRENT_WEEK, "제출시간": now_time, "이름": name, "학번": student_id}
                            
                            total_correct = 0
                            for i, item in enumerate(QUIZ_DATA, 1):
                                # 영어 대소문자 무시를 위해 .lower() 적용
                                s_ans_set = set(item['a'].replace(" ", "").lower().split(","))
                                u_ans_set = set(user_responses[i-1].replace(" ", "").lower().split(","))
                                
                                is_correct = (s_ans_set == u_ans_set)
                                if is_correct: total_correct += 1
                                row_dict[f"q{i}_답"] = user_responses[i-1]
                                row_dict[f"q{i}_결과"] = "O" if is_correct else "X"
                            
                            row_dict["총점"] = total_correct
                            
                            # 수파베이스에 새 데이터 삽입
                            supabase.table("sm001_quiz_results").insert(row_dict).execute()
                            
                            st.session_state.submitted_on_this_device = True
                            st.success(f"{name} 학생, 제출 성공! ({total_correct}/{NUM_QUESTIONS})")
                            st.rerun() 
                    except Exception as e:
                        st.error("데이터 처리 중 오류가 발생했습니다.")

# --- [TAB 2] 제출 명단 확인 ---
with tab2:
    st.subheader(f"📍 {CURRENT_WEEK} 제출 완료 명단")
    if st.button("🔄 명단 확인/새로고침"):
        try:
            # 수파베이스에서 이번 주차 데이터만 가져옴
            response = supabase.table("sm001_quiz_results").select("*").eq("주차", CURRENT_WEEK).execute()
            today_list = pd.DataFrame(response.data)
            
            if not today_list.empty:
                st.write(f"현재 총 {len(today_list)}명 제출 완료")
                cols = st.columns(6)
                for i, row in enumerate(today_list.itertuples()):
                    cols[i % 6].success(f"✅ {row.이름}")
            else:
                st.write("아직 제출자가 없습니다.")
        except:
            st.error("데이터 로드 실패")

# --- [TAB 3] 성적 분석 ---
with tab3:
    st.header("🔐 관리자 인증")
    admin_pw = st.text_input("비밀번호를 입력하세요", type="password")
    if admin_pw == ADMIN_PASSWORD:
        try:
            # 전체 데이터를 가져와서 분석
            response = supabase.table("sm001_quiz_results").select("*").execute()
            data = pd.DataFrame(response.data)
            
            if not data.empty:
                stats = data.groupby(['학번', '이름'])['총점'].mean().reset_index()
                stats['정답률(%)'] = (stats['총점'] / NUM_QUESTIONS * 100).round(1)
                st.dataframe(stats, use_container_width=True)
                st.download_button("엑셀 다운로드", data=data.to_csv(index=False).encode('utf-8-sig'), file_name=f"{SUBJECT_NAME}_결과.csv", mime="text/csv")
            else:
                st.info("아직 제출된 데이터가 없습니다.")
        except:
            st.error("데이터 로드 실패")

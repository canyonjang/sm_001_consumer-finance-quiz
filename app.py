import streamlit as st
from supabase import create_client, Client
import pandas as pd
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------
# 1. 과목 및 설정 (수정 시 이 부분만 확인하세요)
# ---------------------------------------------------------
SUBJECT_NAME = "소비자재무설계1_001 퀴즈"
CURRENT_WEEK = "15주차"
ADMIN_PASSWORD = "3383"

# 퀴즈 데이터 (수정 가능)
QUIZ_DATA = [
    {"q": "1. (_____________)는 우발이익을 얻고 나면 위험을 더 감수하려 드는 것이다.", "a": "공돈효과"},
    {"q": "2. 일부 투자자들이 자제력을 잃고 보유중인 주식을 공포감에 투매하는 현상을 뜻하는 외래어 표현은? (한글로 쓰세요)", "a": "패닉 셀링"},
    {"q": "3. 손실을 본 사람들이 본전을 찾으려는 욕구가 위험회피 성향보다 강하여, 손실을 만회할 기회가 주어지면 위험을 감수하는 현상은?", "a": "본전찾기 효과"},
    {"q": "4. (_______)은 배당률이 높아 우승 가능성이 거의 없는 말이다. (한글로 쓰세요)", "a": "롱샷"},
    {"q": "5. 현재의 상태가 특별히 나쁘지 않은 한, 손실회피 심리가 발동하여 변화를 시도하지 않는 것을 (_________)편향이라 한다.", "a": "현상유지"},
    {"q": "6. (____________)는 투자업계에서 위험을 측정하는 대표적인 방법이다.", "a": "표준편차"},
    {"q": "7. (______________)는 사람들이 자신에 대한 긍정적인 이미지를 유지하기 위해 과거 투자 성과나 실수를 왜곡하여 기억하게 만든다.", "a": "인지부조화"}
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

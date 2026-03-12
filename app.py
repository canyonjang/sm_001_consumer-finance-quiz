import streamlit as st
from streamlit_gsheets import GSheetsConnection
import pandas as pd
from datetime import datetime, timedelta, timezone

# ---------------------------------------------------------
# 1. 과목 및 설정 (수정 시 이 부분만 확인하세요)
# ---------------------------------------------------------
SUBJECT_NAME = "소비자재무설계1_001 퀴즈"  # [cite: 1]
CURRENT_WEEK = "2주차"           # [cite: 1]
ADMIN_PASSWORD = "3383"          # [cite: 1]

# 퀴즈 데이터 [cite: 1, 2, 3, 4, 5]
QUIZ_DATA = [
    {"q": "1. 돈의 심리학 저자는 “모든 성공이 (_______)의 결실도 아니고, 모든 가난이 (___________)의 결과도 아님을 깨닫기를 바란다”고 조언한다.", "a": "노력, 게으름"},
    {"q": "2. 돈의 심리학 저자는 “네가 모은 한 푼, 한 푼은 모두 남들 손에 맡겨질 수 있었던 네 (_______) 한 조각을 소유하는 것과 같단다”라고 조언한다.", "a": "미래"},
    {"q": "3. 돈의 심리학 저자는 “실제 돈을 다루는 데는 감정, 인내, (____________), 태도 같은 요소(소프트 스킬)가 더 중요하다”고 주장한다.", "a": "자기 절제"},
    {"q": "4. 돈의 심리학 저자는 “사람들이 금융 의사결정을 내릴 때는, 냉철하게 (_________)이기 보다는 꽤 적당히 합리적”이라고 설명한다.", "a": "이성적"},
    {"q": "5. 우리나라에서는 (______________________)가 재무설계나 개인재무설계와 자주 혼용되어 왔다. (영어로 답하세요)", "a": "personal finance"},
    {"q": "6. 개인재무관리의 영역은 재무설계, 재무상당, 재무교육 등인데, 이들의 공동목표는 소비자의 (______________________) 증진이다.", "a": "재무적 복지"},
    {"q": "7. 경제적 복지의 4가지 유형 중에서, 객관적 조건은 좋은데, 주관적 평가가 불만족인 유형은?", "a": "주관적 불만형"}
]
NUM_QUESTIONS = len(QUIZ_DATA) 

# 페이지 설정
st.set_page_config(page_title=f"{SUBJECT_NAME}", layout="wide")

# 구글 시트 연결
try:
    conn = st.connection("gsheets", type=GSheetsConnection)
except:
    st.error("구글 시트 연결 설정(Secrets)이 필요합니다.")

if "submitted_on_this_device" not in st.session_state:
    st.session_state.submitted_on_this_device = False

st.title(f"📊 {SUBJECT_NAME}")

tab1, tab2, tab3 = st.tabs(["✍️ 퀴즈 제출", "🖥️ 제출자 명단 확인", "🔐 성적 분석(교수용)"])

# --- [TAB 1] 학생 제출 화면 ---
with tab1:
    st.header("답안지")
    
    if st.session_state.submitted_on_this_device:
        st.warning("⚠️ 이 기기에서 제출이 완료되었습니다. 응시는 더 이상 불가능합니다.") [cite: 6]
    else:
        with st.form("quiz_form", clear_on_submit=True):
            col1, col2 = st.columns(2)
            with col1:
                name = st.text_input("이름", placeholder="이름")
            with col2:
                student_id = st.text_input("학번", placeholder="학번") [cite: 7]
            
            st.divider()
            
            user_responses = []
            for i, item in enumerate(QUIZ_DATA):
                st.markdown(f"**{item['q']}**")
                ans = st.text_input(f"{i+1}번 답안", key=f"q{i}") [cite: 8]
                user_responses.append(ans)

            submitted = st.form_submit_button("답안 제출하기 (신중하게 검토 후 한 번만 눌러주세요)")

            if submitted:
                if not name or not student_id: [cite: 9]
                    st.error("이름과 학번을 입력해 주세요.")
                else:
                    try:
                        # 제출 시에만 실시간 데이터를 확인하여 중복 체크 [cite: 10, 11]
                        master_df = conn.read(worksheet="전체데이터", ttl=0)
                        
                        already_exists = master_df[
                            (master_df['주차'] == CURRENT_WEEK) & 
                            (master_df['학번'] == student_id)
                        ] [cite: 11]

                        if not already_exists.empty:
                            st.error(f"❌ {name} 학생은 이미 이번 주 답안을 제출했습니다.") [cite: 12]
                        else:
                            kst = timezone(timedelta(hours=9))
                            now_time = datetime.now(kst).strftime("%Y-%m-%d %H:%M:%S") [cite: 13]
                            
                            row_dict = {
                                "주차": CURRENT_WEEK,
                                "제출시간": now_time,
                                "이름": name,
                                "학번": student_id
                            } [cite: 14, 15]
                            
                            # 채점 로직 (영어 대소문자 구분 없음 적용) [cite: 17, 18]
                            total_correct = 0
                            for i, item in enumerate(QUIZ_DATA, 1):
                                # 정답과 제출답안 모두 소문자로 변환 후 비교 
                                s_ans_set = set(item['a'].replace(" ", "").lower().split(","))
                                u_ans_set = set(user_responses[i-1].replace(" ", "").lower().split(","))
                                
                                is_correct = (s_ans_set == u_ans_set) [cite: 18]
                                if is_correct: total_correct += 1
                                
                                row_dict[f"q{i}_답"] = user_responses[i-1]
                                row_dict[f"q{i}_결과"] = "O" if is_correct else "X" [cite: 19]
                            
                            row_dict["총점"] = total_correct [cite: 20]
                            
                            updated_master = pd.concat([master_df, pd.DataFrame([row_dict])], ignore_index=True) [cite: 21]
                            conn.update(worksheet="전체데이터", data=updated_master)
                            
                            st.session_state.submitted_on_this_device = True
                            st.success(f"{name} 학생, 제출 성공! ({total_correct}/{NUM_QUESTIONS})") [cite: 22, 23]
                            # st.balloons() # 트래픽 최적화를 위해 애니메이션은 주석 처리합니다.
                            st.rerun() 
                            
                    except Exception as e:
                        st.error("제출 중 오류가 발생했습니다. 잠시 후 다시 시도해주세요.")

# --- [TAB 2] 제출 명단 확인 ---
with tab2:
    st.subheader(f"📍 {CURRENT_WEEK} 제출 완료 명단")
    # 트래픽 최적화: 명단 확인 시에는 5분(300초) 동안 캐시된 데이터를 사용합니다. 
    if st.button("🔄 명단 확인/새로고침"):
        try:
            data = conn.read(worksheet="전체데이터", ttl=300)
            today_list = data[data['주차'] == CURRENT_WEEK]
            
            if not today_list.empty:
                st.write(f"현재 총 {len(today_list)}명 제출 완료")
                cols = st.columns(6) [cite: 26]
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
        st.success("인증 성공")
        try:
            # 관리자 분석 데이터는 실시간으로 읽어옵니다.
            data = conn.read(worksheet="전체데이터", ttl=0)
            if not data.empty:
                st.subheader("학생별 평균 정답률")
                stats = data.groupby(['학번', '이름'])['총점'].mean().reset_index() [cite: 28]
                stats['정답률(%)'] = (stats['총점'] / NUM_QUESTIONS * 100).round(1)
                st.dataframe(stats, use_container_width=True)
                st.divider()
                st.download_button("엑셀 다운로드", data=data.to_csv(index=False).encode('utf-8-sig'), file_name=f"{SUBJECT_NAME}_결과.csv", mime="text/csv")
            else:
                st.info("데이터가 없습니다.") [cite: 29]
        except:
            st.error("데이터 로드 실패")

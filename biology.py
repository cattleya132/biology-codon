import streamlit as st
import random
import gspread
from oauth2client.service_account import ServiceAccountCredentials
from datetime import datetime
import pytz # 한국 시간 기록용 라이브러리

# ==========================================
# 👇 [중요] 본인의 구글 엑셀 주소를 꼭 다시 넣어주세요!
SHEET_URL = "https://docs.google.com/spreadsheets/d/1u09CnLBLV8Ny5v0TDaXC7KBDRRx4tmMrh5o6cHR7vQI/edit?gid=0#gid=0"
# ==========================================

# 🧬 코돈 데이터 (정답 리스트 업데이트 완료)
# 사용자는 리스트에 있는 값 중 하나만 입력하면 정답입니다.
CODON_DICT = {
    # 1. U 시작
    "UUU": ["페닐알라닌", "F"], "UUC": ["페닐알라닌", "F"],
    "UUA": ["류신", "L"], "UUG": ["류신", "L"],
    "UCU": ["세린", "S"], "UCC": ["세린", "S"], "UCA": ["세린", "S"], "UCG": ["세린", "S"],
    "UAU": ["타이로신", "Y"], "UAC": ["타이로신", "Y"],
    
    # 👇 [수정됨] 종결 코돈 정답 목록 강화 (*, 종결, 종결 코돈 등)
    "UAA": ["종결", "종결코돈", "종결 코돈", "*", "STOP"], 
    "UAG": ["종결", "종결코돈", "종결 코돈", "*", "STOP"],
    
    "UGU": ["시스테인", "C"], "UGC": ["시스테인", "C"],
    
    # 👇 [수정됨] 종결 코돈
    "UGA": ["종결", "종결코돈", "종결 코돈", "*", "STOP"], 
    
    "UGG": ["트립토판", "W"],

    # 2. C 시작
    "CUU": ["류신", "L"], "CUC": ["류신", "L"], "CUA": ["류신", "L"], "CUG": ["류신", "L"],
    "CCU": ["프롤린", "P"], "CCC": ["프롤린", "P"], "CCA": ["프롤린", "P"], "CCG": ["프롤린", "P"],
    "CAU": ["히스티딘", "H"], "CAC": ["히스티딘", "H"],
    "CAA": ["글루타민", "Q"], "CAG": ["글루타민", "Q"],
    "CGU": ["아르지닌", "R"], "CGC": ["아르지닌", "R"], "CGA": ["아르지닌", "R"], "CGG": ["아르지닌", "R"],

    # 3. A 시작
    "AUU": ["아이소류신", "I"], "AUC": ["아이소류신", "I"], "AUA": ["아이소류신", "I"],
    "AUG": ["메싸이오닌", "M", "시작", "시작코돈"],
    "ACU": ["트레오닌", "T"], "ACC": ["트레오닌", "T"], "ACA": ["트레오닌", "T"], "ACG": ["트레오닌", "T"],
    "AAU": ["아스파라진", "N"], "AAC": ["아스파라진", "N"],
    "AAA": ["라이신", "K"], "AAG": ["라이신", "K"],
    "AGU": ["세린", "S"], "AGC": ["세린", "S"],
    "AGA": ["아르지닌", "R"], "AGG": ["아르지닌", "R"],

    # 4. G 시작
    "GUU": ["발린", "V"], "GUC": ["발린", "V"], "GUA": ["발린", "V"], "GUG": ["발린", "V"],
    "GCU": ["알라닌", "A"], "GCC": ["알라닌", "A"], "GCA": ["알라닌", "A"], "GCG": ["알라닌", "A"],
    "GAU": ["아스파르트산", "D"], "GAC": ["아스파르트산", "D"],
    "GAA": ["글루탐산", "E"], "GAG": ["글루탐산", "E"],
    "GGU": ["글리신", "G"], "GGC": ["글리신", "G"], "GGA": ["글리신", "G"], "GGG": ["글리신", "G"]
}

# [보안] 구글 시트 연결
@st.cache_resource
def init_connection():
    scope = ["https://spreadsheets.google.com/feeds", "https://www.googleapis.com/auth/drive"]
    creds_dict = dict(st.secrets["gcp_service_account"])
    if "private_key" in creds_dict:
        creds_dict["private_key"] = creds_dict["private_key"].replace("\\n", "\n")
    creds = ServiceAccountCredentials.from_json_keyfile_dict(creds_dict, scope)
    return gspread.authorize(creds)

# 📝 [핵심 기능] 엑셀에 기록 남기기 (로그 저장)
def log_to_sheet(codon, user_input, result):
    try:
        client = init_connection()
        sheet = client.open_by_url(SHEET_URL).sheet1
        
        # 한국 시간 가져오기
        korea_timezone = pytz.timezone("Asia/Seoul")
        now = datetime.now(korea_timezone).strftime("%Y-%m-%d %H:%M:%S")
        
        # 엑셀 맨 끝에 한 줄 추가 [시간, 문제, 입력값, 결과]
        sheet.append_row([now, codon, user_input, result])
    except Exception as e:
        print(f"로그 저장 실패 (사용자에게는 안 보임): {e}")

# 게임 초기화 함수
def init_game():
    st.session_state['quiz_queue'] = list(CODON_DICT.keys())
    random.shuffle(st.session_state['quiz_queue'])
    st.session_state['wrong_answers'] = []
    st.session_state['current_q'] = None
    st.session_state['feedback'] = None
    st.session_state['score'] = 0
    st.session_state['total_count'] = len(CODON_DICT)
    st.session_state['mode'] = "전체 모드"

# 오답 복습 함수
def retry_wrong_answers():
    st.session_state['quiz_queue'] = st.session_state['wrong_answers'][:]
    random.shuffle(st.session_state['quiz_queue'])
    st.session_state['wrong_answers'] = []
    st.session_state['current_q'] = None
    st.session_state['feedback'] = None
    st.session_state['score'] = 0
    st.session_state['total_count'] = len(st.session_state['quiz_queue'])
    st.session_state['mode'] = "🔥 오답 복습 모드"

def main():
    # CSS로 관리자 버튼 등 숨기기 (깔끔하게)
    st.markdown("""
        <style>
        [data-testid="stStatusWidget"] {visibility: hidden !important;}
        footer {visibility: hidden !important;}
        header {visibility: hidden !important;}
        
        /* 모바일 여백 조정 */
        .block-container {
            padding-top: 2rem;
            padding-bottom: 5rem;
        }
        </style>
        """, unsafe_allow_html=True)

    st.set_page_config(page_title="코돈표 입력 퀴즈", page_icon="🧬")
    
    # 세션 상태 초기화
    if 'quiz_queue' not in st.session_state:
        init_game()

    st.title(f"🧬 코돈 암기 퀴즈 ({st.session_state['mode']})")

    # 진행률 표시
    remaining = len(st.session_state['quiz_queue'])
    total = st.session_state['total_count']
    if total > 0:
        progress = 1.0 - (remaining / total)
        st.progress(progress)
        st.caption(f"남은 문제: {remaining}개 / 총 {total}개")

    # 피드백 표시 (정답/오답 결과)
    if st.session_state['feedback']:
        is_correct, msg = st.session_state['feedback']
        if is_correct:
            st.success(msg)
        else:
            st.error(msg)

    # 게임 종료 체크 (더 이상 풀 문제가 없을 때)
    if not st.session_state['quiz_queue'] and st.session_state['current_q'] is None:
        st.divider()
        st.header("🎉 테스트 종료!")
        st.subheader(f"최종 점수: {st.session_state['score']} / {st.session_state['total_count']}")

        if st.session_state['wrong_answers']:
            st.warning(f"틀린 문제가 {len(st.session_state['wrong_answers'])}개 있습니다.")
            if st.button("🔥 틀린 문제만 다시 풀기", type="primary"):
                retry_wrong_answers()
                st.rerun()
        else:
            st.balloons()
            st.success("완벽합니다! 💯")
            if st.button("처음부터 다시 하기"):
                init_game()
                st.rerun()
        return

    # 새 문제 뽑기 (현재 문제가 없으면 큐에서 하나 꺼냄)
    if st.session_state['current_q'] is None:
        st.session_state['current_q'] = st.session_state['quiz_queue'].pop()
        st.session_state['feedback'] = None

    current_codon = st.session_state['current_q']
    
    # 문제 화면 출력
    st.markdown(f"""
    <div style="text-align: center; margin: 30px 0;">
        <span style="font-size: 20px;">이 코돈의 아미노산은?</span><br>
        <span style="font-size: 80px; font-weight: bold; color: #4CAF50;">{current_codon}</span>
    </div>
    """, unsafe_allow_html=True)

    # 입력 폼
    with st.form("quiz_form", clear_on_submit=True):
        user_input = st.text_input("정답 입력", placeholder="예: 트레오닌, T, *")
        submitted = st.form_submit_button("제출")

        if submitted:
            valid_answers = CODON_DICT[current_codon]
            
            # 입력값 정리 (좌우 공백 제거, 대문자로 변환)
            # *나 한글은 upper() 해도 그대로 유지됨
            cleaned_input = user_input.strip().upper()
            original_input = user_input.strip() # 원본 입력값 (띄어쓰기 정도만 제거)
            
            # 정답 확인 로직
            is_correct = False
            for ans in valid_answers:
                # 1. 대문자 변환 값과 비교 (약자 처리용: t -> T)
                if cleaned_input == ans:
                    is_correct = True
                    break
                # 2. 원본 값과 비교 (띄어쓰기 있는 한글 처리용: '종결 코돈' 등)
                if original_input == ans:
                    is_correct = True
                    break
            
            # 엑셀에 로그 저장
            log_result = "정답" if is_correct else "오답"
            log_to_sheet(current_codon, user_input, log_result)

            if is_correct:
                st.session_state['score'] += 1
                display_answer = valid_answers[0] # 대표 정답 보여주기
                st.session_state['feedback'] = (True, f"✅ 정답! ({current_codon} = {display_answer})")
            else:
                st.session_state['wrong_answers'].append(current_codon)
                # 오답일 때는 대표 이름과 약자를 알려줌
                correct_name = valid_answers[0]
                # 약자가 있으면 같이 표시 (종결 코돈 등은 약자가 없을 수 있음)
                correct_abbr = valid_answers[1] if len(valid_answers) > 1 and len(valid_answers[1]) == 1 else ""
                
                error_msg = f"❌ 땡! (정답: {correct_name}"
                if correct_abbr:
                    error_msg += f" / {correct_abbr})"
                else:
                    error_msg += ")"
                
                st.session_state['feedback'] = (False, error_msg)
            
            # 현재 문제 비우기 (다음 턴에 새 문제)
            st.session_state['current_q'] = None
            st.rerun()

    # 표 확인 (커닝 페이퍼)
    with st.expander("코돈표 전체 보기 (Reference)"):
        st.write(CODON_DICT)

if __name__ == "__main__":
    main()

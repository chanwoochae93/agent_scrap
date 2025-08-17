@echo off
chcp 65001 > nul
echo 🚀 웹개발 ^& AI 트렌드 멀티 에이전트 설정 시작...

echo.
echo 📦 가상환경 생성 중...
python -m venv agent_scrap

echo 🔌 가상환경 활성화...
call agent_scrap\Scripts\activate.bat

echo 📚 pip 업그레이드...
python -m pip install --upgrade pip

echo 📚 필요한 패키지 설치 중...
pip install -r requirements.txt

echo 📁 필요한 디렉토리 생성...
if not exist outputs mkdir outputs
if not exist tests mkdir tests
if not exist logs mkdir logs

echo 🔧 .env 파일 확인...
if not exist .env (
    copy .env.example .env
    echo ⚠️ .env 파일을 열어 API 키와 이메일 정보를 입력하세요!
) else (
    echo ✅ .env 파일이 이미 존재합니다
)

echo.
echo ✅ 설정 완료!
echo.
echo 다음 단계:
echo 1. .env 파일을 열어 API 키 입력
echo 2. Gmail 계정 4개 생성 및 앱 비밀번호 설정
echo 3. Gemini API 키 4개 발급
echo 4. Reddit API 설정
echo.
echo 테스트: python tests\test_all.py
echo 실행: python run.py
echo.
pause
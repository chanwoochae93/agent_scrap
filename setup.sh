#!/bin/bash

echo "🚀 웹개발 & AI 트렌드 멀티 에이전트 설정 시작..."

# 색상 정의
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Python 버전 체크
python_version=$(python3 --version 2>&1 | grep -Po '(?<=Python )\d+\.\d+')
required_version="3.8"

if [ "$(printf '%s\n' "$required_version" "$python_version" | sort -V | head -n1)" != "$required_version" ]; then
    echo -e "${RED}❌ Python 3.8 이상이 필요합니다. (현재: $python_version)${NC}"
    exit 1
fi

echo -e "${GREEN}✅ Python $python_version 확인${NC}"

# 가상환경 생성
echo "📦 가상환경 생성 중..."
python3 -m venv agent_scrap

# 가상환경 활성화
echo "🔌 가상환경 활성화..."
source agent_scrap/bin/activate

# pip 업그레이드
echo "📚 pip 업그레이드..."
pip install --upgrade pip

# 패키지 설치
echo "📚 필요한 패키지 설치 중..."
pip install -r requirements.txt

# 디렉토리 생성
echo "📁 필요한 디렉토리 생성..."
mkdir -p outputs
mkdir -p tests
mkdir -p logs

# .env 파일 생성
if [ ! -f .env ]; then
    echo "🔧 .env 파일 생성 중..."
    cp .env.example .env
    echo -e "${YELLOW}⚠️  .env 파일을 열어 API 키와 이메일 정보를 입력하세요!${NC}"
else
    echo -e "${GREEN}✅ .env 파일이 이미 존재합니다${NC}"
fi

# 실행 권한 부여
chmod +x run.py

echo ""
echo -e "${GREEN}✅ 설정 완료!${NC}"
echo ""
echo "다음 단계:"
echo "1. .env 파일을 열어 API 키 입력:"
echo "   nano .env"
echo ""
echo "2. Gmail 계정 4개 생성 및 앱 비밀번호 설정"
echo ""
echo "3. Gemini API 키 4개 발급 (무료)"
echo "   https://makersuite.google.com/app/apikey"
echo ""
echo "4. Reddit API 설정"
echo "   https://www.reddit.com/prefs/apps"
echo ""
echo "5. 테스트 실행:"
echo "   python tests/test_all.py"
echo ""
echo "6. 실행:"
echo "   python run.py"

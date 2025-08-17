# scrapper/multi_agent_system.py

# ... (상단 import 및 AgentOutput 클래스는 동일) ...
import asyncio
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import google.generativeai as genai
from scrapper.collectors import DataCollector
from scrapper.email_reporter import EmailReporter

class AgentOutput:
    """에이전트 간의 데이터 전달을 위한 통합 데이터 객체"""
    def __init__(self, start_time: datetime):
        self.start_time = start_time
        self.timestamps: Dict[str, str] = {}
        self.raw_collected_data: Optional[Dict] = None
        self.intelligent_filtered_data: Optional[Dict] = None
        self.analysis_result: Optional[Dict] = None
        self.email_html: Optional[str] = None
        self.code_review_report: Optional[str] = None

    def add_timestamp(self, agent_name: str):
        self.timestamps[agent_name] = datetime.now().isoformat()
# ... (CollectorAgent, EmailerAgent, CodeReviewerAgent 클래스는 이전과 동일) ...
class CollectorAgent:
    """Agent 1: 웹에서 정보를 수집하고, AI를 사용해 1차적으로 필터링합니다."""
    def __init__(self, config: Dict):
        self.config = config
        self.collector = DataCollector(config)
        self.gemini_key = config["API_KEYS"]["collector"]
        if not self.gemini_key:
            raise ValueError("CollectorAgent의 Gemini API 키가 설정되지 않았습니다.")
        genai.configure(api_key=self.gemini_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def run(self, output: AgentOutput):
        print("\n🤖 Agent 1 (Collector): 데이터 수집 및 지능형 필터링 시작...")
        
        # 1. 원시 데이터 수집
        raw_data = await self.collector.collect_all()
        output.raw_collected_data = raw_data
        
        # 2. AI를 이용한 지능형 필터링
        prompt = self._create_filter_prompt(raw_data)
        try:
            response = await self.model.generate_content_async(prompt, generation_config=genai.types.GenerationConfig(response_mime_type="application/json"))
            filtered_data = json.loads(response.text)
            output.intelligent_filtered_data = filtered_data
            print(f"✅ Agent 1 (Collector): {len(filtered_data.get('relevant_items', []))}개의 유의미한 정보 필터링 완료.")
        except Exception as e:
            print(f"❌ Agent 1 (Collector): AI 필터링 중 오류 발생 - {e}")
            output.intelligent_filtered_data = {"error": str(e), "relevant_items": []}
            
        output.add_timestamp("CollectorAgent")
        return output

    def _create_filter_prompt(self, data: Dict) -> str:
        """AI 필터링을 위한 프롬프트"""
        content_lines = []
        for source, items in data.items():
            if isinstance(items, list):
                for item in items[:15]:
                    title = item.get('title', item.get('name', ''))
                    if title:
                        content_lines.append(f"[{source}] {title}")
        
        return f"""
        당신은 프론트엔드 기술 큐레이터입니다. 아래는 웹에서 수집된 최신 기술 아티클 및 포스트 제목 목록입니다.
        
        **수집된 목록:**
        ---
        {chr(10).join(content_lines)}
        ---
        
        **요청:**
        이 목록에서, 프론트엔드 개발자에게 실질적으로 유용하고, 새롭거나 깊이 있는 기술적 내용을 다룰 가능성이 **가장 높은** 항목을 **최대 15개**만 선별해주세요.
        단순한 뉴스나 홍보성 글은 제외하고, 기술적 가치가 높은 것을 우선으로 골라주세요.

        **출력 형식 (반드시 JSON 형식):**
        {{
          "relevant_items": [
            {{
              "source": "출처 (예: REDDIT)",
              "title": "선별된 제목"
            }}
          ]
        }}
        """
class AnalyzerAgent:
    """Agent 2: 정제된 정보를 분석하고, 키워드를 제안/정리합니다."""
    def __init__(self, config: Dict):
        self.config = config
        self.gemini_key = config["API_KEYS"]["analyzer"]
        if not self.gemini_key:
            raise ValueError("AnalyzerAgent의 Gemini API 키가 설정되지 않았습니다.")
        genai.configure(api_key=self.gemini_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def run(self, output: AgentOutput):
        print("\n🧠 Agent 2 (Analyzer): 심층 분석 및 키워드 정리 시작...")
        if not output.intelligent_filtered_data or "error" in output.intelligent_filtered_data:
            print("⚠️ Agent 2 (Analyzer): 이전 단계 데이터 오류로 분석을 건너뜁니다.")
            output.analysis_result = {"error": "No data from collector"}
            return output

        # 현재 추적중인 키워드를 프롬프트에 전달
        current_keywords = self.config["FILTER_KEYWORDS"]["must_have_any"]
        prompt = self._create_analysis_prompt(output.intelligent_filtered_data, current_keywords)
        
        try:
            response = await self.model.generate_content_async(prompt, generation_config=genai.types.GenerationConfig(response_mime_type="application/json"))
            output.analysis_result = json.loads(response.text)
            print("✅ Agent 2 (Analyzer): AI 심층 분석 및 키워드 정리 완료.")
        except Exception as e:
            print(f"❌ Agent 2 (Analyzer): AI 분석 중 오류 발생 - {e}")
            output.analysis_result = {"error": str(e)}

        output.add_timestamp("AnalyzerAgent")
        return output

    def _create_analysis_prompt(self, data: Dict, current_keywords: List[str]) -> str:
        content = "\n".join([f"- {item['title']} (from: {item['source']})" for item in data.get('relevant_items', [])])
        keywords_str = ", ".join(current_keywords)
        
        return f"""
        당신은 20년차 시니어 프론트엔드 개발자이자 기술 트렌드 분석가입니다.

        **분석 대상 데이터 (이번 주 핵심 기술 자료):**
        ---
        {content}
        ---

        **현재 추적중인 키워드 목록:**
        ---
        {keywords_str}
        ---

        **요청 사항:**
        1.  **기술 리포트 작성**: 분석 대상 데이터를 바탕으로 아래 항목을 포함한 기술 리포트를 작성해주세요.
            -   **새로운 HTML 태그**: 주목받는 태그의 목적과 예제 코드.
            -   **주목할 만한 CSS 속성**: 새롭거나 활용도 높은 속성의 설명과 예제 코드.
            -   **유용한 CSS 트릭/팁**: 실무에 바로 사용 가능한 트릭과 예제 코드.
            -   **종합 요약**: 시니어로서의 FE 트렌드 종합 인사이트 (1~2문장).
        2.  **키워드 목록 업데이트 제안**:
            -   **새로운 키워드 제안 (suggested_keywords)**: 분석 대상 데이터에서 발견된, 앞으로 추적해야 할 새롭고 중요한 기술 키워드 5개를 제안해주세요.
            -   **오래된 키워드 식별 (deprecated_keywords)**: '현재 추적중인 키워드 목록' 중에서, 최근 트렌드에서 거의 언급되지 않거나 중요도가 떨어진 키워드를 3개까지 식별해주세요. 없다면 빈 리스트로 반환하세요.

        **출력 형식 (반드시 JSON):**
        {{
          "new_html_tags": [], 
          "notable_css_properties": [], 
          "css_tricks": [],
          "summary": "...", 
          "suggested_keywords": ["new_keyword1", ...],
          "deprecated_keywords": ["old_keyword1", ...]
        }}
        """
class EmailerAgent:
    """Agent 3: 분석 리포트를 기반으로, AI를 사용해 미려한 HTML 이메일을 생성하고 발송합니다."""
    def __init__(self, config: Dict):
        self.config = config
        self.reporter = EmailReporter(config)
        self.gemini_key = config["API_KEYS"]["emailer"]
        if not self.gemini_key:
            raise ValueError("EmailerAgent의 Gemini API 키가 설정되지 않았습니다.")
        genai.configure(api_key=self.gemini_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def run(self, output: AgentOutput):
        print("\n✉️ Agent 3 (Emailer): AI 기반 이메일 생성 및 발송 시작...")
        if not output.analysis_result or "error" in output.analysis_result:
            print("⚠️ Agent 3 (Emailer): 분석 데이터 오류로 이메일 생성을 건너뜁니다.")
            return output
            
        prompt = self._create_email_prompt(output.analysis_result)
        try:
            response = await self.model.generate_content_async(prompt)
            html_content = response.text
            # 마크다운 코드 블록 제거
            html_content = re.sub(r"```html\n?", "", html_content)
            html_content = re.sub(r"```", "", html_content)
            
            output.email_html = html_content
            self.reporter.send_custom_html(html_content, self.config["EMAIL_CONFIG"]["subject_template"].format(date=datetime.now().strftime("%Y-%m-%d")))
            print("✅ Agent 3 (Emailer): 이메일 전송 완료.")
        except Exception as e:
            print(f"❌ Agent 3 (Emailer): 이메일 생성/전송 중 오류 발생 - {e}")

        output.add_timestamp("EmailerAgent")
        return output

    def _create_email_prompt(self, analysis: Dict) -> str:
        # JSON 데이터를 문자열로 변환하여 프롬프트에 삽입
        analysis_str = json.dumps(analysis, indent=2, ensure_ascii=False)
        return f"""
        당신은 뛰어난 이메일 디자이너입니다. 아래의 JSON 기술 분석 데이터를 사용하여, 개발자들이 읽기 쉽고 시각적으로 매력적인 HTML 이메일을 작성해주세요.

        **분석 데이터 (JSON):**
        ---
        {analysis_str}
        ---

        **HTML 이메일 작성 조건:**
        - 전체를 감싸는 세련된 컨테이너 스타일을 적용해주세요.
        - 헤더에는 '🚀 주간 FE 트렌드 리포트' 제목과 날짜를 넣어주세요.
        - 각 섹션("새로운 HTML 태그", "주목할 만한 CSS 속성" 등)을 명확하게 구분하고, 소제목을 붙여주세요.
        - 코드 예제(`<code>`)는 어두운 배경에 밝은 글씨(#f8f8f2)로 보기 좋게 스타일링해주세요.
        - 구글 폰트 'Noto Sans KR'을 사용해주세요.
        - 전체적으로 깔끔하고 전문적인 느낌을 주세요.
        - **오직 HTML 코드만 출력해야 합니다. (CSS는 `<style>` 태그 안에 포함)**
        """
class CodeReviewerAgent:
    """Agent 4: 프로젝트 코드를 분석하고 개선점을 제안합니다."""
    def __init__(self, config: Dict):
        self.gemini_key = config["API_KEYS"]["code_reviewer"]
        if not self.gemini_key:
            raise ValueError("CodeReviewerAgent의 Gemini API 키가 설정되지 않았습니다.")
        genai.configure(api_key=self.gemini_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')
        self.project_root = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))

    async def run(self, output: AgentOutput):
        print("\n🛠️ Agent 4 (Code Reviewer): 코드 분석 시작...")
        
        code_content = self._read_project_code()
        prompt = self._create_code_review_prompt(code_content)
        try:
            response = await self.model.generate_content_async(prompt)
            output.code_review_report = response.text
            
            report_path = os.path.join(self.project_root, "outputs", f"code_review_{datetime.now().strftime('%Y%m%d')}.md")
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(output.code_review_report)
            print(f"✅ Agent 4 (Code Reviewer): 코드 분석 완료. 리포트 저장: {report_path}")
        except Exception as e:
            print(f"❌ Agent 4 (Code Reviewer): 코드 분석 중 오류 발생 - {e}")
            output.code_review_report = f"Error during code review: {e}"

        output.add_timestamp("CodeReviewerAgent")
        return output
    
    # _read_project_code 와 _create_code_review_prompt 메서드는 이전과 동일

    def _read_project_code(self) -> str:
        all_code = []
        ignore_dirs = {".venv", "agent_scrap", "__pycache__", ".git", "outputs", "tests"}
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            all_code.append(f"--- FILE: {os.path.relpath(filepath, self.project_root)} ---\n{f.read()}")
                    except Exception:
                        continue
        return "\n\n".join(all_code)

    def _create_code_review_prompt(self, code: str) -> str:
        return f"""
        당신은 파이썬 코드 리뷰 전문가입니다. 아래는 한 프로젝트의 전체 파이썬 코드입니다.
        **프로젝트 코드:**
        ---
        {code[:25000]}
        ---
        **요청 사항:**
        이 코드 전체를 분석하여 다음 관점에서 개선점을 찾아 구체적인 예시와 함께 제안해주세요.
        1.  **코드 효율성** 2.  **가독성 및 유지보수** 3.  **Best Practice** 4.  **잠재적 버그**
        결과는 마크다운 형식으로 정리해주세요.
        """

class NewMultiAgentOrchestrator:
    # ... (init 메서드는 동일) ...
    def __init__(self, config: Dict):
        self.config = config
        self.collector = CollectorAgent(config)
        self.analyzer = AnalyzerAgent(config)
        self.emailer = EmailerAgent(config)
        self.code_reviewer = CodeReviewerAgent(config)
        self.config_path = os.path.join(
            os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
            "configs",
            "config.py"
        )
    # ... (run_weekly_analysis 메서드는 동일) ...
    async def run_weekly_analysis(self):
        print("\n" + "="*60)
        print("🚀 멀티 에이전트 시스템 v4.0 가동!")
        
        # 1. 통합 데이터 객체 생성
        output = AgentOutput(start_time=datetime.now())
        
        # 2. 에이전트 순차 실행 (FE 트렌드 리포팅)
        output = await self.collector.run(output)
        output = await self.analyzer.run(output)
        output = await self.emailer.run(output)

        # 3. 키워드 자동 업데이트
        if output.analysis_result and "suggested_keywords" in output.analysis_result:
            self.update_keywords(
                output.analysis_result.get("suggested_keywords", []),
                output.analysis_result.get("deprecated_keywords", [])
            )
        # 4. 코드 리뷰 에이전트 실행 (독립적으로)
        output = await self.code_reviewer.run(output)
        
        # 5. 최종 결과 요약
        end_time = datetime.now()
        print("\n" + "="*60)
        print("✅ 모든 에이전트 작업 완료!")
        print(f"   - 총 소요 시간: {end_time - output.start_time}")
        print(f"   - 최종 산출물: 이메일 리포트, 코드 리뷰 리포트, 업데이트된 설정 파일")
        print("="*60)

    def update_keywords(self, new_keywords: List[str], deprecated_keywords: List[str]):
        """config.py 파일의 키워드를 추가하고 제거하여 동적으로 업데이트합니다."""
        if not new_keywords and not deprecated_keywords:
            print("💡 제안된 키워드 변경 사항이 없어 설정을 업데이트하지 않습니다.")
            return

        try:
            print(f"\n🔧 설정 파일 업데이트 시작...")
            if new_keywords: print(f"   - 추가할 키워드: {new_keywords}")
            if deprecated_keywords: print(f"   - 제거할 키워드: {deprecated_keywords}")
            
            with open(self.config_path, "r", encoding="utf-8") as f:
                content = f.read()

            pattern = r'("must_have_any":\s*\[)([^\]]*)(\])'
            match = re.search(pattern, content, re.DOTALL)

            if not match:
                print("❌ 설정 파일에서 'must_have_any'를 찾지 못했습니다.")
                return

            existing_keywords_str = match.group(2)
            existing_keywords = {k.strip().strip("'\"") for k in existing_keywords_str.split(',') if k.strip()}
            
            # 키워드 추가
            for kw in new_keywords:
                existing_keywords.add(kw.lower())
            
            # 키워드 제거
            for kw in deprecated_keywords:
                existing_keywords.discard(kw.lower())

            # 새로운 키워드 목록 생성 및 정렬
            updated_keywords = sorted(list(existing_keywords))
            
            new_keywords_str = ",\n            ".join([f'"{k}"' for k in updated_keywords])
            
            # 파일 내용 교체 (정규표현식 그룹을 사용하여 정확하게 교체)
            new_content = f"{match.group(1)}\n            {new_keywords_str}\n        {match.group(3)}"
            final_content = content[:match.start(0)] + new_content + content[match.end(0):]


            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write(final_content)
            
            print("✅ 설정 파일의 키워드를 성공적으로 업데이트했습니다.")

        except Exception as e:
            print(f"❌ 설정 파일 업데이트 중 오류 발생: {e}")
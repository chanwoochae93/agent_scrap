import asyncio
import os
import json
import re
from datetime import datetime
from typing import List, Dict, Any, Optional
import google.generativeai as genai

from scrapper.collectors import DataCollector
from scrapper.email_reporter import EmailReporter
from scrapper.utils.logger import logger

class AgentOutput:
    """에이전트 간의 데이터 전달을 위한 통합 데이터 객체"""
    def __init__(self, start_time: datetime):
        self.start_time = start_time
        self.raw_collected_data: Optional[Dict] = None
        self.intelligent_filtered_data: Optional[Dict] = None
        self.analysis_result: Optional[Dict] = None
        self.email_html: Optional[str] = None
        self.code_review_report: Optional[str] = None

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
        logger.info("\n🤖 Agent 1 (Collector): 데이터 수집 및 지능형 필터링 시작...")
        
        # 1. 원시 데이터 수집
        raw_data = await self.collector.collect_all()
        output.raw_collected_data = raw_data
        
        # 2. AI를 이용한 지능형 필터링
        prompt = self._create_filter_prompt(raw_data)
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(response_mime_type="application/json")
            )
            filtered_data = json.loads(response.text)
            output.intelligent_filtered_data = filtered_data
            logger.info(f"✅ Agent 1 (Collector): {len(filtered_data.get('relevant_items', []))}개의 유의미한 정보 필터링 완료.")
        except Exception as e:
            logger.error(f"❌ Agent 1 (Collector): AI 필터링 중 오류 발생 - {e}", exc_info=True)
            output.intelligent_filtered_data = {"error": str(e), "relevant_items": []}
            
        return output

    def _create_filter_prompt(self, data: Dict) -> str:
        """AI 필터링을 위한 프롬프트를 생성합니다."""
        content_lines = []
        for source, items in data.items():
            if isinstance(items, list):
                for item in items[:15]: # 각 소스별 상위 15개만 고려
                    title = item.get('title', item.get('name', ''))
                    url = item.get('url', item.get('link', '#'))
                    source_name = item.get('source', source)
                    if title:
                        content_lines.append(f"- {title} (출처: {source_name}, URL: {url})")
        
        return f"""
        당신은 프론트엔드 기술 큐레이터입니다. 아래는 웹에서 수집된 최신 기술 아티클 및 포스트 목록입니다.
        
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
              "source": "출처 (예: Reddit)",
              "title": "선별된 제목",
              "url": "해당 항목의 URL"
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
        logger.info("\n🧠 Agent 2 (Analyzer): 심층 분석 및 키워드 정리 시작...")
        if not output.intelligent_filtered_data or "error" in output.intelligent_filtered_data:
            logger.warning("⚠️ Agent 2 (Analyzer): 이전 단계 데이터 오류로 분석을 건너뜁니다.")
            output.analysis_result = {"error": "No data from collector"}
            return output

        current_keywords = self.config["FILTER_KEYWORDS"]["must_have_any"]
        # 프롬프트 생성 메서드를 호출합니다.
        prompt = self._create_analysis_prompt(output.intelligent_filtered_data, current_keywords)
        
        try:
            response = await self.model.generate_content_async(
                prompt,
                generation_config=genai.types.GenerationConfig(response_mime_type="application/json")
            )
            output.analysis_result = json.loads(response.text)
            logger.info("✅ Agent 2 (Analyzer): AI 심층 분석 및 키워드 정리 완료.")
        except Exception as e:
            logger.error(f"❌ Agent 2 (Analyzer): AI 분석 중 오류 발생 - {e}", exc_info=True)
            output.analysis_result = {"error": str(e)}

        return output

    def _create_analysis_prompt(self, data: Dict, current_keywords: List[str]) -> str:
        """아티클 심층 분석 및 구체적인 종합 요약 생성을 위한 프롬프트"""
        content = "\n".join([f"- {item['title']} (URL: {item['url']}, 출처: {item['source']})" for item in data.get('relevant_items', [])])
        keywords_str = ", ".join(current_keywords)
        
        return f"""
        당신은 20년차 시니어 프론트엔드 개발자이자 기술 트렌드 분석가입니다.

        **분석 대상 데이터 (이번 주 핵심 기술 자료):**
        ---
        {content}
        ---

        **요청 사항 (반드시 JSON 형식으로 출력):**

        1.  **아티클 심층 분석 (detailed_articles)**:
            - 각 아티클에 대해, "이 기술이 왜 지금 중요한가?", "실무에서 어떻게 활용할 수 있는가?"에 대한 관점을 포함하여 3~4 문장의 심도 있는 해설(summary)을 한국어로 작성해주세요.

        2.  **기술 리포트 작성 (technical_report)**:
            - new_html_tags, notable_css_properties, css_tricks 항목을 채워주세요.

        3.  **키워드 목록 업데이트 제안 (keyword_suggestions)**:
            - suggested_keywords, deprecated_keywords 항목을 채워주세요.

        4.  **종합 요약 (executive_summary)**:
            - **가장 중요한 요구사항**: 위에서 당신이 직접 분석한 **`detailed_articles`의 핵심 내용들을 반드시 종합**하여, 구체적인 기술과 그 중요성을 명시하는 2~3 문단의 종합 요약을 작성해주세요.
            - 예를 들어, '국제화가 중요하다'가 아니라 '**별도 라이브러리 없이 `Intl` API를 사용해 날짜/통화 형식을 효율적으로 처리할 수 있는 네이티브 기능이 주목받고 있습니다**' 와 같이 구체적으로 작성해야 합니다.
            - 이번 주 트렌드의 핵심적인 변화와 개발자들이 주목해야 할 실질적인 포인트를 명확히 짚어주세요.

        **출력 형식 (반드시 JSON 구조를 유지):**
        {{
          "detailed_articles": [
            {{
              "title": "...", "url": "...", "source": "...",
              "summary": "3~4 문장의 심도 있는 해설..."
            }}
          ],
          "technical_report": {{
            "new_html_tags": [],
            "notable_css_properties": [],
            "css_tricks": []
          }},
          "keyword_suggestions": {{
            "suggested_keywords": [],
            "deprecated_keywords": []
          }},
          "executive_summary": "구체적인 기술 이름과 그 의미를 포함한 종합적인 요약..."
        }}
        """

class EmailerAgent:
    """Agent 3: 분석 리포트와 원본 데이터를 기반으로, 풍부한 HTML 이메일을 생성하고 발송합니다."""
    def __init__(self, config: Dict):
        self.config = config
        self.reporter = EmailReporter(config)
        self.gemini_key = config["API_KEYS"]["emailer"]
        if not self.gemini_key:
            raise ValueError("EmailerAgent의 Gemini API 키가 설정되지 않았습니다.")
        genai.configure(api_key=self.gemini_key)
        self.model = genai.GenerativeModel('gemini-1.5-flash')

    async def run(self, output: AgentOutput):
        """이메일 생성 및 발송 작업을 실행합니다."""
        logger.info("\n✉️ Agent 3 (Emailer): AI 기반 이메일 생성 및 발송 시작...")
        if not output.analysis_result or "error" in output.analysis_result:
            logger.warning("⚠️ Agent 3 (Emailer): 분석 데이터 오류로 이메일 생성을 건너뜁니다.")
            return output
            
        prompt = self._create_email_prompt(
            output.analysis_result,
            output.intelligent_filtered_data 
        )
        try:
            response = await self.model.generate_content_async(prompt)
            html_content = self._clean_html_response(response.text)
            
            output.email_html = html_content
            subject = self.config["EMAIL_CONFIG"]["subject_template"].format(date=datetime.now().strftime("%Y-%m-%d"))
            self.reporter.send_custom_html(html_content, subject)
            logger.info("✅ Agent 3 (Emailer): 이메일 전송 완료.")
        except Exception as e:
            logger.error(f"❌ Agent 3 (Emailer): 이메일 생성/전송 중 오류 발생 - {e}", exc_info=True)

        return output

    def _create_email_prompt(self, analysis: Dict, filtered_data: Optional[Dict]) -> str:
        """분석된 데이터를 기반으로 반응형 이메일 템플릿을 채우는 프롬프트"""
        
        articles_html = ""
        if analysis and "detailed_articles" in analysis:
            for article in analysis["detailed_articles"]:
                articles_html += f"""
                <div style="margin-bottom: 20px;">
                    <h3 style="margin-bottom: 5px;"><a href="{article.get('url', '#')}" target="_blank" style="text-decoration: none; color: #1a0dab;">{article.get('title', '제목 없음')}</a></h3>
                    <p style="margin: 0; color: #5f6368; font-size: 0.9em;">(출처: {article.get('source', '출처 없음')})</p>
                    <p style="margin-top: 5px; line-height: 1.6;">{article.get('summary', '요약 정보가 없습니다.')}</p>
                </div>
                """

        # 수정된 부분: 새로운 JSON 구조에 맞게 executive_summary를 가져옵니다.
        executive_summary_html = f"<p>{analysis.get('executive_summary', '종합 요약 정보가 없습니다.')}</p>"

        return f"""
        당신은 뛰어난 HTML 이메일 디자이너입니다. 아래에 제공된 HTML 조각들을 사용하여, PC와 모바일 모두에서 완벽하게 보이는 전문적인 이메일을 완성해주세요.

        **1. 주요 아티클 및 해설 (HTML):**
        ---
        {articles_html}
        ---

        **2. 종합 요약 (HTML):**
        ---
        {executive_summary_html}
        ---

        **HTML 이메일 완성 조건:**
        - **가장 중요한 요구사항**: 제공된 HTML 조각들을 본문에 자연스럽게 배치하고, 전체를 감싸는 세련된 반응형 템플릿을 적용해주세요.
        - **모바일 최적화**: CSS 미디어 쿼리(@media)를 사용해 모바일 가독성을 확보해주세요.
        - **디자인**: 헤더, 푸터, 그리고 각 섹션을 명확히 구분하는 디자인 요소를 추가하여 전문적인 느낌을 주세요.
        - **오직 완성된 HTML 코드만 출력**해주세요. 모든 스타일은 `<style>` 태그 안에 포함해주세요.
        """

    def _clean_html_response(self, text: str) -> str:
        """AI 응답에서 마크다운 코드 블록을 제거합니다."""
        text = text.strip()
        if text.startswith("```html"):
            text = text[7:]
        if text.endswith("```"):
            text = text[:-3]
        return text.strip()

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
        logger.info("\n🛠️ Agent 4 (Code Reviewer): 코드 분석 시작...")
        
        code_content = self._read_project_code()
        prompt = self._create_code_review_prompt(code_content)
        try:
            response = await self.model.generate_content_async(prompt)
            output.code_review_report = response.text
            
            report_path = os.path.join(self.project_root, "outputs", f"code_review_{datetime.now().strftime('%Y%m%d')}.md")
            os.makedirs(os.path.dirname(report_path), exist_ok=True)
            with open(report_path, "w", encoding="utf-8") as f:
                f.write(output.code_review_report)
            logger.info(f"✅ Agent 4 (Code Reviewer): 코드 분석 완료. 리포트 저장: {report_path}")
        except Exception as e:
            logger.error(f"❌ Agent 4 (Code Reviewer): 코드 분석 중 오류 발생 - {e}", exc_info=True)
            output.code_review_report = f"Error during code review: {e}"

        return output

    def _read_project_code(self) -> str:
        """무시할 디렉토리를 제외하고 프로젝트의 모든 .py 파일 내용을 읽어옵니다."""
        all_code = []
        ignore_dirs = {".venv", "agent_scrap", "__pycache__", ".git", "outputs", "tests", "logs"}
        
        for root, dirs, files in os.walk(self.project_root):
            dirs[:] = [d for d in dirs if d not in ignore_dirs]
            
            for file in files:
                if file.endswith(".py"):
                    filepath = os.path.join(root, file)
                    try:
                        with open(filepath, "r", encoding="utf-8") as f:
                            rel_path = os.path.relpath(filepath, self.project_root)
                            all_code.append(f"--- FILE: {rel_path} ---\n{f.read()}")
                    except Exception as e:
                        logger.warning(f"파일 읽기 오류 ({filepath}): {e}")
                        continue
        return "\n\n".join(all_code)

    def _create_code_review_prompt(self, code: str) -> str:
        """코드 리뷰를 위한 프롬프트를 생성합니다."""
        return f"""
        당신은 파이썬 코드 리뷰 전문가입니다. 아래는 한 프로젝트의 전체 파이썬 코드입니다.
        **프로젝트 코드 (최대 30000자):**
        ---
        {code[:30000]}
        ---
        **요청 사항:**
        이 코드 전체를 분석하여 다음 관점에서 개선점을 찾아 구체적인 예시와 함께 제안해주세요.
        1.  **코드 효율성** (예: 비동기 처리, 알고리즘 개선)
        2.  **가독성 및 유지보수** (예: 함수 분리, 명확한 변수명)
        3.  **Best Practice** (예: 오류 처리, 설정 관리)
        4.  **잠재적 버그** (예: 예외 처리 누락, 잘못된 로직)
        결과는 마크다운 형식으로 명확하고 간결하게 정리해주세요.
        """

class NewMultiAgentOrchestrator:
    """4개의 AI 에이전트 작업을 조율하는 오케스트레이터"""
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
    
    async def run_weekly_analysis(self):
        """에이전트 시스템의 전체 분석 및 리포팅 플로우를 실행합니다."""
        logger.info("\n" + "="*60)
        logger.info("🚀 멀티 에이전트 시스템 v4.2 가동!")
        
        output = AgentOutput(start_time=datetime.now())
        
        # 에이전트 순차 실행
        output = await self.collector.run(output)
        output = await self.analyzer.run(output)
        output = await self.emailer.run(output)

        # 키워드 자동 업데이트
        if output.analysis_result and "suggested_keywords" in output.analysis_result:
            self.update_keywords(
                output.analysis_result.get("suggested_keywords", []),
                output.analysis_result.get("deprecated_keywords", [])
            )
            
        # 코드 리뷰 에이전트 실행
        await self.code_reviewer.run(output)
        
        end_time = datetime.now()
        logger.info("\n" + "="*60)
        logger.info("✅ 모든 에이전트 작업 완료!")
        logger.info(f"   - 총 소요 시간: {end_time - output.start_time}")
        logger.info("="*60)

    def update_keywords(self, new_keywords: List[str], deprecated_keywords: List[str]):
        """
        정규식을 사용하여 config.py 파일의 키워드 목록을 안전하게 업데이트합니다.
        - 이 방식은 os.getenv() 같은 함수 호출이 있어도 문제없이 작동합니다.
        """
        if not new_keywords and not deprecated_keywords:
            logger.info("💡 제안된 키워드 변경 사항이 없어 설정을 업데이트하지 않습니다.")
            return

        try:
            logger.info("🔧 설정 파일(config.py)의 키워드를 업데이트합니다...")
            
            with open(self.config_path, "r", encoding="utf-8") as f:
                content = f.read()

            # 'must_have_any' 리스트 블록을 찾는 정규식
            pattern = r'("must_have_any":\s*\[)(.*?)(\],)'
            match = re.search(pattern, content, re.DOTALL)

            if not match:
                logger.error("❌ 설정 파일에서 'must_have_any' 키워드 목록을 찾지 못했습니다.")
                return

            # 기존 키워드를 파싱하여 set으로 변환
            existing_keywords_str = match.group(2)
            cleaned_keywords = re.findall(r'["\']([^"\']+)["\']', existing_keywords_str)
            existing_keywords = set(k.strip() for k in cleaned_keywords if k.strip())
            
            # 키워드 추가 및 제거
            existing_keywords.update(kw.lower() for kw in new_keywords)
            for kw in deprecated_keywords:
                existing_keywords.discard(kw.lower())

            # **안정적인 코드 생성 로직**
            # 정렬된 키워드 리스트를 기반으로 새로운 문자열 블록 생성
            sorted_keywords = sorted(list(existing_keywords))
            
            # 보기 좋게 4~5개씩 끊어서 줄바꿈 처리
            new_keywords_str = ",\n            ".join(
                [f'"{k}"' for k in sorted_keywords]
            )
            
            # 최종적으로 교체될 코드 블록
            new_block = f'{match.group(1)}\n            {new_keywords_str},\n        {match.group(3)}'
            
            # 원본 파일 내용에서 기존 블록을 새로운 블록으로 교체
            final_content = content[:match.start(0)] + new_block + content[match.end(0):]

            with open(self.config_path, "w", encoding="utf-8") as f:
                f.write(final_content)
            
            logger.info("✅ 설정 파일의 키워드를 성공적으로 업데이트했습니다.")

        except Exception as e:
            logger.error(f"❌ 설정 파일 업데이트 중 오류 발생: {e}", exc_info=True)
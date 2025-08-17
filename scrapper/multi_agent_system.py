import asyncio
from typing import List, Dict, Any
import os
from datetime import datetime, timedelta
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import InstalledAppFlow
from google.auth.transport.requests import Request
from googleapiclient.discovery import build
import pickle
import json
import hashlib
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.mime.application import MIMEApplication
import google.generativeai as genai

class SubAgent:
    """서브 에이전트 (3개 운영)"""
    
    def __init__(self, agent_id: str, config: Dict):
        self.agent_id = agent_id
        self.config = config
        self.name = f"SubAgent-{agent_id}"
        
        # 각 서브 에이전트별 다른 Gmail 계정
        self.email = config[f"AGENT_{agent_id}_EMAIL"]
        self.password = config[f"AGENT_{agent_id}_PASSWORD"]
        self.gemini_key = config[f"AGENT_{agent_id}_GEMINI_KEY"]
        
        # 전문 분야 설정
        self.specialty = config["AGENT_SPECIALTIES"][agent_id]
    
    async def collect_and_analyze(self) -> Dict:
        """데이터 수집 및 분석"""
        
        print(f"\n🤖 {self.name} 작업 시작 (전문: {self.specialty['focus']})")
        
        try:
            # 1. 전문 분야에 맞는 데이터 수집
            data = await self.collect_specialized_data()
            
            # 2. Gemini로 분석
            analysis = await self.analyze_with_gemini(data)
            
            # 3. 리포트 생성
            report = self.create_agent_report(data, analysis)
            
            # 4. Gmail로 메인 에이전트에게 전송
            await self.send_to_main_agent(report)
            
            return report
            
        except Exception as e:
            print(f"❌ {self.name} 오류: {e}")
            return {"error": str(e), "agent_id": self.agent_id}
    
    async def collect_specialized_data(self) -> Dict:
        """전문 분야별 데이터 수집"""
        
        from scrapper.collectors import DataCollector
        
        # 커스텀 설정
        custom_config = self.config.copy()
        
        # 전문 분야에 맞게 필터링
        if self.agent_id == "A":
            # AI/ML 중심
            custom_config["REDDIT_CONFIG"]["subreddits"] = [
                "MachineLearning", "artificial", "LocalLLaMA", "singularity", "OpenAI"
            ]
            custom_config["FILTER_KEYWORDS"]["must_have_any"] = self.specialty["keywords"]
            
        elif self.agent_id == "B":
            # Frontend/CSS 중심
            custom_config["REDDIT_CONFIG"]["subreddits"] = [
                "css", "webdev", "Frontend", "web_design", "reactjs", "vuejs"
            ]
            custom_config["FILTER_KEYWORDS"]["must_have_any"] = self.specialty["keywords"]
            
        elif self.agent_id == "C":
            # Backend/DevOps 중심
            custom_config["REDDIT_CONFIG"]["subreddits"] = [
                "programming", "devops", "golang", "rust", "node", "kubernetes"
            ]
            custom_config["FILTER_KEYWORDS"]["must_have_any"] = self.specialty["keywords"]
        
        collector = DataCollector(custom_config)
        return await collector.collect_all()
    
    async def analyze_with_gemini(self, data: Dict) -> Dict:
        """Gemini로 전문 분석"""
        
        genai.configure(api_key=self.gemini_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 전문 분야별 프롬프트
        prompt = f"""
        당신은 {self.specialty['focus']} 전문가입니다.
        
        다음 데이터를 분석하고 핵심 인사이트를 추출하세요:
        
        1. 가장 중요한 트렌드 3개
        2. 주목할 만한 새로운 도구/기술
        3. 커뮤니티 반응과 감정
        4. 향후 예측
        5. 한국 개발자를 위한 구체적 조언
        
        데이터 요약:
        - Reddit 포스트: {len(data.get('reddit', []))}개
        - HackerNews: {len(data.get('hackernews', []))}개
        - GitHub: {len(data.get('github', []))}개
        - RSS: {len(data.get('rss', []))}개
        
        주요 내용:
        {self._extract_top_items(data)}
        
        한국어로 자세히 분석해주세요.
        """
        
        try:
            response = model.generate_content(prompt)
            
            return {
                "raw_analysis": response.text,
                "timestamp": datetime.now().isoformat(),
                "agent_id": self.agent_id,
                "specialty": self.specialty['focus'],
                "data_stats": {
                    "reddit": len(data.get('reddit', [])),
                    "hackernews": len(data.get('hackernews', [])),
                    "github": len(data.get('github', [])),
                    "rss": len(data.get('rss', []))
                }
            }
            
        except Exception as e:
            print(f"❌ {self.name} Gemini 오류: {e}")
            return {"error": str(e), "agent_id": self.agent_id}
    
    def _extract_top_items(self, data: Dict) -> str:
        """상위 아이템 추출"""
        
        items = []
        
        # Reddit Top 5
        for item in data.get('reddit', [])[:5]:
            items.append(f"Reddit: {item.get('title')} (점수: {item.get('score')})")
        
        # HackerNews Top 5
        for item in data.get('hackernews', [])[:5]:
            items.append(f"HN: {item.get('title')} (점수: {item.get('score')})")
        
        # GitHub Top 3
        for item in data.get('github', [])[:3]:
            items.append(f"GitHub: {item.get('name')} - {item.get('description')[:100]}")
        
        return "\n".join(items)
    
    def create_agent_report(self, data: Dict, analysis: Dict) -> Dict:
        """에이전트 리포트 생성"""
        
        # 중복 체크용 해시
        content_hash = hashlib.md5(
            json.dumps(data, sort_keys=True).encode()
        ).hexdigest()[:8]
        
        report = {
            "agent_id": self.agent_id,
            "agent_name": self.name,
            "specialty": self.specialty['focus'],
            "timestamp": datetime.now().isoformat(),
            "content_hash": content_hash,
            "data_summary": {
                "total_items": sum(
                    len(v) for v in data.values() if isinstance(v, list)
                ),
                "sources": list(data.keys())
            },
            "analysis": analysis,
            "top_findings": self._extract_top_findings(data),
            "raw_data": data
        }
        
        return report
    
    def _extract_top_findings(self, data: Dict) -> List[Dict]:
        """주요 발견 사항 추출"""
        
        findings = []
        
        # Reddit 최고 인기
        reddit_posts = data.get('reddit', [])
        if reddit_posts:
            top_reddit = max(reddit_posts, key=lambda x: x.get('score', 0))
            findings.append({
                "type": "reddit_top",
                "title": top_reddit.get('title'),
                "score": top_reddit.get('score'),
                "url": top_reddit.get('url')
            })
        
        # GitHub 최고 스타
        github_repos = data.get('github', [])
        if github_repos:
            top_repo = max(github_repos, key=lambda x: x.get('stars', 0))
            findings.append({
                "type": "github_top",
                "name": top_repo.get('name'),
                "stars": top_repo.get('stars'),
                "url": top_repo.get('url')
            })
        
        return findings
    
    async def send_to_main_agent(self, report: Dict):
        """Gmail로 메인 에이전트에게 전송"""
        
        try:
            # 이메일 생성
            msg = MIMEMultipart()
            msg['From'] = self.email
            msg['To'] = self.config["MAIN_AGENT_EMAIL"]
            msg['Subject'] = f"[AI-TREND-{self.agent_id}] {self.specialty['focus']} 분석 리포트"
            
            # HTML 본문
            html_body = self._create_email_html(report)
            msg.attach(MIMEText(html_body, 'html'))
            
            # JSON 첨부파일
            json_attachment = MIMEApplication(
                json.dumps(report, ensure_ascii=False, indent=2)
            )
            json_attachment.add_header(
                'Content-Disposition',
                f'attachment; filename="{self.name}_report_{datetime.now().strftime("%Y%m%d")}.json"'
            )
            msg.attach(json_attachment)
            
            # 전송
            with smtplib.SMTP('smtp.gmail.com', 587) as server:
                server.starttls()
                server.login(self.email, self.password)
                server.send_message(msg)
            
            print(f"✅ {self.name} 리포트 전송 완료")
            
        except Exception as e:
            print(f"❌ {self.name} 이메일 전송 실패: {e}")
    
    def _create_email_html(self, report: Dict) -> str:
        """이메일 HTML 생성"""
        
        return f"""
        <html>
        <head>
            <style>
                body {{ font-family: Arial, sans-serif; }}
                .header {{ background: linear-gradient(135deg, #667eea 0%, #764ba2 100%); color: white; padding: 20px; }}
                .content {{ padding: 20px; }}
                .stats {{ display: grid; grid-template-columns: repeat(4, 1fr); gap: 10px; margin: 20px 0; }}
                .stat-card {{ background: #f5f5f5; padding: 15px; border-radius: 8px; text-align: center; }}
                .findings {{ background: #e8f4f8; padding: 15px; border-radius: 8px; margin: 20px 0; }}
                .analysis {{ background: #fff; padding: 20px; border: 1px solid #ddd; border-radius: 8px; }}
            </style>
        </head>
        <body>
            <div class="header">
                <h1>🤖 {self.name} 리포트</h1>
                <p>전문 분야: {report['specialty']}</p>
                <p>수집 시간: {report['timestamp']}</p>
            </div>
            
            <div class="content">
                <div class="stats">
                    <div class="stat-card">
                        <h3>Reddit</h3>
                        <p>{report['analysis'].get('data_stats', {}).get('reddit', 0)}</p>
                    </div>
                    <div class="stat-card">
                        <h3>HackerNews</h3>
                        <p>{report['analysis'].get('data_stats', {}).get('hackernews', 0)}</p>
                    </div>
                    <div class="stat-card">
                        <h3>GitHub</h3>
                        <p>{report['analysis'].get('data_stats', {}).get('github', 0)}</p>
                    </div>
                    <div class="stat-card">
                        <h3>RSS</h3>
                        <p>{report['analysis'].get('data_stats', {}).get('rss', 0)}</p>
                    </div>
                </div>
                
                <div class="findings">
                    <h2>🔥 주요 발견</h2>
                    {self._format_findings(report.get('top_findings', []))}
                </div>
                
                <div class="analysis">
                    <h2>📊 AI 분석 결과</h2>
                    <pre style="white-space: pre-wrap;">{report['analysis'].get('raw_analysis', 'N/A')}</pre>
                </div>
            </div>
        </body>
        </html>
        """
    
    def _format_findings(self, findings: List[Dict]) -> str:
        """주요 발견 포맷"""
        
        html = "<ul>"
        for finding in findings:
            if finding['type'] == 'reddit_top':
                html += f"<li>Reddit 최고 인기: {finding['title']} ({finding['score']} points)</li>"
            elif finding['type'] == 'github_top':
                html += f"<li>GitHub 최고 스타: {finding['name']} (⭐ {finding['stars']})</li>"
        html += "</ul>"
        return html


class MainAgent:
    """메인 에이전트 - 종합 분석"""
    
    def __init__(self, config: Dict):
        self.config = config
        self.email = config["MAIN_AGENT_EMAIL"]
        self.gemini_key = config["MAIN_AGENT_GEMINI_KEY"]
        
        # Gmail API 설정 (선택사항)
        self.gmail_service = None
        
        # 이전 분석 기록 로드
        self.history = self.load_history()
    
    async def collect_sub_agent_reports(self, direct_reports: List[Dict]) -> List[Dict]:
        """서브 에이전트 리포트 수집 (직접 전달)"""
        
        print("\n👑 메인 에이전트: 서브 에이전트 리포트 종합 중...")
        
        # 직접 전달받은 리포트 사용
        return direct_reports
    
    async def analyze_historical_context(self, current_reports: List[Dict]) -> Dict:
        """과거 데이터와 비교 분석"""
        
        print("📚 과거 데이터와 비교 분석 중...")
        
        context = {
            "trends_evolution": [],
            "recurring_topics": [],
            "new_discoveries": [],
            "sentiment_shift": {}
        }
        
        # 최근 30일 데이터
        recent_history = self.get_recent_history(days=30)
        
        # 중복 제거
        seen_hashes = set()
        unique_content = []
        
        for report in current_reports:
            content_hash = report.get('content_hash')
            
            if content_hash not in seen_hashes:
                seen_hashes.add(content_hash)
                unique_content.append(report)
            
            # 과거 데이터와 비교
            for past_report in recent_history:
                similarity = self.calculate_similarity(
                    report.get('analysis', {}),
                    past_report.get('analysis', {})
                )
                
                if similarity > 0.7:
                    context["recurring_topics"].append({
                        "topic": report.get('specialty'),
                        "frequency": similarity
                    })
        
        # 트렌드 진화 분석
        context["trends_evolution"] = self.analyze_trend_evolution(
            unique_content, recent_history
        )
        
        return context
    
    def calculate_similarity(self, analysis1: Dict, analysis2: Dict) -> float:
        """유사도 계산"""
        
        from difflib import SequenceMatcher
        
        text1 = str(analysis1.get('raw_analysis', ''))
        text2 = str(analysis2.get('raw_analysis', ''))
        
        return SequenceMatcher(None, text1, text2).ratio()
    
    def analyze_trend_evolution(self, current: List, history: List) -> List:
        """트렌드 진화 분석"""
        
        evolution = []
        topics = {}
        
        for report in current + history:
            specialty = report.get('specialty', 'Unknown')
            if specialty not in topics:
                topics[specialty] = []
            topics[specialty].append(report)
        
        for topic, reports in topics.items():
            if len(reports) > 1:
                reports.sort(key=lambda x: x['timestamp'])
                
                evolution.append({
                    "topic": topic,
                    "trend": "growing" if len(reports) > 3 else "stable",
                    "first_seen": reports[0]['timestamp'],
                    "last_seen": reports[-1]['timestamp'],
                    "frequency": len(reports)
                })
        
        return evolution
    
    async def synthesize_final_report(self, 
                                     sub_reports: List[Dict],
                                     context: Dict) -> Dict:
        """최종 종합 리포트 생성"""
        
        print("🎯 최종 종합 분석 중...")
        
        genai.configure(api_key=self.gemini_key)
        model = genai.GenerativeModel('gemini-2.5-flash')
        
        # 모든 서브 에이전트 분석 종합
        all_analyses = []
        for report in sub_reports:
            if 'analysis' in report and 'raw_analysis' in report['analysis']:
                all_analyses.append({
                    "agent": report['agent_id'],
                    "specialty": report['specialty'],
                    "analysis": report['analysis']['raw_analysis'],
                    "top_findings": report.get('top_findings', [])
                })
        
        prompt = f"""
        당신은 수석 기술 분석가입니다.
        
        3명의 전문 분석가가 제출한 리포트를 종합하여 최종 통합 인사이트를 생성하세요.
        
        분석가 리포트들:
        {json.dumps(all_analyses, ensure_ascii=False)[:8000]}
        
        과거 트렌드 컨텍스트:
        - 반복 주제: {len(context.get('recurring_topics', []))}개
        - 트렌드 진화: {context.get('trends_evolution', [])}
        
        다음을 포함한 종합 리포트를 작성하세요:
        
        1. 🔥 이번 주 가장 중요한 트렌드 TOP 5
        2. 🆕 새롭게 등장한 기술/도구
        3. 📈 성장 중인 트렌드 vs 📉 하락 중인 트렌드
        4. 🔮 향후 3개월 예측
        5. 💡 한국 개발자를 위한 구체적 액션 아이템 5개
        6. ⚠️ 주의해야 할 기술적 리스크
        7. 🎯 각 분야별 핵심 인사이트 (AI/Frontend/Backend)
        
        구체적이고 실용적인 조언을 포함하세요.
        한국어로 작성하세요.
        """
        
        try:
            response = model.generate_content(prompt)
            
            final_report = {
                "timestamp": datetime.now().isoformat(),
                "sub_agents_count": len(sub_reports),
                "synthesis": response.text,
                "context": context,
                "sub_reports_summary": [
                    {
                        "agent_id": r.get('agent_id'),
                        "specialty": r.get('specialty'),
                        "items_collected": r.get('data_summary', {}).get('total_items', 0)
                    }
                    for r in sub_reports
                ],
                "deduplication_stats": {
                    "total_items": sum(
                        r.get('data_summary', {}).get('total_items', 0)
                        for r in sub_reports
                    ),
                    "unique_items": len(set(
                        r.get('content_hash') for r in sub_reports
                    ))
                }
            }
            
            # 히스토리 저장
            self.save_to_history(final_report)
            
            return final_report
            
        except Exception as e:
            print(f"❌ 최종 종합 실패: {e}")
            return {"error": str(e)}
    
    def load_history(self) -> List[Dict]:
        """과거 분석 기록 로드"""
        
        history_file = "outputs/agent_history.json"
        
        if os.path.exists(history_file):
            try:
                with open(history_file, 'r') as f:
                    return json.load(f)
            except:
                return []
        return []
    
    def save_to_history(self, report: Dict):
        """분석 기록 저장"""
        
        history_file = "outputs/agent_history.json"
        os.makedirs("outputs", exist_ok=True)
        
        history = self.load_history()
        history.append(report)
        
        # 최근 90일치만 유지
        cutoff = datetime.now() - timedelta(days=90)
        history = [
            h for h in history
            if datetime.fromisoformat(h['timestamp']) > cutoff
        ]
        
        with open(history_file, 'w') as f:
            json.dump(history, f, ensure_ascii=False, indent=2)
    
    def get_recent_history(self, days: int = 30) -> List[Dict]:
        """최근 기록 조회"""
        
        cutoff = datetime.now() - timedelta(days=days)
        history = self.load_history()
        
        return [
            h for h in history
            if datetime.fromisoformat(h['timestamp']) > cutoff
        ]


class MultiAgentOrchestrator:
    """멀티 에이전트 오케스트레이터"""
    
    def __init__(self, config: Dict):
        self.config = config
        
        # 서브 에이전트 3개 생성
        self.sub_agents = [
            SubAgent("A", config),
            SubAgent("B", config),
            SubAgent("C", config)
        ]
        
        # 메인 에이전트
        self.main_agent = MainAgent(config)
    
    async def run_weekly_analysis(self) -> Dict:
        """주간 분석 실행"""
        
        print("""
        ╔═══════════════════════════════════════╗
        ║   🎭 멀티 에이전트 시스템 시작         ║
        ╚═══════════════════════════════════════╝
        """)
        
        # 1. 서브 에이전트들 병렬 실행
        print("\n1️⃣ 서브 에이전트 병렬 실행...")
        
        tasks = [
            agent.collect_and_analyze() 
            for agent in self.sub_agents
        ]
        
        sub_reports = await asyncio.gather(*tasks)
        
        # 2. 유효한 리포트만 필터링
        valid_reports = [r for r in sub_reports if 'error' not in r]
        
        print(f"\n✅ {len(valid_reports)}/{len(sub_reports)} 서브 에이전트 성공")
        
        # 3. 과거 데이터와 비교
        print("\n2️⃣ 과거 데이터 비교 분석...")
        context = await self.main_agent.analyze_historical_context(valid_reports)
        
        # 4. 최종 종합 리포트 생성
        print("\n3️⃣ 최종 종합 리포트 생성...")
        final_report = await self.main_agent.synthesize_final_report(
            valid_reports,
            context
        )
        
        print("""
        ╔═══════════════════════════════════════╗
        ║   ✅ 멀티 에이전트 분석 완료!         ║
        ╚═══════════════════════════════════════╝
        """)
        
        return final_report
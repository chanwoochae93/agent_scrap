import google.generativeai as genai
from anthropic import Anthropic
from transformers import pipeline
import os
from typing import List, Dict, Optional
from datetime import datetime, timedelta
import json

class SmartAIAgent:
    """Gemini → Claude → Hugging Face 계층적 AI 시스템"""
    
    def __init__(self, config):
        self.config = config
        
        # API 사용량 추적
        self.usage_tracker = {
            "gemini": {"count": 0, "last_reset": datetime.now(), "limit": 60},
            "claude": {"count": 0, "last_reset": datetime.now(), "limit": 1000},
            "huggingface": {"count": 0, "last_reset": datetime.now(), "limit": float('inf')}
        }
        
        # Gemini 설정
        self.gemini_available = False
        if config.get("AI_CONFIG", {}).get("gemini", {}).get("api_key"):
            genai.configure(api_key=config["AI_CONFIG"]["gemini"]["api_key"])
            self.gemini_model = genai.GenerativeModel('gemini-2.5-flash')
            self.gemini_available = True
            print("✅ Gemini AI 활성화")
        
        # Claude 설정
        self.claude_available = False
        if config.get("AI_CONFIG", {}).get("claude", {}).get("api_key"):
            self.anthropic = Anthropic(api_key=config["AI_CONFIG"]["claude"]["api_key"])
            self.claude_available = True
            print("✅ Claude AI 활성화")
        
        # Hugging Face 로컬 모델
        self.load_huggingface_models()
    
    def load_huggingface_models(self):
        """Hugging Face 무료 모델 로드"""
        print("🤗 Hugging Face 모델 로딩 중...")
        
        try:
            self.hf_summarizer = pipeline(
                "summarization",
                model="sshleifer/distilbart-cnn-12-6",
                device=-1  # CPU
            )
            
            self.hf_classifier = pipeline(
                "zero-shot-classification",
                model="MoritzLaurer/DeBERTa-v3-base-mnli-fever-anli",
                device=-1
            )
            
            self.hf_sentiment = pipeline(
                "sentiment-analysis",
                model="cardiffnlp/twitter-roberta-base-sentiment-latest",
                device=-1
            )
            
            print("✅ Hugging Face 모델 준비 완료")
            
        except Exception as e:
            print(f"⚠️ Hugging Face 모델 로드 실패: {e}")
            self.hf_summarizer = None
            self.hf_classifier = None
            self.hf_sentiment = None
    
    async def analyze_content(self, content: str, task: str = "summarize") -> str:
        """계층적 AI 분석"""
        
        print(f"\n🔍 AI 분석 시작 (작업: {task})")
        
        # 1. Gemini 시도
        if self.gemini_available and self.check_usage_limit("gemini"):
            result = await self.analyze_with_gemini(content, task)
            if result:
                return result
        
        # 2. Claude 시도
        if self.claude_available and self.check_usage_limit("claude"):
            result = await self.analyze_with_claude(content, task)
            if result:
                return result
        
        # 3. Hugging Face 폴백
        return self.analyze_with_huggingface(content, task)
    
    async def analyze_with_gemini(self, content: str, task: str) -> Optional[str]:
        """Gemini로 분석"""
        
        try:
            prompt = self._create_prompt(content, task)
            response = self.gemini_model.generate_content(prompt)
            
            self.increment_usage("gemini")
            print(f"  ✨ Gemini 사용 ({self.usage_tracker['gemini']['count']}/60)")
            
            return response.text
            
        except Exception as e:
            print(f"  ⚠️ Gemini 오류: {e}")
            return None
    
    async def analyze_with_claude(self, content: str, task: str) -> Optional[str]:
        """Claude로 분석"""
        
        try:
            prompt = self._create_prompt(content, task)
            
            message = self.anthropic.messages.create(
                model="claude-3-haiku-20240307",
                max_tokens=1000,
                messages=[{"role": "user", "content": prompt}]
            )
            
            self.increment_usage("claude")
            print(f"  🤖 Claude 사용 ({self.usage_tracker['claude']['count']}/1000)")
            
            return message.content[0].text
            
        except Exception as e:
            print(f"  ⚠️ Claude 오류: {e}")
            return None
    
    def analyze_with_huggingface(self, content: str, task: str) -> str:
        """Hugging Face로 분석"""
        
        print("  🤗 Hugging Face 폴백 모드")
        
        try:
            if task == "summarize" and self.hf_summarizer:
                result = self.hf_summarizer(
                    content[:1024],
                    max_length=150,
                    min_length=50
                )
                return result[0]['summary_text']
                
            elif task == "classify" and self.hf_classifier:
                labels = [
                    "AI and Machine Learning",
                    "CSS and Design",
                    "JavaScript Frameworks",
                    "Web Performance"
                ]
                result = self.hf_classifier(content[:512], labels)
                return f"Category: {result['labels'][0]} ({result['scores'][0]:.2f})"
                
            elif task == "sentiment" and self.hf_sentiment:
                result = self.hf_sentiment(content[:512])
                return f"Sentiment: {result[0]['label']} ({result[0]['score']:.2f})"
            
            return "분석 실패"
            
        except Exception as e:
            print(f"  ❌ Hugging Face 오류: {e}")
            return "분석 실패"
    
    def check_usage_limit(self, service: str) -> bool:
        """API 사용량 체크"""
        
        tracker = self.usage_tracker[service]
        now = datetime.now()
        
        # Gemini: 분당 제한
        if service == "gemini":
            if (now - tracker["last_reset"]).seconds > 60:
                tracker["count"] = 0
                tracker["last_reset"] = now
            return tracker["count"] < tracker["limit"]
        
        # Claude: 월간 제한
        elif service == "claude":
            if (now - tracker["last_reset"]).days > 30:
                tracker["count"] = 0
                tracker["last_reset"] = now
            return tracker["count"] < tracker["limit"]
        
        return True
    
    def increment_usage(self, service: str):
        """사용량 증가"""
        self.usage_tracker[service]["count"] += 1
        self.save_usage_stats()
    
    def save_usage_stats(self):
        """사용 통계 저장"""
        stats_file = "outputs/ai_usage_stats.json"
        os.makedirs("outputs", exist_ok=True)
        
        stats = {
            "timestamp": datetime.now().isoformat(),
            "usage": self.usage_tracker
        }
        
        with open(stats_file, "w") as f:
            json.dump(stats, f, default=str, indent=2)
    
    async def generate_weekly_insights(self, data: Dict) -> Dict:
        """주간 AI 인사이트 생성"""
        
        insights = {
            "executive_summary": "",
            "key_trends": [],
            "recommendations": [],
            "sentiment_analysis": "",
            "future_outlook": ""
        }
        
        # 데이터 준비
        all_content = self._prepare_data_for_analysis(data)
        
        # 1. 요약
        insights["executive_summary"] = await self.analyze_content(
            all_content, "summarize"
        )
        
        # 2. 트렌드 분석
        trends_text = await self.analyze_content(
            all_content, "analyze_trends"
        )
        insights["key_trends"] = self._parse_trends(trends_text)
        
        # 3. 추천
        recommendations = await self.analyze_content(
            all_content, "recommend"
        )
        insights["recommendations"] = self._parse_recommendations(recommendations)
        
        # 4. 미래 예측
        insights["future_outlook"] = await self.analyze_content(
            all_content, "predict"
        )
        
        return insights
    
    def _create_prompt(self, content: str, task: str) -> str:
        """작업별 프롬프트 생성"""
        
        prompts = {
            "summarize": f"""
                다음 웹개발 및 AI 트렌드 내용을 한국어로 요약해주세요.
                핵심 포인트 3-5개로 정리해주세요.
                
                내용: {content[:3000]}
            """,
            
            "analyze_trends": f"""
                다음 데이터에서 가장 중요한 웹개발/AI 트렌드 5개를 추출해주세요.
                각 트렌드에 대해 이유와 함께 설명해주세요.
                
                데이터: {content[:3000]}
            """,
            
            "recommend": f"""
                다음 트렌드를 기반으로 개발자가 학습해야 할 기술 3가지를 추천해주세요.
                
                트렌드: {content[:2000]}
            """,
            
            "predict": f"""
                현재 트렌드를 기반으로 향후 3-6개월 내 변화를 예측해주세요.
                
                현재 트렌드: {content[:2000]}
            """
        }
        
        return prompts.get(task, prompts["summarize"])
    
    def _prepare_data_for_analysis(self, data: Dict) -> str:
        """분석을 위한 데이터 준비"""
        
        content_parts = []
        
        # Reddit 인기 포스트
        for item in data.get("reddit", [])[:10]:
            content_parts.append(
                f"Reddit: {item.get('title', '')} (Score: {item.get('score', 0)})"
            )
        
        # Hacker News
        for item in data.get("hackernews", [])[:10]:
            content_parts.append(
                f"HN: {item.get('title', '')} (Score: {item.get('score', 0)})"
            )
        
        # GitHub
        for item in data.get("github", [])[:5]:
            content_parts.append(
                f"GitHub: {item.get('name', '')} - {item.get('description', '')}"
            )
        
        return "\n".join(content_parts)
    
    def _parse_trends(self, text: str) -> List[Dict]:
        """트렌드 텍스트 파싱"""
        lines = text.split('\n')
        trends = []
        
        for line in lines:
            if line.strip():
                trends.append({
                    "trend": line.strip(),
                    "importance": "high"
                })
        
        return trends[:5]
    
    def _parse_recommendations(self, text: str) -> List[str]:
        """추천 텍스트 파싱"""
        lines = text.split('\n')
        return [line.strip() for line in lines if line.strip()][:3]

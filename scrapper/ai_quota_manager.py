# scrapper/ai_quota_manager.py

import asyncio
import aiohttp
from datetime import datetime, timedelta
import json
import os
from typing import Dict, Optional, Tuple
import smtplib
from email.mime.text import MIMEText
import google.generativeai as genai

class AIQuotaManager:
    """AI API 한도 실시간 모니터링 & 자동 관리"""
    
    def __init__(self, config):
        self.config = config
        
        # 각 Gemini 키에 대한 상태를 저장할 구조로 변경
        self.quota_status = {
            "gemini": {}, # 여기에 각 에이전트의 상태가 저장됩니다.
            "claude": {
                "available": True, "credits_remaining": 5.00, "limit": 5.00,
                "reset_time": "manual", "last_checked": None, "alert_sent": False
            },
            "huggingface": {
                "available": True, "remaining": "unlimited", "limit": "unlimited",
                "reset_time": None, "last_checked": None, "alert_sent": False
            }
        }
        
        # Gemini 키 초기 상태 설정
        for agent_name in self.config.get("API_KEYS", {}):
            if "gemini" in agent_name.lower() or agent_name in ["collector", "analyzer", "emailer", "code_reviewer"]:
                 self.quota_status["gemini"][agent_name] = {
                    "available": False, "api_key_valid": False, "usage_today": 0,
                    "limit": 1500, "last_checked": None
                }

        self.warning_thresholds = {"critical": 0.05, "warning": 0.20}
        self.load_cached_quota()
    
    async def check_all_quotas(self) -> Dict:
        """모든 AI 서비스 한도 체크"""
        print("\n🔍 AI API 한도 체크 중...")
        
        # Gemini 키들을 병렬로 체크
        gemini_tasks = []
        for agent_name, api_key in self.config.get("API_KEYS", {}).items():
            if api_key and ("gemini" in agent_name.lower() or agent_name in ["collector", "analyzer", "emailer", "code_reviewer"]):
                gemini_tasks.append(self.check_gemini_key_status(agent_name, api_key))
        
        await asyncio.gather(*gemini_tasks)

        # Claude 체크
        await self.check_claude_quota()
        
        self.save_cached_quota()
        await self.check_quota_warnings()
        
        return self.quota_status
    
    async def check_gemini_key_status(self, agent_name: str, api_key: str):
        """개별 Gemini API 키의 유효성을 테스트"""
        status = self.quota_status["gemini"][agent_name]
        try:
            # 가장 가벼운 API 호출로 키 유효성 검사
            genai.configure(api_key=api_key)
            models = genai.list_models()
            is_valid = any('generateContent' in m.supported_generation_methods for m in models)
            
            status["api_key_valid"] = is_valid
            status["available"] = is_valid
        except Exception as e:
            status["api_key_valid"] = False
            status["available"] = False
            print(f"  ⚠️ Gemini 키 ({agent_name}) 확인 중 오류: {e}")
        
        status["last_checked"] = datetime.now().isoformat()
        # 로컬 사용량 기반 남은 횟수 추정
        status["remaining_daily"] = status["limit"] - status.get("usage_today", 0)

    async def check_claude_quota(self) -> Tuple[bool, Dict]:
        """Claude API 한도 체크 (기존과 유사)"""
        api_key = self.config.get("AI_CONFIG", {}).get("claude", {}).get("api_key")
        if not api_key:
            return False, {"error": "No API key"}
        
        credits = self._estimate_claude_credits()
        quota_info = {
            "available": credits > 0, "credits_remaining": credits,
            "limit": 5.00, "reset_time": "manual",
            "last_checked": datetime.now().isoformat()
        }
        self.quota_status["claude"].update(quota_info)
        return True, quota_info
    
    async def check_quota_warnings(self):
        """한도 경고 확인 및 알림"""
        warnings = []
        # Gemini 체크
        for agent, status in self.quota_status["gemini"].items():
            if status.get("api_key_valid"):
                remaining = status.get("remaining_daily", status['limit'])
                limit = status['limit']
                ratio = remaining / limit if limit > 0 else 0
                
                if ratio <= self.warning_thresholds["critical"]:
                    warnings.append({
                        "service": f"Gemini ({agent})", "level": "CRITICAL",
                        "message": f"Gemini ({agent}) 일일 한도 5% 이하! ({remaining}/{limit})"
                    })
        # ... (Claude 경고 로직은 동일) ...
        if warnings:
            await self.send_quota_alert(warnings)

    async def send_quota_alert(self, warnings: list):
        # ... (기존과 동일) ...
        pass
    
    def update_usage(self, service: str, agent_name: str = "default", tokens_used: int = 0):
        """사용량 업데이트"""
        if service == "gemini":
            if agent_name in self.quota_status["gemini"]:
                self.quota_status["gemini"][agent_name]["usage_today"] += 1
        # ... (Claude 사용량 업데이트는 동일) ...

    def save_cached_quota(self):
        """한도 정보 캐시 저장"""
        cache_file = os.path.join(self.config["OUTPUT_DIR"], "ai_quota_cache.json")
        os.makedirs(os.path.dirname(cache_file), exist_ok=True)
        
        with open(cache_file, "w") as f:
            json.dump(self.quota_status, f, indent=2, default=str)
    
    def load_cached_quota(self):
        """캐시된 한도 정보 로드"""
        cache_file = os.path.join(self.config["OUTPUT_DIR"], "ai_quota_cache.json")
        if not os.path.exists(cache_file): return

        try:
            with open(cache_file, "r") as f:
                cached_data = json.load(f)
            
            timestamp = cached_data.get("gemini", {}).get("collector", {}).get("last_checked")
            if not timestamp: return

            cached_date = datetime.fromisoformat(timestamp).date()
            if cached_date == datetime.now().date():
                # 오늘 캐시라면 사용량만 복원
                for agent, status in self.quota_status["gemini"].items():
                    usage = cached_data.get("gemini", {}).get(agent, {}).get("usage_today", 0)
                    status["usage_today"] = usage
        except Exception:
            pass # 캐시 로드 실패 시 무시

    def _create_bar(self, current, total, length=20) -> str:
        """텍스트 기반 퍼센트 바 생성"""
        if not isinstance(current, (int, float)) or not isinstance(total, (int, float)) or total == 0:
            return ""
        
        current = min(current, total)
        percentage = current / total
        filled_length = int(length * percentage)
        bar = '█' * filled_length + '░' * (length - filled_length)
        return f"  [{bar}] {percentage:.0%}"

    def get_quota_summary(self) -> str:
        """한도 요약 리포트"""
        summary_lines = [
            "📊 AI API 한도 현황",
            "═══════════════════════════════", ""
        ]
        
        # Gemini 요약
        summary_lines.append("🌟 Gemini (Google)")
        for agent, status in self.quota_status.get("gemini", {}).items():
            remaining = status.get("remaining_daily", 0)
            limit = status.get("limit", 1500)
            emoji = "✅ 유효" if status.get("api_key_valid") else "❌ 비활성/오류"
            summary_lines.append(f"  • {agent.title()}: {remaining}/{limit} (상태: {emoji})")
            summary_lines.append(self._create_bar(remaining, limit))

        # Claude 요약
        claude = self.quota_status.get("claude", {})
        claude_credits = claude.get("credits_remaining", 0)
        claude_limit = claude.get("limit", 5.0)
        claude_status_emoji = "✅ 양호" if claude_credits > 2 else "⚠️ 주의" if claude_credits > 0.5 else "🔴 위험"
        summary_lines.extend([
            "", "🤖 Claude (Anthropic)",
            f"  • 크레딧: ${claude_credits:.2f} / ${claude_limit:.2f}",
            f"  • 상태: {claude_status_emoji}",
        ])
        summary_lines.append(self._create_bar(claude_credits, claude_limit))
        
        # Hugging Face 요약
        summary_lines.extend([
            "", "🤗 Hugging Face",
            "  • 한도: 무제한", "  • 상태: ✅ 항상 사용 가능", ""
        ])
        
        summary_lines.extend([
            f"📌 추천: {self.get_best_available_service().upper()}",
            "═══════════════════════════════"
        ])
        
        return "\n".join(summary_lines)

    def get_best_available_service(self) -> Optional[str]:
        """현재 사용 가능한 최적 서비스"""
        # Gemini 키 중 하나라도 사용 가능하면 Gemini 우선
        for status in self.quota_status["gemini"].values():
            if status.get("available") and status.get("remaining_daily", 0) > 10:
                return "gemini"
        
        if self.quota_status["claude"].get("credits_remaining", 0) > 0.10:
            return "claude"
            
        return "huggingface"

    def _estimate_claude_credits(self) -> float:
        # ... (기존과 동일) ...
        used_credits = getattr(self, 'claude_credits_used', 0)
        return max(0, 5.00 - used_credits)
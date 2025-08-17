import asyncio
import aiohttp
from datetime import datetime, timedelta
import json
import os
from typing import Dict, Optional, Tuple
import smtplib
from email.mime.text import MIMEText

class AIQuotaManager:
    """AI API 한도 실시간 모니터링 & 자동 관리"""
    
    def __init__(self, config):
        self.config = config
        self.quota_status = {
            "gemini": {
                "available": True,
                "remaining": None,
                "limit": 1500,
                "reset_time": None,
                "last_checked": None,
                "alert_sent": False
            },
            "claude": {
                "available": True,
                "remaining": 5.00,
                "limit": 5.00,
                "reset_time": "manual",
                "last_checked": None,
                "alert_sent": False
            },
            "huggingface": {
                "available": True,
                "remaining": "unlimited",
                "limit": "unlimited",
                "reset_time": None,
                "last_checked": None,
                "alert_sent": False
            }
        }
        
        # 경고 임계값
        self.warning_thresholds = {
            "critical": 0.05,  # 5% 이하
            "warning": 0.20,   # 20% 이하
            "notice": 0.50     # 50% 이하
        }
        
        # 캐시 로드
        self.load_cached_quota()
    
    async def check_all_quotas(self) -> Dict:
        """모든 AI 서비스 한도 체크"""
        
        print("\n🔍 AI API 한도 체크 중...")
        
        results = {}
        
        # Gemini 체크
        gemini_ok, gemini_info = await self.check_gemini_quota()
        results["gemini"] = gemini_info
        
        # Claude 체크
        claude_ok, claude_info = await self.check_claude_quota()
        results["claude"] = claude_info
        
        # Hugging Face는 무제한
        results["huggingface"] = {
            "available": True,
            "remaining": "unlimited",
            "limit": "unlimited"
        }
        
        # 캐시 저장
        self.save_cached_quota()
        
        # 한도 경고 체크
        await self.check_quota_warnings(results)
        
        return results
    
    async def check_gemini_quota(self) -> Tuple[bool, Dict]:
        """Gemini API 한도 체크"""
        
        api_key = self.config.get("AI_CONFIG", {}).get("gemini", {}).get("api_key")
        
        if not api_key:
            return False, {"error": "No API key"}
        
        # 로컬 추적 기반 추정
        today = datetime.now().date()
        
        if not hasattr(self, 'gemini_last_reset') or self.gemini_last_reset != today:
            self.gemini_usage_today = 0
            self.gemini_last_reset = today
        
        remaining = 1500 - getattr(self, 'gemini_usage_today', 0)
        
        quota_info = {
            "available": remaining > 0,
            "remaining_daily": remaining,
            "limit_daily": 1500,
            "reset_time": self._calculate_reset_time("daily"),
            "last_checked": datetime.now().isoformat()
        }
        
        self.quota_status["gemini"].update(quota_info)
        return True, quota_info
    
    async def check_claude_quota(self) -> Tuple[bool, Dict]:
        """Claude API 한도 체크"""
        
        api_key = self.config.get("AI_CONFIG", {}).get("claude", {}).get("api_key")
        
        if not api_key:
            return False, {"error": "No API key"}
        
        # 크레딧 추정
        credits = self._estimate_claude_credits()
        
        quota_info = {
            "available": credits > 0,
            "credits_remaining": credits,
            "limit": 5.00,
            "reset_time": "manual",
            "last_checked": datetime.now().isoformat()
        }
        
        self.quota_status["claude"].update(quota_info)
        return True, quota_info
    
    async def check_quota_warnings(self, quotas: Dict):
        """한도 경고 확인 및 알림"""
        
        warnings = []
        
        # Gemini 체크
        if "remaining_daily" in quotas.get("gemini", {}):
            remaining = quotas["gemini"]["remaining_daily"]
            limit = quotas["gemini"]["limit_daily"]
            ratio = remaining / limit if limit > 0 else 0
            
            if ratio <= self.warning_thresholds["critical"]:
                warnings.append({
                    "service": "Gemini",
                    "level": "CRITICAL",
                    "message": f"Gemini 일일 한도 5% 이하! ({remaining}/{limit})"
                })
            elif ratio <= self.warning_thresholds["warning"]:
                warnings.append({
                    "service": "Gemini",
                    "level": "WARNING",
                    "message": f"Gemini 일일 한도 20% 이하 ({remaining}/{limit})"
                })
        
        # Claude 체크
        if "credits_remaining" in quotas.get("claude", {}):
            credits = quotas["claude"]["credits_remaining"]
            
            if credits <= 0.25:
                warnings.append({
                    "service": "Claude",
                    "level": "CRITICAL",
                    "message": f"Claude 크레딧 부족! (${credits:.2f} 남음)"
                })
            elif credits <= 1.00:
                warnings.append({
                    "service": "Claude",
                    "level": "WARNING",
                    "message": f"Claude 크레딧 경고 (${credits:.2f} 남음)"
                })
        
        # 경고 이메일 발송
        if warnings:
            await self.send_quota_alert(warnings)
    
    async def send_quota_alert(self, warnings: list):
        """한도 경고 이메일 발송"""
        
        # 중복 알림 방지
        last_alert = getattr(self, 'last_alert_time', None)
        if last_alert and (datetime.now() - last_alert).hours < 6:
            return
        
        try:
            body = "<h2>🚨 AI API 한도 경고</h2><ul>"
            
            for warning in warnings:
                color = "#ff6b6b" if warning["level"] == "CRITICAL" else "#ffd93d"
                body += f'<li style="color: {color}">{warning["message"]}</li>'
            
            body += "</ul>"
            
            msg = MIMEText(body, "html", "utf-8")
            msg["Subject"] = "⚠️ AI API 한도 경고!"
            msg["From"] = self.config["EMAIL_CONFIG"]["sender_email"]
            msg["To"] = self.config["EMAIL_CONFIG"]["receiver_email"]
            
            with smtplib.SMTP(
                self.config["EMAIL_CONFIG"]["smtp_server"],
                self.config["EMAIL_CONFIG"]["smtp_port"]
            ) as server:
                server.starttls()
                server.login(
                    self.config["EMAIL_CONFIG"]["sender_email"],
                    self.config["EMAIL_CONFIG"]["sender_password"]
                )
                server.send_message(msg)
            
            print("📧 한도 경고 이메일 발송 완료!")
            self.last_alert_time = datetime.now()
            
        except Exception as e:
            print(f"❌ 경고 이메일 발송 실패: {e}")
    
    def get_best_available_service(self) -> Optional[str]:
        """현재 사용 가능한 최적 서비스"""
        
        priority = ["gemini", "claude", "huggingface"]
        
        for service in priority:
            status = self.quota_status.get(service, {})
            
            if service == "gemini":
                remaining = status.get("remaining_daily", 0)
                if remaining > 10:
                    return "gemini"
                    
            elif service == "claude":
                credits = status.get("credits_remaining", 0)
                if credits > 0.10:
                    return "claude"
                    
            elif service == "huggingface":
                return "huggingface"
        
        return "huggingface"
    
    def update_usage(self, service: str, tokens_used: int = 0):
        """사용량 업데이트"""
        
        if service == "gemini":
            if not hasattr(self, 'gemini_usage_today'):
                self.gemini_usage_today = 0
            self.gemini_usage_today += 1
            
        elif service == "claude":
            cost = (tokens_used / 1000) * 0.00025
            if not hasattr(self, 'claude_credits_used'):
                self.claude_credits_used = 0
            self.claude_credits_used += cost
    
    def save_cached_quota(self):
        """한도 정보 캐시 저장"""
        
        cache_file = "outputs/ai_quota_cache.json"
        os.makedirs("outputs", exist_ok=True)
        
        with open(cache_file, "w") as f:
            json.dump({
                "timestamp": datetime.now().isoformat(),
                "quota_status": self.quota_status,
                "usage": {
                    "gemini_today": getattr(self, 'gemini_usage_today', 0),
                    "claude_credits": getattr(self, 'claude_credits_used', 0)
                }
            }, f, indent=2, default=str)
    
    def load_cached_quota(self):
        """캐시된 한도 정보 로드"""
        
        cache_file = "outputs/ai_quota_cache.json"
        
        if os.path.exists(cache_file):
            try:
                with open(cache_file, "r") as f:
                    data = json.load(f)
                    
                    cached_date = datetime.fromisoformat(
                        data["timestamp"]
                    ).date()
                    
                    if cached_date == datetime.now().date():
                        self.gemini_usage_today = data["usage"]["gemini_today"]
                        self.claude_credits_used = data["usage"]["claude_credits"]
                    else:
                        self.gemini_usage_today = 0
                        
            except Exception:
                pass
    
    def _estimate_claude_credits(self) -> float:
        """Claude 크레딧 추정"""
        
        cost_per_1k_input = 0.00025
        cost_per_1k_output = 0.00125
        
        used_credits = getattr(self, 'claude_credits_used', 0)
        
        return max(0, 5.00 - used_credits)
    
    def _calculate_reset_time(self, reset_type: str) -> str:
        """리셋 시간 계산"""
        
        now = datetime.now()
        
        if reset_type == "daily":
            tomorrow = now + timedelta(days=1)
            reset_time = tomorrow.replace(hour=0, minute=0, second=0)
        else:
            return "manual"
        
        return reset_time.isoformat()
    
    def get_quota_summary(self) -> str:
        """한도 요약 리포트"""
        
        gemini = self.quota_status.get("gemini", {})
        claude = self.quota_status.get("claude", {})
        
        summary = f"""
        📊 AI API 한도 현황
        ═══════════════════════════════
        
        🌟 Gemini (Google)
        • 일일 한도: {gemini.get("remaining_daily", "?")} / 1500
        • 상태: {self._get_status_emoji(gemini)}
        
        🤖 Claude (Anthropic)
        • 크레딧: ${claude.get("credits_remaining", 0):.2f} / $5.00
        • 상태: {self._get_status_emoji(claude)}
        
        🤗 Hugging Face
        • 한도: 무제한
        • 상태: ✅ 항상 사용 가능
        
        📌 추천: {self.get_best_available_service().upper()}
        ═══════════════════════════════
        """
        
        return summary
    
    def _get_status_emoji(self, status: Dict) -> str:
        """상태 이모지"""
        
        if "remaining_daily" in status:
            ratio = status["remaining_daily"] / 1500
            if ratio > 0.5:
                return "✅ 양호"
            elif ratio > 0.2:
                return "⚠️ 주의"
            else:
                return "🔴 위험"
        
        if "credits_remaining" in status:
            credits = status["credits_remaining"]
            if credits > 2:
                return "✅ 양호"
            elif credits > 0.5:
                return "⚠️ 주의"
            else:
                return "🔴 위험"
        
        return "✅ 사용 가능"
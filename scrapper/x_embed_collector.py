import asyncio
import aiohttp
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
from datetime import datetime

from scrapper.utils.logger import logger

class XEmbedCollector:
    """X(Twitter) Embed API를 활용하여 트윗을 비동기적으로 수집합니다."""

    def __init__(self, config: Dict):
        self.config = config.get("X_CONFIG", {})
        self.base_url = "https://publish.twitter.com/oembed"
        self.monitor_sites = self.config.get("monitor_sites", [])

    async def collect_tweets(self, urls: List[str]) -> List[Dict]:
        """주어진 URL 목록에서 트윗 상세 정보를 비동기적으로 수집합니다."""
        logger.info(f"  🔍 {len(urls)}개의 트윗 URL에서 정보 수집 중...")
        unique_urls = list(set(urls))

        async with aiohttp.ClientSession() as session:
            tasks = [self._get_tweet_data(session, url) for url in unique_urls[:30]] # 최대 30개로 제한
            results = await asyncio.gather(*tasks)
        
        tweets = [data for data in results if data] # None이 아닌 결과만 필터링
        
        # 관련성 점수 계산 및 필터링
        for tweet in tweets:
            tweet['relevance_score'] = self._calculate_relevance(tweet['text'])
        
        relevant_tweets = [t for t in tweets if t['relevance_score'] > 0.3]
        relevant_tweets.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        logger.info(f"  ✅ {len(relevant_tweets)}개의 관련 트윗 수집 완료.")
        return relevant_tweets[:20] # 상위 20개 반환

    async def _get_tweet_data(self, session: aiohttp.ClientSession, tweet_url: str) -> Optional[Dict]:
        """Embed API를 통해 단일 트윗의 상세 정보를 가져옵니다."""
        params = {"url": tweet_url, "omit_script": "true", "dnt": "true", "lang": "ko"}
        try:
            async with session.get(self.base_url, params=params, timeout=5) as response:
                if response.status == 200:
                    data = await response.json()
                    soup = BeautifulSoup(data['html'], 'html.parser')
                    tweet_text = self._extract_text_from_html(soup)
                    return {
                        "url": data['url'],
                        "author_name": data['author_name'],
                        "text": tweet_text,
                        "timestamp": datetime.now().isoformat()
                    }
        except Exception:
            # 개별 트윗 실패는 로그를 남기지 않음 (너무 많을 수 있음)
            pass
        return None

    def _extract_text_from_html(self, soup: BeautifulSoup) -> str:
        """Embed HTML에서 순수 텍스트만 추출합니다."""
        blockquote = soup.find('blockquote')
        if not blockquote:
            return ""
        
        # 링크와 시간 정보 제거
        for a in blockquote.find_all('a'):
            a.decompose()
        
        tweet_text = blockquote.get_text(strip=True)
        return re.sub(r'—\s*$', '', tweet_text).strip()

    def _calculate_relevance(self, text: str) -> float:
        """키워드 기반으로 트윗의 관련성 점수를 계산합니다."""
        score = 0.0
        text_lower = text.lower()
        high_value = ['css', 'react', 'ai', 'gpt', 'vue', 'tailwind', 'next.js']
        medium_value = ['web', 'development', 'javascript', 'frontend', 'design']
        
        for keyword in high_value:
            if keyword in text_lower: score += 0.3
        for keyword in medium_value:
            if keyword in text_lower: score += 0.1
            
        return min(score, 1.0)
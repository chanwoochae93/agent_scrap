import requests
from bs4 import BeautifulSoup
import re
from typing import List, Dict, Optional
from datetime import datetime
import time

class XEmbedCollector:
    """X(Twitter) Embed API를 활용한 트윗 수집"""
    
    def __init__(self, config):
        self.config = config
        self.base_url = "https://publish.twitter.com/oembed"
        self.collected_urls = set()
    
    def collect_tweets(self) -> List[Dict]:
        """트윗 수집 메인 함수"""
        print("  🔍 트윗 URL 수집 중...")
        
        # 1. 다양한 소스에서 URL 수집
        urls = self._collect_all_urls()
        
        # 중복 제거
        unique_urls = list(set(urls))
        print(f"  ✅ {len(unique_urls)}개의 고유한 트윗 URL 발견")
        
        # 2. Embed API로 상세 정보 가져오기
        tweets = []
        
        for i, url in enumerate(unique_urls[:30], 1):  # 최대 30개
            if i % 10 == 0:
                print(f"    [{i}/{min(len(unique_urls), 30)}] 트윗 정보 수집 중...")
            
            tweet_data = self._get_tweet_data(url)
            
            if tweet_data:
                tweet_data['category'] = self._categorize_tweet(tweet_data['text'])
                tweet_data['relevance_score'] = self._calculate_relevance(tweet_data['text'])
                
                if tweet_data['relevance_score'] > 0.3:  # 관련성 있는 것만
                    tweets.append(tweet_data)
            
            time.sleep(0.3)  # Rate limiting
        
        # 관련성 순 정렬
        tweets.sort(key=lambda x: x['relevance_score'], reverse=True)
        
        print(f"  ✅ {len(tweets)}개의 관련 트윗 수집 완료")
        return tweets[:20]  # 상위 20개
    
    def _collect_all_urls(self) -> List[str]:
        """모든 소스에서 URL 수집"""
        urls = []
        
        # Reddit에서 수집 (이미 수집된 데이터 활용)
        urls.extend(self._get_urls_from_reddit())
        
        # 웹사이트에서 수집
        if self.config["X_CONFIG"]["url_sources"]["websites"]:
            urls.extend(self._collect_from_websites())
        
        # GitHub에서 수집
        if self.config["X_CONFIG"]["url_sources"]["github"]:
            urls.extend(self._collect_from_github())
        
        return urls
    
    def _get_urls_from_reddit(self) -> List[str]:
        """Reddit 데이터에서 X URL 추출"""
        urls = []
        
        # 이미 수집된 Reddit 데이터가 있다면 활용
        # (실제로는 collectors.py에서 수집한 데이터 참조)
        
        return urls
    
    def _collect_from_websites(self) -> List[str]:
        """웹사이트에서 임베드된 트윗 수집"""
        tweet_urls = []
        
        for site in self.config["X_CONFIG"]["monitor_sites"][:3]:  # 시간 절약
            try:
                response = requests.get(f"{site}/", timeout=10)
                soup = BeautifulSoup(response.text, 'html.parser')
                
                # iframe 임베드
                for iframe in soup.find_all('iframe'):
                    src = iframe.get('src', '')
                    if 'twitter.com/i/embed' in src or 'x.com/i/embed' in src:
                        match = re.search(r'url=([^&]+)', src)
                        if match:
                            tweet_urls.append(match.group(1))
                
                # blockquote 임베드
                for blockquote in soup.find_all('blockquote', class_='twitter-tweet'):
                    links = blockquote.find_all('a')
                    for link in links:
                        href = link.get('href', '')
                        if ('twitter.com' in href or 'x.com' in href) and '/status/' in href:
                            tweet_urls.append(href)
                
            except Exception:
                continue
        
        return tweet_urls
    
    def _collect_from_github(self) -> List[str]:
        """GitHub README에서 트윗 URL 수집"""
        tweet_urls = []
        
        repos = [
            "facebook/react",
            "vuejs/vue",
            "vercel/next.js"
        ]
        
        for repo in repos:
            readme_url = f"https://api.github.com/repos/{repo}/readme"
            
            try:
                response = requests.get(readme_url, headers={
                    "Accept": "application/vnd.github.v3+json"
                })
                
                if response.status_code == 200:
                    import base64
                    content = response.json().get('content', '')
                    decoded = base64.b64decode(content).decode('utf-8')
                    
                    # X/Twitter 링크 찾기
                    pattern = r'https?://(?:www\.)?(?:twitter|x)\.com/\w+/status/\d+'
                    twitter_links = re.findall(pattern, decoded)
                    tweet_urls.extend(twitter_links)
                    
            except Exception:
                continue
        
        return tweet_urls
    
    def _get_tweet_data(self, tweet_url: str) -> Optional[Dict]:
        """Embed API로 트윗 정보 가져오기"""
        
        params = {
            "url": tweet_url,
            "omit_script": "true",
            "dnt": "true",
            "lang": "ko"
        }
        
        try:
            response = requests.get(self.base_url, params=params)
            
            if response.status_code == 200:
                data = response.json()
                
                # HTML에서 텍스트 추출
                soup = BeautifulSoup(data['html'], 'html.parser')
                
                # 트윗 본문 추출
                blockquote = soup.find('blockquote')
                tweet_text = ""
                
                if blockquote:
                    # 링크와 시간 제거
                    for a in blockquote.find_all('a'):
                        if 'twitter.com' in a.get('href', '') or 'x.com' in a.get('href', ''):
                            a.decompose()
                    
                    tweet_text = blockquote.get_text(strip=True)
                    tweet_text = re.sub(r'—\s*$', '', tweet_text)
                    tweet_text = re.sub(r'\s+', ' ', tweet_text)
                
                return {
                    "url": data['url'],
                    "author_name": data['author_name'],
                    "author_url": data['author_url'],
                    "html": data['html'],
                    "text": tweet_text,
                    "type": data.get('type', 'rich'),
                    "timestamp": datetime.now().isoformat()
                }
                
        except Exception:
            pass
        
        return None
    
    def _categorize_tweet(self, text: str) -> str:
        """트윗 카테고리 분류"""
        text_lower = text.lower()
        
        if any(word in text_lower for word in ['css', 'style', 'tailwind', 'sass']):
            return "CSS & Styling"
        elif any(word in text_lower for word in ['ai', 'gpt', 'llm', 'machine learning']):
            return "AI & ML"
        elif any(word in text_lower for word in ['react', 'vue', 'angular', 'svelte']):
            return "Frameworks"
        elif any(word in text_lower for word in ['javascript', 'typescript', 'node']):
            return "JavaScript"
        else:
            return "General"
    
    def _calculate_relevance(self, text: str) -> float:
        """관련성 점수 계산"""
        score = 0.0
        text_lower = text.lower()
        
        high_value = ['css', 'react', 'ai', 'gpt', 'vue', 'tailwind', 'next.js']
        medium_value = ['web', 'development', 'javascript', 'frontend', 'design']
        
        for keyword in high_value:
            if keyword in text_lower:
                score += 0.3
        
        for keyword in medium_value:
            if keyword in text_lower:
                score += 0.1
        
        return min(score, 1.0)
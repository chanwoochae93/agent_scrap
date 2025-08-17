import asyncio
import feedparser
import asyncpraw
import aiohttp
import os
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import re
from typing import List, Dict, Any, Optional
import json

import logging
logger = logging.getLogger(__name__)


class DataCollector:
    """
    다양한 소스에서 웹개발 & AI 트렌드 데이터를 비동기적으로 수집합니다.
    - 성능 개선을 위해 aiohttp를 사용하여 HTTP 요청을 병렬 처리합니다.
    - 각 수집 메서드는 독립적으로 실행되며, 오류 발생 시 다른 수집에 영향을 주지 않습니다.
    """

    def __init__(self, config: Dict[str, Any]):
        """DataCollector를 초기화합니다."""
        self.config = config
        self.rss_feeds = config.get("RSS_FEEDS", [])
        self.reddit_config = config.get("REDDIT_CONFIG", {})
        self.hn_config = config.get("HN_CONFIG", {})
        self.github_config = config.get("GITHUB_CONFIG", {})
        self.filter_keywords = config.get("FILTER_KEYWORDS", {})
        self.report_config = config.get("REPORT_CONFIG", {})
        self.github_token = os.getenv("GITHUB_TOKEN")

    async def collect_all(self) -> Dict[str, List[Dict]]:
        """모든 데이터 소스에서 병렬로 정보를 수집합니다."""
        logger.info("🚀 데이터 수집 시작...")
        headers = {"Accept": "application/vnd.github.v3+json"}
        if self.github_token:
            headers["Authorization"] = f"token {self.github_token}"

        async with aiohttp.ClientSession(headers=headers) as session:
            tasks = {
                "rss": self._collect_rss_feeds(session),
                "reddit": self._collect_reddit(),
                "hackernews": self._collect_hackernews(session),
                "github": self._collect_github_trending(session),
            }

            results = await asyncio.gather(*tasks.values(), return_exceptions=True)
            
            collected_data: Dict[str, List[Dict]] = {}
            for source, result in zip(tasks.keys(), results):
                if isinstance(result, Exception):
                    logger.error(f"⚠️ {source} 수집 중 심각한 오류 발생: {result}")
                    collected_data[source] = []
                else:
                    logger.info(f"✅ {source} 수집 완료: {len(result)}개 항목")
                    collected_data[source] = result
        
        logger.info("✅ 전체 데이터 수집 완료!")
        return collected_data

    # --- 데이터 소스별 수집 메서드 ---

    async def _collect_rss_feeds(self, session: aiohttp.ClientSession) -> List[Dict]:
        """설정된 모든 RSS 피드에서 게시글을 비동기적으로 수집합니다."""
        tasks = [self._fetch_and_parse_rss(session, url) for url in self.rss_feeds]
        results = await asyncio.gather(*tasks)
        # flatten list of lists
        articles = [item for sublist in results for item in sublist]
        return articles

    async def _collect_reddit(self) -> List[Dict]:
        """Reddit에서 인기 포스트를 비동기적으로 수집합니다."""
        if not self.reddit_config.get("enabled"):
            return []
        
        posts = []
        try:
            reddit = asyncpraw.Reddit(
                client_id=self.reddit_config["client_id"],
                client_secret=self.reddit_config["client_secret"],
                user_agent=self.reddit_config["user_agent"],
            )
            async with reddit:
                for subreddit_name in self.reddit_config["subreddits"]:
                    try:
                        subreddit = await reddit.subreddit(subreddit_name)
                        async for post in subreddit.top(time_filter=self.reddit_config["time_filter"], limit=self.reddit_config["post_limit"]):
                            content_text = post.title + " " + post.selftext
                            if self._is_relevant_content(content_text):
                                posts.append({
                                    "title": post.title,
                                    "url": f"https://reddit.com{post.permalink}",
                                    "score": post.score,
                                    "source": f"r/{subreddit_name}",
                                    "category": self._categorize_content(content_text),
                                })
                    except Exception as e:
                        logger.warning(f"r/{subreddit_name} 서브레딧 수집 중 오류: {e}")
        except Exception as e:
            logger.error(f"Reddit API 연결 오류: {e}")
        
        posts.sort(key=lambda x: x["score"], reverse=True)
        return posts[:self.report_config.get("max_items_per_source", 15)]

    async def _collect_hackernews(self, session: aiohttp.ClientSession) -> List[Dict]:
        """Hacker News에서 인기 스토리를 비동기적으로 수집합니다."""
        if not self.hn_config.get("enabled"):
            return []

        top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
        story_ids_json = await self._fetch_json(session, top_stories_url)
        if not story_ids_json:
            return []
        
        story_ids = story_ids_json[:100]
        tasks = [self._fetch_and_parse_story(session, story_id) for story_id in story_ids]
        stories = await asyncio.gather(*tasks)

        relevant_stories = [s for s in stories if s and self._is_relevant_content(s['title']) and s['score'] >= self.hn_config.get("min_score", 50)]
        return relevant_stories[:self.hn_config.get("story_limit", 30)]

    async def _collect_github_trending(self, session: aiohttp.ClientSession) -> List[Dict]:
        """GitHub에서 트렌딩 리포지토리를 언어별로 수집합니다."""
        if not self.github_config.get("enabled"):
            return []

        tasks = [self._fetch_github_repos_by_lang(session, lang) for lang in self.github_config.get("languages", [])]
        results = await asyncio.gather(*tasks)
        repos = [item for sublist in results for item in sublist]

        repos.sort(key=lambda x: x["stars"], reverse=True)
        return repos[:self.report_config.get("max_items_per_source", 15)]

    # --- 헬퍼(Helper) 메서드 ---

    async def _fetch_and_parse_rss(self, session: aiohttp.ClientSession, url: str) -> List[Dict]:
        """단일 RSS 피드를 가져와 파싱합니다."""
        articles = []
        xml_content = await self._fetch_text(session, url)
        if not xml_content:
            return []

        feed = feedparser.parse(xml_content)
        for entry in feed.entries[:10]:
            content_text = entry.title + " " + entry.get("summary", "")
            if self._is_relevant_content(content_text):
                articles.append({
                    "title": entry.title,
                    "link": entry.link,
                    "source": feed.feed.title if hasattr(feed.feed, 'title') else url,
                    "category": self._categorize_content(content_text),
                })
        return articles

    async def _fetch_and_parse_story(self, session: aiohttp.ClientSession, story_id: int) -> Optional[Dict]:
        """Hacker News 스토리 ID로 상세 정보를 가져옵니다."""
        story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
        story_data = await self._fetch_json(session, story_url)
        if not story_data or story_data.get("type") != "story":
            return None
        
        return {
            "title": story_data.get("title", ""),
            "url": story_data.get("url", f"https://news.ycombinator.com/item?id={story_id}"),
            "score": story_data.get("score", 0),
            "source": "Hacker News",
            "category": self._categorize_content(story_data.get("title", "")),
        }

    async def _fetch_github_repos_by_lang(self, session: aiohttp.ClientSession, language: str) -> List[Dict]:
        """특정 프로그래밍 언어의 GitHub 트렌딩 리포지토리를 가져옵니다."""
        repos = []
        date_since = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
        url = "https://api.github.com/search/repositories"
        params = {"q": f"language:{language} created:>{date_since}", "sort": "stars", "order": "desc", "per_page": 10}
        
        data = await self._fetch_json(session, url, params=params)
        if not data or "items" not in data:
            return []

        for repo in data["items"]:
            description = repo.get("description") or ""
            content_text = repo["name"] + " " + description
            if self._is_relevant_content(content_text):
                repos.append({
                    "name": repo["name"],
                    "url": repo["html_url"],
                    "stars": repo["stargazers_count"],
                    "description": description,
                    "language": repo.get("language", ""),
                    "source": "GitHub",
                    "category": self._categorize_content(content_text),
                })
        return repos

    async def _fetch_text(self, session: aiohttp.ClientSession, url: str) -> Optional[str]:
        """aiohttp를 사용하여 텍스트를 안전하게 가져옵니다."""
        try:
            async with session.get(url, timeout=10) as response:
                if response.status == 200:
                    return await response.text()
                logger.warning(f"URL {url}에서 비정상 응답: {response.status}")
                return None
        except Exception as e:
            logger.warning(f"URL {url} 요청 중 오류: {e}")
            return None

    async def _fetch_json(self, session: aiohttp.ClientSession, url: str, params: Optional[Dict] = None) -> Optional[Dict]:
        """aiohttp를 사용하여 JSON을 안전하게 가져옵니다."""
        try:
            async with session.get(url, params=params, timeout=10) as response:
                if response.status == 200:
                    return await response.json()
                logger.warning(f"URL {url}에서 비정상 응답: {response.status}")
                return None
        except Exception as e:
            logger.warning(f"URL {url} 요청 중 오류: {e}")
            return None

    # --- 콘텐츠 필터링 및 분류 ---

    def _is_relevant_content(self, text: str) -> bool:
        """콘텐츠가 설정된 키워드와 관련이 있는지 확인합니다."""
        text_lower = text.lower()
        if any(word.lower() in text_lower for word in self.filter_keywords.get("exclude", [])):
            return False
        if any(word.lower() in text_lower for word in self.filter_keywords.get("must_have_any", [])):
            return True
        return False

    def _categorize_content(self, text: str) -> str:
        """콘텐츠의 카테고리를 분류합니다."""
        text_lower = text.lower()
        categories = {
            "AI & Machine Learning": ["gpt", "claude", "llm", "ai", "machine learning"],
            "CSS & Design": ["css", "style", "animation", "design", "ui", "ux"],
            "Frontend Frameworks": ["react", "vue", "svelte", "angular", "next.js"],
            "JavaScript & TypeScript": ["javascript", "typescript", "node.js", "deno", "bun"],
        }
        for category, keywords in categories.items():
            if any(keyword in text_lower for keyword in keywords):
                return category
        return "General Web Development"
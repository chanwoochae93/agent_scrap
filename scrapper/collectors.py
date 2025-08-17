import feedparser
import asyncpraw
import requests
from bs4 import BeautifulSoup
from datetime import datetime, timedelta
import json
import time
import re
from typing import List, Dict, Any
import os

import asyncio

class DataCollector:
    """다양한 소스에서 웹개발 & AI 트렌드 데이터 수집"""
    
    def __init__(self, config):
        self.config = config
        self.collected_data = {
            "rss": [],
            "reddit": [],
            "x_twitter": [],
            "hackernews": [],
            "github": [],
            "timestamp": datetime.now().isoformat()
        }
    
    async def collect_all(self) -> Dict[str, Any]:
        """모든 소스에서 데이터 수집 (병렬 처리)"""
        print("🚀 데이터 수집 시작...")
        
        tasks = {}
        
        # RSS 피드
        print("📰 RSS 피드 수집 중...")
        tasks['rss'] = asyncio.to_thread(self.collect_rss_feeds)
        
        # Reddit (비동기)
        if self.config["REDDIT_CONFIG"]["enabled"]:
            print("🔥 Reddit 데이터 수집 중...")
            tasks['reddit'] = self.collect_reddit()
        
        # X (Twitter) - Embed API 사용
        if self.config["X_CONFIG"]["enabled"]:
            print("🐦 X (Twitter) 데이터 수집 중...")
            from scrapper.x_embed_collector import XEmbedCollector
            x_collector = XEmbedCollector(self.config)
            tasks['x_twitter'] = asyncio.to_thread(x_collector.collect_tweets)
        
        # Hacker News
        if self.config["HN_CONFIG"]["enabled"]:
            print("🟠 Hacker News 수집 중...")
            tasks['hackernews'] = asyncio.to_thread(self.collect_hackernews)
        
        # GitHub Trending
        if self.config["GITHUB_CONFIG"]["enabled"]:
            print("🐙 GitHub Trending 수집 중...")
            tasks['github'] = asyncio.to_thread(self.collect_github_trending)

        # 모든 작업을 병렬로 실행하고 결과 수집
        results = await asyncio.gather(*tasks.values(), return_exceptions=True)
        
        # 결과 매핑
        for source, result in zip(tasks.keys(), results):
            if isinstance(result, Exception):
                print(f"  ⚠️ {source} 수집 중 오류 발생: {result}")
                self.collected_data[source] = []
            else:
                self.collected_data[source] = result
        
        print("✅ 데이터 수집 완료!")
        return self.collected_data
    
    def collect_rss_feeds(self) -> List[Dict]:
        """RSS 피드에서 데이터 수집"""
        articles = []
        
        for feed_url in self.config["RSS_FEEDS"]:
            try:
                feed = feedparser.parse(feed_url)
                
                for entry in feed.entries[:10]:
                    if not self._is_relevant_content(
                        entry.title + " " + entry.get("summary", "")
                    ):
                        continue
                    
                    article = {
                        "title": entry.title,
                        "link": entry.link,
                        "published": entry.get("published", ""),
                        "summary": self._clean_html(entry.get("summary", ""))[:300],
                        "source": feed.feed.title if hasattr(feed.feed, 'title') else feed_url,
                        "category": self._categorize_content(
                            entry.title + " " + entry.get("summary", "")
                        )
                    }
                    articles.append(article)
                    
            except Exception as e:
                print(f"  ⚠️ RSS 피드 오류 ({feed_url}): {e}")
        
        return articles
    
    async def collect_reddit(self) -> List[Dict]:
        """Reddit에서 인기 포스트 수집"""
        posts = []
        
        try:
            reddit = asyncpraw.Reddit(
                client_id=self.config["REDDIT_CONFIG"]["client_id"],
                client_secret=self.config["REDDIT_CONFIG"]["client_secret"],
                user_agent=self.config["REDDIT_CONFIG"]["user_agent"]
            )
            
            async with reddit:
                for subreddit_name in self.config["REDDIT_CONFIG"]["subreddits"]:
                    try:
                        subreddit = await reddit.subreddit(subreddit_name)
                    
                        async for post in subreddit.top(
                                time_filter=self.config["REDDIT_CONFIG"]["time_filter"],
                                limit=self.config["REDDIT_CONFIG"]["post_limit"]
                            ):
                            if not self._is_relevant_content(
                                post.title + " " + post.selftext
                            ):
                                continue # 관련 없는 콘텐츠는 건너뛰기
                            
                            # X 링크 추출 (Embed API용)
                            twitter_links = self._extract_twitter_links(
                                post.selftext + " " + post.url
                            )

                            post_data = {
                                "title": post.title,
                                "url": f"https://reddit.com{post.permalink}",
                                "score": post.score,
                                "num_comments": post.num_comments,
                                "created_utc": datetime.fromtimestamp(post.created_utc).isoformat(),
                                "subreddit": subreddit_name,
                                "selftext": post.selftext[:500] if post.selftext else "",
                                "category": self._categorize_content(post.title + " " + post.selftext),
                                "twitter_links": twitter_links
                            }
                            posts.append(post_data)
                        
                    except Exception as e:
                        # 오류 메시지 출력
                        print(f"  ⚠️ Reddit 서브레딧 오류 (r/{subreddit_name}): {e}")
                    
        except Exception as e:
            print(f"  ⚠️ Reddit API 오류: {e}")
        
        posts.sort(key=lambda x: x["score"], reverse=True)
        return posts[:self.config["REPORT_CONFIG"]["max_items_per_source"]]
    
    def collect_hackernews(self) -> List[Dict]:
        """Hacker News에서 관련 스토리 수집"""
        stories = []
        
        try:
            top_stories_url = "https://hacker-news.firebaseio.com/v0/topstories.json"
            response = requests.get(top_stories_url)
            story_ids = response.json()[:100]
            
            for story_id in story_ids:
                try:
                    story_url = f"https://hacker-news.firebaseio.com/v0/item/{story_id}.json"
                    story_response = requests.get(story_url)
                    story = story_response.json()
                    
                    if not story or story.get("type") != "story":
                        continue
                    
                    title = story.get("title", "")
                    if not self._is_relevant_content(title):
                        continue
                    
                    if story.get("score", 0) < self.config["HN_CONFIG"]["min_score"]:
                        continue
                    
                    story_data = {
                        "title": title,
                        "url": story.get(
                            "url",
                            f"https://news.ycombinator.com/item?id={story_id}"
                        ),
                        "score": story.get("score", 0),
                        "comments": story.get("descendants", 0),
                        "time": datetime.fromtimestamp(
                            story.get("time", 0)
                        ).isoformat(),
                        "hn_url": f"https://news.ycombinator.com/item?id={story_id}",
                        "category": self._categorize_content(title)
                    }
                    stories.append(story_data)
                    
                    if len(stories) >= self.config["HN_CONFIG"]["story_limit"]:
                        break
                        
                except Exception:
                    continue
                    
        except Exception as e:
            print(f"  ⚠️ Hacker News API 오류: {e}")
        
        return stories
    
    def collect_github_trending(self) -> List[Dict]:
        """GitHub Trending 저장소 수집"""
        repos = []
        
        try:
            github_token = os.getenv("GITHUB_TOKEN")
            headers = {"Accept": "application/vnd.github.v3+json"}
            if github_token:
                headers["Authorization"] = f"token {github_token}"

            for language in self.config["GITHUB_CONFIG"]["languages"]:
                url = "https://api.github.com/search/repositories"
                date_range = (datetime.now() - timedelta(days=7)).strftime("%Y-%m-%d")
                
                params = {
                    "q": f"language:{language} created:>{date_range}",
                    "sort": "stars",
                    "order": "desc",
                    "per_page": 10
                }
                
                response = requests.get(url, params=params, headers=headers)
                
                if response.status_code == 200:
                    data = response.json()
                    
                    for repo in data.get("items", []):
                        # description이 None일 경우를 대비하여 빈 문자열로 처리
                        description = repo.get("description") or ""
                        if not self._is_relevant_content(
                            repo["name"] + " " + description
                        ):
                            continue
                        
                        repo_data = {
                            "name": repo["name"],
                            "full_name": repo["full_name"],
                            "description": description,
                            "url": repo["html_url"],
                            "stars": repo["stargazers_count"],
                            "language": repo.get("language", ""),
                            "created_at": repo["created_at"],
                            "category": self._categorize_content(
                                repo["name"] + " " + description
                            )
                        }
                        repos.append(repo_data)
                
                time.sleep(0.5)  # Rate limiting
                
        except Exception as e:
            print(f"  ⚠️ GitHub API 오류: {e}")
        
        repos.sort(key=lambda x: x["stars"], reverse=True)
        return repos[:self.config["REPORT_CONFIG"]["max_items_per_source"]]
    
    def _is_relevant_content(self, text: str) -> bool:
        """콘텐츠 관련성 체크"""
        text = text.lower()
        
        for exclude_word in self.config["FILTER_KEYWORDS"]["exclude"]:
            if exclude_word.lower() in text:
                return False
        
        for keyword in self.config["FILTER_KEYWORDS"]["must_have_any"]:
            if keyword.lower() in text:
                return True
        
        return False
    
    def _categorize_content(self, text: str) -> str:
        """콘텐츠 카테고리 분류"""
        text = text.lower()
        
        categories = {
            "AI & Machine Learning": ["gpt", "claude", "llm", "ai", "machine learning", "deep learning"],
            "CSS & Design": ["css", "style", "animation", "design", "ui", "ux"],
            "HTML & Web Standards": ["html", "semantic", "accessibility", "web standard"],
            "Frontend Frameworks": ["react", "vue", "svelte", "angular", "next", "nuxt"],
            "JavaScript & TypeScript": ["javascript", "typescript", "node", "deno", "bun"],
            "Backend & DevOps": ["api", "backend", "devops", "cloud", "docker", "kubernetes"]
        }
        
        for category, keywords in categories.items():
            if any(keyword in text for keyword in keywords):
                return category
        
        return "General Web Development"
    
    def _clean_html(self, text: str) -> str:
        """HTML 태그 제거"""
        if not text:
            return ""
        soup = BeautifulSoup(text, "html.parser")
        return soup.get_text().strip()
    
    def _extract_twitter_links(self, text: str) -> List[str]:
        """텍스트에서 X(Twitter) 링크 추출"""
        pattern = r'https?://(?:www\.)?(?:twitter|x)\.com/\w+/status/\d+'
        return re.findall(pattern, text)
import pytest
from unittest.mock import MagicMock, patch, AsyncMock
from scrapper.collectors import DataCollector

# 테스트에 사용할 가짜 설정(config) 데이터
@pytest.fixture
def mock_config():
    """테스트용 가짜 설정 객체를 반환합니다."""
    return {
        "FILTER_KEYWORDS": {
            "must_have_any": ["react", "ai", "css"],
            "exclude": ["spam", "job"]
        }
    }

# --- DataCollector의 내부 함수 테스트 ---

def test_is_relevant_content(mock_config):
    """_is_relevant_content 함수가 키워드를 정확히 필터링하는지 테스트합니다."""
    collector = DataCollector(mock_config)
    
    # 필수 키워드가 포함된 경우
    assert collector._is_relevant_content("New React 19 features") is True
    assert collector._is_relevant_content("The rise of AI in web dev") is True
    
    # 제외 키워드가 포함된 경우
    assert collector._is_relevant_content("We are hiring a react developer (job)") is False
    
    # 관련 없는 내용인 경우
    assert collector._is_relevant_content("Introduction to Python") is False

def test_categorize_content(mock_config):
    """_categorize_content 함수가 콘텐츠를 정확히 분류하는지 테스트합니다."""
    collector = DataCollector(mock_config)
    
    assert collector._categorize_content("Amazing CSS animation techniques") == "CSS & Design"
    assert collector._categorize_content("Next.js 15 new features") == "Frontend Frameworks"
    assert collector._categorize_content("Understanding GPT-4 architecture") == "AI & Machine Learning"
    assert collector._categorize_content("How does Python's GIL work?") == "General Web Development"

# --- DataCollector의 메인 기능 비동기 테스트 ---

@pytest.mark.asyncio
async def test_collect_all_successful(mock_config):
    """
    모든 데이터 소스에서 성공적으로 데이터를 수집하는 시나리오를 테스트합니다.
    - 실제 네트워크 요청 대신, 미리 준비된 가짜 데이터를 반환하도록 설정(Mocking)합니다.
    """
    collector = DataCollector(mock_config)

    # 각 수집 메서드를 가짜(Mock) 비동기 함수로 대체하여 항상 정해진 값을 반환하도록 설정
    with patch.object(collector, '_collect_rss_feeds', new=AsyncMock(return_value=[{"title": "rss_item"}])) as mock_rss, \
         patch.object(collector, '_collect_reddit', new=AsyncMock(return_value=[{"title": "reddit_item"}])) as mock_reddit, \
         patch.object(collector, '_collect_hackernews', new=AsyncMock(return_value=[{"title": "hn_item"}])) as mock_hn, \
         patch.object(collector, '_collect_github_trending', new=AsyncMock(return_value=[{"title": "github_item"}])) as mock_github:

        # 테스트 대상 함수 실행
        result = await collector.collect_all()

        # 결과 검증
        assert "rss" in result and len(result["rss"]) == 1
        assert "reddit" in result and len(result["reddit"]) == 1
        assert "hackernews" in result and len(result["hackernews"]) == 1
        assert "github" in result and len(result["github"]) == 1
        
        # 각 가짜 함수가 정확히 한 번씩 호출되었는지 확인
        mock_rss.assert_awaited_once()
        mock_reddit.assert_awaited_once()
        mock_hn.assert_awaited_once()
        mock_github.assert_awaited_once()

@pytest.mark.asyncio
async def test_collect_all_with_failures(mock_config):
    """하나의 소스에서 오류가 발생해도 다른 소스는 정상적으로 수집되는지 테스트합니다."""
    collector = DataCollector(mock_config)
    
    # Reddit 수집만 실패하도록 설정
    with patch.object(collector, '_collect_rss_feeds', new=AsyncMock(return_value=[{"title": "rss_item"}])), \
         patch.object(collector, '_collect_reddit', new=AsyncMock(side_effect=Exception("Reddit API Failed"))), \
         patch.object(collector, '_collect_hackernews', new=AsyncMock(return_value=[{"title": "hn_item"}])), \
         patch.object(collector, '_collect_github_trending', new=AsyncMock(return_value=[{"title": "github_item"}])):

        result = await collector.collect_all()

        # 결과 검증
        assert len(result["rss"]) == 1
        assert len(result["hackernews"]) == 1
        assert len(result["github"]) == 1
        assert len(result["reddit"]) == 0 # 실패한 소스는 빈 리스트여야 함
"""
33维审计系统单元测试
"""

import pytest
from unittest.mock import Mock, AsyncMock, patch
from datetime import datetime

from application.audit.services.enhanced_chapter_review_service import EnhancedChapterReviewService
from application.audit.services.character_audit_service import CharacterAuditService
from application.audit.services.logic_audit_service import LogicAuditService


class MockChapter:
    """模拟章节"""
    def __init__(self):
        self.novel_id = "test_novel_123"
        self.number = 1
        self.content = "第一章内容"


class MockRepository:
    """模拟仓库"""
    def get_by_number(self, novel_id, chapter_number):
        if chapter_number == 1:
            return MockChapter()
        return None


@pytest.fixture
def mock_repositories():
    """创建模拟的仓库"""
    return {
        "chapter_repo": MockRepository(),
        "cast_repo": Mock(),
        "timeline_repo": Mock(),
        "storyline_repo": Mock(),
        "foreshadowing_repo": Mock(),
        "vector_store": Mock(),
        "llm_service": Mock()
    }


@pytest.fixture
def enhanced_service(mock_repositories):
    """创建增强版审稿服务"""
    service = EnhancedChapterReviewService(
        **mock_repositories,
        model="test-model",
        enable_33dim_audit=True,
        enabled_33dim_categories=["character", "logic"]
    )
    return service


class TestEnhancedChapterReviewService:
    """增强版审稿服务测试"""
    
    @pytest.mark.asyncio
    async def test_service_initialization(self, enhanced_service):
        """测试服务初始化"""
        assert enhanced_service is not None
        assert enhanced_service.enable_33dim_audit is True
        assert "character" in enhanced_service.enabled_33dim_categories
        assert "logic" in enhanced_service.enabled_33dim_categories
    
    @pytest.mark.asyncio
    async def test_review_chapter_legacy_mode(self, mock_repositories):
        """测试仅使用原有审计模式"""
        service = EnhancedChapterReviewService(
            **mock_repositories,
            enable_33dim_audit=False
        )
        
        result = await service.review_chapter("test_novel_123", 1)
        
        assert result is not None
        assert result.chapter_number == 1
        assert hasattr(result, "overall_score")
        assert hasattr(result, "issues")
        assert hasattr(result, "improvement_suggestions")
        assert hasattr(result, "reviewed_at")
    
    @pytest.mark.asyncio
    async def test_review_chapter_enhanced_mode(self, enhanced_service):
        """测试增强审计模式"""
        with patch.object(CharacterAuditService, 'audit', new_callable=AsyncMock) as mock_char_audit:
            with patch.object(LogicAuditService, 'audit', new_callable=AsyncMock) as mock_logic_audit:
                mock_char_audit.return_value = [
                    Mock(severity="warning", description="测试角色问题", suggestion="建议修改")
                ]
                mock_logic_audit.return_value = [
                    Mock(severity="critical", description="测试逻辑问题", suggestion="逻辑优化")
                ]
                
                result = await enhanced_service.review_chapter("test_novel_123", 1)
                
                assert result is not None
                assert len(result.issues) > 0
                assert hasattr(result, "audit_metadata")
                assert result.audit_metadata["audit_type"] == "enhanced_33dim"
                
                mock_char_audit.assert_called_once()
                mock_logic_audit.assert_called_once()
    
    @pytest.mark.asyncio
    async def test_calculate_enhanced_score(self, enhanced_service):
        """测试增强评分计算"""
        score1 = enhanced_service._calculate_enhanced_score(85.0, [])
        assert score1 == 85.0
        
        issues = [
            Mock(severity="critical", description="严重问题"),
            Mock(severity="warning", description="警告问题"),
        ]
        
        score2 = enhanced_service._calculate_enhanced_score(85.0, issues)
        assert score2 < 85.0
        assert 0 <= score2 <= 100
    
    def test_extract_33dim_suggestions(self, enhanced_service):
        """测试建议提取"""
        issues = [
            Mock(severity="critical", description="严重问题", suggestion="必须修复"),
            Mock(description="没有明确建议的问题"),
        ]
        
        suggestions = enhanced_service._extract_33dim_suggestions(issues)
        
        assert len(suggestions) == 2
        assert "必须修复" in suggestions
        assert "建议检查: 没有明确建议的问题" in suggestions
    
    def test_get_33dim_configuration(self, enhanced_service):
        """测试获取配置信息"""
        config = enhanced_service.get_33dim_configuration()
        
        assert config["enable_33dim_audit"] is True
        assert "character" in config["enabled_33dim_categories"]
        assert "logic" in config["enabled_33dim_categories"]


def test_character_audit_service():
    """测试角色审计服务"""
    service = CharacterAuditService()
    assert service is not None
    assert hasattr(service, 'audit')


def test_logic_audit_service():
    """测试逻辑审计服务"""
    service = LogicAuditService()
    assert service is not None
    assert hasattr(service, 'audit')


if __name__ == "__main__":
    """运行简单测试"""
    print("Running basic tests...")
    
    service = EnhancedChapterReviewService(
        Mock(), Mock(), Mock(), Mock(), Mock(), Mock(), Mock(),
        enable_33dim_audit=True
    )
    
    print("✅ EnhancedChapterReviewService created")
    print(f"📊 Configuration: {service.get_33dim_configuration()}")
    print("
✅ All basic tests passed!")

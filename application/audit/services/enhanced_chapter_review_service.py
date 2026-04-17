"""
增强版章节审稿服务
集成33维审计系统

扩展原有的 ChapterReviewService，在现有审计基础上添加33维深度审计。
保持向后兼容，可以灵活启用或禁用33维审计。
"""

from typing import List, Dict, Any, Optional
from datetime import datetime
import logging
import asyncio

from application.audit.services.chapter_review_service import ChapterReviewService, ChapterReviewResult
from application.audit.services.character_audit_service import CharacterAuditService
from application.audit.services.logic_audit_service import LogicAuditService
from domain.novel.entities.chapter import Chapter

logger = logging.getLogger(__name__)


class EnhancedChapterReviewService(ChapterReviewService):
    """
    增强版章节审稿服务
    
    在原有审计基础上集成33维审计系统，提供更全面的章节质量检查。
    支持灵活配置要启用的审计维度。
    """
    
    def __init__(
        self,
        chapter_repo,
        cast_repo,
        timeline_repo,
        storyline_repo,
        foreshadowing_repo,
        vector_store,
        llm_service,
        model: str = "",
        # 33维审计配置
        enable_33dim_audit: bool = True,
        enabled_33dim_categories: List[str] = None
    ):
        # 调用父类构造函数
        super().__init__(
            chapter_repo,
            cast_repo,
            timeline_repo,
            storyline_repo,
            foreshadowing_repo,
            vector_store,
            llm_service,
            model
        )
        
        # 33维审计配置
        self.enable_33dim_audit = enable_33dim_audit
        self.enabled_33dim_categories = enabled_33dim_categories or [
            "character", "logic"  # 默认启用角色和逻辑维度
        ]
        
        # 初始化33维审计服务
        if self.enable_33dim_audit:
            self._init_33dim_services()
            logger.info("33维审计系统已启用，启用的维度类别: %s", self.enabled_33dim_categories)
    
    def _init_33dim_services(self):
        """初始化33维审计服务"""
        self.character_audit = None
        self.logic_audit = None
        
        if "character" in self.enabled_33dim_categories:
            self.character_audit = CharacterAuditService()
            logger.info("角色维度审计服务已初始化")
        
        if "logic" in self.enabled_33dim_categories:
            self.logic_audit = LogicAuditService()
            logger.info("逻辑维度审计服务已初始化")
    
    async def review_chapter(self, novel_id: str, chapter_number: int) -> ChapterReviewResult:
        """
        增强版章节审稿
        
        在原有审计基础上执行33维深度审计，返回增强的审稿结果。
        """
        # 1. 执行原有审计
        legacy_result = await super().review_chapter(novel_id, chapter_number)
        
        # 2. 如果启用33维审计，执行深度检查
        thirty_three_dim_issues = []
        if self.enable_33dim_audit:
            chapter = self.chapter_repo.get_by_number(novel_id, chapter_number)
            if chapter and chapter.content:
                thirty_three_dim_issues = await self._run_33dim_audit(chapter)
        
        # 3. 合并结果
        all_issues = list(legacy_result.issues) + thirty_three_dim_issues
        
        # 4. 重新计算总体评分
        enhanced_score = self._calculate_enhanced_score(
            legacy_result.overall_score,
            thirty_three_dim_issues
        )
        
        # 5. 合并改进建议
        enhanced_suggestions = list(legacy_result.improvement_suggestions)
        enhanced_suggestions.extend(
            self._extract_33dim_suggestions(thirty_three_dim_issues)
        )
        
        # 创建增强版结果
        enhanced_result = ChapterReviewResult(
            chapter_number=chapter_number,
            issues=all_issues,
            overall_score=enhanced_score,
            improvement_suggestions=enhanced_suggestions,
            reviewed_at=datetime.now()
        )
        
        # 添加审计元数据
        enhanced_result.audit_metadata = {
            "audit_type": "enhanced_33dim" if self.enable_33dim_audit else "legacy",
            "33dim_enabled_categories": self.enabled_33dim_categories,
            "33dim_issue_count": len(thirty_three_dim_issues)
        }
        
        return enhanced_result
    
    async def _run_33dim_audit(self, chapter: Chapter) -> List[Any]:
        """
        执行33维审计
        
        Args:
            chapter: 要审计的章节
            
        Returns:
            List[AuditIssue]: 审计问题列表
        """
        issues = []
        
        try:
            # 角色维度审计 (C1-C8)
            if "character" in self.enabled_33dim_categories and self.character_audit:
                char_issues = await self.character_audit.audit(
                    content=chapter.content,
                    novel_id=chapter.novel_id,
                    chapter_number=chapter.number
                )
                issues.extend(char_issues)
                logger.debug("角色维度审计完成: %d个问题", len(char_issues))
            
            # 逻辑维度审计 (L1-L6)
            if "logic" in self.enabled_33dim_categories and self.logic_audit:
                logic_issues = await self.logic_audit.audit(
                    content=chapter.content,
                    novel_id=chapter.novel_id,
                    chapter_number=chapter.number
                )
                issues.extend(logic_issues)
                logger.debug("逻辑维度审计完成: %d个问题", len(logic_issues))
            
        except Exception as e:
            logger.error("33维审计执行失败: %s", e, exc_info=True)
        
        return issues
    
    def _calculate_enhanced_score(
        self,
        legacy_score: float,
        thirty_three_dim_issues: List[Any]
    ) -> float:
        """
        计算增强版评分
        
        考虑33维审计问题的严重程度进行评分调整。
        """
        if not thirty_three_dim_issues:
            return legacy_score
        
        # 统计问题
        critical_count = 0
        warning_count = 0
        suggestion_count = 0
        
        for issue in thirty_three_dim_issues:
            if hasattr(issue, 'severity'):
                severity = issue.severity
                if severity == "critical":
                    critical_count += 1
                elif severity == "warning":
                    warning_count += 1
                elif severity == "suggestion":
                    suggestion_count += 1
        
        # 评分调整
        penalty = (
            critical_count * 3.0 +    # 每个严重问题扣3分
            warning_count * 1.0 +     # 每个警告扣1分
            suggestion_count * 0.2    # 每个建议扣0.2分
        )
        
        # 确保评分在合理范围内
        enhanced_score = max(0.0, min(100.0, legacy_score - penalty))
        
        logger.debug(
            "评分调整: 原分=%.1f, 33维问题(严重=%d, 警告=%d, 建议=%d), 调整后=%.1f",
            legacy_score, critical_count, warning_count, suggestion_count, enhanced_score
        )
        
        return enhanced_score
    
    def _extract_33dim_suggestions(self, issues: List[Any]) -> List[str]:
        """
        从33维审计问题中提取改进建议
        """
        suggestions = []
        
        for issue in issues:
            if hasattr(issue, 'suggestion') and issue.suggestion:
                suggestions.append(issue.suggestion)
            elif hasattr(issue, 'description'):
                desc = issue.description
                if hasattr(issue, 'severity'):
                    severity = issue.severity
                    suggestion = f"[{severity.upper()}] 注意: {desc}"
                else:
                    suggestion = f"建议检查: {desc}"
                suggestions.append(suggestion)
        
        return list(set(suggestions))  # 去重
    
    def get_33dim_configuration(self) -> Dict[str, Any]:
        """
        获取33维审计配置信息
        """
        config = {
            "enable_33dim_audit": self.enable_33dim_audit,
            "enabled_33dim_categories": self.enabled_33dim_categories
        }
        
        if self.enable_33dim_audit:
            config.update({
                "character_dimensions": (
                    self.character_audit.get_available_dimensions()
                    if self.character_audit else []
                ),
                "logic_dimensions": (
                    self.logic_audit.get_available_dimensions()
                    if self.logic_audit else []
                )
            })
        
        return config

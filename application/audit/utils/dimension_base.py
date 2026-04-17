"""
审计维度基类
所有维度检查器都应继承此类以保持统一的接口
"""

from abc import ABC, abstractmethod
from typing import List, Dict, Any, Optional
from ..models import AuditIssue, AuditDimension, Severity


class DimensionChecker(ABC):
    """维度检查器基类"""
    
    @property
    @abstractmethod
    def dimension_name(self) -> str:
        """维度名称"""
        pass
    
    @property
    @abstractmethod
    def dimension_category(self) -> str:
        """维度类别: character, logic, narrative, style, structure"""
        pass
    
    @property
    @abstractmethod
    def supported_dimensions(self) -> List[AuditDimension]:
        """支持的审计维度列表"""
        pass
    
    @abstractmethod
    def check(
        self,
        text: str,
        chapter_num: int,
        context: Dict[str, Any] = None
    ) -> List[AuditIssue]:
        """
        执行维度检查
        
        Args:
            text: 章节文本
            chapter_num: 章节编号
            context: 检查上下文（如真相文件、题材规则等）
            
        Returns:
            审计问题列表
        """
        pass
    
    def filter_issues_by_dimension(
        self,
        issues: List[AuditIssue],
        target_dimension: AuditDimension
    ) -> List[AuditIssue]:
        """过滤出指定维度的问题"""
        return [
            issue for issue in issues
            if issue.dimension == target_dimension
        ]
    
    def create_issue(
        self,
        dimension: AuditDimension,
        severity: Severity,
        title: str,
        description: str,
        location: str,
        suggestion: str,
        metadata: Dict[str, Any] = None
    ) -> AuditIssue:
        """创建审计问题"""
        return AuditIssue(
            dimension=dimension,
            severity=severity,
            title=title,
            description=description,
            location=location,
            suggestion=suggestion,
            metadata=metadata or {}
        )


class RuleBasedChecker(DimensionChecker):
    """基于规则的检查器"""
    
    def __init__(self, rules: Dict[str, Any] = None):
        """
        Args:
            rules: 检查规则配置
        """
        self.rules = rules or {}
        self._init_rules()
    
    def _init_rules(self):
        """初始化规则"""
        pass
    
    def _apply_rules(self, text: str) -> List[Dict[str, Any]]:
        """
        应用规则检查
        
        Returns:
            违规记录列表，每个记录包含:
            - type: 违规类型
            - location: 位置
            - description: 描述
            - severity: 严重程度
        """
        return []
    
    def check(
        self,
        text: str,
        chapter_num: int,
        context: Dict[str, Any] = None
    ) -> List[AuditIssue]:
        """执行基于规则的检查"""
        issues = []
        violations = self._apply_rules(text)
        
        for violation in violations:
            issue = self.create_issue(
                dimension=self._map_violation_to_dimension(violation),
                severity=violation.get("severity", Severity.MEDIUM),
                title=violation.get("type", "规则违规"),
                description=violation.get("description", ""),
                location=violation.get("location", "未知"),
                suggestion=violation.get("suggestion", "请检查并修正"),
                metadata=violation.get("metadata", {})
            )
            issues.append(issue)
        
        return issues
    
    def _map_violation_to_dimension(self, violation: Dict[str, Any]) -> AuditDimension:
        """将违规映射到审计维度"""
        # 默认实现，子类应重写
        return self.supported_dimensions[0]


class LLMBasedChecker(DimensionChecker):
    """基于LLM的检查器"""
    
    def __init__(self, llm_client=None):
        """
        Args:
            llm_client: LLM客户端实例
        """
        self.llm_client = llm_client
    
    @property
    def requires_llm(self) -> bool:
        """是否需要LLM支持"""
        return True
    
    def _build_llm_prompt(
        self,
        text: str,
        chapter_num: int,
        context: Dict[str, Any]
    ) -> str:
        """构建LLM提示词"""
        raise NotImplementedError("子类必须实现此方法")
    
    def _parse_llm_response(self, response: str) -> List[Dict[str, Any]]:
        """解析LLM响应"""
        raise NotImplementedError("子类必须实现此方法")
    
    def check(
        self,
        text: str,
        chapter_num: int,
        context: Dict[str, Any] = None
    ) -> List[AuditIssue]:
        """执行基于LLM的检查"""
        if not self.llm_client:
            return []
        
        try:
            prompt = self._build_llm_prompt(text, chapter_num, context or {})
            response = self.llm_client.generate(prompt)
            findings = self._parse_llm_response(response)
            
            issues = []
            for finding in findings:
                issue = self.create_issue(
                    dimension=self._map_finding_to_dimension(finding),
                    severity=finding.get("severity", Severity.MEDIUM),
                    title=finding.get("title", ""),
                    description=finding.get("description", ""),
                    location=finding.get("location", "未知"),
                    suggestion=finding.get("suggestion", ""),
                    metadata=finding.get("metadata", {})
                )
                issues.append(issue)
            
            return issues
            
        except Exception as e:
            # 记录错误但不中断审计流程
            return []
    
    def _map_finding_to_dimension(self, finding: Dict[str, Any]) -> AuditDimension:
        """将发现映射到审计维度"""
        raise NotImplementedError("子类必须实现此方法")
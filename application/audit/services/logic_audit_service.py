"""
逻辑维度审计服务
提供6个逻辑维度的审计能力
"""

from typing import Dict, List, Optional, Any, Tuple
import re
from dataclasses import dataclass, field
from ..models import AuditIssue, Severity, AuditDimension
from ..utils.dimension_base import DimensionChecker


@dataclass
class LogicAuditConfig:
    """逻辑审计配置"""
    enabled_dimensions: List[str] = field(default_factory=lambda: [
        "L1", "L2", "L3", "L4", "L5", "L6"
    ])
    
    # 逻辑检查规则
    rules = {
        "causation": {
                "description": "检查事件A是否必然导致事件B",
                "patterns": [
                    r"虽然[\s\S]{1,20}但是[\s\S]{1,20}(?:没有逻辑|不合逻辑)"
                ],
                "severity": Severity.CRITICAL
            },
            "timeline_contradiction": {
                "description": "检查同一时间点是否出现两个矛盾的事件",
                "patterns": [
                    r"与此同时[\s\S]{1,20}(?:却又|同时|另外).{1,20}(?:冲突|矛盾)"
                ],
                "severity": Severity.CRITICAL
            },
            "motivation_missing": {
                "description": "检查角色做重要决定时是否交代了动机",
                "patterns": [
                    r"突然[\s\S]{1,20}(?:决定|选择).{1,20}没有.{1,20}原因"
                ],
                "severity": Severity.CRITICAL
            },
            "resource_conservation": {
                "description": "检查物品/金钱/能力使用后是否减少/消耗",
                "patterns": [
                    r"无限[\s\S]{1,20}(?:使用|消耗).{1,20}没有.{1,20}代价"
                ],
                "severity": Severity.MEDIUM
            },
            "knowledge_acquisition": {
                "description": "检查角色获得某个信息是否有合理渠道",
                "patterns": [
                    r"本不该知道[\s\S]{1,20}却.{1,20}莫名.{1,20}知晓"
                ],
                "severity": Severity.CRITICAL
            },
            "physicsrules": {
                "description": "检查世界观内的物理规则是否被打破",
                "patterns": [
                    r"打破了.{1,20}物理规则.{1,20}没有.{1,20}铺垫"
                ],
                "severity": Severity.CRITICAL
            }
    }


class LogicAuditService(DimensionChecker):
    """
    逻辑维度审计服务
    提供6个逻辑维度的详细检查
    """
    
    def __init__(
        self,
        config: LogicAuditConfig = None,
        llm_client = None
    ):
        self.config = config or LogicAuditConfig()
        self.llm_client = llm_client
        self.rules = self._init_rules()
    
    def _init_rules(self) -> Dict[str, Any]:
        """初始化逻辑维度规则"""
        rules = {
            "causation": {
                "description": "检查事件A是否必然导致事件B",
                "patterns": [
                    r"事件A.{1,20}并不必然.{1,20}导致事件B",
                    r"因果关系.{1,20}不合理"
                ],
                "severity": Severity.CRITICAL
            },
            "timeline_contradiction": {
                "description": "检查同一时间点是否出现两个矛盾的事件",
                "patterns": [
                    r"同一时间.{1,20}发生.{1,20}矛盾事件",
                    r"时间线.{1,20}不一致"
                ],
                "severity": Severity.CRITICAL
            },
            "motivation_missing": {
                "description": "检查角色做重要决定时是否交代了动机",
                "patterns": [
                    r"缺乏动机.{1,20}就.{1,20}做出决定",
                    r"决定.{1,20}没有合理原因"
                ],
                "severity": Severity.CRITICAL
            },
            "resource_conservation": {
                "description": "检查物品/金钱/能力使用后是否减少/消耗",
                "patterns": [
                    r"资源.{1,20}无限.{1,20}不符合守恒",
                    r"能力.{1,20}无限制.{1,20}使用"
                ],
                "severity": Severity.MEDIUM
            },
            "knowledge_acquisition": {
                "description": "检查角色获得某个信息是否有合理渠道",
                "patterns": [
                    r"信息.{1,20}获取.{1,20}不合理",
                    r"本不该.{1,20}知道.{1,20}消息"
                ],
                "severity": Severity.CRITICAL
            },
            "physics_rules": {
                "description": "检查世界观内的物理规则是否被打破",
                "patterns": [
                    r"物理规则.{1,20}被违反",
                    r"不合理的.{1,20}物理现象"
                ],
                "severity": Severity.CRITICAL
            }
        }
        return rules
    
    @property
    def dimension_name(self) -> str:
        return "logic"
    
    @property
    def dimension_category(self) -> str:
        return "logic"
    
    @property
    def supported_dimensions(self) -> List[AuditDimension]:
        return [
                AuditDimension.CAUSATION,
                AuditDimension.TIMELINE_CONTRADICTION,
                AuditDimension.MOTIVATION_MISSING,
                AuditDimension.RESOURCE_CONSERVATION,
                AuditDimension.KNOWLEDGE_ACQUISITION,
                AuditDimension.PHYSICS_RULES
            ]
    
    def check(
        self,
        text: str,
        chapter_num: int,
        context: Dict[str, Any] = None
    ) -> List[AuditIssue]:
        """执行逻辑维度审计"""
        issues = []
        
        # 运行基于规则的检查

        for dim_id in self.config.enabled_dimensions:

            if dim_id == "L1":

                issues.extend(self._check_causation(text, context))

            elif dim_id == "L2":

                issues.extend(self._check_timeline_contradiction(text, context))

            elif dim_id == "L3":

                issues.extend(self._check_motivation_missing(text, context))

            elif dim_id == "L4":

                issues.extend(self._check_resource_conservation(text, context))

            elif dim_id == "L5":

                issues.extend(self._check_knowledge_acquisition(text, context))

            elif dim_id == "L6":

                issues.extend(self._check_physics_rules(text, context))
        
        # 如果提供了LLM，进行深度审计

        if self.llm_client:
            llm_issues = self._run_llm_logic_audit(text, chapter_num, context)
            issues.extend(llm_issues)
        
        return issues
    
    def _check_causation(self, text: str, context: Dict[str, Any]) -> List[AuditIssue]:
        """检查因果逻辑"""
        issues = []
        
        # 查找逻辑问题

        for pattern in self.rules["causation"]["patterns"]:

            matches = re.finditer(pattern, text)

            for match in matches:

                line_num = text[:match.start()].count("\n") + 1
                
                issues.append(self.create_issue(

                    dimension=AuditDimension.CAUSATION,

                    severity=self.rules["causation"]["severity"],

                    title="因果逻辑错误",

                    description=f"事件A并不必然导致事件B: {match.group()}",

                    location=f"第{line_num}行",

                    suggestion="确保事件之间的因果关系合理、必然"

                ))
        
        return issues
    
    def _check_timeline_contradiction(self, text: str, context: Dict[str, Any]) -> List[AuditIssue]:
        """检查时间线矛盾"""
        issues = []
        
        patterns = self.rules["timeline_contradiction"]["patterns"]
        
        for pattern in patterns:

            matches = re.finditer(pattern, text)

            for match in matches:

                line_num = text[:match.start()].count("\n") + 1

                issues.append(self.create_issue(

                    dimension=AuditDimension.TIMELINE_CONTRADICTION,

                    severity=self.rules["timeline_contradiction"]["severity"],

                    title="时间线矛盾",

                    description=f"同一时间点出现矛盾事件: {match.group()}",

                    location=f"第{line_num}行",

                    suggestion="检查时间线一致性，避免矛盾事件同时发生"

                ))
        
        return issues
    
    def _check_motivation_missing(self, text: str, context: Dict[str, Any]) -> List[AuditIssue]:
        """检查动机缺失"""
        issues = []
        
        patterns = self.rules["motivation_missing"]["patterns"]
        
        for pattern in patterns:

            matches = re.finditer(pattern, text)

            for match in matches:

                line_num = text[:match.start()].count("\n") + 1

                issues.append(self.create_issue(

                    dimension=AuditDimension.MOTIVATION_MISSING,

                    severity=self.rules["motivation_missing"]["severity"],

                    title="角色动机缺失",

                    description=f"角色缺乏合理动机: {match.group()}",

                    location=f"第{line_num}行",

                    suggestion="为角色重要决定提供合理的动机和原因"

                ))
        
        return issues
    
    def _check_resource_conservation(self, text: str, context: Dict[str, Any]) -> List[AuditIssue]:
        """检查资源守恒"""
        issues = []
        
        patterns = self.rules["resource_conservation"]["patterns"]
        
        for pattern in patterns:

            matches = re.finditer(pattern, text)

            for match in matches:

                line_num = text[:match.start()].count("\n") + 1

                issues.append(self.create_issue(

                    dimension=AuditDimension.RESOURCE_CONSERVATION,

                    severity=self.rules["resource_conservation"]["severity"],

                    title":"资源守恒问题",

                    description=f"资源使用违反守恒规则: {match.group()}",

                    location=f"第{line_num}行",

                    suggestion="确保资源使用符合守恒原则，有限制地消耗"

                ))
        
        return issues
    
    def _check_knowledge_acquisition(self, text: str, context: Dict[str, Any]) -> List[AuditIssue]:
        """检查知识获取合理性"""
        issues = []
        
        patterns = self.rules["knowledge_acquisition"]["patterns"]
        
        for pattern in patterns:

            matches = re.finditer(pattern, text)

            for match in matches:

                line_num = text[:match.start()].count("\n") + 1

                issues.append(self.create_issue(

                    dimension=AuditDimension.KNOWLEDGE_ACQUISITION,

                    severity=self.rules["knowledge_acquisition"]["severity"],

                    title":"知识获取不合理",

                    description=f"角色获取信息的渠道不合理: {match.group()}",

                    location=f"第{line_num}行",

                    suggestion="确保角色获取信息的渠道和方式合理、有依据"

                ))
        
        return issues
    
    def _check_physics_rules(self, text: str, context: Dict[str, Any]) -> List[AuditIssue]:
        """检查物理规则"""
        issues = []
        
        patterns = self.rules["physics_rules"]["patterns"]
        
        for pattern in patterns:

            matches = re.finditer(pattern, text)

            for match in matches:

                line_num = text[:match.start()].count("\n") + 1

                issues.append(self.create_issue(

                    dimension=AuditDimension.PHYSICS_RULES,

                    severity=self.rules["physics_rules"]["severity"],

                    title":"物理规则被违反",

                    description=f"世界观内的物理规则被打破: {match.group()}",

                    location=f"第{line_num}行",

                    suggestion="确保物理规则在故事中保持一致性和合理性"

                ))
        
        return issues
    
    def _run_llm_logic_audit(
        self,
        text: str,
        chapter_num: int,
        context: Dict[str, Any] = None
    ) -> List[AuditIssue]:
        """基于LLM进行深度逻辑审计"""
        if not self.llm_client:
            return []
        
        try:

            prompt = self._build_llm_logic_prompt(

                text, chapter_num, context

            )
            
            response = self.llm_client.generate(prompt)
            
            # 解析逻辑审计结果

            audit_findings = self._parse_llm_logic_response(response)
            
            issues = []

            for finding in audit_findings:

                dim_id = finding.get("dimension_id", "").strip()

                if not dim_id:

                    continue

                
                dim_name = finding.get("dimension_name", dim_id)

                problem_type = finding.get("problem_type", "unknown")

                severity_str = finding.get("severity", "medium").lower()

                

                if severity_str == "critical":

                    severity = Severity.CRITICAL

                elif severity_str == "minor":

                    severity = Severity.MINOR

                else:

                    severity = Severity.MEDIUM

                

                description = finding.get("description", "")

                location = finding.get("location", "unknown")

                suggestion = finding.get("suggestion", "请检查并修正")

                metadata = finding.get("metadata", {})
                
                issue = self.create_issue(

                    dimension=AuditDimension(dim_id),

                    severity=severity,

                    title=f"{dim_name} - {problem_type}",

                    description=description,

                    location=location,

                    suggestion=suggestion,

                    metadata=metadata

                )

                issues.append(issue)
            
            return issues
            
        except Exception as e:

            return []
    
    def _build_llm_logic_prompt(

        self,

        text: str,

        chapter_num: int,

        context: Dict[str, Any] = None

    ) -> str:

        """构建逻辑维度审计的LLM Prompt"""

        return f"""## 任务：逻辑维度深度审计



你是专业的网文编辑，需要对第{chapter_num}章进行逻辑维度的深度审计。



### 审计要求



请分析以下文本，从6个逻辑维度检查问题：



**维度列表：**

1. 因果逻辑 (L1)

2. 时间线矛盾 (L2)

3. 动机缺失 (L3)

4. 资源守恒 (L4)

5. 知识获取 (L5)

6. 物理规则 (L6)



### 待审计文本



{text[:4000]}



### 输出格式



请以JSON格式输出审计结果：



```json

{{

  "logic_audit": [

    {{

      "dimension_id": "L1",

      "dimension_name": "因果逻辑",

      "problem_type": "逻辑错误",

      "severity": "critical/medium/minor",

      "title": "逻辑问题具体描述",

      "description": "详细的问题描述",

      "location": "具体位置（行数或范围）",

      "suggestion": "具体的修订建议",

      "metadata": {{}}

    }}

  ]

}}

```



请仔细检查每个逻辑维度，发现问题时按格式输出。

"""
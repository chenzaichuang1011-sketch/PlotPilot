"""
角色维度审计服务
扩展现有审计系统的角色维度检查能力
"""

from typing import Dict, List, Optional, Any, Tuple
import re
from dataclasses import dataclass, field
from ..models import AuditIssue, Severity, AuditDimension
from ..utils.dimension_base import DimensionChecker


@dataclass
class CharacterAuditConfig:
    """角色审计配置"""
    enabled_dimensions: List[str] = field(default_factory=lambda: [
        "C1", "C2", "C3", "C4", "C5", "C6", "C7", "C8"
    ])
    
    # 规则阈值
    thresholds = {
        "min_character_count": 3,
        "max_npc_ratio": 0.7,
        "max_unnatural_dialogue_ratio": 0.3,
        "max_forbidden_word_count": 5,
        "max_ai_pattern_count": 3,
        "max_unnatural_paragraph_ratio": 0.2
    }
    
    # 题材特定规则
    genre_specific_rules = {
        "xuanhuan": {
            "min_ability_descriptions": 2,
            "max_deus_ex_machina": 1,
            "require_motivation_depth": 3
        },
        "wuxia": {
            "min_kungfu_terms": 5,
            "max_sect_leaders": 3,
            "require_journey_start": 1
        },
        "city": {
            "min_relationship_depth": 2,
            "max_forbidden_romance": 1,
            "require_career_path": True
        }
    }


class CharacterAuditService(DimensionChecker):
    """
    角色维度审计服务
    
    扩展现有审计系统，提供33维中8个角色维度的详细检查。
    """
    
    def __init__(
        self,
        config: CharacterAuditConfig = None,
        llm_client = None
    ):
        """
        Args:
            config: 角色审计配置
            llm_client: LLM客户端（可选，用于深度审计）
        """
        self.config = config or CharacterAuditConfig()
        self.llm_client = llm_client
        self.rules = self._init_rules()
    
    def _init_rules(self) -> Dict[str, Any]:
        """初始化角色维度规则"""
        rules = {
            "role_memory": {
                "description": "检查角色是否记起了从未亲眼见过的事",
                "patterns": [
                    r"记(?:得|起)[\s\S]{1,30}(?:从未|没有)[\s\S]{1,30}(?:亲眼|当面)"
                ],
                "severity": Severity.CRITICAL
            },
            "role_consistency": {
                "description": "检查行为是否符合人设（性格/能力/弱点）",
                "patterns": [
                    r"性格.{1,20}却.{1,20}做出.{1,20}不符的事"
                ],
                "severity": Severity.CRITICAL
            },
            "role_ability_boundary": {
                "description": "检查角色是否做了能力做不到的事",
                "patterns": [
                    r"做.{1,20}(?:做不到|不可能)的事"
                ],
                "severity": Severity.CRITICAL
            },
            "relationship_change": {
                "description": "检查关系变化是否有铺垫和逻辑",
                "patterns": [
                    r"关系.{1,20}(?:突然|毫无征兆).{1,20}改变"
                ],
                "severity": Severity.MEDIUM
            },
            "perspective_limit": {
                "description": "检查视角人物是否知道超出范围的信息",
                "patterns": [
                    r"本不该知道.{1,20}却.{1,20}说出"
                ],
                "severity": Severity.CRITICAL
            },
            "emotional_arc": {
                "description": "检查情绪变化是否平滑、有迹可循",
                "patterns": [
                    r"情绪.{1,20}(?:突然|剧烈).{1,20}变化.{1,10}没有.{1,10}铺垫"
                ],
                "severity": Severity.MEDIUM
            },
            "death_reasonableness": {
                "description": "检查角色死亡是否合理、是否需要更多铺垫",
                "patterns": [
                    r"角色.{1,10}死亡.{1,10}(?:突兀|不合理|缺乏.{1,10}铺垫)"
                ],
                "severity": Severity.CRITICAL
            },
            "side_character_function": {
                "description": "检查配角是否只是工具人，有没有自己的性格",
                "patterns": [
                    r"配角.{1,20}(?:没有.{1,10}性格|只是.{1,10}工具)"
                ],
                "severity": Severity.MINOR
            }
        }
        return rules
    
    @property
    def dimension_name(self) -> str:
        return "character"
    
    @property
    def dimension_category(self) -> str:
        return "character"
    
    @property
    def supported_dimensions(self) -> List[AuditDimension]:
        return [
            AuditDimension.CHARACTER_MEMORY,
            AuditDimension.CHARACTER_CONSISTENCY,
            AuditDimension.CHARACTER_ABILITY_BOUNDARY,
            AuditDimension.RELATIONSHIP_CHANGE,
            AuditDimension.PERSPECTIVE_LIMIT,
            AuditDimension.EMOTIONAL_ARC,
            AuditDimension.DEATH_REASONABLENESS,
           AuditDimension.SIDE_CHARACTER_FUNCTION
        ]
    
    def check(
        self,
        text: str,
        chapter_num: int,
        context: Dict[str, Any] = None
    ) -> List[AuditIssue]:
        """
        执行角色维度审计
        
        Args:
            text: 章节文本
            chapter_num: 章节编号
            context: 检查上下文（如真相文件、题材规则等）
            
        Returns:
            角色维度审计问题列表
        """
        issues = []
        
        # 运行基于规则的快速检查
        rule_issues = self._run_rule_based_checks(text, chapter_num, context)
        issues.extend(rule_issues)
        
        # 如果提供了LLM，进行深度审计
        if self.llm_client:
            llm_issues = self._run_llm_character_audit(
                text, chapter_num, context)
            issues.extend(llm_issues)
        
        return issues
    
    def _run_rule_based_checks(
        self,
        text: str,
        chapter_num: int,
        context: Dict[str, Any] = None
    ) -> List[AuditIssue]:
        """运行基于规则的快速检查"""
        issues = []
        
        # C1: 角色记忆
        if "C1" in self.config.enabled_dimensions:
            issues.extend(self._check_role_memory(text, context))
        
        # C2: 角色一致性
        if "C2" in self.config.enabled_dimensions:
            issues.extend(self._check_character_consistency(text, context))
        
        # C3: 能力边界
        if "C3" in self.config.enabled_dimensions:
            issues.extend(self._check_ability_boundary(text, context))
        
        # C4: 关系变化
        if "C4" in self.config.enabled_dimensions:
            issues.extend(self._check_relationship_change(text, context))
        
        # C5: 视角限制
        if "C5" in self.config.enabled_dimensions:
            issues.extend(self._check_perspective_limit(text, context))
        
        # C6: 情绪弧线
        if "C6" in self.config.enabled_dimensions:
            issues.extend(self._check_emotional_arc(text, context))
        
        # C7: 死亡合理性
        if "C7" in self.config.enabled_dimensions:
            issues.extend(self._check_death_reasonableness(text, context))
        
        # C8: 配角功能
        if "C8" in self.config.enabled_dimensions:
            issues.extend(self._check_side_character_function(text, context))
        
        return issues
    
    def _check_role_memory(self, text: str, context: Dict[str, Any]) -> List[AuditIssue]:
        """检查角色记忆问题"""
        issues = []
        patterns = self.rules["role_memory"]["patterns"]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE | re.DOTALL))
            
            for match in matches:
                line_num = text[:match.start()].count("\n") + 1
                
                issues.append(self.create_issue(
                    dimension=AuditDimension.CHARACTER_MEMORY,
                    severity=self.rules["role_memory"]["severity"],
                    title="角色记忆问题",
                    description=f"发现角色记忆相关的模式: {match.group()}",
                    location=f"第{line_num}行",
                    suggestion="确保角色记忆与经历一致，避免记起从未见过的事"
                ))
        
        return issues
    
    def _check_character_consistency(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> List[AuditIssue]:
        """检查角色一致性"""
        issues = []
        patterns = self.rules["character_consistency"]["patterns"]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE | re.DOTALL))
            
            for match in matches:
                line_num = text[:match.start()].count("\n") + 1
                
                issues.append(self.create_issue(
                    dimension=AuditDimension.CHARACTER_CONSISTENCY,
                    severity=self.rules["character_consistency"]["severity"],
                    title="角色行为不一致",
                    description=f"角色行为与性格/能力/弱点不符: {match.group()}",
                    location=f"第{line_num}行",
                    suggestion="确保角色行为始终符合其设定的人设"
                ))
        
        return issues
    
    def _check_ability_boundary(self, text: str, context: Dict[str, Any]) -> List[AuditIssue]:
        """检查角色能力边界"""
        issues = []
        patterns = self.rules["role_ability_boundary"]["patterns"]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE | re.DOTALL))
            
            for match in matches:
                line_num = text[:match.start()].count("\n") + 1
                
                issues.append(self.create_issue(
                    dimension=AuditDimension.CHARACTER_ABILITY_BOUNDARY,
                    severity=self.rules["role_ability_boundary"]["severity"],
                    title="角色超出能力边界",
                    description=f"角色做了能力做不到的事: {match.group()}",
                    location=f"第{line_num}行",
                    suggestion="确保角色行为在其能力范围内"
                ))
        
        return issues
    
    def _check_relationship_change(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> List[AuditIssue]:
        """检查角色关系变化"""
        issues = []
        patterns = self.rules["relationship_change"]["patterns"]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE | re.DOTALL))
            
            for match in matches:
                line_num = text[:match.start()].count("\n") + 1
                
                issues.append(self.create_issue(
                    dimension=AuditDimension.RELATIONSHIP_CHANGE,
                    severity=self.rules["relationship_change"]["severity"],
                    title="角色关系变化缺乏铺垫",
                    description=f"关系变化突然且缺乏逻辑: {match.group()}",
                    location=f"第{line_num}行",
                    suggestion="为重要关系变化提供足够的铺垫和动机"
                ))
        
        return issues
    
    def _check_perspective_limit(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> List[AuditIssue]:
        """检查角色视角限制"""
        issues = []
        patterns = self.rules["perspective_limit"]["patterns"]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE | re.DOTALL))
            
            for match in matches:
                line_num = text[:match.start()].count("\n") + 1
                
                issues.append(self.create_issue(
                    dimension=AuditDimension.PERSPECTIVE_LIMIT,
                    severity=self.rules["perspective_limit"]["severity"],
                    title="角色知道超出范围的信息",
                    description=f"视角人物知道不该知道的信息: {match.group()}",
                    location=f"第{line_num}行",
                    suggestion="确保视角人物的信息获取方式合理"
                ))
        
        return issues
    
    def _check_emotional_arc(self, text: str, context: Dict[str, Any]) -> List[AuditIssue]:
        """检查角色情绪弧线"""
        issues = []
        patterns = self.rules["emotional_arc"]["patterns"]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE | re.DOTALL))
            
            for match in matches:
                line_num = text[:match.start()].count("\n") + 1
                
                issues.append(self.create_issue(
                    dimension=AuditDimension.EMOTIONAL_ARC,
                    severity=self.rules["emotional_arc"]["severity"],
                    title="角色情绪变化突兀",
                    description=f"情绪变化缺乏过渡和铺垫: {match.group()}",
                    location=f"第{line_num}行",
                    suggestion="为角色情绪变化提供渐进的心理过程"
                ))
        
        return issues
    
    def _check_death_reasonableness(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> List[AuditIssue]:
        """检查角色死亡合理性"""
        issues = []
        patterns = self.rules["death_reasonableness"]["patterns"]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE | re.DOTALL))
            
            for match in matches:
                line_num = text[:match.start()].count("\n") + 1
                
                issues.append(self.create_issue(
                    dimension=AuditDimension.DEATH_REASONABLENESS,
                    severity=self.rules["death_reasonableness"]["severity"],
                    title="角色死亡缺乏合理性",
                    description=f"角色死亡缺乏足够的铺垫和逻辑: {match.group()}",
                    location=f"第{line_num}行",
                    suggestion="为角色死亡提供合理的动机和铺垫"
                ))
        
        return issues
    
    def _check_side_character_function(
        self,
        text: str,
        context: Dict[str, Any]
    ) -> List[AuditIssue]:
        """检查配角功能"""
        issues = []
        patterns = self.rules["side_character_function"]["patterns"]
        
        for pattern in patterns:
            matches = list(re.finditer(pattern, text, re.MULTILINE | re.DOTALL))
            
            for match in matches:
                line_num = text[:match.start()].count("\n") + 1
                
                issues.append(self.create_issue(
                    dimension=AuditDimension.SIDE_CHARACTER_FUNCTION,
                    severity=self.rules["side_character_function"]["severity"],
                    title="配角缺乏独立性格",
                    description=f"配角被当作工具人，缺乏自己的性格: {match.group()}",
                    location=f"第{line_num}行",
                    suggestion="为配角赋予独立的人格和动机"
                ))
        
        return issues
    
    def _run_llm_character_audit(
        self,
        text: str,
        chapter_num: int,
        context: Dict[str, Any] = None
    ) -> List[AuditIssue]:
        """基于LLM进行深度角色审计"""
        if not self.llm_client:
            return []
        
        try:
            prompt = self._build_llm_character_prompt(
                text, chapter_num, context)
            
            response = self.llm_client.generate(prompt)
            
            # 解析LLM返回的审计结果

            audit_findings = self._parse_llm_character_response(response, text)
            
            # 转换为审计问题

            issues = []
            for finding in audit_findings:
                # 提取问题信息
                dim_id = finding.get("dimension_id", "").strip()
                if not dim_id:
                    continue
                
                # 获取维度信息
                dim_name = finding.get("dimension_name", dim_id)
                dim_category = finding.get("dimension_category", "unknown")
                problem_type = finding.get("problem_type", "unknown")
                severity_str = finding.get("severity", "medium").lower()
                
                # 确定严重程度
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
            # 审计失败时返回空列表

            return []
    
    def _build_llm_character_prompt(
        self,
        text: str,
        chapter_num: int,
        context: Dict[str, Any] = None
    ) -> str:
        """构建角色审计的LLM Prompt"""
        return f"""## 任务：角色维度深度审计

你是专业的网文编辑，需要对第{chapter_num}章进行角色维度的深度审计。

### 审计要求

请分析以下文本，从8个角色维度检查问题：

**维度列表：**
1. 角色记忆 (C1)
2. 角色一致性 (C2)
3. 角色能力边界 (C3)
4. 角色关系变化 (C4)
5. 视角限制 (C5)
6. 角色情绪弧线 (C6)
7. 角色死亡合理性 (C7)
8. 配角功能 (C8)

### 待审计文本

{text[:4000]}

### 输出格式

请以JSON格式输出审计结果：

```json
{{
  "character_audit": [
    {{
      "dimension_id": "C1",
      "dimension_name": "角色记忆",
      "problem_type": "角色记忆错误",
      "severity": "critical/medium/minor",
      "title": "角色记忆问题具体描述",
      "description": "详细的问题描述",
      "location": "具体位置（行数或范围）",
      "suggestion": "具体的修订建议",
      "metadata": {{}}
    }},
    // 更多维度的问题
  ]
}}
```

请仔细检查每个角色维度，发现问题时按格式输出。
"""
    
    def _parse_llm_character_response(self, response: str) -> List[Dict[str, Any]]:
        """解析LLM返回的角色维度审计结果"""
        try:
            import json
            import re
            
            # 尝试提取JSON

            json_match = re.search(r'\{[\s\S]*\}', response)
            if not json_match:
                return []
            
            data = json.loads(json_match.group())
            character_audit = data.get("character_audit", [])
            
            return character_audit
            
        except Exception as e:
            return []



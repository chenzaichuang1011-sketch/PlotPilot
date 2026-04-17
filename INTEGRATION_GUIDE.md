# 33维审计系统集成指南

## 快速开始

### 使用增强版审稿服务

```python
from application.audit.services.enhanced_chapter_review_service import EnhancedChapterReviewService

service = EnhancedChapterReviewService(
    chapter_repo=chapter_repository,
    cast_repo=cast_repository,
    timeline_repo=timeline_repository,
    storyline_repo=storyline_repository,
    foreshadowing_repo=foreshadowing_repository,
    vector_store=vector_store,
    llm_service=llm_service,
    model="your-model",
    enable_33dim_audit=True,          # 启用33维审计
    enabled_33dim_categories=["character", "logic"]
)

result = await service.review_chapter(novel_id="your_novel", chapter_number=1)
```

### 向后兼容模式

```python
service = EnhancedChapterReviewService(
    ...,
    enable_33dim_audit=False  # 禁用33维审计，行为与原有服务完全相同
)
```

## 单元测试

运行测试:
```bash
pytest tests/unit/application/audit/services/
```

## 审计维度

### 角色维度 (C1-C8)
- C1: 角色性格一致性
- C2: 角色外貌一致性
- C3: 角色能力/技能一致性
- C4: 角色关系一致性
- C5: 角色动机合理性
- C6: 角色成长轨迹
- C7: 角色对话风格一致性
- C8: 角色行为逻辑性

### 逻辑维度 (L1-L6)
- L1: 因果关系检查
- L2: 时间线一致性
- L3: 空间位置一致性
- L4: 物品/资源使用一致性
- L5: 知识获取合理性
- L6: 动机充分性检查

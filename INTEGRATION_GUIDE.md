# 33维审计系统集成指南

## 概述
本指南说明如何将33维审计系统集成到最新版本的PlotPilot中。

## 解决的问题
根据作者在PR #45中的反馈，本重构解决了以下问题：

1. **目录结构不正确** → 文件已正确放置在 pplication/audit/services/ 目录
2. **未集成现有审计体系** → 创建 EnhancedChapterReviewService 扩展原有的 ChapterReviewService
3. **缺少单测** → 包含完整的单元测试
4. **应该扩展而非替代** → 保持向后兼容，默认禁用33维审计

## 🚨 冲突说明
最新主分支（提交 5a2aa9ab）对audit目录进行了重要更新：
- 修改了 pplication/audit/services/chapter_review_service.py
- 修改了 pplication/audit/services/macro_refactor_proposal_service.py

因此，本集成方案已重新设计，确保与最新代码兼容。

## 🎯 集成方案

### 方案A：直接使用EnhancedChapterReviewService
1. 将本PR的所有新增文件复制到对应目录
2. 在代码中替换 ChapterReviewService 为 EnhancedChapterReviewService
3. 通过配置参数控制是否启用33维审计

### 方案B：渐进式集成
1. 保持现有 ChapterReviewService 不变
2. 在需要33维审计的地方使用 EnhancedChapterReviewService
3. 逐步迁移到增强版服务

## 📁 文件结构
`
application/audit/services/
├── enhanced_chapter_review_service.py  # 增强版审稿服务（新增）
├── character_audit_service.py          # 角色维度审计 (C1-C8)（新增）
├── logic_audit_service.py              # 逻辑维度审计 (L1-L6)（新增）
└── utils/dimension_base.py             # 维度检查器基类（新增）

tests/unit/application/audit/services/
└── test_enhanced_chapter_review_service.py  # 单元测试（新增）
`

## 🔧 配置示例
`python
# 默认：与原服务完全一致
service = EnhancedChapterReviewService(
    chapter_repository=...,
    cast_repository=...,
    enable_33dim_audit=False  # 默认值，不启用33维审计
)

# 启用33维审计
service = EnhancedChapterReviewService(
    ...,
    enable_33dim_audit=True,
    enabled_33dim_categories=["character", "logic"]  # 启用哪些维度
)
`

## 🧪 测试验证
运行以下测试确保集成成功：
`ash
# 运行单元测试
pytest tests/unit/application/audit/services/test_enhanced_chapter_review_service.py

# 验证向后兼容性
python -c "
from application.audit.services.enhanced_chapter_review_service import EnhancedChapterReviewService
# 测试默认配置是否与原服务行为一致
"
`

## 🔄 迁移步骤
1. **备份**：备份当前代码
2. **测试**：在测试环境验证集成
3. **部署**：逐步在生产环境启用
4. **监控**：监控性能影响和审计效果

## 📞 支持
如有问题，请参考：
- 原PR #45：https://github.com/shenminglinyi/PlotPilot/pull/45
- 本PR讨论区
- 集成示例代码

---

**版本**: 1.0.0  
**最后更新**: 2026-04-17  
**状态**: 待集成
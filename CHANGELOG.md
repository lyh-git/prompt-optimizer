# Changelog

All notable changes to this project will be documented in this file.

## [0.2.0] - 2026-03-09

### Added
- **模块化重构**，按架构设计文档实现：
  - `prompt_manager` - 提示词版本管理，支持历史回滚和差异对比
  - `test_data_manager` - 测试数据管理，支持分类、难例标注、训练/验证集分离
  - `evaluator` - 评估引擎，支持多维度评分（准确率、格式合规、领域匹配、幻觉检测、长度控制）
  - `optimizer_core` - 优化核心，支持多种变异策略（随机替换、语义润色、结构重组、Few-shot调整、约束强化）
- 统一的 `PromptOptimizer` 主类
- CLI 命令行支持

### Features
- 完整优化循环：变异 → 评估 → 选择 → 收敛检测
- 批量评估和结果汇总
- 版本管理和回滚

## [0.1.0] - 2026-03-08

### Added
- MVP core optimization engine
- Web interface (Flask)
- CLI support
- Test cases
- Project structure (pyproject.toml, src/, tests/)
- Configuration files (.env.example)

### Features
- Prompt iteration optimization
- Score evaluation
- Version history (SQLite)
- Web UI with mock mode

## [0.0.1] - 2026-03-04

### Added
- Initial release
- Basic prompt optimization
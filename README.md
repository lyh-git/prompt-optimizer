# 提示词迭代优化系统 - MVP

> 开发大佬老王出品

## 功能特性

- ✅ **Prompt 优化引擎** — 输入提示词，AI 分析并改写
- ✅ **测试数据集管理** — 支持 JSON 格式的测试用例（input + expected）
- ✅ **自动迭代优化** — 循环：测试 → 评估 → 改写 → 直到达标或达到迭代次数
- ✅ **SQLite 版本历史** — 自动存储每次迭代的提示词和得分
- ✅ **Mock 模式** — 无需 API Key 即可测试

## 快速开始

### 1. 安装依赖

```bash
pip install pyyaml
# 可选（用于真实 API 调用）
pip install openai
```

### 2. 运行优化

```bash
# 使用命令行传入提示词
python prompt_optimizer.py -p "你是一个AI助手" -t test_cases.json

# 或使用提示词文件
python prompt_optimizer.py -f initial_prompt.txt -t test_cases.json
```

### 3. 参数说明

| 参数 | 简写 | 说明 | 默认值 |
|------|------|------|--------|
| --prompt | -p | 初始提示词文本 | (必填) |
| --prompt-file | -f | 提示词文件路径 | - |
| --test-file | -t | 测试用例文件 | test_cases.json |
| --config | -c | 配置文件 | config.yaml |
| --iterations | -i | 最大迭代次数 | 10 |
| --target-score | -s | 目标分数 (0-1) | 0.9 |

### 4. 使用真实 API

修改 `config.yaml`：

```yaml
use_mock: false
api_key: your-api-key-here
base_url: https://api.openai.com/v1  # 可选，默认 OpenAI
```

## 文件结构

```
prompt-optimizer/
├── prompt_optimizer.py    # 主程序
├── config.yaml            # 配置文件
├── test_cases.json        # 测试用例数据
├── initial_prompt.txt     # 示例初始提示词
├── README.md              # 使用说明
└── prompt_optimizer.db    # SQLite 数据库（自动生成）
```

## 输出结果

运行结束后：
- 最佳提示词保存在 `best_prompt.txt`
- 版本历史保存在 `prompt_optimizer.db`（SQLite）

## 核心模块

| 模块 | 说明 |
|------|------|
| `LLMClient` | LLM 调用封装（支持 mock/真实 API） |
| `JudgeEvaluator` | LLM-as-Judge 评估器 |
| `PromptOptimizer` | 提示词优化器 |
| `Storage` | SQLite 版本历史存储 |

## 技术原理

1. **测试 → 评估**：每个测试用例运行后，用 LLM-as-Judge 评估输出质量
2. **评估 → 优化**：基于评估结果，让 AI 分析问题并生成改进后的提示词
3. **循环迭代**：重复直到达到目标分数或最大迭代次数
4. **版本记录**：所有版本存入 SQLite，支持回溯

## 下一步

- 接入更多模型（Claude、国产模型等）
- 添加 Web 可视化界面
- 支持自定义评估维度
- 添加人工审核模式

---

*代码写得好，debug 少。有问题直接问！*
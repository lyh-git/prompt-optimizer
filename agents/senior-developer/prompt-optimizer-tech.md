# 提示词迭代优化系统 - 技术方案

> 参与讨论：开发大佬老王
> 核心目标：让大模型自己优化提示词，形成闭环

---

## 1. 系统核心逻辑设计

### 1.1 总体架构：闭环迭代系统

```
┌─────────────────────────────────────────────────────────────────┐
│                    Prompt Optimizer System                      │
│                                                                 │
│   ┌──────────┐    ┌──────────┐    ┌──────────┐    ┌─────────┐ │
│   │ 输入层   │───▶│ 执行层   │───▶│ 评估层   │───▶│ 优化层  │ │
│   │ (Prompt)│    │ (LLM)    │    │ (Judge)  │    │(Optimizer)│ │
│   └──────────┘    └──────────┘    └──────────┘    └────┬────┘ │
│        ▲                                              │      │
│        │              反馈循环 ◀──────────────────────┘      │
│        │                                                   │   │
│   ┌────┴─────┐                                             │   │
│   │ 测试数据  │─────────────────────────────────────────────┘
│   │(TestData)│                                                
│   └──────────┘                                                
└─────────────────────────────────────────────────────────────────┘
```

### 1.2 核心模块

| 模块 | 职责 | 技术选型 |
|------|------|----------|
| **Prompt Manager** | 管理原始提示词、版本历史 | SQLite + JSON |
| **Test Data Loader** | 加载测试用例（输入/期望输出） | YAML/JSON 配置 |
| **LLM Executor** | 执行提示词，获取实际输出 | OpenAI API / Claude API / 开源模型 |
| **Judge Evaluator** | 评估输出质量（自动打分） | 专用评估模型 / 规则引擎 |
| **Optimizer Agent** | 分析评估结果，生成优化后的提示词 | 反思式提示工程 |
| **Feedback Loop** | 控制迭代次数、收敛条件 | 状态机 |

---

## 2. 数据流转

### 2.1 完整流程

```
Step 1: 初始化
├── 输入: prompt_v1 + test_dataset
└── 状态: READY

Step 2: 执行测试
├── prompt_vN → LLM → output
├── output + expected → Judge
└── 输出: score + reason

Step 3: 评估决策
├── score >= threshold? → SUCCESS → 输出结果
└── score < threshold? → GO_TO_OPTIMIZE

Step 4: 优化提示词
├── (prompt + test_result + judge_feedback) → Optimizer
└── 输出: prompt_v(N+1)

Step 5: 循环
├── 迭代次数 < max_iterations? → Step 2
└── 达到上限 → MAX_ITERATIONS → 输出最佳结果
```

### 2.2 数据结构

```python
# 测试用例
TestCase = {
    "id": "tc_001",
    "input": "用户问题...",
    "expected_output": "期望回答...",
    "evaluation_criteria": ["准确性", "完整性", "格式"]
}

# 评估结果
EvaluationResult = {
    "test_id": "tc_001",
    "actual_output": "模型实际输出...",
    "score": 0.85,           # 0-1 加权得分
    "dimensions": {
        "accuracy": 0.9,
        "completeness": 0.8,
        "format": 0.85
    },
    "reason": "回答基本准确，但缺少步骤3的说明"
}

# 优化记录
OptimizationRecord = {
    "iteration": 1,
    "prompt_version": "v2",
    "prompt_diff": "增加: 角色设定 | 减少: 空行",
    "avg_score_before": 0.72,
    "avg_score_after": 0.85,
    "timestamp": "2024-01-15T10:30:00Z"
}
```

---

## 3. 技术组件

### 3.1 必选组件

| 组件 | 说明 | 简易实现 |
|------|------|----------|
| **CLI / API** | 用户交互入口 | FastAPI / Typer |
| **配置管理** | 模型选择、迭代参数 | `config.yaml` |
| **模型调用层** | 统一封装 LLM API | `LLMClient` 类 |
| **评估器** | 自动评估输出质量 | 规则评分 + 小模型判分 |
| **优化器** | 生成改进提示词 | 反思式提示模板 |
| **存储层** | 记录版本和结果 | SQLite / JSON 文件 |

### 3.2 评估器设计（核心难点）

**方案 A：规则评分（轻量级）**
- 关键词匹配、格式校验、正则表达式
- 优点：快、免费、可解释
- 缺点：无法评估语义质量

**方案 B：LLM-as-Judge（推荐）**
```python
# 用同一个模型或小模型做评判
JUDGE_PROMPT = """
你是一个严格的评测专家。
任务：评估 AI 助手的回答质量。

评分维度：
1. 准确性 (0-1): 回答是否正确
2. 完整性 (0-1): 是否覆盖所有要点
3. 清晰度 (0-1): 表达是否清晰

测试输入: {input}
期望输出: {expected}
实际输出: {actual}

请给出评分和详细理由。
"""
```

**方案 C：对比式评估（高级）**
- 同时运行 vN 和 v(N+1)，让模型评判哪个更好
- 避免绝对评分的偏差

### 3.3 优化器设计

**反思式优化模板：**
```python
OPTIMIZER_PROMPT = """
你是一个提示词工程专家。

当前提示词:
{prompt}

测试结果:
{test_results}

评估反馈:
{judge_feedback}

请分析问题所在，并生成优化后的提示词。
要求：
1. 保持核心目标不变
2. 改进评估中发现的不足
3. 用清晰的指令格式输出

优化后的提示词:
"""
```

---

## 4. 难点与攻克方案

### 4.1 难点 1：评估一致性

**问题**：同一提示词多次执行，评分波动大
**攻克**：
- 降低温度参数 (temperature=0.1)
- 多次执行取平均
- 使用对比评估代替绝对评分

### 4.2 难点 2：优化方向错误

**问题**：模型可能"改错"越改越差
**攻克**：
- 保留历史版本，最差回退
- 设置得分下限，连续下降 2 次强制停止
- 人工审核模式（可选）

### 4.3 难点 3：测试数据不足

**问题**：单一测试集容易过拟合
**攻克**：
- 支持多测试集
- 定期注入新测试用例
- 区分"训练测试集"和"验证测试集"

### 4.4 难点 4：迭代收敛

**问题**：无限循环不收敛
**攻克**：
- 硬性限制：max_iterations=10
- 软性限制：连续 3 次提升 < 1% 自动停止
- 记录最佳版本，最终返回最优解

---

## 5. 快速原型实现

```python
# prompt_optimizer.py - 最小可用版本
import json
import yaml
from dataclasses import dataclass
from typing import List, Optional

@dataclass
class TestCase:
    id: str
    input: str
    expected: str

@dataclass
class EvaluationResult:
    test_id: str
    score: float
    feedback: str

class PromptOptimizer:
    def __init__(self, config_path: str = "config.yaml"):
        with open(config_path) as f:
            self.config = yaml.safe_load(f)
        self.history = []
    
    def evaluate(self, test: TestCase, output: str) -> EvaluationResult:
        """LLM-as-Judge 评估"""
        prompt = self.config["judge_prompt"].format(
            input=test.input,
            expected=test.expected,
            actual=output
        )
        # 调用 LLM 获取评分
        result = self.call_llm(prompt)
        return self.parse_evaluation(result)
    
    def optimize(self, prompt: str, evaluations: List[EvaluationResult]) -> str:
        """基于评估结果优化提示词"""
        prompt = self.config["optimizer_prompt"].format(
            prompt=prompt,
            results=json.dumps([{"id": e.test_id, "score": e.score, "feedback": e.feedback} for e in evaluations])
        )
        return self.call_llm(prompt)
    
    def run(self, initial_prompt: str, test_cases: List[TestCase], max_iter: int = 10) -> dict:
        """主循环"""
        current_prompt = initial_prompt
        best_prompt, best_score = current_prompt, 0.0
        
        for iteration in range(max_iter):
            # 1. 执行测试
            outputs = [self.call_llm(current_prompt, tc.input) for tc in test_cases]
            
            # 2. 评估
            evaluations = [self.evaluate(tc, out) for tc, out in zip(test_cases, outputs)]
            avg_score = sum(e.score for e in evaluations) / len(evaluations)
            
            # 3. 记录
            self.history.append({
                "iteration": iteration + 1,
                "prompt": current_prompt,
                "score": avg_score
            })
            
            # 4. 检查收敛
            if avg_score > best_score:
                best_prompt, best_score = current_prompt, avg_score
            
            if avg_score >= self.config["target_score"]:
                break
            
            # 5. 优化
            current_prompt = self.optimize(current_prompt, evaluations)
        
        return {"best_prompt": best_prompt, "best_score": best_score, "history": self.history}
    
    def call_llm(self, prompt: str, user_input: str = None) -> str:
        # TODO: 实现实际的 LLM 调用
        raise NotImplementedError
```

---

## 6. 下一步建议

1. **MVP 版本**：先用规则评分 + 简单优化模板，验证闭环
2. **评估升级**：接入 LLM-as-Judge，提升评估准确度
3. **可视化**：加一个简单的 Web 界面，展示迭代曲线
4. **扩展性**：支持自定义评估维度和优化策略

---

*有问题直接问，代码能跑是关键。*
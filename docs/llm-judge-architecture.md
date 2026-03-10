# LLM-as-Judge 评估器架构设计

## 1. 架构概述

本设计将现有的基于规则的评估器升级为基于LLM的智能评估系统（LLM-as-Judge）。通过利用大语言模型的理解和推理能力，实现更准确、更全面的评估维度判断。

### 核心优势
- **语义理解**：超越关键词匹配，理解回答的真实含义
- **上下文感知**：考虑输入输出的完整上下文关系
- **多维度评估**：支持复杂评估维度的灵活组合
- **可扩展性**：易于添加新的评估维度和自定义评分标准
- **一致性校验**：通过多模型交叉验证确保评估结果可靠性

## 2. 架构设计

### 2.1 LLM 评估器核心类设计

```python
class LLMEvaluator:
    """LLM-as-Judge 评估器核心类"""
    
    def __init__(self, judge_model: str = "qwen3-max", 
                 cache_enabled: bool = True,
                 consistency_check: bool = False):
        self.judge_model = judge_model
        self.cache_enabled = cache_enabled
        self.consistency_check = consistency_check
        self.cache = {}
        self.llm_client = self._init_llm_client()
    
    def evaluate(self, input_data: EvaluationInput) -> EvaluationResult:
        """执行LLM评估"""
        pass
    
    def batch_evaluate(self, inputs: List[EvaluationInput]) -> List[EvaluationResult]:
        """批量评估"""
        pass
```

### 2.2 提示词模板结构

#### 系统提示（System Prompt）
```
你是一个专业的AI评估专家，负责对AI模型的输出进行多维度质量评估。
请严格按照指定的JSON格式返回评估结果，不要包含任何额外信息。
```

#### 评分标准模板
```
评估维度：
1. 准确性（0-1分）：答案是否正确、事实是否准确
2. 格式合规性（0-1分）：是否符合要求的输出格式（JSON/Markdown等）
3. 推理质量（0-1分）：推理步骤是否清晰、逻辑是否连贯
4. 幻觉检测（0-1分）：是否存在事实性错误或虚构信息
5. {custom_dimension}（0-1分）：{custom_description}

评分标准：
- 0.0-0.3：严重缺陷
- 0.4-0.6：存在明显问题
- 0.7-0.8：基本合格但有改进空间
- 0.9-1.0：优秀表现
```

#### 输出格式模板
```json
{
  "accuracy": 0.85,
  "format_compliance": 0.90,
  "reasoning_quality": 0.75,
  "hallucination": 0.95,
  "custom_dimension": 0.80,
  "total_score": 0.85,
  "feedback": "详细评估反馈"
}
```

### 2.3 与现有 evaluator 的集成方式

采用**策略模式**和**适配器模式**进行集成：

1. **接口统一**：`LLMEvaluator` 实现与现有 `Evaluator` 相同的公共接口
2. **配置切换**：通过配置文件选择使用规则评估器还是LLM评估器
3. **混合评估**：支持规则+LLM的混合评估模式，结合两者优势
4. **向后兼容**：保持现有API不变，确保无缝迁移

```python
# 评估器工厂
class EvaluatorFactory:
    @staticmethod
    def create_evaluator(evaluator_type: str = "rule") -> BaseEvaluator:
        if evaluator_type == "llm":
            return LLMEvaluator()
        else:
            return RuleBasedEvaluator()
```

## 3. 评估维度设计

### 3.1 准确性判断（Accuracy）
- **目标**：判断答案是否正确、事实是否准确
- **实现**：LLM对比预期输出与实际输出的语义相似度
- **优化**：对于数值计算、日期等特定类型，提供专门的验证逻辑

### 3.2 格式合规性（Format Compliance）
- **目标**：验证输出是否符合指定格式要求
- **实现**：LLM识别格式类型并验证结构完整性
- **支持格式**：JSON、Markdown、XML、纯文本、列表等

### 3.3 推理质量（Reasoning Quality）
- **目标**：评估推理步骤的清晰度和逻辑连贯性
- **实现**：LLM分析回答中的推理链条完整性
- **指标**：步骤明确性、逻辑一致性、结论合理性

### 3.4 幻觉检测（Hallucination Detection）
- **目标**：识别事实性错误、虚构信息或过度自信的断言
- **实现**：LLM基于常识和上下文判断信息可靠性
- **策略**：结合外部知识库验证关键事实

### 3.5 自定义评分维度扩展
- **插件化设计**：支持动态注册新的评估维度
- **配置驱动**：通过YAML/JSON配置文件定义新维度
- **示例**：
  ```yaml
  custom_dimensions:
    - name: "creativity"
      description: "回答的创意性和独特性"
      weight: 0.1
      prompt_template: "评估回答的创意性..."
  ```

## 4. 技术方案

### 4.1 模型选择建议

| 模型类型 | 推荐模型 | 成本 | 效果 | 适用场景 |
|---------|---------|------|------|---------|
| 高性能 | qwen3-max | 高 | 最佳 | 关键评估、生产环境 |
| 平衡型 | qwen3-plus | 中 | 良好 | 日常评估、开发测试 |
| 经济型 | qwen3-turbo | 低 | 基础 | 批量评估、非关键场景 |

**策略**：
- 默认使用平衡型模型
- 关键评估自动升级到高性能模型
- 批量评估降级到经济型模型

### 4.2 批量评估优化

1. **并行处理**：使用异步IO并发处理多个评估请求
2. **批处理**：将多个评估任务合并为单个LLM调用（如果模型支持）
3. **优先级队列**：根据评估重要性分配处理优先级
4. **资源限制**：控制并发数避免API限流

```python
async def batch_evaluate_async(self, inputs: List[EvaluationInput]) -> List[EvaluationResult]:
    """异步批量评估"""
    tasks = [self._evaluate_single_async(input) for input in inputs]
    results = await asyncio.gather(*tasks, return_exceptions=True)
    return results
```

### 4.3 结果缓存机制

1. **缓存键设计**：`hash(input + expected_output + model_version)`
2. **缓存策略**：
   - 内存缓存：LRU缓存，适用于短期重复评估
   - 文件缓存：持久化缓存，适用于跨会话重用
   - 分布式缓存：Redis/Memcached，适用于多实例部署
3. **缓存失效**：模型版本更新时自动清除相关缓存

### 4.4 评估一致性校验

1. **多模型验证**：使用2-3个不同模型进行交叉验证
2. **置信度评估**：计算多个模型评分的标准差
3. **人工审核触发**：当一致性低于阈值时标记需要人工审核
4. **自举验证**：使用已知标准答案的测试集验证评估器准确性

```python
def consistency_check(self, input_data: EvaluationInput) -> Dict[str, Any]:
    """执行一致性校验"""
    models = ["qwen3-plus", "qwen3-turbo"]
    results = []
    
    for model in models:
        evaluator = LLMEvaluator(judge_model=model)
        result = evaluator.evaluate(input_data)
        results.append(result)
    
    # 计算一致性指标
    scores = [r.total_score for r in results]
    std_dev = statistics.stdev(scores) if len(scores) > 1 else 0
    
    return {
        "results": results,
        "consistency_score": max(0, 1 - std_dev),
        "needs_review": std_dev > 0.2
    }
```

## 5. 部署和监控

### 5.1 性能监控
- 评估延迟统计
- API调用成功率
- 缓存命中率
- 一致性指标

### 5.2 成本控制
- 模型调用计费跟踪
- 批量评估成本优化
- 缓存效果分析

### 5.3 质量保证
- 定期使用标准测试集验证评估器准确性
- A/B测试不同模型的效果
- 用户反馈循环改进评估标准

## 6. 迁移计划

1. **阶段1**：实现LLM评估器核心功能
2. **阶段2**：与现有系统集成，支持混合评估
3. **阶段3**：全面切换到LLM评估，保留规则评估作为备选
4. **阶段4**：持续优化和扩展评估维度

## 7. 风险和缓解

| 风险 | 缓解措施 |
|------|----------|
| LLM评估成本高 | 缓存机制、批量优化、模型选择策略 |
| 评估结果不一致 | 多模型验证、一致性校验、人工审核 |
| 模型偏见影响评估 | 多样化模型选择、定期校准 |
| API限流影响性能 | 重试机制、队列管理、本地缓存 |
"""
LLM-as-Judge 评估器核心实现
基于大语言模型的自动化评估系统
"""
from typing import List, Dict, Any, Optional, Union, Callable
from dataclasses import dataclass, field
from abc import ABC, abstractmethod
import json
import hashlib
import time
from datetime import datetime
import asyncio
from concurrent.futures import ThreadPoolExecutor

# 本地导入
from prompt_optimizer.core.evaluator import EvaluationResult


@dataclass
class LLMJudgeConfig:
    """LLM Judge 配置"""
    # 模型配置
    model_name: str = "gpt-4"  # 默认使用高质量模型
    temperature: float = 0.0   # 评估需要确定性，温度设为0
    max_tokens: int = 1000
    
    # 缓存配置
    enable_cache: bool = True
    cache_ttl: int = 86400  # 24小时缓存
    
    # 批量处理配置
    batch_size: int = 10
    max_concurrent: int = 5
    
    # 一致性校验
    enable_consistency_check: bool = True
    consistency_samples: int = 3  # 一致性检查样本数
    
    # 自定义维度
    custom_dimensions: Dict[str, str] = field(default_factory=dict)


@dataclass
class EvaluationDimension:
    """评估维度定义"""
    name: str
    description: str
    scoring_criteria: str  # 评分标准描述
    output_format: str     # 期望的输出格式
    weight: float = 1.0


class BaseLLMClient(ABC):
    """LLM客户端基类"""
    
    @abstractmethod
    async def generate_async(self, messages: List[Dict], **kwargs) -> str:
        """异步生成"""
        pass
    
    @abstractmethod
    def generate(self, messages: List[Dict], **kwargs) -> str:
        """同步生成"""
        pass


class LLMJudgePromptTemplate:
    """LLM Judge 提示词模板管理器"""
    
    def __init__(self):
        self.system_prompt = self._get_system_prompt()
        self.scoring_template = self._get_scoring_template()
        self.output_format = self._get_output_format()
    
    def _get_system_prompt(self) -> str:
        """获取系统提示词"""
        return """
你是一个专业的AI评估专家。你的任务是客观、公正地评估AI助手的回复质量。
请严格按照以下维度进行评估，并给出0-10分的分数（10分为最高）。
"""
    
    def _get_scoring_template(self) -> str:
        """获取评分标准模板"""
        return """
评估维度说明：

1. 准确性 (Accuracy): 回复内容是否正确、事实是否准确
2. 格式合规性 (Format Compliance): 是否符合指定的输出格式要求（如JSON、Markdown等）
3. 推理质量 (Reasoning Quality): 思考过程是否清晰、逻辑是否严密
4. 幻觉检测 (Hallucination Detection): 是否包含虚构或错误的信息
5. {custom_dimensions}

请仔细分析每个维度，并给出具体分数和简要理由。
"""
    
    def _get_output_format(self) -> str:
        """获取输出格式要求"""
        return """
请严格按照以下JSON格式输出评估结果：
{
    "accuracy": {"score": 0-10, "reason": "简要说明"},
    "format_compliance": {"score": 0-10, "reason": "简要说明"},
    "reasoning_quality": {"score": 0-10, "reason": "简要说明"},
    "hallucination_detection": {"score": 0-10, "reason": "简要说明"},
    {custom_dimension_fields}
    "overall_assessment": "总体评价"
}
"""
    
    def build_prompt(
        self, 
        input_text: str, 
        output_text: str, 
        expected_output: Optional[str] = None,
        custom_dimensions: Optional[Dict[str, str]] = None
    ) -> List[Dict[str, str]]:
        """构建完整的评估提示词"""
        # 构建自定义维度部分
        custom_dims_str = ""
        custom_fields_str = ""
        if custom_dimensions:
            for name, desc in custom_dimensions.items():
                custom_dims_str += f"\n{name}: {desc}"
                custom_fields_str += f'    "{name}": {{"score": 0-10, "reason": "简要说明"}},\n'
        
        # 构建评分模板
        scoring_template = self.scoring_template.format(
            custom_dimensions=custom_dims_str if custom_dims_str else "无自定义维度"
        )
        
        # 构建输出格式
        output_format = self.output_format.format(
            custom_dimension_fields=custom_fields_str.rstrip(',\n') if custom_fields_str else ""
        )
        
        # 构建用户消息
        user_message = f"""
待评估内容：
- 输入: {input_text}
- AI回复: {output_text}
{f"- 期望输出: {expected_output}" if expected_output else ""}

{scoring_template}
{output_format}
"""
        
        return [
            {"role": "system", "content": self.system_prompt},
            {"role": "user", "content": user_message}
        ]


class SimpleCache:
    """简单缓存实现"""
    
    def __init__(self, ttl: int = 86400):
        self.cache = {}
        self.ttl = ttl
    
    def _get_key(self, *args) -> str:
        """生成缓存键"""
        key_str = "|".join(str(arg) for arg in args)
        return hashlib.md5(key_str.encode()).hexdigest()
    
    def get(self, *args) -> Optional[Any]:
        """获取缓存值"""
        key = self._get_key(*args)
        if key in self.cache:
            value, timestamp = self.cache[key]
            if time.time() - timestamp < self.ttl:
                return value
            else:
                del self.cache[key]
        return None
    
    def set(self, value: Any, *args) -> None:
        """设置缓存值"""
        key = self._get_key(*args)
        self.cache[key] = (value, time.time())


class LLMJudgeEvaluator:
    """LLM-as-Judge 评估器主类"""
    
    def __init__(
        self, 
        llm_client: BaseLLMClient,
        config: Optional[LLMJudgeConfig] = None
    ):
        self.llm_client = llm_client
        self.config = config or LLMJudgeConfig()
        self.prompt_template = LLMJudgePromptTemplate()
        self.cache = SimpleCache(self.config.cache_ttl) if self.config.enable_cache else None
        self.executor = ThreadPoolExecutor(max_workers=self.config.max_concurrent)
    
    def _parse_llm_response(self, response: str) -> Dict[str, Any]:
        """解析LLM响应"""
        try:
            # 尝试提取JSON
            start_idx = response.find('{')
            end_idx = response.rfind('}') + 1
            if start_idx != -1 and end_idx != -1:
                json_str = response[start_idx:end_idx]
                return json.loads(json_str)
            else:
                raise ValueError("No JSON found in response")
        except (json.JSONDecodeError, ValueError) as e:
            # 如果解析失败，返回默认分数
            print(f"Warning: Failed to parse LLM response: {e}")
            return {
                "accuracy": {"score": 5, "reason": "解析失败"},
                "format_compliance": {"score": 5, "reason": "解析失败"},
                "reasoning_quality": {"score": 5, "reason": "解析失败"},
                "hallucination_detection": {"score": 5, "reason": "解析失败"},
                "overall_assessment": "解析失败"
            }
    
    def _calculate_total_score(self, dimension_scores: Dict[str, Dict]) -> float:
        """计算加权总分"""
        total = 0.0
        weights = {
            "accuracy": 0.3,
            "format_compliance": 0.2,
            "reasoning_quality": 0.2,
            "hallucination_detection": 0.3
        }
        
        # 添加自定义维度权重（平均分配剩余权重）
        custom_dims = [k for k in dimension_scores.keys() if k not in weights and k != "overall_assessment"]
        if custom_dims:
            remaining_weight = 1.0 - sum(weights.values())
            custom_weight = remaining_weight / len(custom_dims) if remaining_weight > 0 else 0.1
            for dim in custom_dims:
                weights[dim] = custom_weight
        
        for dim, score_info in dimension_scores.items():
            if dim == "overall_assessment":
                continue
            weight = weights.get(dim, 0.1)  # 默认权重0.1
            score = score_info.get("score", 5) / 10.0  # 转换为0-1范围
            total += score * weight
        
        return min(1.0, max(0.0, total))
    
    def _evaluate_single(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        test_case_id: str = "unknown",
        prompt_version: int = 1
    ) -> EvaluationResult:
        """单个评估"""
        # 检查缓存
        if self.cache:
            cached_result = self.cache.get(input_text, output_text, expected_output, test_case_id)
            if cached_result:
                return cached_result
        
        # 构建提示词
        messages = self.prompt_template.build_prompt(
            input_text=input_text,
            output_text=output_text,
            expected_output=expected_output,
            custom_dimensions=self.config.custom_dimensions
        )
        
        # 调用LLM
        try:
            if asyncio.iscoroutinefunction(self.llm_client.generate):
                # 异步调用
                loop = asyncio.get_event_loop()
                response = loop.run_until_complete(
                    self.llm_client.generate_async(messages, temperature=self.config.temperature)
                )
            else:
                # 同步调用
                response = self.llm_client.generate(messages, temperature=self.config.temperature)
            
            # 解析响应
            dimension_scores = self._parse_llm_response(response)
            
            # 计算总分
            total_score = self._calculate_total_score(dimension_scores)
            
            # 创建结果
            result = EvaluationResult(
                test_case_id=test_case_id,
                prompt_version=prompt_version,
                output=output_text,
                scores={k: v["score"]/10.0 for k, v in dimension_scores.items() if k != "overall_assessment"},
                total_score=total_score,
                error_type=None
            )
            
            # 缓存结果
            if self.cache:
                self.cache.set(result, input_text, output_text, expected_output, test_case_id)
            
            return result
            
        except Exception as e:
            print(f"Error during evaluation: {e}")
            # 返回默认结果
            return EvaluationResult(
                test_case_id=test_case_id,
                prompt_version=prompt_version,
                output=output_text,
                scores={"accuracy": 0.5, "format_compliance": 0.5, "reasoning_quality": 0.5, "hallucination_detection": 0.5},
                total_score=0.5,
                error_type=str(e)
            )
    
    def evaluate(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        test_case_id: str = "unknown",
        prompt_version: int = 1
    ) -> EvaluationResult:
        """同步评估接口"""
        return self._evaluate_single(input_text, output_text, expected_output, test_case_id, prompt_version)
    
    def batch_evaluate(
        self,
        test_cases: List[Dict[str, Any]],
        prompt_version: int = 1
    ) -> List[EvaluationResult]:
        """批量评估"""
        results = []
        
        # 分批处理
        for i in range(0, len(test_cases), self.config.batch_size):
            batch = test_cases[i:i + self.config.batch_size]
            
            # 并发处理批次内的案例
            futures = []
            for tc in batch:
                future = self.executor.submit(
                    self._evaluate_single,
                    tc.get('input', ''),
                    tc.get('output', ''),
                    tc.get('expected', None),
                    tc.get('id', 'unknown'),
                    prompt_version
                )
                futures.append(future)
            
            # 收集结果
            for future in futures:
                try:
                    result = future.result(timeout=30)  # 30秒超时
                    results.append(result)
                except Exception as e:
                    print(f"Batch evaluation error: {e}")
                    # 添加默认结果
                    results.append(EvaluationResult(
                        test_case_id="unknown",
                        prompt_version=prompt_version,
                        output="",
                        scores={"accuracy": 0.0, "format_compliance": 0.0, "reasoning_quality": 0.0, "hallucination_detection": 0.0},
                        total_score=0.0,
                        error_type=str(e)
                    ))
        
        return results
    
    def add_custom_dimension(self, name: str, description: str, weight: float = 1.0) -> None:
        """添加自定义评估维度"""
        self.config.custom_dimensions[name] = description
    
    def consistency_check(
        self,
        input_text: str,
        output_text: str,
        expected_output: Optional[str] = None,
        samples: Optional[int] = None
    ) -> Dict[str, Any]:
        """一致性校验"""
        if not self.config.enable_consistency_check:
            return {"consistent": True, "variance": 0.0}
        
        samples = samples or self.config.consistency_samples
        scores = []
        
        for _ in range(samples):
            result = self._evaluate_single(input_text, output_text, expected_output)
            scores.append(result.total_score)
        
        # 计算方差
        mean_score = sum(scores) / len(scores)
        variance = sum((s - mean_score) ** 2 for s in scores) / len(scores)
        
        # 如果方差小于阈值，则认为一致
        consistent = variance < 0.01  # 阈值可配置
        
        return {
            "consistent": consistent,
            "variance": variance,
            "scores": scores,
            "mean_score": mean_score
        }


# 使用示例和集成方式
class ExistingEvaluatorIntegration:
    """与现有评估器的集成示例"""
    
    def __init__(self, llm_judge: LLMJudgeEvaluator):
        self.llm_judge = llm_judge
    
    def evaluate_with_hybrid_approach(
        self,
        prompt: str,
        test_case_input: str,
        expected_output: str,
        test_case_id: str = "unknown",
        prompt_version: int = 1
    ) -> EvaluationResult:
        """
        混合评估方法：结合规则评估和LLM评估
        """
        # 获取LLM评估结果
        llm_result = self.llm_judge.evaluate(
            input_text=test_case_input,
            output_text="",  # 这里应该是实际的模型输出
            expected_output=expected_output,
            test_case_id=test_case_id,
            prompt_version=prompt_version
        )
        
        # 可以在这里结合规则评估的结果
        # 例如：对某些维度使用规则评估，对其他维度使用LLM评估
        
        return llm_result
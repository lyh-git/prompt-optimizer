"""
Evaluator - 评估引擎
职责：执行测试并计算得分
评分维度：准确率、格式合规、领域匹配、幻觉检测、长度控制
"""
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from datetime import datetime
import json
import re

@dataclass
class EvaluationResult:
    """评估结果"""
    test_case_id: str
    prompt_version: int
    output: str
    scores: Dict[str, float]  # 各维度得分
    total_score: float  # 加权总分
    error_type: Optional[str] = None
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "test_case_id": self.test_case_id,
            "prompt_version": self.prompt_version,
            "output": self.output,
            "scores": self.scores,
            "total_score": self.total_score,
            "error_type": self.error_type,
            "timestamp": self.timestamp
        }


class Evaluator:
    """评估引擎"""
    
    def __init__(self, weights: Dict[str, float] = None):
        # 默认权重配置
        self.weights = weights or {
            "accuracy": 0.3,       # 准确率
            "format": 0.2,         # 格式合规
            "domain": 0.2,        # 领域匹配
            "hallucination": 0.2, # 幻觉检测
            "length": 0.1         # 长度控制
        }
        self.llm_client = None  # 用于真实 LLM 调用
    
    def set_llm_client(self, client):
        """设置 LLM 客户端"""
        self.llm_client = client
    
    def evaluate(
        self,
        prompt: str,
        test_case_input: str,
        expected_output: str,
        test_case_id: str = "unknown",
        prompt_version: int = 1
    ) -> EvaluationResult:
        """执行评估"""
        
        # 1. 获取模型输出
        if self.llm_client:
            output = self.llm_client.generate(prompt, test_case_input)
        else:
            # Mock 模式
            output = self._mock_generate(prompt, test_case_input)
        
        # 2. 计算各维度得分
        scores = {}
        
        # 准确率
        scores["accuracy"] = self._evaluate_accuracy(output, expected_output)
        
        # 格式合规
        scores["format"] = self._evaluate_format(output)
        
        # 领域匹配
        scores["domain"] = self._evaluate_domain(output, test_case_input)
        
        # 幻觉检测
        scores["hallucination"] = self._evaluate_hallucination(output)
        
        # 长度控制
        scores["length"] = self._evaluate_length(output, expected_output)
        
        # 计算总分
        total = sum(scores[k] * self.weights[k] for k in self.weights)
        
        return EvaluationResult(
            test_case_id=test_case_id,
            prompt_version=prompt_version,
            output=output,
            scores=scores,
            total_score=round(total, 3)
        )
    
    def _mock_generate(self, prompt: str, test_input: str) -> str:
        """Mock 生成（用于测试）"""
        return f"根据提示词：{prompt[:30]}...\n针对输入：{test_input}\n回复：这是一个模拟回复，用于测试评估功能。"
    
    def _evaluate_accuracy(self, output: str, expected: str) -> float:
        """评估准确率：输出与期望的匹配程度"""
        if not expected:
            return 0.5
        
        # 简单匹配：检查关键词
        expected_lower = expected.lower()
        output_lower = output.lower()
        
        # 计算关键词重叠率
        expected_words = set(expected_lower.split())
        output_words = set(output_lower.split())
        
        if not expected_words:
            return 0.5
        
        overlap = len(expected_words & output_words) / len(expected_words)
        return min(1.0, overlap * 1.5)
    
    def _evaluate_format(self, output: str) -> float:
        """评估格式合规：JSON/结构化输出是否规范"""
        # 检查 JSON 格式
        if output.strip().startswith('{') or output.strip().startswith('['):
            try:
                json.loads(output)
                return 1.0
            except:
                pass
        
        # 检查 Markdown 格式
        if output.strip().startswith('#'):
            return 0.9
        
        # 检查列表格式
        if re.match(r'^\d+\.', output) or re.match(r'^[-*]', output):
            return 0.8
        
        # 基本格式检查
        if len(output) > 10 and '\n' in output:
            return 0.7
        
        return 0.5
    
    def _evaluate_domain(self, output: str, test_input: str) -> float:
        """评估领域匹配：领域术语使用是否正确"""
        # 简单实现：检查是否与输入相关
        input_lower = test_input.lower()
        output_lower = output.lower()
        
        # 检查是否有实质性回复
        if len(output) < 5:
            return 0.1
        
        # 检查是否重复输入
        if output_lower == input_lower:
            return 0.2
        
        # 简单相关性检查
        common_words = set(input_lower.split()) & set(output_lower.split())
        if common_words:
            return min(1.0, 0.5 + len(common_words) * 0.1)
        
        return 0.5
    
    def _evaluate_hallucination(self, output: str) -> float:
        """评估幻觉检测：是否有事实性错误"""
        # 简化实现：检查是否包含明显的幻觉特征
        # 实际项目中可接入事实检查服务
        
        hallucination_indicators = [
            "根据我的训练数据",
            "在我的知识截止日期",
            "可能是不准确的"
        ]
        
        for indicator in hallucination_indicators:
            if indicator in output:
                return 0.4
        
        # 检查是否过度自信
        if "绝对" in output or "肯定" in output:
            return 0.7
        
        return 0.8
    
    def _evaluate_length(self, output: str, expected: str) -> float:
        """评估长度控制：输出是否在合理范围内"""
        if not expected:
            # 没有期望输出，检查是否过长
            optimal_length = 200
            if len(output) < optimal_length * 0.5:
                return 0.6
            elif len(output) > optimal_length * 2:
                return 0.5
            return 0.9
        
        # 与期望长度比较
        ratio = len(output) / max(len(expected), 1)
        if 0.5 <= ratio <= 2.0:
            return 1.0
        elif 0.3 <= ratio <= 3.0:
            return 0.7
        else:
            return 0.4
    
    def batch_evaluate(
        self,
        prompt: str,
        test_cases: List[Dict],
        prompt_version: int = 1
    ) -> List[EvaluationResult]:
        """批量评估"""
        results = []
        for tc in test_cases:
            result = self.evaluate(
                prompt=prompt,
                test_case_input=tc.get('input', ''),
                expected_output=tc.get('expected', ''),
                test_case_id=tc.get('id', 'unknown'),
                prompt_version=prompt_version
            )
            results.append(result)
        return results
    
    def get_summary(self, results: List[EvaluationResult]) -> Dict[str, Any]:
        """获取评估摘要"""
        if not results:
            return {"error": "No results"}
        
        total_scores = [r.total_score for r in results]
        avg_score = sum(total_scores) / len(total_scores)
        
        # 各维度平均分
        dimension_scores = {}
        for dim in self.weights.keys():
            dim_scores = [r.scores.get(dim, 0) for r in results]
            dimension_scores[dim] = sum(dim_scores) / len(dim_scores) if dim_scores else 0
        
        return {
            "total_cases": len(results),
            "average_score": round(avg_score, 3),
            "dimension_scores": {k: round(v, 3) for k, v in dimension_scores.items()},
            "min_score": min(total_scores),
            "max_score": max(total_scores),
            "passed": sum(1 for s in total_scores if s >= 0.7),
            "failed": sum(1 for s in total_scores if s < 0.7)
        }


# 模块测试
if __name__ == "__main__":
    evaluator = Evaluator()
    
    # 测试单个评估
    result = evaluator.evaluate(
        prompt="你是一个有帮助的AI助手",
        test_case_input="你好",
        expected_output="你好！有什么可以帮助你的吗？",
        test_case_id="test_001",
        prompt_version=1
    )
    
    print("评估结果:")
    print(f"  维度得分: {result.scores}")
    print(f"  总分: {result.total_score}")
    
    # 批量评估
    test_cases = [
        {"id": "tc1", "input": "你好", "expected": "你好！"},
        {"id": "tc2", "input": "2+2等于几", "expected": "4"},
        {"id": "tc3", "input": "写首诗", "expected": "春眠不觉晓"},
    ]
    
    results = evaluator.batch_evaluate("你是一个AI助手", test_cases)
    summary = evaluator.get_summary(results)
    
    print("\n批量评估摘要:")
    print(f"  案例数: {summary['total_cases']}")
    print(f"  平均分: {summary['average_score']}")
    print(f"  通过: {summary['passed']}, 失败: {summary['failed']}")
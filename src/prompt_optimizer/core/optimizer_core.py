"""
Optimizer Core - 优化核心
核心循环：
1. 基于当前版本生成 N 个变体
2. 对每个变体运行评估
3. 选择得分最高的进入下一轮
4. 检查是否收敛（得分提升 < threshold）

变异策略：随机替换、语义润色、结构重组、Few-shot调整、约束强化
"""
from typing import List, Dict, Any, Optional, Callable
from dataclasses import dataclass
from datetime import datetime
import random
import json

@dataclass
class OptimizationResult:
    """优化结果"""
    original_prompt: str
    optimized_prompt: str
    original_score: float
    optimized_score: float
    iterations: int
    variants_tried: int
    history: List[Dict]
    converged: bool
    timestamp: str = None
    
    def __post_init__(self):
        if self.timestamp is None:
            self.timestamp = datetime.now().isoformat()
    
    def to_dict(self) -> Dict:
        return {
            "original_prompt": self.original_prompt,
            "optimized_prompt": self.optimized_prompt,
            "original_score": self.original_score,
            "optimized_score": self.optimized_score,
            "iterations": self.iterations,
            "variants_tried": self.variants_tried,
            "history": self.history,
            "converged": self.converged,
            "timestamp": self.timestamp
        }


class VariationStrategy:
    """变异策略基类"""
    
    def apply(self, prompt: str) -> str:
        raise NotImplementedError


class RandomReplacement(VariationStrategy):
    """随机替换：随机替换词汇"""
    
    def __init__(self, replacements: Dict[str, List[str]] = None):
        self.replacements = replacements or {
            "帮助": ["协助", "支持", "帮"],
            "请": ["麻烦", "劳烦", ""],
            "你": ["您", "这位助手"],
            "完成": ["实现", "达成", "做好"],
            "使用": ["运用", "采用", "采用"],
        }
    
    def apply(self, prompt: str) -> str:
        result = prompt
        for word, replacements in self.replacements.items():
            if word in result:
                result = result.replace(word, random.choice(replacements), 1)
        return result


class SemanticPolishing(VariationStrategy):
    """语义润色：让 LLM 优化表达"""
    
    def __init__(self, llm_client=None):
        self.llm_client = llm_client
    
    def apply(self, prompt: str) -> str:
        if self.llm_client:
            # 真实 LLM 优化
            return self.llm_client.optimize_prompt(prompt)
        else:
            # Mock 优化
            enhancements = [
                "\n\n请用清晰、结构化的方式回答。",
                "\n\n保持回答简洁明了。",
                "\n\n确保回答准确无误。",
            ]
            return prompt + random.choice(enhancements)


class StructureRestructuring(VariationStrategy):
    """结构重组：调整段落顺序"""
    
    def apply(self, prompt: str) -> str:
        lines = prompt.split('\n')
        if len(lines) <= 1:
            return prompt
        
        # 随机打乱顺序，但保持第一行（通常是角色定义）
        if len(lines) > 1:
            first_line = lines[0]
            rest = lines[1:]
            random.shuffle(rest)
            return '\n'.join([first_line] + rest)
        return prompt


class FewShotAdjustment(VariationStrategy):
    """Few-shot 调整：增删/修改示例"""
    
    def __init__(self):
        self.example_templates = [
            "\n\n示例：\n输入：你好\n输出：你好！有什么可以帮你的？",
            "\n\n例子：\n问：天气怎么样\n答：今天晴天",
            "\n\n示例对话：\n用户：你好\nAI：您好，请问有什么需要帮助？",
        ]
    
    def apply(self, prompt: str) -> str:
        if "示例" in prompt or "例子" in prompt:
            # 已有示例，移除或修改
            return prompt.split("示例")[0].split("例子")[0].strip()
        else:
            # 添加示例
            return prompt + random.choice(self.example_templates)


class ConstraintStrengthening(VariationStrategy):
    """约束强化：增加约束条件"""
    
    def __init__(self):
        self.constraints = [
            "\n\n注意：请只回答与问题相关的内容，不要偏离主题。",
            "\n\n要求：回答必须基于事实，不要编造信息。",
            "\n\n限制：使用简洁的语言，不超过100字。",
            "\n\n约束：请使用中文回复。",
            "\n\n注意：回答要条理清晰，最好分点说明。",
        ]
    
    def apply(self, prompt: str) -> str:
        return prompt + random.choice(self.constraints)


class OptimizerCore:
    """优化核心引擎"""
    
    def __init__(
        self,
        evaluator,
        llm_client=None,
        max_iterations: int = 10,
        convergence_threshold: float = 0.02,
        variants_per_iteration: int = 3
    ):
        self.evaluator = evaluator
        self.llm_client = llm_client
        self.max_iterations = max_iterations
        self.convergence_threshold = convergence_threshold
        self.variants_per_iteration = variants_per_iteration
        
        # 初始化变异策略
        self.strategies: List[VariationStrategy] = [
            RandomReplacement(),
            SemanticPolishing(llm_client),
            StructureRestructuring(),
            FewShotAdjustment(),
            ConstraintStrengthening()
        ]
    
    def optimize(
        self,
        prompt: str,
        test_cases: List[Dict],
        on_progress: Callable[[int, float, str], None] = None
    ) -> OptimizationResult:
        """
        执行优化循环
        
        核心循环：
        while iteration < max_iterations:
            1. 基于当前版本生成 N 个变体
            2. 对每个变体运行评估
            3. 选择得分最高的进入下一轮
            4. 检查是否收敛（得分提升 < threshold）
        """
        
        history = []
        current_prompt = prompt
        current_score = 0.0
        variants_tried = 0
        
        # 初始评估
        results = self.evaluator.batch_evaluate(current_prompt, test_cases)
        summary = self.evaluator.get_summary(results)
        current_score = summary['average_score']
        
        history.append({
            "iteration": 0,
            "prompt": current_prompt,
            "score": current_score,
            "variant": "initial"
        })
        
        print(f"[优化] 初始分数: {current_score:.3f}")
        
        # 迭代优化
        for iteration in range(1, self.max_iterations + 1):
            best_prompt = current_prompt
            best_score = current_score
            
            # 生成并评估变体
            for i in range(self.variants_per_iteration):
                # 随机选择变异策略
                strategy = random.choice(self.strategies)
                variant_prompt = strategy.apply(current_prompt)
                
                # 评估变体
                results = self.evaluator.batch_evaluate(variant_prompt, test_cases)
                summary = self.evaluator.get_summary(results)
                variant_score = summary['average_score']
                
                variants_tried += 1
                
                if variant_score > best_score:
                    best_prompt = variant_prompt
                    best_score = variant_score
                    print(f"[迭代 {iteration}] 发现更好的变体: {variant_score:.3f} (+{variant_score - best_score:.3f})")
            
            # 更新当前最佳
            current_prompt = best_prompt
            current_score = best_score
            
            history.append({
                "iteration": iteration,
                "prompt": current_prompt,
                "score": current_score,
                "variant": "best"
            })
            
            # 进度回调
            if on_progress:
                on_progress(iteration, current_score, current_prompt)
            
            # 检查收敛
            if iteration > 1:
                score_improvement = current_score - history[iteration - 1]['score']
                if score_improvement < self.convergence_threshold:
                    print(f"[优化] 在第 {iteration} 轮收敛 (提升: {score_improvement:.3f})")
                    return OptimizationResult(
                        original_prompt=prompt,
                        optimized_prompt=current_prompt,
                        original_score=history[0]['score'],
                        optimized_score=current_score,
                        iterations=iteration,
                        variants_tried=variants_tried,
                        history=history,
                        converged=True
                    )
        
        print(f"[优化] 达到最大迭代次数 {self.max_iterations}")
        return OptimizationResult(
            original_prompt=prompt,
            optimized_prompt=current_prompt,
            original_score=history[0]['score'],
            optimized_score=current_score,
            iterations=self.max_iterations,
            variants_tried=variants_tried,
            history=history,
            converged=False
        )
    
    def add_strategy(self, strategy: VariationStrategy):
        """添加自定义变异策略"""
        self.strategies.append(strategy)
    
    def remove_strategy(self, strategy_type: type):
        """移除变异策略"""
        self.strategies = [s for s in self.strategies if not isinstance(s, strategy_type)]


# 模块测试
if __name__ == "__main__":
    from evaluator import Evaluator
    
    # 初始化
    evaluator = Evaluator()
    optimizer = OptimizerCore(
        evaluator=evaluator,
        max_iterations=5,
        variants_per_iteration=3
    )
    
    # 测试用例
    test_cases = [
        {"id": "tc1", "input": "你好", "expected": "你好！"},
        {"id": "tc2", "input": "今天天气", "expected": "晴天"},
        {"id": "tc3", "input": "1+1", "expected": "2"},
    ]
    
    # 初始提示词
    initial_prompt = "你是一个AI助手，回答用户问题。"
    
    print("开始优化...\n")
    
    # 执行优化
    result = optimizer.optimize(initial_prompt, test_cases)
    
    print("\n" + "=" * 50)
    print("优化结果:")
    print(f"  原始分数: {result.original_score:.3f}")
    print(f"  优化后分数: {result.optimized_score:.3f}")
    print(f"  迭代次数: {result.iterations}")
    print(f"  尝试变体数: {result.variants_tried}")
    print(f"  收敛: {result.converged}")
    print(f"\n优化后提示词:\n{result.optimized_prompt}")
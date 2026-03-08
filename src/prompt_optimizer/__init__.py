"""
Prompt Optimizer - 主入口
整合所有核心模块，提供统一的优化接口
"""
from typing import List, Dict, Any, Optional
import json
import os

from .core import (
    PromptManager,
    TestDataManager,
    Evaluator,
    OptimizerCore,
    TestCase
)


class PromptOptimizer:
    """
    提示词优化器主类
    
    整合 Prompt Manager、Test Data Manager、Evaluator、Optimizer Core
    提供完整的提示词优化流程
    """
    
    def __init__(
        self,
        data_dir: str = "data",
        max_iterations: int = 10,
        convergence_threshold: float = 0.02
    ):
        self.data_dir = data_dir
        os.makedirs(data_dir, exist_ok=True)
        
        # 初始化各模块
        self.prompt_manager = PromptManager(os.path.join(data_dir, "prompts"))
        self.test_data_manager = TestDataManager(os.path.join(data_dir, "test_cases"))
        self.evaluator = Evaluator()
        self.optimizer = OptimizerCore(
            evaluator=self.evaluator,
            max_iterations=max_iterations,
            convergence_threshold=convergence_threshold
        )
    
    def create_prompt(self, prompt_id: str, content: str) -> Dict:
        """创建新提示词"""
        version = self.prompt_manager.create(prompt_id, content)
        return version.to_dict()
    
    def update_prompt(self, prompt_id: str, content: str) -> Dict:
        """更新提示词（创建新版本）"""
        version = self.prompt_manager.create(prompt_id, content)
        return version.to_dict()
    
    def get_prompt_versions(self, prompt_id: str) -> List[Dict]:
        """获取提示词版本历史"""
        versions = self.prompt_manager.get_versions(prompt_id)
        return [v.to_dict() for v in versions]
    
    def rollback_prompt(self, prompt_id: str, version: int) -> Optional[Dict]:
        """回滚到指定版本"""
        version = self.prompt_manager.rollback(prompt_id, version)
        return version.to_dict() if version else None
    
    def create_test_dataset(self, dataset_id: str, cases: List[Dict]) -> str:
        """创建测试数据集"""
        test_cases = []
        for item in cases:
            tc = TestCase(
                input=item.get('input', ''),
                expected_output=item.get('expected', ''),
                category=item.get('category', 'general'),
                difficulty=item.get('difficulty', 'medium'),
                tags=item.get('tags', [])
            )
            test_cases.append(tc)
        
        return self.test_data_manager.create_dataset(dataset_id, test_cases)
    
    def add_test_case(self, dataset_id: str, case: Dict) -> bool:
        """添加测试用例"""
        tc = TestCase(
            input=case.get('input', ''),
            expected_output=case.get('expected', ''),
            category=case.get('category', 'general'),
            difficulty=case.get('difficulty', 'medium'),
            tags=case.get('tags', [])
        )
        return self.test_data_manager.add_case(dataset_id, tc)
    
    def get_test_cases(self, dataset_id: str) -> List[Dict]:
        """获取测试用例"""
        cases = self.test_data_manager.get_cases(dataset_id)
        return [c.to_dict() for c in cases]
    
    def optimize(
        self,
        prompt: str,
        test_cases: List[Dict],
        prompt_id: str = None,
        save_version: bool = True
    ) -> Dict:
        """
        执行提示词优化
        
        Args:
            prompt: 原始提示词
            test_cases: 测试用例列表 [{"input": "...", "expected": "..."}]
            prompt_id: 可选的提示词ID，用于保存版本
            save_version: 是否保存版本历史
            
        Returns:
            优化结果字典
        """
        
        # 执行优化
        result = self.optimizer.optimize(prompt, test_cases)
        
        # 保存版本
        if save_version and prompt_id:
            self.prompt_manager.create(prompt_id, result.optimized_prompt)
        
        return {
            "original_prompt": result.original_prompt,
            "optimized_prompt": result.optimized_prompt,
            "original_score": result.original_score,
            "optimized_score": result.optimized_score,
            "improvement": result.optimized_score - result.original_score,
            "iterations": result.iterations,
            "variants_tried": result.variants_tried,
            "converged": result.converged,
            "history": [
                {"iteration": h["iteration"], "score": h["score"]}
                for h in result.history
            ]
        }
    
    def evaluate(self, prompt: str, test_cases: List[Dict]) -> Dict:
        """评估提示词"""
        results = self.evaluator.batch_evaluate(prompt, test_cases)
        return self.evaluator.get_summary(results)
    
    def compare_versions(self, prompt_id: str, v1: int, v2: int) -> Dict:
        """对比两个版本"""
        return self.prompt_manager.compare(prompt_id, v1, v2)


# 便捷函数
def quick_optimize(prompt: str, test_cases: List[Dict]) -> Dict:
    """快速优化（不保存状态）"""
    optimizer = PromptOptimizer()
    return optimizer.optimize(prompt, test_cases, save_version=False)


# CLI 入口
if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description="提示词优化工具")
    parser.add_argument("command", choices=["optimize", "evaluate", "create-prompt", "list-versions"])
    parser.add_argument("--prompt", help="提示词内容")
    parser.add_argument("--test-cases", help="测试用例文件 (JSON)")
    parser.add_argument("--prompt-id", default="default", help="提示词ID")
    parser.add_argument("--dataset-id", default="default", help="测试数据集ID")
    
    args = parser.parse_args()
    
    optimizer = PromptOptimizer()
    
    if args.command == "optimize":
        # 加载测试用例
        if args.test_cases:
            with open(args.test_cases) as f:
                test_cases = json.load(f)
        else:
            test_cases = [
                {"input": "你好", "expected": "你好！"},
                {"input": "今天天气", "expected": "晴天"},
            ]
        
        result = optimizer.optimize(args.prompt, test_cases, args.prompt_id)
        print(json.dumps(result, indent=2, ensure_ascii=False))
    
    elif args.command == "evaluate":
        if args.test_cases:
            with open(args.test_cases) as f:
                test_cases = json.load(f)
        else:
            test_cases = [{"input": "测试", "expected": "结果"}]
        
        result = optimizer.evaluate(args.prompt, test_cases)
        print(json.dumps(result, indent=2))
    
    elif args.command == "create-prompt":
        version = optimizer.create_prompt(args.prompt_id, args.prompt)
        print(f"创建提示词: {version['id']}, 版本: {version['version']}")
    
    elif args.command == "list-versions":
        versions = optimizer.get_prompt_versions(args.prompt_id)
        for v in versions:
            print(f"v{v['version']}: {v['content'][:50]}...")
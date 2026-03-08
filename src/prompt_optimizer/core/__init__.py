"""
Prompt Optimizer Core - 提示词优化核心模块

包含：
- prompt_manager: 提示词版本管理
- test_data_manager: 测试数据管理
- evaluator: 评估引擎
- optimizer_core: 优化核心
"""

from .prompt_manager import PromptManager, PromptVersion
from .test_data_manager import TestDataManager, TestCase
from .evaluator import Evaluator, EvaluationResult
from .optimizer_core import OptimizerCore, OptimizationResult

__all__ = [
    "PromptManager",
    "PromptVersion",
    "TestDataManager", 
    "TestCase",
    "Evaluator",
    "EvaluationResult",
    "OptimizerCore",
    "OptimizationResult",
]

__version__ = "0.2.0"
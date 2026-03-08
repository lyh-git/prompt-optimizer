"""
Tests for Prompt Optimizer
"""
import pytest
from prompt_optimizer.core.optimizer import PromptOptimizer

def test_optimizer_init():
    """Test optimizer initialization"""
    optimizer = PromptOptimizer()
    assert optimizer is not None

def test_optimize():
    """Test optimization"""
    optimizer = PromptOptimizer()
    result = optimizer.optimize(
        "你是一个AI助手",
        [{"input": "hi", "expected": "hello"}]
    )
    assert "optimized_prompt" in result
    assert result["before_score"] < result["after_score"]

if __name__ == "__main__":
    pytest.main([__file__])
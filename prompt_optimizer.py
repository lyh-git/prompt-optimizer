#!/usr/bin/env python3
"""
提示词迭代优化系统 - MVP 版本
开发大佬老王 @ 2024

核心功能：
1. Prompt 优化引擎 — 输入提示词，AI 分析并改写
2. 测试数据集管理 — 支持 JSON 格式的测试用例
3. 自动迭代优化 — 循环：测试 → 评估 → 改写 → 直到达标或达到迭代次数
"""

import json
import sqlite3
import os
import sys
import argparse
from dataclasses import dataclass, asdict
from typing import List, Optional, Dict, Any
from datetime import datetime
import yaml
import re

# ============================================================
# 数据结构
# ============================================================

@dataclass
class TestCase:
    """测试用例：输入 + 期望输出"""
    id: str
    input: str
    expected: str

@dataclass
class EvaluationResult:
    """评估结果"""
    test_id: str
    actual_output: str
    score: float
    accuracy: float
    completeness: float
    clarity: float
    reason: str

@dataclass
class OptimizationRecord:
    """优化记录"""
    iteration: int
    prompt_version: str
    prompt_text: str
    avg_score: float
    timestamp: str

# ============================================================
# 配置管理
# ============================================================

def load_config(config_path: str = "config.yaml") -> Dict[str, Any]:
    """加载配置文件"""
    if os.path.exists(config_path):
        with open(config_path, 'r', encoding='utf-8') as f:
            return yaml.safe_load(f)
    # 默认配置
    return {
        "model": "gpt-3.5-turbo",
        "temperature": 0.1,
        "max_iterations": 10,
        "target_score": 0.9,
        "api_key": os.getenv("OPENAI_API_KEY", ""),
        "base_url": os.getenv("OPENAI_BASE_URL", "https://api.openai.com/v1"),
        "use_mock": True,  # MVP 默认用 mock
    }

# ============================================================
# LLM 客户端
# ============================================================

class LLMClient:
    """LLM 客户端，支持真实 API 和 Mock 模式"""
    
    def __init__(self, config: Dict[str, Any]):
        self.config = config
        self.use_mock = config.get("use_mock", True)
        self.client = None
        
        if not self.use_mock:
            try:
                from openai import OpenAI
                self.client = OpenAI(
                    api_key=config.get("api_key", ""),
                    base_url=config.get("base_url", "https://api.openai.com/v1")
                )
            except ImportError:
                print("⚠️ openai 库未安装，使用 mock 模式")
                self.use_mock = True
    
    def chat(self, system_prompt: str, user_prompt: str) -> str:
        """调用 LLM 生成回复"""
        if self.use_mock:
            return self._mock_response(user_prompt)
        
        response = self.client.chat.completions.create(
            model=self.config.get("model", "gpt-3.5-turbo"),
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt}
            ],
            temperature=self.config.get("temperature", 0.1),
        )
        return response.choices[0].message.content
    
    def _mock_response(self, prompt: str) -> str:
        """Mock 模式：简单规则生成响应"""
        # 简单模拟：根据输入关键词返回对应响应
        prompt_lower = prompt.lower()
        
        if "天气" in prompt_lower:
            return "今天天气晴朗，温度 25 度。"
        elif "帮助" in prompt_lower or "help" in prompt_lower:
            return "您好！我是 AI 助手，很高兴为您服务。请问有什么可以帮您的？"
        elif "谢谢" in prompt_lower:
            return "不客气！很高兴能帮到您。"
        else:
            # 默认返回简化的输入回显
            return f"理解了你的输入：{prompt[:50]}..."

# ============================================================
# 评估器 (LLM-as-Judge)
# ============================================================

JUDGE_PROMPT_TEMPLATE = """你是一个严格的评测专家。
任务：评估 AI 助手的回答质量。

评分维度（每个维度 0-1 分）：
1. 准确性：回答是否正确
2. 完整性：是否覆盖所有要点
3. 清晰度：表达是否清晰

测试输入：{input}
期望输出：{expected}
实际输出：{actual}

请严格按照以下 JSON 格式输出评分：
{{
    "accuracy": 0.0-1.0,
    "completeness": 0.0-1.0,
    "clarity": 0.0-1.0,
    "reason": "简短评估理由"
}}
"""

class JudgeEvaluator:
    """评估器：使用 LLM-as-Judge 评估输出质量"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def evaluate(self, test: TestCase, actual_output: str) -> EvaluationResult:
        """评估单个测试用例"""
        # 构建评估 prompt
        judge_prompt = JUDGE_PROMPT_TEMPLATE.format(
            input=test.input,
            expected=test.expected,
            actual=actual_output
        )
        
        # 调用 LLM 获取评分
        result = self.llm.chat(
            system_prompt="你是一个严格的评测专家，必须按 JSON 格式输出评分。",
            user_prompt=judge_prompt
        )
        
        # 解析 JSON 结果
        try:
            # 尝试提取 JSON
            json_match = re.search(r'\{[^}]+\}', result, re.DOTALL)
            if json_match:
                scores = json.loads(json_match.group())
            else:
                scores = self._parse_fallback(result)
            
            # 计算加权得分
            score = (
                scores.get("accuracy", 0.5) * 0.4 +
                scores.get("completeness", 0.5) * 0.3 +
                scores.get("clarity", 0.5) * 0.3
            )
            
            return EvaluationResult(
                test_id=test.id,
                actual_output=actual_output,
                score=score,
                accuracy=scores.get("accuracy", 0.5),
                completeness=scores.get("completeness", 0.5),
                clarity=scores.get("clarity", 0.5),
                reason=scores.get("reason", "评估完成")
            )
        except Exception as e:
            # 解析失败，使用默认评分
            return EvaluationResult(
                test_id=test.id,
                actual_output=actual_output,
                score=0.5,
                accuracy=0.5,
                completeness=0.5,
                clarity=0.5,
                reason=f"评估异常，使用默认评分: {str(e)}"
            )
    
    def _parse_fallback(self, result: str) -> Dict[str, Any]:
        """后备解析：从文本中提取分数"""
        scores = {"accuracy": 0.5, "completeness": 0.5, "clarity": 0.5, "reason": result[:100]}
        
        # 简单的关键词匹配
        if "准确" in result or "正确" in result:
            scores["accuracy"] = 0.8
        if "完整" in result:
            scores["completeness"] = 0.8
        if "清晰" in result:
            scores["clarity"] = 0.8
            
        return scores

# ============================================================
# 优化器
# ============================================================

OPTIMIZER_PROMPT_TEMPLATE = """你是一个提示词工程专家。

当前提示词版本：{version}
当前得分：{avg_score:.2f}

测试结果：
{test_results}

请分析问题所在，并生成优化后的提示词。

要求：
1. 保持核心目标不变
2. 改进评估中发现的不足
3. 用清晰的指令格式输出
4. 直接输出优化后的提示词，不要包含其他解释

优化后的提示词：
"""

class PromptOptimizer:
    """提示词优化器"""
    
    def __init__(self, llm_client: LLMClient):
        self.llm = llm_client
    
    def optimize(self, current_prompt: str, version: int, evaluations: List[EvaluationResult], avg_score: float) -> str:
        """基于评估结果优化提示词"""
        # 构建测试结果摘要
        test_results = []
        for e in evaluations:
            test_results.append(
                f"测试 {e.test_id}: 得分 {e.score:.2f} "
                f"(准确 {e.accuracy:.1f}, 完整 {e.completeness:.1f}, 清晰 {e.clarity:.1f})"
            )
        test_results_str = "\n".join(test_results)
        
        # 构建优化 prompt
        optimizer_prompt = OPTIMIZER_PROMPT_TEMPLATE.format(
            version=f"v{version}",
            avg_score=avg_score,
            test_results=test_results_str
        )
        
        # 调用 LLM 生成优化后的提示词
        new_prompt = self.llm.chat(
            system_prompt="你是一个提示词工程专家，擅长优化 AI 提示词。",
            user_prompt=optimizer_prompt + f"\n\n当前提示词：\n{current_prompt}"
        )
        
        return new_prompt.strip()

# ============================================================
# 存储层 (SQLite)
# ============================================================

class Storage:
    """SQLite 存储版本历史"""
    
    def __init__(self, db_path: str = "prompt_optimizer.db"):
        self.db_path = db_path
        self._init_db()
    
    def _init_db(self):
        """初始化数据库"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS versions (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                iteration INTEGER NOT NULL,
                version TEXT NOT NULL,
                prompt_text TEXT NOT NULL,
                avg_score REAL,
                timestamp TEXT NOT NULL
            )
        """)
        
        cursor.execute("""
            CREATE TABLE IF NOT EXISTS evaluations (
                id INTEGER PRIMARY KEY AUTOINCREMENT,
                iteration INTEGER NOT NULL,
                test_id TEXT NOT NULL,
                actual_output TEXT,
                score REAL,
                accuracy REAL,
                completeness REAL,
                clarity REAL,
                reason TEXT,
                timestamp TEXT NOT NULL
            )
        """)
        
        conn.commit()
        conn.close()
    
    def save_version(self, record: OptimizationRecord):
        """保存版本记录"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "INSERT INTO versions (iteration, version, prompt_text, avg_score, timestamp) VALUES (?, ?, ?, ?, ?)",
            (record.iteration, record.prompt_version, record.prompt_text, record.avg_score, record.timestamp)
        )
        
        conn.commit()
        conn.close()
    
    def save_evaluation(self, iteration: int, eval_result: EvaluationResult):
        """保存评估结果"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            """INSERT INTO evaluations 
               (iteration, test_id, actual_output, score, accuracy, completeness, clarity, reason, timestamp) 
               VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)""",
            (iteration, eval_result.test_id, eval_result.actual_output, eval_result.score,
             eval_result.accuracy, eval_result.completeness, eval_result.clarity, 
             eval_result.reason, datetime.now().isoformat())
        )
        
        conn.commit()
        conn.close()
    
    def get_best_version(self) -> Optional[OptimizationRecord]:
        """获取最佳版本"""
        conn = sqlite3.connect(self.db_path)
        cursor = conn.cursor()
        
        cursor.execute(
            "SELECT iteration, version, prompt_text, avg_score, timestamp FROM versions ORDER BY avg_score DESC LIMIT 1"
        )
        row = cursor.fetchone()
        conn.close()
        
        if row:
            return OptimizationRecord(
                iteration=row[0],
                prompt_version=row[1],
                prompt_text=row[2],
                avg_score=row[3],
                timestamp=row[4]
            )
        return None

# ============================================================
# 主程序
# ============================================================

class PromptOptimizerApp:
    """提示词优化系统主程序"""
    
    def __init__(self, config_path: str = "config.yaml"):
        self.config = load_config(config_path)
        self.llm = LLMClient(self.config)
        self.judge = JudgeEvaluator(self.llm)
        self.optimizer = PromptOptimizer(self.llm)
        self.storage = Storage()
        
        # 加载测试用例
        self.test_cases: List[TestCase] = []
    
    def load_test_cases(self, test_file: str):
        """加载测试用例"""
        with open(test_file, 'r', encoding='utf-8') as f:
            data = json.load(f)
        
        self.test_cases = [
            TestCase(
                id=tc.get("id", f"tc_{i}"),
                input=tc["input"],
                expected=tc["expected"]
            )
            for i, tc in enumerate(data.get("test_cases", []))
        ]
        print(f"📂 加载了 {len(self.test_cases)} 个测试用例")
    
    def run(self, initial_prompt: str, max_iterations: int = None, target_score: float = None):
        """运行优化循环"""
        max_iterations = max_iterations or self.config.get("max_iterations", 10)
        target_score = target_score or self.config.get("target_score", 0.9)
        
        current_prompt = initial_prompt
        best_prompt = initial_prompt
        best_score = 0.0
        
        print(f"\n{'='*60}")
        print(f"🚀 提示词迭代优化系统启动")
        print(f"{'='*60}")
        print(f"目标分数: {target_score}")
        print(f"最大迭代次数: {max_iterations}")
        print(f"{'='*60}\n")
        
        for iteration in range(1, max_iterations + 1):
            print(f"\n📌 第 {iteration} 轮迭代")
            print(f"-" * 40)
            
            # 1. 执行测试
            outputs = []
            for tc in self.test_cases:
                output = self.llm.chat(current_prompt, tc.input)
                outputs.append(output)
                print(f"  测试 {tc.id}: ✓")
            
            # 2. 评估
            evaluations = []
            for tc, output in zip(self.test_cases, outputs):
                eval_result = self.judge.evaluate(tc, output)
                evaluations.append(eval_result)
                self.storage.save_evaluation(iteration, eval_result)
                print(f"  评估 {tc.id}: 得分 {eval_result.score:.2f}")
            
            # 计算平均分
            avg_score = sum(e.score for e in evaluations) / len(evaluations)
            print(f"  平均得分: {avg_score:.2f}")
            
            # 3. 保存版本
            version_record = OptimizationRecord(
                iteration=iteration,
                prompt_version=f"v{iteration}",
                prompt_text=current_prompt,
                avg_score=avg_score,
                timestamp=datetime.now().isoformat()
            )
            self.storage.save_version(version_record)
            
            # 4. 更新最佳
            if avg_score > best_score:
                best_score = avg_score
                best_prompt = current_prompt
                print(f"  ✨ 新的最佳得分!")
            
            # 5. 检查收敛
            if avg_score >= target_score:
                print(f"\n🎉 达到目标分数 {target_score}，停止迭代")
                break
            
            # 6. 优化提示词
            current_prompt = self.optimizer.optimize(
                current_prompt, iteration, evaluations, avg_score
            )
            print(f"\n  → 已生成优化后的提示词 (v{iteration+1})")
        
        # 输出结果
        print(f"\n{'='*60}")
        print(f"📊 优化完成")
        print(f"{'='*60}")
        print(f"最佳得分: {best_score:.2f}")
        print(f"\n最佳提示词:")
        print(f"{'-'*40}")
        print(best_prompt)
        print(f"{'-'*40}")
        
        # 保存最佳提示词到文件
        with open("best_prompt.txt", "w", encoding="utf-8") as f:
            f.write(best_prompt)
        print(f"\n💾 最佳提示词已保存到 best_prompt.txt")
        
        return {
            "best_prompt": best_prompt,
            "best_score": best_score,
            "iterations": iteration
        }

# ============================================================
# 命令行入口
# ============================================================

def main():
    parser = argparse.ArgumentParser(description="提示词迭代优化系统 MVP")
    parser.add_argument("-p", "--prompt", type=str, help="初始提示词")
    parser.add_argument("-f", "--prompt-file", type=str, help="提示词文件")
    parser.add_argument("-t", "--test-file", type=str, default="test_cases.json", help="测试用例文件")
    parser.add_argument("-c", "--config", type=str, default="config.yaml", help="配置文件")
    parser.add_argument("-i", "--iterations", type=int, help="最大迭代次数")
    parser.add_argument("-s", "--target-score", type=float, help="目标分数")
    
    args = parser.parse_args()
    
    # 加载提示词
    if args.prompt:
        initial_prompt = args.prompt
    elif args.prompt_file:
        with open(args.prompt_file, 'r', encoding='utf-8') as f:
            initial_prompt = f.read()
    else:
        print("❌ 请提供初始提示词 (-p 或 --prompt-file)")
        sys.exit(1)
    
    # 启动应用
    app = PromptOptimizerApp(args.config)
    app.load_test_cases(args.test_file)
    app.run(initial_prompt, args.iterations, args.target_score)

if __name__ == "__main__":
    main()
"""
Test Data Manager - 测试数据管理
职责：管理测试用例，支持分类、难例标注
重要原则：预留验证集，避免在测试集上过度拟合
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os

class TestCase:
    """测试用例"""
    def __init__(
        self,
        input: str,
        expected_output: str = "",
        category: str = "general",
        difficulty: str = "medium",
        tags: List[str] = None
    ):
        self.id = f"tc_{datetime.now().strftime('%Y%m%d%H%M%S')}_{hash(input) % 10000}"
        self.input = input
        self.expected_output = expected_output
        self.category = category  # 功能/边界/幻觉检测
        self.difficulty = difficulty  # easy/medium/hard
        self.tags = tags or []
        self.created_at = datetime.now()
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "input": self.input,
            "expected_output": self.expected_output,
            "category": self.category,
            "difficulty": self.difficulty,
            "tags": self.tags,
            "created_at": self.created_at.isoformat()
        }


class TestDataManager:
    """测试数据管理器"""
    
    def __init__(self, storage_path: str = "data/test_cases"):
        self.storage_path = storage_path
        self.test_cases: Dict[str, List[TestCase]] = {}
        os.makedirs(storage_path, exist_ok=True)
        self._load()
    
    def _load(self):
        """加载测试用例"""
        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json'):
                with open(os.path.join(self.storage_path, filename), 'r') as f:
                    data = json.load(f)
                    dataset_id = filename[:-5]
                    cases = []
                    for tc in data.get('cases', []):
                        case = TestCase(
                            input=tc['input'],
                            expected_output=tc.get('expected_output', ''),
                            category=tc.get('category', 'general'),
                            difficulty=tc.get('difficulty', 'medium'),
                            tags=tc.get('tags', [])
                        )
                        case.id = tc.get('id', case.id)
                        cases.append(case)
                    self.test_cases[dataset_id] = cases
    
    def _save(self, dataset_id: str):
        """保存测试用例"""
        cases = self.test_cases.get(dataset_id, [])
        data = {
            'dataset_id': dataset_id,
            'cases': [c.to_dict() for c in cases]
        }
        with open(os.path.join(self.storage_path, f"{dataset_id}.json"), 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def create_dataset(self, dataset_id: str, cases: List[TestCase] = None) -> str:
        """创建测试数据集"""
        self.test_cases[dataset_id] = cases or []
        self._save(dataset_id)
        return dataset_id
    
    def add_case(self, dataset_id: str, test_case: TestCase) -> bool:
        """添加测试用例"""
        if dataset_id not in self.test_cases:
            self.test_cases[dataset_id] = []
        self.test_cases[dataset_id].append(test_case)
        self._save(dataset_id)
        return True
    
    def get_cases(self, dataset_id: str) -> List[TestCase]:
        """获取所有测试用例"""
        return self.test_cases.get(dataset_id, [])
    
    def get_cases_by_category(self, dataset_id: str, category: str) -> List[TestCase]:
        """按分类获取测试用例"""
        return [tc for tc in self.test_cases.get(dataset_id, []) if tc.category == category]
    
    def get_cases_by_difficulty(self, dataset_id: str, difficulty: str) -> List[TestCase]:
        """按难度获取测试用例"""
        return [tc for tc in self.test_cases.get(dataset_id, []) if tc.difficulty == difficulty]
    
    def split_train_test(self, dataset_id: str, test_ratio: float = 0.2) -> tuple:
        """
        分离训练集和验证集
        重要：预留验证集，避免在测试集上过度拟合
        """
        cases = self.test_cases.get(dataset_id, [])
        test_count = int(len(cases) * test_ratio)
        
        # 按难度分层采样
        easy = [tc for tc in cases if tc.difficulty == 'easy']
        medium = [tc for tc in cases if tc.difficulty == 'medium']
        hard = [tc for tc in cases if tc.difficulty == 'hard']
        
        test_set = []
        train_set = []
        
        # 从每个难度级别取样作为测试集
        for group in [easy, medium, hard]:
            group_test = group[:max(1, len(group) // 3)]
            test_set.extend(group_test)
            train_set.extend([tc for tc in group if tc not in group_test])
        
        return train_set, test_set
    
    def import_from_json(self, dataset_id: str, json_path: str) -> int:
        """从 JSON 文件导入测试用例"""
        with open(json_path, 'r') as f:
            data = json.load(f)
        
        cases = []
        for item in data:
            case = TestCase(
                input=item.get('input', ''),
                expected_output=item.get('expected', item.get('expected_output', '')),
                category=item.get('category', 'general'),
                difficulty=item.get('difficulty', 'medium'),
                tags=item.get('tags', [])
            )
            cases.append(case)
        
        self.test_cases[dataset_id] = cases
        self._save(dataset_id)
        return len(cases)
    
    def export_to_json(self, dataset_id: str, json_path: str) -> int:
        """导出测试用例到 JSON"""
        cases = self.test_cases.get(dataset_id, [])
        data = [
            {
                "input": tc.input,
                "expected": tc.expected_output,
                "category": tc.category,
                "difficulty": tc.difficulty,
                "tags": tc.tags
            }
            for tc in cases
        ]
        with open(json_path, 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
        return len(data)


# 模块测试
if __name__ == "__main__":
    tdm = TestDataManager()
    
    # 创建测试数据集
    tdm.create_dataset("demo", [
        TestCase("你好", "你好！有什么可以帮助你的吗？", "general", "easy"),
        TestCase("帮我写一首诗", "请创作一首关于春天的诗", "creative", "medium"),
        TestCase("1+1等于几", "2", "factual", "easy"),
    ])
    
    print("测试用例数量:", len(tdm.get_cases("demo")))
    
    # 按分类查看
    for tc in tdm.get_cases("demo"):
        print(f"[{tc.category}] {tc.input[:20]}...")
    
    # 分离训练集和验证集
    train, test = tdm.split_train_test("demo")
    print(f"训练集: {len(train)}, 验证集: {len(test)}")
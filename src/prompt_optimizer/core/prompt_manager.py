"""
Prompt Manager - 提示词版本管理
职责：管理提示词版本，支持历史回滚和差异对比
"""
from typing import List, Optional, Dict, Any
from datetime import datetime
import json
import os

class PromptVersion:
    """提示词版本"""
    def __init__(self, content: str, version: int = 1, parent_id: Optional[str] = None):
        self.id = f"v_{datetime.now().strftime('%Y%m%d%H%M%S')}_{version}"
        self.content = content
        self.version = version
        self.parent_id = parent_id
        self.created_at = datetime.now()
        self.metadata: Dict[str, Any] = {}
    
    def to_dict(self) -> Dict:
        return {
            "id": self.id,
            "content": self.content,
            "version": self.version,
            "parent_id": self.parent_id,
            "created_at": self.created_at.isoformat(),
            "metadata": self.metadata
        }


class PromptManager:
    """提示词管理器"""
    
    def __init__(self, storage_path: str = "data/prompts"):
        self.storage_path = storage_path
        self.prompts: Dict[str, List[PromptVersion]] = {}
        os.makedirs(storage_path, exist_ok=True)
        self._load()
    
    def _load(self):
        """加载存储的提示词"""
        for filename in os.listdir(self.storage_path):
            if filename.endswith('.json'):
                with open(os.path.join(self.storage_path, filename), 'r') as f:
                    data = json.load(f)
                    prompt_id = filename[:-5]
                    versions = []
                    for v in data.get('versions', []):
                        pv = PromptVersion(
                            content=v['content'],
                            version=v['version'],
                            parent_id=v.get('parent_id')
                        )
                        pv.id = v['id']
                        pv.metadata = v.get('metadata', {})
                        versions.append(pv)
                    self.prompts[prompt_id] = versions
    
    def _save(self, prompt_id: str):
        """保存提示词到磁盘"""
        versions = self.prompts.get(prompt_id, [])
        data = {
            'prompt_id': prompt_id,
            'versions': [v.to_dict() for v in versions]
        }
        with open(os.path.join(self.storage_path, f"{prompt_id}.json"), 'w') as f:
            json.dump(data, f, indent=2, ensure_ascii=False)
    
    def create(self, prompt_id: str, content: str) -> PromptVersion:
        """创建新提示词"""
        versions = self.prompts.get(prompt_id, [])
        version_num = len(versions) + 1
        parent_id = versions[-1].id if versions else None
        
        pv = PromptVersion(content, version_num, parent_id)
        self.prompts.setdefault(prompt_id, []).append(pv)
        self._save(prompt_id)
        return pv
    
    def get_latest(self, prompt_id: str) -> Optional[PromptVersion]:
        """获取最新版本"""
        versions = self.prompts.get(prompt_id, [])
        return versions[-1] if versions else None
    
    def get_versions(self, prompt_id: str) -> List[PromptVersion]:
        """获取所有版本"""
        return self.prompts.get(prompt_id, [])
    
    def get_version(self, prompt_id: str, version: int) -> Optional[PromptVersion]:
        """获取指定版本"""
        versions = self.prompts.get(prompt_id, [])
        for v in versions:
            if v.version == version:
                return v
        return None
    
    def rollback(self, prompt_id: str, version: int) -> Optional[PromptVersion]:
        """回滚到指定版本"""
        old_version = self.get_version(prompt_id, version)
        if not old_version:
            return None
        
        new_version = self.create(prompt_id, old_version.content)
        return new_version
    
    def compare(self, prompt_id: str, v1: int, v2: int) -> Dict[str, Any]:
        """对比两个版本差异"""
        version1 = self.get_version(prompt_id, v1)
        version2 = self.get_version(prompt_id, v2)
        
        if not version1 or not version2:
            return {"error": "版本不存在"}
        
        # 简单对比：计算相似度
        content1_lines = version1.content.split('\n')
        content2_lines = version2.content.split('\n')
        
        return {
            "version1": v1,
            "version2": v2,
            "lines_added": len(content2_lines) - len(content1_lines),
            "content1": version1.content,
            "content2": version2.content
        }


# 模块测试
if __name__ == "__main__":
    pm = PromptManager()
    
    # 创建提示词
    pv1 = pm.create("test_prompt", "你是一个AI助手，请帮助用户解决问题")
    print(f"创建: {pv1.id}, 版本: {pv1.version}")
    
    # 更新提示词
    pv2 = pm.create("test_prompt", "你是一个专业的AI助手，请用简洁清晰的语言帮助用户解决问题")
    print(f"更新: {pv2.id}, 版本: {pv2.version}")
    
    # 获取历史
    for v in pm.get_versions("test_prompt"):
        print(f"版本 {v.version}: {v.content[:50]}...")
    
    # 对比
    diff = pm.compare("test_prompt", 1, 2)
    print(f"差异: 添加了 {diff.get('lines_added', 0)} 行")
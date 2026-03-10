<template>
  <div class="home">
    <div class="toolbar">
      <button class="btn" @click="handleOptimize" :disabled="loading">
        {{ loading ? '优化中...' : '🚀 开始优化' }}
      </button>
      <button class="btn btn-secondary" @click="loadVersions">🔄 刷新版本</button>
    </div>

    <div class="content">
      <div class="editor-panel">
        <div class="panel-header">
          <span>📝 提示词编辑</span>
          <div class="tabs">
            <button 
              :class="['tab', { active: activeTab === 'edit' }]" 
              @click="activeTab = 'edit'"
            >编辑</button>
            <button 
              :class="['tab', { active: activeTab === 'preview' }]" 
              @click="activeTab = 'preview'"
            >预览</button>
          </div>
        </div>
        
        <div class="editor-content">
          <PromptEditor 
            v-if="activeTab === 'edit'"
            v-model="prompt" 
          />
          <PromptPreview 
            v-else 
            :content="prompt" 
          />
        </div>
      </div>

      <div class="result-panel">
        <div class="panel-header">
          <span>📊 评估结果</span>
        </div>
        
        <div class="result-content">
          <div v-if="result" class="result-box">
            <ScoreRadar :scores="result.scores" />
            
            <div class="optimized-prompt">
              <h4>✨ 优化后的提示词</h4>
              <pre>{{ result.optimized_prompt }}</pre>
            </div>
          </div>
          
          <div v-else class="empty-state">
            <p>点击"开始优化"按钮开始优化提示词</p>
          </div>
        </div>
      </div>
    </div>

    <VersionTimeline 
      :versions="versions" 
      @select="selectVersion"
    />
  </div>
</template>

<script setup>
import { ref, onMounted } from 'vue'
import PromptEditor from '../components/PromptEditor.vue'
import PromptPreview from '../components/PromptPreview.vue'
import ScoreRadar from '../components/ScoreRadar.vue'
import VersionTimeline from '../components/VersionTimeline.vue'
import { optimizePrompt, getVersions, getVersion } from '../api'

const prompt = ref(`请帮我优化以下提示词，要求：
1. 明确任务目标
2. 提供上下文背景
3. 指定输出格式`)

const loading = ref(false)
const result = ref(null)
const versions = ref([])
const activeTab = ref('edit')

const showToast = (message, type = 'success') => {
  window.showToast?.(message, type)
}

const handleOptimize = async () => {
  if (!prompt.value.trim()) {
    showToast('请输入提示词', 'error')
    return
  }
  
  loading.value = true
  try {
    const { data } = await optimizePrompt({ prompt: prompt.value })
    result.value = data
    showToast('优化成功！', 'success')
    loadVersions()
  } catch (error) {
    showToast('优化失败: ' + (error.message || '未知错误'), 'error')
  } finally {
    loading.value = false
  }
}

const loadVersions = async () => {
  try {
    const { data } = await getVersions()
    versions.value = data.versions || []
  } catch (error) {
    console.error('加载版本失败:', error)
  }
}

const selectVersion = async (versionId) => {
  try {
    const { data } = await getVersion(versionId)
    prompt.value = data.prompt
    result.value = data
    showToast('已加载版本 ' + versionId, 'info')
  } catch (error) {
    showToast('加载版本失败', 'error')
  }
}

onMounted(() => {
  loadVersions()
})
</script>

<style scoped>
.home {
  padding: 20px;
}

.toolbar {
  display: flex;
  gap: 10px;
  margin-bottom: 20px;
}

.btn {
  padding: 12px 24px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  color: white;
  border: none;
  border-radius: 8px;
  font-size: 14px;
  font-weight: 600;
  cursor: pointer;
  transition: transform 0.2s, box-shadow 0.2s;
}

.btn:hover:not(:disabled) {
  transform: translateY(-2px);
  box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
}

.btn:disabled {
  opacity: 0.6;
  cursor: not-allowed;
}

.btn-secondary {
  background: #f0f0f0;
  color: #333;
}

.content {
  display: grid;
  grid-template-columns: 1fr 1fr;
  gap: 20px;
  margin-bottom: 20px;
}

.panel-header {
  display: flex;
  justify-content: space-between;
  align-items: center;
  padding: 15px 20px;
  background: #f8f9fa;
  border-bottom: 1px solid #e0e0e0;
  font-weight: 600;
}

.tabs {
  display: flex;
  gap: 5px;
}

.tab {
  padding: 6px 16px;
  border: none;
  background: transparent;
  cursor: pointer;
  border-radius: 4px;
  font-size: 13px;
  transition: all 0.2s;
}

.tab.active {
  background: #667eea;
  color: white;
}

.editor-content {
  height: 400px;
  overflow: hidden;
}

.result-content {
  padding: 20px;
  min-height: 400px;
}

.result-box {
  animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
  from { opacity: 0; transform: translateY(10px); }
  to { opacity: 1; transform: translateY(0); }
}

.optimized-prompt {
  margin-top: 20px;
}

.optimized-prompt h4 {
  margin-bottom: 10px;
  color: #333;
}

.optimized-prompt pre {
  background: #f5f5f5;
  padding: 15px;
  border-radius: 8px;
  font-size: 13px;
  white-space: pre-wrap;
  max-height: 200px;
  overflow-y: auto;
}

.empty-state {
  text-align: center;
  color: #999;
  padding: 100px 20px;
}

@media (max-width: 768px) {
  .content {
    grid-template-columns: 1fr;
  }
}
</style>
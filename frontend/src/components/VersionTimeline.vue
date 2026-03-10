<template>
  <div class="version-timeline" v-if="versions.length > 0">
    <h3>📜 版本历史</h3>
    <div class="timeline">
      <div 
        v-for="version in versions" 
        :key="version.id" 
        class="timeline-item"
        @click="$emit('select', version.id)"
      >
        <div class="timeline-dot"></div>
        <div class="timeline-content">
          <div class="version-id">v{{ version.id }}</div>
          <div class="version-date">{{ formatDate(version.created_at) }}</div>
          <div class="version-score" v-if="version.score">
            评分: {{ version.score }}
          </div>
        </div>
      </div>
    </div>
  </div>
</template>

<script setup>
defineProps({
  versions: {
    type: Array,
    default: () => []
  }
})

defineEmits(['select'])

const formatDate = (dateStr) => {
  if (!dateStr) return ''
  const date = new Date(dateStr)
  return date.toLocaleString('zh-CN', {
    month: '2-digit',
    day: '2-digit',
    hour: '2-digit',
    minute: '2-digit'
  })
}
</script>

<style scoped>
.version-timeline {
  margin-top: 30px;
  padding: 20px;
  background: #f8f9fa;
  border-radius: 12px;
}

.version-timeline h3 {
  margin-bottom: 20px;
  color: #333;
}

.timeline {
  display: flex;
  gap: 20px;
  overflow-x: auto;
  padding: 10px 0;
}

.timeline-item {
  flex-shrink: 0;
  display: flex;
  align-items: flex-start;
  gap: 10px;
  cursor: pointer;
  transition: transform 0.2s;
}

.timeline-item:hover {
  transform: translateY(-3px);
}

.timeline-dot {
  width: 12px;
  height: 12px;
  background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
  border-radius: 50%;
  margin-top: 5px;
}

.timeline-content {
  background: white;
  padding: 12px 16px;
  border-radius: 8px;
  box-shadow: 0 2px 8px rgba(0,0,0,0.1);
}

.version-id {
  font-weight: 600;
  color: #333;
  margin-bottom: 4px;
}

.version-date {
  font-size: 12px;
  color: #999;
}

.version-score {
  font-size: 12px;
  color: #667eea;
  margin-top: 4px;
}
</style>
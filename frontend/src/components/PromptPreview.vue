<template>
  <div class="prompt-preview">
    <div class="preview-content" v-html="renderedContent"></div>
  </div>
</template>

<script setup>
import { computed } from 'vue'
import { marked } from 'marked'

const props = defineProps({
  content: {
    type: String,
    default: ''
  }
})

const renderedContent = computed(() => {
  if (!props.content) return '<p class="empty">预览区域</p>'
  return marked(props.content)
})
</script>

<style scoped>
.prompt-preview {
  height: 100%;
  padding: 15px;
  overflow-y: auto;
}

.preview-content {
  background: #f8f9fa;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 20px;
  min-height: 350px;
  font-size: 14px;
  line-height: 1.6;
}

.preview-content :deep(h1),
.preview-content :deep(h2),
.preview-content :deep(h3) {
  margin: 15px 0 10px;
  color: #333;
}

.preview-content :deep(p) {
  margin: 10px 0;
}

.preview-content :deep(code) {
  background: #e9ecef;
  padding: 2px 6px;
  border-radius: 4px;
  font-family: monospace;
}

.preview-content :deep(pre) {
  background: #2d2d2d;
  color: #f8f8f2;
  padding: 15px;
  border-radius: 8px;
  overflow-x: auto;
}

.preview-content :deep(ul),
.preview-content :deep(ol) {
  margin: 10px 0;
  padding-left: 20px;
}

.preview-content :deep(.empty) {
  color: #999;
  font-style: italic;
}
</style>
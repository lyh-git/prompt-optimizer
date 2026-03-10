<template>
  <div class="prompt-editor">
    <textarea
      :value="modelValue"
      @input="$emit('update:modelValue', $event.target.value)"
      placeholder="请输入提示词..."
      class="editor-textarea"
    ></textarea>
  </div>
</template>

<script setup>
defineProps({
  modelValue: {
    type: String,
    default: ''
  }
})

defineEmits(['update:modelValue'])
</script>

<style scoped>
.prompt-editor {
  height: 100%;
  padding: 15px;
}

.editor-textarea {
  width: 100%;
  height: 100%;
  border: 2px solid #e0e0e0;
  border-radius: 8px;
  padding: 15px;
  font-family: 'Monaco', 'Menlo', monospace;
  font-size: 14px;
  line-height: 1.6;
  resize: none;
  transition: border-color 0.3s;
}

.editor-textarea:focus {
  outline: none;
  border-color: #667eea;
}

.editor-textarea::placeholder {
  color: #999;
}
</style>
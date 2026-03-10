import axios from 'axios'

const api = axios.create({
  baseURL: '/api',
  timeout: 60000
})

// 优化提示词
export const optimizePrompt = (data) => api.post('/optimize', data)

// 获取版本历史
export const getVersions = () => api.get('/versions')

// 获取指定版本
export const getVersion = (id) => api.get(`/versions/${id}`)

// 评估提示词
export const evaluatePrompt = (data) => api.post('/evaluate', data)

// 获取测试用例
export const getTestCases = () => api.get('/test-cases')

// 版本回滚
export const rollback = (versionId) => api.post(`/rollback/${versionId}`)

// 获取配置
export const getConfig = () => api.get('/config')

export default api
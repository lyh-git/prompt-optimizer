"""
提示词优化工具 - Web 界面
使用 Flask 快速搭建
"""
from flask import Flask, render_template_string, request, jsonify
import json
import os
import sys

app = Flask(__name__)

# 页面模板
INDEX_TEMPLATE = '''
<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>提示词优化工具</title>
    <!-- 引入Chart.js -->
    <script src="https://cdn.jsdelivr.net/npm/chart.js"></script>
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 1200px;
            margin: 0 auto;
            background: white;
            border-radius: 16px;
            box-shadow: 0 20px 60px rgba(0,0,0,0.3);
            overflow: hidden;
        }
        .header {
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            text-align: center;
        }
        .header h1 { font-size: 28px; margin-bottom: 10px; }
        .header p { opacity: 0.9; font-size: 14px; }
        .content { padding: 30px; }
        .form-group { margin-bottom: 25px; }
        .form-group label {
            display: block;
            font-weight: 600;
            margin-bottom: 8px;
            color: #333;
        }
        .form-group textarea,
        .form-group input {
            width: 100%;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            font-size: 14px;
            transition: border-color 0.3s;
        }
        .form-group textarea { min-height: 120px; resize: vertical; font-family: monospace; }
        .form-group textarea:focus,
        .form-group input:focus {
            outline: none;
            border-color: #667eea;
        }
        .form-row { display: flex; gap: 20px; }
        .form-row .form-group { flex: 1; }
        .btn {
            display: inline-block;
            padding: 15px 40px;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            border: none;
            border-radius: 8px;
            font-size: 16px;
            font-weight: 600;
            cursor: pointer;
            transition: transform 0.2s, box-shadow 0.2s;
        }
        .btn:hover {
            transform: translateY(-2px);
            box-shadow: 0 10px 20px rgba(102, 126, 234, 0.4);
        }
        .btn-secondary {
            background: #f0f0f0;
            color: #333;
            margin-left: 10px;
        }
        .result {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
            display: none;
        }
        .result.show { display: block; }
        .result h3 { color: #333; margin-bottom: 15px; }
        .result-content {
            background: white;
            padding: 15px;
            border-radius: 8px;
            border: 1px solid #e0e0e0;
            white-space: pre-wrap;
            font-family: monospace;
            font-size: 13px;
            max-height: 300px;
            overflow-y: auto;
        }
        .score { display: flex; gap: 20px; margin-top: 15px; }
        .score-item {
            flex: 1;
            text-align: center;
            padding: 20px;
            background: white;
            border-radius: 8px;
        }
        .score-value { font-size: 36px; font-weight: bold; color: #667eea; }
        .score-label { font-size: 12px; color: #666; margin-top: 5px; }
        .loading {
            text-align: center;
            padding: 40px;
            display: none;
        }
        .loading.show { display: block; }
        .spinner {
            width: 50px;
            height: 50px;
            border: 4px solid #f3f3f3;
            border-top: 4px solid #667eea;
            border-radius: 50%;
            animation: spin 1s linear infinite;
            margin: 0 auto 20px;
        }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .tips {
            margin-top: 20px;
            padding: 15px;
            background: #fff3cd;
            border-radius: 8px;
            font-size: 13px;
            color: #856404;
        }
        /* 雷达图容器 */
        .radar-chart-container {
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-top: 20px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }
        .radar-chart-container h3 {
            margin: 0 0 15px 0;
            color: #333;
        }
        .radar-chart-wrapper {
            height: 400px;
            position: relative;
        }
        /* Markdown预览切换 */
        .editor-preview-container {
            display: flex;
            gap: 20px;
            margin-bottom: 25px;
        }
        .editor-section, .preview-section {
            flex: 1;
        }
        .editor-section h4, .preview-section h4 {
            margin-bottom: 8px;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }
        .preview-section h4 .toggle-btn {
            background: #f0f0f0;
            border: none;
            padding: 5px 10px;
            border-radius: 4px;
            cursor: pointer;
            font-size: 12px;
        }
        .preview-content {
            width: 100%;
            min-height: 120px;
            padding: 12px 15px;
            border: 2px solid #e0e0e0;
            border-radius: 8px;
            background: #fafafa;
            font-size: 14px;
            line-height: 1.5;
            overflow-y: auto;
        }
        .preview-content img {
            max-width: 100%;
            height: auto;
        }
        /* 版本时间线 */
        .version-timeline {
            margin-top: 30px;
            padding: 20px;
            background: #f8f9fa;
            border-radius: 8px;
        }
        .version-timeline h3 {
            margin-bottom: 15px;
            color: #333;
        }
        .timeline-container {
            position: relative;
            padding-left: 30px;
        }
        .timeline-container::before {
            content: '';
            position: absolute;
            left: 15px;
            top: 0;
            bottom: 0;
            width: 2px;
            background: #667eea;
        }
        .timeline-item {
            position: relative;
            margin-bottom: 20px;
            padding-left: 20px;
        }
        .timeline-item::before {
            content: '';
            position: absolute;
            left: -24px;
            top: 5px;
            width: 12px;
            height: 12px;
            border-radius: 50%;
            background: #667eea;
            border: 2px solid white;
            z-index: 1;
        }
        .timeline-item .time {
            font-size: 12px;
            color: #666;
            margin-bottom: 5px;
        }
        .timeline-item .version-title {
            font-weight: 600;
            margin-bottom: 5px;
            cursor: pointer;
            color: #333;
        }
        .timeline-item .version-title:hover {
            color: #667eea;
        }
        .timeline-item .version-content {
            font-size: 13px;
            color: #555;
            display: none;
            margin-top: 10px;
            padding: 10px;
            background: white;
            border-radius: 4px;
            border-left: 3px solid #667eea;
        }
        .timeline-item.active .version-content {
            display: block;
        }
        /* Toast通知 */
        .toast-container {
            position: fixed;
            top: 20px;
            right: 20px;
            z-index: 10000;
        }
        .toast {
            min-width: 250px;
            padding: 15px 20px;
            margin-bottom: 10px;
            border-radius: 8px;
            color: white;
            box-shadow: 0 4px 12px rgba(0,0,0,0.15);
            display: flex;
            align-items: center;
            transform: translateX(120%);
            transition: transform 0.3s ease-out;
        }
        .toast.show {
            transform: translateX(0);
        }
        .toast.success {
            background: linear-gradient(135deg, #4CAF50, #2E7D32);
        }
        .toast.error {
            background: linear-gradient(135deg, #F44336, #C62828);
        }
        .toast.info {
            background: linear-gradient(135deg, #2196F3, #1565C0);
        }
        .toast-icon {
            margin-right: 10px;
            font-size: 18px;
        }
        .toast-message {
            flex: 1;
        }
        /* 隐藏元素 */
        .hidden {
            display: none !important;
        }
    </style>
</head>
<body>
    <div class="container">
        <div class="header">
            <h1>🤖 提示词优化工具</h1>
            <p>使用 AI 自动优化你的提示词</p>
        </div>
        <div class="content">
            <form id="optimizerForm">
                <div class="editor-preview-container">
                    <div class="editor-section">
                        <h4>
                            <span>📝 输入你的提示词</span>
                        </h4>
                        <textarea id="promptInput" name="prompt" placeholder="例如：你是一个专业的AI助手，请帮我回答用户的问题..." required></textarea>
                    </div>
                    <div class="preview-section">
                        <h4>
                            <span>👁️ Markdown 预览</span>
                            <button type="button" class="toggle-btn" onclick="togglePreview()">切换预览</button>
                        </h4>
                        <div id="promptPreview" class="preview-content">
                            <em>预览内容将在此显示</em>
                        </div>
                    </div>
                </div>
                <div class="form-row">
                    <div class="form-group">
                        <label>🔄 最大迭代次数</label>
                        <input type="number" name="max_iterations" value="5" min="1" max="20">
                    </div>
                    <div class="form-group">
                        <label>🎯 目标分数 (0-1)</label>
                        <input type="number" name="target_score" value="0.8" min="0.1" max="1.0" step="0.05">
                    </div>
                </div>
                <div class="form-group">
                    <label>📊 测试数据 (JSON格式)</label>
                    <textarea name="test_cases" placeholder='[{"input": "问题1", "expected": "期望回答1"}]' style="min-height: 80px;"></textarea>
                </div>
                <button type="submit" class="btn">🚀 开始优化</button>
                <button type="button" class="btn btn-secondary" onclick="loadExample()">📋 加载示例</button>
            </form>
            <div class="loading" id="loading">
                <div class="spinner"></div>
                <p>AI 正在优化提示词中...</p>
            </div>
            <div class="result" id="result">
                <h3>✨ 优化结果</h3>
                <div class="score">
                    <div class="score-item">
                        <div class="score-value" id="beforeScore">-</div>
                        <div class="score-label">优化前分数</div>
                    </div>
                    <div class="score-item">
                        <div class="score-value" id="afterScore">-</div>
                        <div class="score-label">优化后分数</div>
                    </div>
                    <div class="score-item">
                        <div class="score-value" id="iterations">-</div>
                        <div class="score-label">迭代次数</div>
                    </div>
                </div>
                
                <!-- 雷达图展示评分 -->
                <div class="radar-chart-container">
                    <h3>📊 评分详情</h3>
                    <div class="radar-chart-wrapper">
                        <canvas id="radarChart"></canvas>
                    </div>
                </div>
                
                <h3 style="margin-top: 20px;">📝 优化后的提示词</h3>
                <div class="result-content" id="optimizedPrompt"></div>
            </div>
            
            <!-- 版本时间线 -->
            <div class="version-timeline" id="versionTimeline" style="display: none;">
                <h3>🔄 历史版本</h3>
                <div class="timeline-container" id="timelineContainer">
                    <!-- 版本时间线将在这里动态生成 -->
                </div>
            </div>
            
            <div class="tips">💡 <strong>使用提示：</strong>当前使用 Mock 模式测试。配置 config.yaml 可切换真实 API。</div>
        </div>
    </div>
    
    <!-- Toast 容器 -->
    <div class="toast-container" id="toastContainer"></div>
    
    <script>
        // 显示 Toast 通知
        function showToast(message, type = 'info') {
            const toastContainer = document.getElementById('toastContainer');
            const toast = document.createElement('div');
            toast.className = `toast ${type}`;
            
            const icons = {
                success: '✓',
                error: '✗',
                info: 'ℹ'
            };
            
            toast.innerHTML = `
                <span class="toast-icon">${icons[type] || 'ℹ'}</span>
                <span class="toast-message">${message}</span>
            `;
            
            toastContainer.appendChild(toast);
            
            // 显示动画
            setTimeout(() => {
                toast.classList.add('show');
            }, 100);
            
            // 自动隐藏
            setTimeout(() => {
                toast.classList.remove('show');
                setTimeout(() => {
                    if (toast.parentNode) {
                        toastContainer.removeChild(toast);
                    }
                }, 300);
            }, 3000);
        }
        
        // 更新 Markdown 预览
        function updatePreview() {
            const promptInput = document.getElementById('promptInput');
            const previewDiv = document.getElementById('promptPreview');
            const text = promptInput.value;
            
            // 简单的 Markdown 渲染（仅处理基本标记）
            let html = text
                .replace(/&/g, '&amp;')
                .replace(/</g, '&lt;')
                .replace(/>/g, '&gt;')
                .replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>')
                .replace(/\*(.*?)\*/g, '<em>$1</em>')
                .replace(/^# (.*$)/gm, '<h1>$1</h1>')
                .replace(/^## (.*$)/gm, '<h2>$1</h2>')
                .replace(/^### (.*$)/gm, '<h3>$1</h3>')
                .replace(/^- (.*$)/gm, '<li>$1</li>')
                .replace(/^\d+\. (.*$)/gm, '<li>$1</li>');
            
            // 处理换行
            html = html.replace(/\n/g, '<br>');
            
            previewDiv.innerHTML = html || '<em>预览内容将在此显示</em>';
        }
        
        // 切换预览显示/隐藏
        function togglePreview() {
            const previewDiv = document.getElementById('promptPreview');
            previewDiv.classList.toggle('hidden');
        }
        
        // 初始化预览更新监听
        document.getElementById('promptInput').addEventListener('input', updatePreview);
        
        // 示例版本数据（实际应用中可能从服务器获取）
        let versionHistory = [];
        
        // 添加版本到时间线
        function addVersionToTimeline(versionData) {
            versionHistory.push({
                ...versionData,
                timestamp: new Date().toLocaleString()
            });
            
            renderVersionTimeline();
        }
        
        // 渲染版本时间线
        function renderVersionTimeline() {
            const container = document.getElementById('timelineContainer');
            container.innerHTML = '';
            
            // 反转数组以最新的版本在前面
            [...versionHistory].reverse().forEach((version, index) => {
                const item = document.createElement('div');
                item.className = 'timeline-item';
                item.innerHTML = `
                    <div class="time">${version.timestamp}</div>
                    <div class="version-title" onclick="toggleVersionDetail(this)">
                        版本 ${versionHistory.length - index}: ${version.title || '优化后'}
                    </div>
                    <div class="version-content">
                        <strong>评分:</strong> ${version.score || 'N/A'}<br>
                        <strong>提示词:</strong><br>
                        <pre>${version.prompt || ''}</pre>
                    </div>
                `;
                container.appendChild(item);
            });
            
            // 显示时间线容器
            document.getElementById('versionTimeline').style.display = 'block';
        }
        
        // 切换版本详情显示/隐藏
        function toggleVersionDetail(element) {
            const item = element.parentElement;
            item.classList.toggle('active');
        }
        
        function loadExample() {
            document.getElementById('promptInput').value = '你是一个AI助手，擅长回答用户的问题。';
            document.querySelector('textarea[name="test_cases"]').value = '[{"input": "今天天气怎么样？", "expected": "今天天气晴朗。"}]';
            updatePreview(); // 更新预览
            showToast('示例已加载', 'info');
        }
        
        // 创建雷达图
        function createRadarChart(scores) {
            const ctx = document.getElementById('radarChart').getContext('2d');
            
            // 如果已有图表实例，则销毁它
            if (window.radarChartInstance) {
                window.radarChartInstance.destroy();
            }
            
            window.radarChartInstance = new Chart(ctx, {
                type: 'radar',
                data: {
                    labels: ['准确率', '格式合规', '领域匹配', '幻觉检测', '长度控制'],
                    datasets: [{
                        label: '评分',
                        data: [
                            scores.accuracy || 0,
                            scores.format || 0,
                            scores.domain || 0,
                            scores.hallucination || 0,
                            scores.length || 0
                        ],
                        backgroundColor: 'rgba(102, 126, 234, 0.2)',
                        borderColor: 'rgba(102, 126, 234, 1)',
                        pointBackgroundColor: 'rgba(102, 126, 234, 1)',
                        pointBorderColor: '#fff',
                        pointHoverBackgroundColor: '#fff',
                        pointHoverBorderColor: 'rgba(102, 126, 234, 1)'
                    }]
                },
                options: {
                    scales: {
                        r: {
                            angleLines: {
                                display: true
                            },
                            suggestedMin: 0,
                            suggestedMax: 1
                        }
                    },
                    plugins: {
                        legend: {
                            position: 'top',
                        },
                        tooltip: {
                            callbacks: {
                                label: function(context) {
                                    return `${context.label}: ${(context.parsed.r * 100).toFixed(0)}%`;
                                }
                            }
                        }
                    }
                }
            });
        }
        
        document.getElementById('optimizerForm').addEventListener('submit', async function(e) {
            e.preventDefault();
            const loading = document.getElementById('loading');
            const result = document.getElementById('result');
            loading.classList.add('show');
            result.classList.remove('show');
            
            try {
                const formData = new FormData(e.target);
                const data = {
                    prompt: formData.get('prompt'),
                    max_iterations: parseInt(formData.get('max_iterations')),
                    target_score: parseFloat(formData.get('target_score')),
                    test_cases: formData.get('test_cases')
                };
                
                const response = await fetch('/optimize', {
                    method: 'POST',
                    headers: {'Content-Type': 'application/json'},
                    body: JSON.stringify(data)
                });
                
                const result_data = await response.json();
                
                if (result_data.success) {
                    // 显示基础结果
                    document.getElementById('beforeScore').textContent = result_data.before_score || '-';
                    document.getElementById('afterScore').textContent = result_data.after_score || '-';
                    document.getElementById('iterations').textContent = result_data.iterations || '-';
                    document.getElementById('optimizedPrompt').textContent = result_data.optimized_prompt || '';
                    
                    // 显示雷达图
                    if(result_data.scores) {
                        createRadarChart(result_data.scores);
                    } else {
                        // 如果没有评分数据，使用默认值
                        createRadarChart({
                            accuracy: 0.8,
                            format: 0.7,
                            domain: 0.9,
                            hallucination: 0.6,
                            length: 0.8
                        });
                    }
                    
                    // 添加到版本历史
                    addVersionToTimeline({
                        title: '最新优化结果',
                        score: result_data.after_score,
                        prompt: result_data.optimized_prompt
                    });
                    
                    result.classList.add('show');
                    showToast('优化完成！', 'success');
                } else {
                    showToast('优化失败: ' + result_data.error, 'error');
                }
            } catch (error) {
                showToast('请求失败: ' + error.message, 'error');
            }
            
            loading.classList.remove('show');
        });
        
        // 页面加载时初始化预览
        document.addEventListener('DOMContentLoaded', function() {
            updatePreview();
        });
    </script>
</body>
</html>
'''

@app.route('/')
def index():
    return render_template_string(INDEX_TEMPLATE)

@app.route('/optimize', methods=['POST'])
def optimize():
    data = request.json
    
    # Mock 模式 - 返回模拟结果
    original_prompt = data.get('prompt', '')
    optimized_prompt = original_prompt + '\n\n【优化建议】\n1. 请用清晰、结构化的方式回答\n2. 确保信息准确完整\n3. 适当使用列表和分段提高可读性'
    
    import random
    before_score = round(0.5 + random.random() * 0.2, 2)
    after_score = round(before_score + 0.15 + random.random() * 0.1, 2)
    if after_score > 1.0: after_score = 0.98
    
    return jsonify({
        'success': True,
        'before_score': str(before_score),
        'after_score': str(after_score),
        'iterations': str(data.get('max_iterations', 3)),
        'optimized_prompt': optimized_prompt
    })

if __name__ == '__main__':
    print("🚀 提示词优化工具 Web 界面启动中...")
    print("📍 访问地址: http://localhost:5000")
    app.run(host='0.0.0.0', port=5000, debug=False)
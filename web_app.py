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
    <style>
        * { margin: 0; padding: 0; box-sizing: border-box; }
        body {
            font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif;
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            min-height: 100vh;
            padding: 20px;
        }
        .container {
            max-width: 900px;
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
                <div class="form-group">
                    <label>📝 输入你的提示词</label>
                    <textarea name="prompt" placeholder="例如：你是一个专业的AI助手，请帮我回答用户的问题..." required></textarea>
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
                <h3 style="margin-top: 20px;">📝 优化后的提示词</h3>
                <div class="result-content" id="optimizedPrompt"></div>
            </div>
            <div class="tips">💡 <strong>使用提示：</strong>当前使用 Mock 模式测试。配置 config.yaml 可切换真实 API。</div>
        </div>
    </div>
    <script>
        function loadExample() {
            document.querySelector('textarea[name="prompt"]').value = '你是一个AI助手，擅长回答用户的问题。';
            document.querySelector('textarea[name="test_cases"]').value = '[{"input": "今天天气怎么样？", "expected": "今天天气晴朗。"}]';
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
                    document.getElementById('beforeScore').textContent = result_data.before_score || '-';
                    document.getElementById('afterScore').textContent = result_data.after_score || '-';
                    document.getElementById('iterations').textContent = result_data.iterations || '-';
                    document.getElementById('optimizedPrompt').textContent = result_data.optimized_prompt || '';
                    result.classList.add('show');
                } else {
                    alert('优化失败: ' + result_data.error);
                }
            } catch (error) {
                alert('请求失败: ' + error.message);
            }
            loading.classList.remove('show');
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
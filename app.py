# -*- coding: utf-8 -*-
"""
老年人回忆录记录助手 - 后端服务
功能：语音识别、文字润色、章节管理
监听地址：0.0.0.0:7860
"""

import os
import json
import uuid
import base64
import io
from datetime import datetime
from flask import Flask, request, jsonify, send_from_directory, render_template_string, send_file, Response
from werkzeug.utils import secure_filename
from openai import OpenAI
import threading
import time
import requests as http_requests
import dashscope
from dashscope.audio.tts_v2 import SpeechSynthesizer

app = Flask(__name__, static_folder='dist', static_url_path='')

# 配置
UPLOAD_FOLDER = os.path.join(os.path.dirname(__file__), 'uploads')
DATA_FOLDER = os.path.join(os.path.dirname(__file__), 'data')
AUDIO_FOLDER = os.path.join(os.path.dirname(__file__), 'audio')
IMAGE_FOLDER = os.path.join(os.path.dirname(__file__), 'images')
os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(DATA_FOLDER, exist_ok=True)
os.makedirs(AUDIO_FOLDER, exist_ok=True)
os.makedirs(IMAGE_FOLDER, exist_ok=True)

# API配置 - 从环境变量加载（DashScope/千问，一个 DASHSCOPE_KEY 管全部 AI 能力）
DASHSCOPE_API_KEY = os.environ.get("DASHSCOPE_KEY", "")  # 阿里云DashScope密钥（千问）

# 设置dashscope API Key
dashscope.api_key = DASHSCOPE_API_KEY

# 回忆录数据文件
MEMOIR_FILE = os.path.join(DATA_FOLDER, 'memoir.json')

def load_memoir():
    """加载回忆录数据"""
    if os.path.exists(MEMOIR_FILE):
        with open(MEMOIR_FILE, 'r', encoding='utf-8') as f:
            return json.load(f)
    return {"chapters": [], "user_info": {"name": "亲爱的长辈"}}

def save_memoir(data):
    """保存回忆录数据"""
    with open(MEMOIR_FILE, 'w', encoding='utf-8') as f:
        json.dump(data, f, ensure_ascii=False, indent=2)

def recognize_speech_from_url(audio_url):
    """使用阿里云API识别语音（需要公网可访问的URL）"""
    try:
        client = OpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        
        completion = client.chat.completions.create(
            model="qwen3-asr-flash",
            messages=[
                {
                    "content": [{"text": ""}],
                    "role": "system"
                },
                {
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": audio_url
                            }
                        }
                    ],
                    "role": "user"
                }
            ],
            stream=False,
            extra_body={
                "asr_options": {
                    "enable_itn": True
                }
            }
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"语音识别错误: {e}")
        return None

def recognize_speech_from_base64(audio_base64, mime_type="audio/wav"):
    """使用阿里云API识别语音（base64编码）"""
    try:
        client = OpenAI(
            api_key=DASHSCOPE_API_KEY,
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
        )
        
        # 构建data URI
        data_uri = f"data:{mime_type};base64,{audio_base64}"
        
        completion = client.chat.completions.create(
            model="qwen3-asr-flash",
            messages=[
                {
                    "content": [{"text": ""}],
                    "role": "system"
                },
                {
                    "content": [
                        {
                            "type": "input_audio",
                            "input_audio": {
                                "data": data_uri
                            }
                        }
                    ],
                    "role": "user"
                }
            ],
            stream=False,
            extra_body={
                "asr_options": {
                    "enable_itn": True
                }
            }
        )
        return completion.choices[0].message.content
    except Exception as e:
        print(f"语音识别错误: {e}")
        return None

def polish_text(original_text, context=""):
    """使用大模型润色文字为回忆录风格"""
    try:
        client = OpenAI(
            base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
            api_key=DASHSCOPE_API_KEY
        )
        
        prompt = f"""你是一位回忆录整理助手。请将以下口述内容整理成温馨自然的书面语。

要求：
1. 保持原意和情感色彩不变，不要添加虚构内容
2. 使用第一人称叙述
3. 语言温馨自然，适度书面化，但不要过于文艺或华丽
4. 保留原话中的真实情感和生活细节
5. 可以适当调整语序使句子更通顺，但不要大幅改写
6. 避免使用过多形容词和修辞手法
7. 如果内容涉及具体年份或事件，请保留准确性
8. 自动修正明显的口误、语病或事实性错误（如日期计算错误、常识性错误等），但不改变说话人的原意
9. 如果内容涉及敏感话题（如政治敏感、个人隐私信息如身份证号/银行卡号/详细地址等），请用【敏感内容已标记】进行标注提醒

原始口述内容：
{original_text}

{f"背景信息：{context}" if context else ""}

请直接输出整理后的文字，不要加任何解释："""

        response = client.chat.completions.create(
            model='qwen-plus',
            messages=[{
                'role': 'user',
                'content': [{'type': 'text', 'text': prompt}]
            }],
            stream=False
        )
        
        result = response.choices[0].message.content
        # 清理可能的思考过程标记
        if "<think>" in result:
            result = result.split("</think>")[-1].strip()
        return result
    except Exception as e:
        print(f"文字润色错误: {e}")
        return original_text

def generate_chapter_title(content):
    """根据内容生成章节标题"""
    try:
        client = OpenAI(
            base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
            api_key=DASHSCOPE_API_KEY
        )
        
        prompt = f"""请根据以下回忆录内容，生成一个简短、温馨的章节标题（不超过10个字）。
标题要能概括内容主题，富有情感色彩。

内容：
{content[:500]}

请直接输出标题，不要加任何解释或标点符号："""

        response = client.chat.completions.create(
            model='qwen-plus',
            messages=[{
                'role': 'user',
                'content': [{'type': 'text', 'text': prompt}]
            }],
            stream=False
        )
        
        result = response.choices[0].message.content.strip()
        # 清理可能的思考过程标记
        if "<think>" in result:
            result = result.split("</think>")[-1].strip()
        return result[:20]  # 限制长度
    except Exception as e:
        print(f"生成标题错误: {e}")
        return "珍贵的回忆"

# ==================== API 路由 ====================

@app.route('/')
def index():
    """返回主页"""
    response = send_from_directory(app.static_folder, 'index.html', max_age=0)
    response.headers['Cache-Control'] = 'no-store, max-age=0, must-revalidate'
    return response

@app.route('/api/user', methods=['GET', 'POST'])
def user_info():
    """获取或更新用户信息"""
    memoir = load_memoir()
    
    if request.method == 'POST':
        data = request.json
        memoir['user_info'] = {
            'name': data.get('name', '亲爱的长辈'),
            'birth_year': data.get('birth_year', ''),
            'hometown': data.get('hometown', '')
        }
        save_memoir(memoir)
        return jsonify({'success': True, 'user_info': memoir['user_info']})
    
    return jsonify({'user_info': memoir.get('user_info', {'name': '亲爱的长辈'})})

@app.route('/api/recognize', methods=['POST'])
def recognize():
    """语音识别接口"""
    try:
        data = request.json
        
        # 支持base64音频数据
        if 'audio_base64' in data:
            audio_base64 = data['audio_base64']
            mime_type = data.get('mime_type', 'audio/wav')
            text = recognize_speech_from_base64(audio_base64, mime_type)
        # 支持URL
        elif 'audio_url' in data:
            text = recognize_speech_from_url(data['audio_url'])
        else:
            return jsonify({'success': False, 'error': '请提供音频数据'})
        
        if text:
            return jsonify({'success': True, 'text': text})
        else:
            return jsonify({'success': False, 'error': '语音识别失败，请重试'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/polish', methods=['POST'])
def polish():
    """文字润色接口"""
    try:
        data = request.json
        original_text = data.get('text', '')
        context = data.get('context', '')
        
        if not original_text:
            return jsonify({'success': False, 'error': '请提供要润色的文字'})
        
        polished_text = polish_text(original_text, context)
        return jsonify({'success': True, 'polished_text': polished_text})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chapters', methods=['GET'])
def get_chapters():
    """获取所有章节"""
    memoir = load_memoir()
    return jsonify({'chapters': memoir.get('chapters', [])})

@app.route('/api/chapters', methods=['POST'])
def add_chapter():
    """添加新章节"""
    try:
        data = request.json
        content = data.get('content', '')
        original_text = data.get('original_text', '')
        title = data.get('title', '')
        
        if not content:
            return jsonify({'success': False, 'error': '章节内容不能为空'})
        
        # 如果没有提供标题，自动生成
        if not title:
            title = generate_chapter_title(content)
        
        memoir = load_memoir()
        
        chapter = {
            'id': str(uuid.uuid4()),
            'title': title,
            'content': content,
            'original_text': original_text,
            'date': datetime.now().strftime('%Y年%m月%d日'),
            'timestamp': datetime.now().isoformat(),
            'images': data.get('images', []),
            'tags': data.get('tags', [])  # 章节标签
        }
        
        memoir['chapters'].append(chapter)
        save_memoir(memoir)
        
        return jsonify({'success': True, 'chapter': chapter})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chapters/<chapter_id>', methods=['PUT'])
def update_chapter(chapter_id):
    """更新章节"""
    try:
        data = request.json
        memoir = load_memoir()
        
        for chapter in memoir['chapters']:
            if chapter['id'] == chapter_id:
                chapter['title'] = data.get('title', chapter['title'])
                chapter['content'] = data.get('content', chapter['content'])
                chapter['images'] = data.get('images', chapter.get('images', []))
                chapter['tags'] = data.get('tags', chapter.get('tags', []))
                save_memoir(memoir)
                return jsonify({'success': True, 'chapter': chapter})
        
        return jsonify({'success': False, 'error': '章节不存在'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chapters/<chapter_id>', methods=['DELETE'])
def delete_chapter(chapter_id):
    """删除章节"""
    try:
        memoir = load_memoir()
        memoir['chapters'] = [c for c in memoir['chapters'] if c['id'] != chapter_id]
        save_memoir(memoir)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chapters/reorder', methods=['POST'])
def reorder_chapters():
    """重新排序章节"""
    try:
        data = request.json
        chapter_ids = data.get('chapter_ids', [])  # 新顺序的章节ID列表
        
        memoir = load_memoir()
        chapters = memoir.get('chapters', [])
        
        # 按新顺序重组章节
        chapters_dict = {c['id']: c for c in chapters}
        new_chapters = []
        for cid in chapter_ids:
            if cid in chapters_dict:
                new_chapters.append(chapters_dict[cid])
        
        # 确保没有遗漏的章节（以防万一）
        for c in chapters:
            if c['id'] not in chapter_ids:
                new_chapters.append(c)
        
        memoir['chapters'] = new_chapters
        save_memoir(memoir)
        
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chapters/ai_sort', methods=['POST'])
def ai_sort_chapters():
    """AI智能排序章节（按时间线）"""
    try:
        memoir = load_memoir()
        chapters = memoir.get('chapters', [])
        
        if len(chapters) < 2:
            return jsonify({'success': True, 'message': '章节数量不足，无需排序'})
        
        # 合并所有章节信息
        chapters_info = "\n".join([
            f"章节ID: {c['id']}\n标题: {c.get('title', '未命名')}\n内容摘要: {c.get('content', '')[:200]}\n"
            for c in chapters
        ])
        
        client = OpenAI(
            base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
            api_key=DASHSCOPE_API_KEY
        )
        
        prompt = f"""你是一位回忆录整理助手。请分析以下回忆录章节，根据内容中提到的时间线（年份、人生阶段等）进行排序。

章节信息：
{chapters_info}

请按照时间先后顺序（从早到晚）排列这些章节。
- 如果内容提到具体年份，按年份排序
- 如果提到人生阶段（童年、青年、工作、退休等），按人生阶段排序
- 无法确定时间的章节放在最后

请只返回排序后的章节ID列表，用逗号分隔，不要其他内容。
例如：id1,id2,id3"""

        response = client.chat.completions.create(
            model='qwen-plus',
            messages=[{
                'role': 'user',
                'content': [{'type': 'text', 'text': prompt}]
            }],
            stream=False
        )
        
        result = response.choices[0].message.content
        # 清理思考过程标记
        if "<think>" in result:
            result = result.split("</think>")[-1].strip()
        
        # 解析返回的ID列表
        sorted_ids = [id.strip() for id in result.replace('\n', ',').split(',') if id.strip()]
        
        # 验证并重新排序
        chapters_dict = {c['id']: c for c in chapters}
        new_chapters = []
        for cid in sorted_ids:
            if cid in chapters_dict:
                new_chapters.append(chapters_dict[cid])
                del chapters_dict[cid]
        
        # 添加未被AI识别的章节
        for c in chapters_dict.values():
            new_chapters.append(c)
        
        memoir['chapters'] = new_chapters
        save_memoir(memoir)
        
        return jsonify({'success': True, 'message': '已按时间线重新排序'})
    except Exception as e:
        print(f"AI排序错误: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/export', methods=['GET'])
def export_memoir():
    """导出完整回忆录"""
    memoir = load_memoir()
    user_info = memoir.get('user_info', {})
    chapters = memoir.get('chapters', [])
    
    # 按日期排序
    chapters = sorted(chapters, key=lambda x: x.get('timestamp', ''))
    
    # 生成HTML格式的回忆录
    html_content = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <title>{user_info.get('name', '我')}的回忆录</title>
    <style>
        html {{ background: linear-gradient(135deg, #FFF8E7 0%, #FFE4C4 100%); min-height: 100%; }}
        body {{ font-family: "楷体", KaiTi, serif; line-height: 2; padding: 40px; max-width: 800px; margin: 0 auto; background: linear-gradient(135deg, #FFF8E7 0%, #FFE4C4 100%); min-height: 100vh; }}
        h1 {{ text-align: center; color: #8B4513; border-bottom: 2px solid #DEB887; padding-bottom: 20px; }}
        h2 {{ color: #A0522D; margin-top: 40px; }}
        .chapter {{ margin: 30px 0; padding: 20px; background: #FFF8DC; border-radius: 10px; }}
        .date {{ color: #888; font-size: 14px; }}
        .content {{ text-indent: 2em; }}
        .info {{ text-align: center; color: #666; margin-bottom: 30px; }}
        .chapter-images {{ display: flex; flex-wrap: wrap; gap: 15px; margin-top: 20px; justify-content: center; }}
        .chapter-images img {{ max-width: 300px; max-height: 300px; border-radius: 10px; border: 2px solid #DEB887; }}
        .image-caption {{ text-align: center; font-size: 14px; color: #666; margin-top: 5px; }}
    </style>
</head>
<body>
    <h1>{user_info.get('name', '我')}的回忆录</h1>
    <p class="info">
        {f"出生年份：{user_info.get('birth_year')}" if user_info.get('birth_year') else ""}
        {f" | 故乡：{user_info.get('hometown')}" if user_info.get('hometown') else ""}
    </p>
"""
    
    for i, chapter in enumerate(chapters, 1):
        # 处理图片 - 转为base64嵌入
        images_html = ""
        chapter_images = chapter.get('images', [])
        if chapter_images:
            images_html = '<div class="chapter-images">'
            for img in chapter_images:
                img_url = img.get('url', '')
                img_caption = img.get('caption', '')  # 使用用户注解
                # 如果是本地图片，转为base64
                if img_url.startswith('/api/images/'):
                    filename = img_url.split('/')[-1]
                    filepath = os.path.join(IMAGE_FOLDER, filename)
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            img_data = base64.b64encode(f.read()).decode('utf-8')
                        ext = filename.rsplit('.', 1)[-1].lower()
                        mime = 'image/jpeg' if ext in ['jpg', 'jpeg'] else f'image/{ext}'
                        img_url = f"data:{mime};base64,{img_data}"
                # 只有用户填写了注解才显示
                caption_html = f'<p class="image-caption">{img_caption}</p>' if img_caption else ''
                images_html += f'''
                <div>
                    <img src="{img_url}" alt="图片">
                    {caption_html}
                </div>'''
            images_html += '</div>'
        
        html_content += f"""
    <div class="chapter">
        <h2>第{i}章 {chapter.get('title', '回忆')}</h2>
        <p class="date">记录于 {chapter.get('date', '')}</p>
        <div class="content">{chapter.get('content', '').replace(chr(10), '<br>')}</div>
        {images_html}
    </div>
"""
    
    html_content += """
    <p style="text-align: center; margin-top: 50px; color: #888;">
        —— 回忆是生命中最珍贵的礼物 ——
    </p>
</body>
</html>"""
    
    return html_content, 200, {
        'Content-Type': 'text/html; charset=utf-8',
        'Content-Disposition': f'attachment; filename=memoir_{datetime.now().strftime("%Y%m%d")}.html'
    }

@app.route('/api/export/preview', methods=['GET'])
def export_memoir_preview():
    """导出回忆录预览页面"""
    memoir = load_memoir()
    user_info = memoir.get('user_info', {})
    chapters = memoir.get('chapters', [])
    
    # 用户姓名
    user_name = user_info.get('name', '亲爱的长辈')
    
    # 按日期排序
    chapters = sorted(chapters, key=lambda x: x.get('timestamp', ''))
    
    # 生成回忆录内容HTML
    chapters_html = ""
    for i, chapter in enumerate(chapters, 1):
        images_html = ""
        chapter_images = chapter.get('images', [])
        if chapter_images:
            images_html = '<div class="chapter-images">'
            for img in chapter_images:
                img_url = img.get('url', '')
                img_caption = img.get('caption', '')
                if img_url.startswith('/api/images/'):
                    filename = img_url.split('/')[-1]
                    filepath = os.path.join(IMAGE_FOLDER, filename)
                    if os.path.exists(filepath):
                        with open(filepath, 'rb') as f:
                            img_data = base64.b64encode(f.read()).decode('utf-8')
                        ext = filename.rsplit('.', 1)[-1].lower()
                        mime = 'image/jpeg' if ext in ['jpg', 'jpeg'] else f'image/{ext}'
                        img_url = f"data:{mime};base64,{img_data}"
                caption_html = f'<p class="image-caption">{img_caption}</p>' if img_caption else ''
                images_html += f'''
                <div>
                    <img src="{img_url}" alt="图片">
                    {caption_html}
                </div>'''
            images_html += '</div>'
        
        chapters_html += f"""
    <div class="chapter">
        <h2>第{i}章 {chapter.get('title', '回忆')}</h2>
        <p class="date">记录于 {chapter.get('date', '')}</p>
        <div class="content">{chapter.get('content', '').replace(chr(10), '<br>')}</div>
        {images_html}
    </div>
"""
    
    # 生成带预览工具栏的HTML
    preview_html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{user_name}的回忆录-预览</title>
    <style>
        * {{ box-sizing: border-box; margin: 0; padding: 0; }}
        
        /* 预览工具栏 */
        .preview-toolbar {{
            position: fixed;
            top: 0;
            left: 0;
            right: 0;
            background: linear-gradient(135deg, #8B4513 0%, #A0522D 100%);
            padding: 15px 20px;
            display: flex;
            justify-content: center;
            align-items: center;
            gap: 20px;
            z-index: 1000;
            box-shadow: 0 4px 15px rgba(139, 69, 19, 0.3);
        }}
        
        .preview-toolbar h2 {{
            color: white;
            font-size: 20px;
            margin: 0;
        }}
        
        .download-btn {{
            background: linear-gradient(135deg, #2E7D32 0%, #43A047 100%);
            color: white;
            border: none;
            padding: 15px 40px;
            font-size: 20px;
            font-weight: bold;
            border-radius: 10px;
            cursor: pointer;
            min-width: 180px;
            min-height: 50px;
            transition: all 0.3s;
            box-shadow: 0 4px 10px rgba(46, 125, 50, 0.3);
        }}
        
        .download-btn:hover {{
            transform: scale(1.05);
            box-shadow: 0 6px 15px rgba(46, 125, 50, 0.4);
        }}
        
        .download-btn:active {{
            transform: scale(0.98);
        }}
        
        .close-btn {{
            background: rgba(255,255,255,0.2);
            color: white;
            border: 2px solid white;
            padding: 10px 25px;
            font-size: 16px;
            border-radius: 8px;
            cursor: pointer;
            transition: all 0.3s;
        }}
        
        .close-btn:hover {{
            background: rgba(255,255,255,0.3);
        }}
        
        /* 回忆录内容 */
        body {{ 
            font-family: "楷体", KaiTi, serif; 
            line-height: 2; 
            padding: 100px 40px 40px 40px; 
            max-width: 800px; 
            margin: 0 auto; 
            background: linear-gradient(135deg, #FFF8E7 0%, #FFE4C4 100%);
            min-height: 100vh;
        }}
        
        h1 {{ 
            text-align: center; 
            color: #8B4513; 
            border-bottom: 2px solid #DEB887; 
            padding-bottom: 20px; 
            font-size: 32px;
            margin-bottom: 20px;
        }}
        
        h2 {{ 
            color: #A0522D; 
            margin-top: 40px; 
            font-size: 24px;
        }}
        
        .chapter {{ 
            margin: 30px 0; 
            padding: 25px; 
            background: #FFF8DC; 
            border-radius: 15px;
            box-shadow: 0 2px 10px rgba(0,0,0,0.1);
        }}
        
        .date {{ 
            color: #888; 
            font-size: 16px; 
        }}
        
        .content {{ 
            text-indent: 2em; 
            font-size: 18px;
            line-height: 2.2;
        }}
        
        .info {{ 
            text-align: center; 
            color: #666; 
            margin-bottom: 30px; 
            font-size: 16px;
        }}
        
        .chapter-images {{ 
            display: flex; 
            flex-wrap: wrap; 
            gap: 15px; 
            margin-top: 20px; 
            justify-content: center; 
        }}
        
        .chapter-images img {{ 
            max-width: 300px; 
            max-height: 300px; 
            border-radius: 10px; 
            border: 2px solid #DEB887; 
        }}
        
        .image-caption {{ 
            text-align: center; 
            font-size: 14px; 
            color: #666; 
            margin-top: 5px; 
        }}
        
        .footer {{
            text-align: center; 
            margin-top: 50px; 
            color: #888;
            font-size: 16px;
        }}
        
        /* 放大镜功能 */
        .magnifier-toggle {{
            position: fixed;
            bottom: 30px;
            right: 30px;
            width: 56px;
            height: 56px;
            border-radius: 50%;
            background: linear-gradient(135deg, #8B4513 0%, #A0522D 100%);
            border: 3px solid #FFF8E7;
            box-shadow: 0 4px 15px rgba(139, 69, 19, 0.4);
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: center;
            font-size: 28px;
            color: white;
            z-index: 9998;
            transition: all 0.3s ease;
        }}
        
        .magnifier-toggle:hover {{ transform: scale(1.1); }}
        .magnifier-toggle:active {{ transform: scale(0.95); }}
        .magnifier-toggle.active {{ background: linear-gradient(135deg, #2E7D32 0%, #43A047 100%); }}
        
        .magnifier-lens {{
            position: fixed;
            width: 180px;
            height: 180px;
            border-radius: 50%;
            border: 4px solid #8B4513;
            box-shadow: 0 0 20px rgba(0, 0, 0, 0.3);
            overflow: hidden;
            pointer-events: none;
            z-index: 9999;
            display: none;
            background: white;
        }}
        
        .magnifier-lens.active {{ display: block; }}
        
        .magnifier-zoom-indicator {{
            position: fixed;
            bottom: 100px;
            right: 30px;
            background: rgba(139, 69, 19, 0.9);
            color: white;
            padding: 8px 16px;
            border-radius: 20px;
            font-size: 20px;
            font-weight: bold;
            z-index: 9998;
            display: none;
        }}
        
        .magnifier-zoom-indicator.active {{ display: block; }}
        
        /* 打印样式 */
        @media print {{
            .preview-toolbar, .magnifier-toggle, .magnifier-lens, .magnifier-zoom-indicator {{
                display: none !important;
            }}
            body {{
                padding: 20px;
                background: white;
            }}
        }}
    </style>
</head>
<body>
    <!-- 预览工具栏 -->
    <div class="preview-toolbar">
        <h2>回忆录预览</h2>
        <button class="download-btn" onclick="downloadMemoir()">&#128190; 下载回忆录</button>
        <button class="close-btn" onclick="window.close()">关闭预览</button>
    </div>
    
    <!-- 放大镜 -->
    <div class="magnifier-toggle" onclick="toggleMagnifier()">&#128269;</div>
    <div class="magnifier-lens" id="magnifierLens"></div>
    <div class="magnifier-zoom-indicator" id="magnifierZoom">2.0倍</div>
    
    <!-- 回忆录内容 -->
    <h1>{user_name}的回忆录</h1>
    <p class="info">
        {f"出生年份：{user_info.get('birth_year')}" if user_info.get('birth_year') else ""}
        {f" | 故乡：{user_info.get('hometown')}" if user_info.get('hometown') else ""}
    </p>
    
    {chapters_html}
    
    <p class="footer">—— 回忆是生命中最珍贵的礼物 ——</p>
    
    <script>
        // 下载回忆录
        function downloadMemoir() {{
            window.location.href = '/api/export';
        }}
        
        // 放大镜功能
        let magnifierActive = false;
        let magnifierZoom = 2.0;
        let magnifierX = 0, magnifierY = 0;
        let isDragging = false;
        let pageSnapshot = null;
        
        function toggleMagnifier() {{
            const toggle = document.querySelector('.magnifier-toggle');
            const lens = document.getElementById('magnifierLens');
            const zoomIndicator = document.getElementById('magnifierZoom');
            
            magnifierActive = !magnifierActive;
            
            if (magnifierActive) {{
                toggle.classList.add('active');
                lens.classList.add('active');
                zoomIndicator.classList.add('active');
                createPageSnapshot();
                magnifierX = window.innerWidth / 2;
                magnifierY = window.innerHeight / 2;
                updateMagnifierPosition();
                
                document.addEventListener('mousemove', onMove);
                document.addEventListener('mousedown', onDragStart);
                document.addEventListener('mouseup', onDragEnd);
                document.addEventListener('wheel', onWheel, {{ passive: false }});
                document.addEventListener('touchmove', onTouchMove, {{ passive: false }});
                document.addEventListener('touchstart', onTouchStart, {{ passive: false }});
                document.addEventListener('touchend', onDragEnd);
            }} else {{
                closeMagnifier();
            }}
        }}
        
        function closeMagnifier() {{
            const toggle = document.querySelector('.magnifier-toggle');
            const lens = document.getElementById('magnifierLens');
            const zoomIndicator = document.getElementById('magnifierZoom');
            
            magnifierActive = false;
            toggle.classList.remove('active');
            lens.classList.remove('active');
            zoomIndicator.classList.remove('active');
            lens.innerHTML = '';
            pageSnapshot = null;
            
            document.removeEventListener('mousemove', onMove);
            document.removeEventListener('mousedown', onDragStart);
            document.removeEventListener('mouseup', onDragEnd);
            document.removeEventListener('wheel', onWheel);
            document.removeEventListener('touchmove', onTouchMove);
            document.removeEventListener('touchstart', onTouchStart);
            document.removeEventListener('touchend', onDragEnd);
        }}
        
        function createPageSnapshot() {{
            const lens = document.getElementById('magnifierLens');
            lens.innerHTML = '';
            const container = document.createElement('div');
            container.id = 'snapshot';
            container.style.cssText = `position:absolute;top:0;left:0;width:${{document.documentElement.scrollWidth}}px;height:${{document.documentElement.scrollHeight}}px;transform-origin:0 0;pointer-events:none;`;
            
            // 克隆整个 body 内容
            const content = document.body.cloneNode(true);
            // 移除放大镜相关元素
            content.querySelectorAll('.preview-toolbar,.magnifier-toggle,.magnifier-lens,.magnifier-zoom-indicator').forEach(el => el.remove());
            
            // 计算原页面内容的居中偏移
            const bodyStyle = window.getComputedStyle(document.body);
            const maxWidth = parseInt(bodyStyle.maxWidth) || document.documentElement.scrollWidth;
            const marginLeft = (document.documentElement.clientWidth - Math.min(maxWidth, document.documentElement.clientWidth)) / 2;
            
            // 保持与原页面完全相同的布局位置
            content.style.cssText = `position:absolute;left:${{marginLeft}}px;top:0;width:${{maxWidth}}px;max-width:${{maxWidth}}px;margin:0;`;
            container.appendChild(content);
            pageSnapshot = container;
            lens.appendChild(container);
        }}
        
        function onMove(e) {{
            if (isDragging) {{
                magnifierX = e.clientX;
                magnifierY = e.clientY;
                updateMagnifierPosition();
            }}
        }}
        
        function onDragStart(e) {{
            if (e.target.closest('.magnifier-toggle,.download-btn,.close-btn')) return;
            isDragging = true;
            magnifierX = e.clientX;
            magnifierY = e.clientY;
            updateMagnifierPosition();
        }}
        
        function onDragEnd() {{ isDragging = false; }}
        
        function onWheel(e) {{
            if (!magnifierActive) return;
            const lens = document.getElementById('magnifierLens');
            const rect = lens.getBoundingClientRect();
            if (e.clientX >= rect.left && e.clientX <= rect.right && e.clientY >= rect.top && e.clientY <= rect.bottom) {{
                e.preventDefault();
                magnifierZoom = e.deltaY < 0 ? Math.min(3.0, magnifierZoom + 0.2) : Math.max(1.2, magnifierZoom - 0.2);
                document.getElementById('magnifierZoom').textContent = magnifierZoom.toFixed(1) + '倍';
                updateMagnifierPosition();
            }}
        }}
        
        function onTouchStart(e) {{
            if (e.target.closest('.magnifier-toggle')) return;
            if (e.touches.length === 1) {{
                isDragging = true;
                magnifierX = e.touches[0].clientX;
                magnifierY = e.touches[0].clientY;
                updateMagnifierPosition();
            }}
        }}
        
        function onTouchMove(e) {{
            if (!magnifierActive || !isDragging) return;
            e.preventDefault();
            if (e.touches.length === 1) {{
                magnifierX = e.touches[0].clientX;
                magnifierY = e.touches[0].clientY;
                updateMagnifierPosition();
            }}
        }}
        
        function updateMagnifierPosition() {{
            const lens = document.getElementById('magnifierLens');
            const halfLens = 90;
            lens.style.left = (magnifierX - halfLens) + 'px';
            lens.style.top = (magnifierY - halfLens) + 'px';
            
            if (pageSnapshot) {{
                const scrollX = window.scrollX, scrollY = window.scrollY;
                // 计算偏移使鼠标位置出现在放大镜中心
                const pageX = magnifierX + scrollX;
                const pageY = magnifierY + scrollY;
                const offsetX = halfLens / magnifierZoom - pageX;
                const offsetY = halfLens / magnifierZoom - pageY;
                pageSnapshot.style.transform = `scale(${{magnifierZoom}}) translate(${{offsetX}}px, ${{offsetY}}px)`;
            }}
        }}
        
        window.addEventListener('scroll', function() {{
            if (magnifierActive) updateMagnifierPosition();
        }});
    </script>
</body>
</html>"""
    
    return preview_html, 200, {'Content-Type': 'text/html; charset=utf-8'}

# ==================== 角色人设定义 ====================

PERSONA_PROMPTS = {
    'granddaughter': {
        'name': '小甜甜',
        'description': '10岁的刁蛮孙女',
        'system_prompt': """你是一个10岁的小女孩"小甜甜"，是用户（爷爷/奶奶）的孙女。你性格活泼、有点刁蛮任性但很可爱，对爷爷奶奶的故事充满好奇。

角色要求：
1. 用小孩子的语气说话，会撒娇、会好奇地追问，偶尔会耍小脾气
2. 说话简短、口语化，会用"哇""好厉害""然后呢然后呢"这样的语气词
3. 会叫用户"爷爷"或"奶奶"（根据上下文判断）
4. 对过去的事情充满好奇，会问一些天真的问题，比如"那时候真的没有手机吗？""那你们怎么玩呢？"
5. 有时候会联系自己的生活来对比，比如"我们学校可不是这样的！"
6. 偶尔会有些小脾气，"爷爷你怎么不早点告诉我这个故事呀！"
7. 核心目的是通过童真的好奇心引导老人讲述更多回忆
8. 回复要简短（2-4句话），符合小孩子的表达习惯""",
    },
    'young_adult': {
        'name': '小明',
        'description': '初入社会迷茫的20岁青年',
        'system_prompt': """你是一个20岁刚大学毕业的年轻人"小明"，初入社会感到迷茫，很渴望从长辈那里获得人生经验和智慧。

角色要求：
1. 用年轻人的语气说话，礼貌但有时带点焦虑和困惑
2. 会向长辈请教人生经验，"您当年是怎么应对的？""您觉得我该怎么办？"
3. 称呼用户为"爷爷""奶奶"或"叔叔""阿姨"（根据上下文）
4. 会分享自己的困惑来引出话题，比如"我现在找工作特别迷茫，您年轻时第一份工作是怎么找的？"
5. 对长辈的经历表达真诚的敬佩，"哇，那时候真不容易""您真厉害"
6. 会追问细节和感受，"当时心里是什么感觉？""后来怎么样了？"
7. 核心目的是通过年轻人求教的方式，让老人以过来人的身份分享经历和智慧
8. 回复适中（2-5句话），真诚、有感情""",
    },
    'old_friend': {
        'name': '老李',
        'description': '多年老友',
        'system_prompt': """你是用户的多年老朋友"老李"，你们是同龄人，年轻时就认识了。你们之间的对话轻松、随意，像老朋友喝茶聊天一样。

角色要求：
1. 用同辈的语气说话，亲切但随意，可以开玩笑
2. 称呼用户"老伙计""老朋友"或直接用"你"
3. 会分享"自己"的类似经历来引出对方的回忆，比如"我记得那会儿我们那条街上...你们那边呢？"
4. 说话带有怀旧的感觉，"哎，那时候的日子啊...""想想都过去几十年了"
5. 会共情和附和，"可不是嘛""谁说不是呢""我也是这么觉得"
6. 偶尔会有善意的调侃，"你这记性还挺好啊""你可别忽悠我"
7. 核心目的是通过老朋友闲聊的方式，在轻松氛围中引导老人回忆往事
8. 回复自然随意（2-5句话），像聊天一样口语化""",
    },
    'grandson': {
        'name': '小虎',
        'description': '15岁阳光大男孩',
        'system_prompt': """你是一个15岁的中学男孩"小虎"，是用户（爷爷/奶奶）的孙子。你性格阳光、热血，对历史和英雄故事特别感兴趣。

角色要求：
1. 用少年的语气说话，热情、直接，有时带点中二
2. 会叫用户"爷爷"或"奶奶"，语气亲热但不撒娇
3. 特别喜欢听"当年的壮举"，比如"爷爷你们那时候真的要自己盖房子？太酷了吧！"
4. 会用现代年轻人的比喻来理解过去的事，"那不就相当于现在的...""这也太硬核了"
5. 会主动提问细节，"具体怎么做的？""后来成功了吗？"
6. 有时会表达崇拜，"爷爷你也太厉害了""这比电视剧还精彩"
7. 核心目的是用少年的热血和崇拜引导老人讲述人生中自豪的经历
8. 回复简洁有力（2-4句话），充满活力""",
    },
    'daughter': {
        'name': '小芳',
        'description': '贴心的中年女儿',
        'system_prompt': """你是一位45岁的中年女性"小芳"，是用户（爸爸/妈妈）的女儿。你是一位母亲，也在照顾着自己的父母，对父母的过去充满温情。

角色要求：
1. 用女儿的语气说话，温柔体贴，带着心疼和感恩
2. 称呼用户"爸""妈"，偶尔会说"老爸""老妈"
3. 会从自己为人父母的角度出发来理解长辈，"我现在当了妈才知道当年您有多不容易"
4. 会关心情感层面，"那时候您心里难受吗？""您当时有没有想放弃过？"
5. 会提起家里的旧事引发回忆，"我记得小时候家里那个老柜子...""咱家以前那张全家福..."
6. 偶尔表达遗憾，"我要是早点问就好了""怎么以前没听您说过"
7. 核心目的是以女儿的身份，用亲情的温度引导父母回忆家庭故事
8. 回复温暖有感情（3-5句话），细腻而真诚""",
    },
    'reporter': {
        'name': '小周',
        'description': '热心的社区记者',
        'system_prompt': """你是一位30岁的社区报记者"小周"，正在做一期"身边的故事"专题报道，想记录普通人的精彩人生。

角色要求：
1. 用记者的语气说话，专业但亲和，善于引导对方展开叙述
2. 称呼用户"叔叔""阿姨"或"大爷""大妈"
3. 会先夸赞再提问，"您的经历真的很特别""这段故事太有意思了，能详细说说吗？"
4. 善于追问具体的时间、地点、人物、细节，"那是哪一年的事？""当时周围的人怎么看？"
5. 会帮助用户理清时间线，"所以是先...然后又...对吗？"
6. 偶尔会表达社会意义，"这段历史应该被更多人知道""现在的年轻人都不了解这些了"
7. 核心目的是以采访的方式，系统地引导老人回忆并讲述完整的人生故事
8. 回复清晰有条理（3-5句话），兼具专业性和亲和力""",
    },
    'neighbor': {
        'name': '王大姐',
        'description': '热情的邻居大姐',
        'system_prompt': """你是一位55岁的邻居"王大姐"，性格热情爽朗，是小区里有名的热心肠。你最喜欢串门聊天，特别喜欢听别人的故事。

角色要求：
1. 说话热情、爽快，带着浓浓的市井生活气息
2. 称呼用户"老姐姐""老哥""老妹儿"等邻里之间的称呼
3. 会用自己的见闻来接话，"哎呀你可别说了，我家那口子当年也是...""我听谁谁谁也说过类似的"
4. 爱感叹，"哎呀真是""你说巧不巧""这事儿要搁现在都没人信"
5. 会八卦但是善意的，对故事细节特别感兴趣，"然后呢？""他怎么说的？""最后怎么着了？"
6. 经常感慨人生，"这人啊一辈子""日子过得真快""还是以前的人实在"
7. 核心目的是用邻里闲聊的轻松氛围引导老人自然地分享日常故事
8. 回复生活化（2-5句话），语言接地气、有烟火味""",
    },
    'teacher': {
        'name': '陈老师',
        'description': '退休历史教师',
        'system_prompt': """你是一位65岁的退休历史教师"陈老师"，你热爱历史，更重视普通人的口述历史。你认为每个人的人生都是一部独特的历史。

角色要求：
1. 说话沉稳、有学识，但不居高临下，尊重每一段经历
2. 称呼用户"老同志""老师傅"或"您"
3. 善于将个人经历与时代背景联系起来，"那时候正好赶上...""那个年代的人都不容易"
4. 会帮助用户认识到自己经历的价值，"您说的这些就是活历史""这段经历非常珍贵"
5. 会从宏观角度引导，"那个时代的生活和现在比，您觉得最大的区别是什么？"
6. 偶尔补充历史背景帮助回忆，"那大概是七几年的事？""那时候应该刚改革开放吧"
7. 核心目的是用口述历史的方式，赋予老人的回忆时代意义和历史价值
8. 回复有深度但通俗（3-5句话），温和而有引导性""",
    },
    'default': {
        'name': '回忆录助手',
        'description': '温柔耐心的AI助手',
        'system_prompt': """你是一位温柔、耐心的回忆录助手，正在帮助一位老人记录他/她的人生故事。
你的任务是通过温和的对话，引导老人回忆过去的美好时光。

对话原则：
1. 语气要温柔、亲切，像晚辈和长辈聊天
2. 多用鼓励性的语言，让老人感到被尊重和理解
3. 适时提出引导性的问题，帮助老人展开回忆
4. 如果老人提到了某个话题，要表现出兴趣并追问细节
5. 回复要简短、易懂，适合老年人阅读""",
    },
}

@app.route('/api/chat', methods=['POST'])
def chat():
    """AI陪聊功能 - 引导用户回忆（支持角色人设）"""
    try:
        data = request.json
        message = data.get('message', '')
        mode = data.get('mode', 'elder')
        persona = data.get('persona', 'default')
        
        client = OpenAI(
            base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
            api_key=DASHSCOPE_API_KEY
        )
        
        # 获取角色人设
        persona_config = PERSONA_PROMPTS.get(persona, PERSONA_PROMPTS['default'])
        system_prompt = persona_config['system_prompt']
        
        prompt = f"""{system_prompt}

用户说：{message}

请按照你的角色设定回复，并尝试引导用户分享更多回忆："""

        response = client.chat.completions.create(
            model='qwen-plus',
            messages=[{
                'role': 'user',
                'content': [{'type': 'text', 'text': prompt}]
            }],
            stream=False
        )
        
        result = response.choices[0].message.content
        # 清理可能的思考过程标记
        if "<think>" in result:
            result = result.split("</think>")[-1].strip()
        
        return jsonify({'success': True, 'reply': result})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/personas', methods=['GET'])
def get_personas():
    """获取可用的角色人设列表"""
    personas = []
    for pid, pdata in PERSONA_PROMPTS.items():
        personas.append({
            'id': pid,
            'name': pdata['name'],
            'description': pdata['description'],
        })
    return jsonify({'personas': personas})

@app.route('/api/suggest_topics', methods=['GET'])
def suggest_topics():
    """推荐回忆话题（根据角色人设调整语气）"""
    mode = request.args.get('mode', 'elder')
    persona = request.args.get('persona', 'default')
    
    if persona == 'granddaughter':
        topics = [
            {"title": "童年游戏", "prompt": "爷爷/奶奶，你们小时候都玩什么呀？有没有像我玩的那种游戏？"},
            {"title": "上学趣事", "prompt": "爷爷/奶奶，你们上学的时候老师凶不凶呀？会不会罚站？"},
            {"title": "好吃的东西", "prompt": "爷爷/奶奶，你们小时候有什么好吃的零食呀？我最喜欢吃冰淇淋！"},
            {"title": "过年故事", "prompt": "爷爷/奶奶，你们小时候过年是不是特别热闹？有没有放很多烟花？"},
            {"title": "害怕的事", "prompt": "爷爷/奶奶，你小时候有没有害怕的东西呀？我可勇敢了！"},
        ]
    elif persona == 'young_adult':
        topics = [
            {"title": "第一份工作", "prompt": "爷爷/奶奶，您年轻时第一份工作是做什么的？我现在找工作好迷茫啊..."},
            {"title": "人生选择", "prompt": "爷爷/奶奶，您人生中做过最重要的决定是什么？后来有没有后悔过？"},
            {"title": "克服困难", "prompt": "爷爷/奶奶，您遇到过最大的困难是什么？是怎么挺过来的？"},
            {"title": "恋爱建议", "prompt": "爷爷/奶奶，您和爱人是怎么认识的？现在的年轻人谈恋爱和以前有什么不同吗？"},
            {"title": "生活智慧", "prompt": "爷爷/奶奶，如果给20岁的自己一个建议，您会说什么？"},
        ]
    elif persona == 'old_friend':
        topics = [
            {"title": "当年旧事", "prompt": "老伙计，还记得咱们年轻那会儿吗？那时候日子过得可真不一样啊..."},
            {"title": "工作往事", "prompt": "哎，说起来你当年那份工作怎么样？我记得那会儿大家都挺拼的。"},
            {"title": "家乡味道", "prompt": "老朋友，你还记得咱们那边以前过年都吃什么吗？我最近老是想起那个味道。"},
            {"title": "养儿育女", "prompt": "你家孩子现在怎么样了？想当初带孩子那会儿，可真不容易啊。"},
            {"title": "岁月感悟", "prompt": "老伙计，这辈子过得真快啊，你觉得这一生最值得的是什么？"},
        ]
    elif persona == 'grandson':
        topics = [
            {"title": "英雄事迹", "prompt": "爷爷，您年轻的时候有没有做过什么特别厉害的事？比如见义勇为什么的！"},
            {"title": "技术变迁", "prompt": "爷爷，你们那时候没有电脑也没有手机，那平时都怎么联系人啊？太不可思议了！"},
            {"title": "体育运动", "prompt": "爷爷，您年轻时候爱运动吗？有没有什么拿手的运动项目？"},
            {"title": "盖房建设", "prompt": "爷爷，听说你们那时候房子都是自己盖的？真的假的？太硬核了吧！"},
            {"title": "难忘冒险", "prompt": "爷爷，您人生中有没有什么特别惊险刺激的经历？给我讲讲呗！"},
        ]
    elif persona == 'daughter':
        topics = [
            {"title": "养育之恩", "prompt": "妈/爸，我小时候你们带我是不是特别辛苦？我现在带孩子才体会到..."},
            {"title": "家庭往事", "prompt": "妈/爸，我记得咱家以前那个老房子，您还记得搬进去时候的事吗？"},
            {"title": "爱情故事", "prompt": "妈/爸，您和爸/妈当初是怎么走到一起的？我好像从来没认真听你们讲过。"},
            {"title": "困难时期", "prompt": "妈/爸，你们那时候经济条件不好，是怎么把我们几个拉扯大的？"},
            {"title": "年轻梦想", "prompt": "妈/爸，您年轻时候有什么梦想吗？后来实现了吗？"},
        ]
    elif persona == 'reporter':
        topics = [
            {"title": "人生转折", "prompt": "请问您人生中最大的转折点是什么时候？当时发生了什么事？"},
            {"title": "时代见证", "prompt": "您经历过哪些大的社会变化？当时身边的人都是什么反应？"},
            {"title": "职业生涯", "prompt": "您从事的这份职业有什么特别之处？能给我们读者讲讲最难忘的一件事吗？"},
            {"title": "家乡故事", "prompt": "您的家乡这些年变化大吗？能描述一下您小时候家乡的样子吗？"},
            {"title": "人生金句", "prompt": "如果用一句话总结您的人生感悟，您会说什么？"},
        ]
    elif persona == 'neighbor':
        topics = [
            {"title": "家常里短", "prompt": "哎老姐姐/老哥，你们家以前住哪个片区的？我听说那边以前可热闹了！"},
            {"title": "拿手好菜", "prompt": "说起做饭，我可佩服你了！你那拿手菜是跟谁学的？给我说说呗。"},
            {"title": "赶集逛街", "prompt": "你还记得以前赶集是什么样吗？现在的超市可比不了那个热闹劲儿！"},
            {"title": "邻里旧事", "prompt": "你还记得以前的老邻居们吗？那时候邻里之间真是比现在亲多了。"},
            {"title": "带孩子", "prompt": "你家那几个孩子小时候淘不淘？我家那个可把我折腾够呛！"},
        ]
    elif persona == 'teacher':
        topics = [
            {"title": "求学年代", "prompt": "您上学时候的学校是什么样的？那时候的教育和现在有什么不同？"},
            {"title": "时代洪流", "prompt": "您经历过的最大的社会变革是什么？它对您的生活产生了什么影响？"},
            {"title": "手艺传承", "prompt": "您有什么特别的手艺或技能吗？是怎么学会的？现在还有人会吗？"},
            {"title": "乡土文化", "prompt": "您记忆中家乡有哪些独特的风俗习惯？现在还保留着吗？"},
            {"title": "人生哲学", "prompt": "经历了这么多年的风风雨雨，您对人生最大的感悟是什么？"},
        ]
    else:
        topics = [
            {"title": "童年趣事", "prompt": "您小时候最喜欢玩什么游戏？有什么有趣的童年回忆吗？"},
            {"title": "求学时光", "prompt": "您上学的时候是什么样的？还记得您的老师和同学吗？"},
            {"title": "初入社会", "prompt": "您第一份工作是什么？当时是怎么找到这份工作的？"},
            {"title": "爱情故事", "prompt": "您和爱人是怎么认识的？能分享一下你们的故事吗？"},
            {"title": "为人父母", "prompt": "您的孩子小时候是什么样的？有什么难忘的育儿经历吗？"},
            {"title": "人生智慧", "prompt": "回顾这一生，您觉得最重要的人生经验是什么？"},
            {"title": "难忘的人", "prompt": "在您的人生中，有哪些人对您影响最大？"},
            {"title": "故乡记忆", "prompt": "您的家乡是什么样的？有什么特别的风俗或美食吗？"},
            {"title": "节日回忆", "prompt": "您印象最深的一个春节或节日是哪一个？"},
            {"title": "生活变迁", "prompt": "这些年来，您觉得生活最大的变化是什么？"}
        ]
    return jsonify({'topics': topics})

@app.route('/api/tts', methods=['POST'])
def text_to_speech():
    """文字转语音接口"""
    try:
        data = request.json
        text = data.get('text', '')
        persona = data.get('persona', '')
        
        if not text:
            return jsonify({'success': False, 'error': '请提供要转换的文字'})
        
        # 限制文字长度，避免过长
        if len(text) > 2000:
            text = text[:2000] + "..."
        
        # 根据人设选择对应音色
        persona_voice_map = {
            'granddaughter': 'longhuhu_v3',     # 天真烂漫女童 6~10岁 → 小甜甜(10岁孙女)
            'grandson':      'longniuniu_v3',    # 阳光男童声 6~15岁 → 小虎(15岁少年)
            'young_adult':   'longcheng_v3',     # 智慧青年男 20~25岁 → 小明(20岁)
            'daughter':      'longyuan_v3',      # 温暖治愈女 35~40岁 → 小芳(45岁女儿)
            'old_friend':    'longlaobo_v3',     # 沧桑岁月爷 60岁以上 → 老李(老友)
            'neighbor':      'longanran_v3',     # 活泼质感女 30~40岁 → 王大姐(热情邻居)
            'reporter':      'longshuo_v3',      # 博才干练男 25~30岁 → 小周(社区记者)
            'teacher':       'longxiu_v3',       # 博才说书男 25~35岁 → 陈老师(退休教师)
            'default':       'longanyang',       # 阳光大男孩 20~30岁 → 回忆录助手
        }
        voice = persona_voice_map.get(persona, 'longanyang')
        
        # 生成唯一的音频文件名
        audio_id = str(uuid.uuid4())
        audio_path = os.path.join(AUDIO_FOLDER, f'{audio_id}.mp3')
        
        # 使用CosyVoice合成语音
        synthesizer = SpeechSynthesizer(
            model="cosyvoice-v3-flash",
            voice=voice
        )
        audio = synthesizer.call(text)
        
        # 保存音频文件
        with open(audio_path, 'wb') as f:
            f.write(audio)
        
        return jsonify({
            'success': True, 
            'audio_url': f'/api/audio/{audio_id}.mp3'
        })
    except Exception as e:
        print(f"语音合成错误: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/audio/<filename>')
def serve_audio(filename):
    """提供音频文件"""
    return send_file(
        os.path.join(AUDIO_FOLDER, filename),
        mimetype='audio/mpeg'
    )

@app.route('/api/upload_image', methods=['POST'])
def upload_image():
    """上传图片接口"""
    try:
        if 'image' not in request.files:
            return jsonify({'success': False, 'error': '请选择图片'})
        
        file = request.files['image']
        if file.filename == '':
            return jsonify({'success': False, 'error': '请选择图片'})
        
        # 检查文件类型
        allowed_extensions = {'png', 'jpg', 'jpeg', 'gif', 'webp'}
        ext = file.filename.rsplit('.', 1)[-1].lower() if '.' in file.filename else ''
        if ext not in allowed_extensions:
            return jsonify({'success': False, 'error': '不支持的图片格式'})
        
        # 生成唯一文件名
        image_id = str(uuid.uuid4())
        filename = f'{image_id}.{ext}'
        filepath = os.path.join(IMAGE_FOLDER, filename)
        
        # 保存图片
        file.save(filepath)
        
        return jsonify({
            'success': True,
            'image_id': image_id,
            'image_url': f'/api/images/{filename}'
        })
    except Exception as e:
        print(f"图片上传错误: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/images/<filename>')
def serve_image(filename):
    """提供图片文件"""
    return send_file(
        os.path.join(IMAGE_FOLDER, filename),
        mimetype='image/jpeg'
    )

@app.route('/api/suggest_image_position', methods=['POST'])
def suggest_image_position():
    """AI分析文字内容，建议图片插入位置"""
    try:
        data = request.json
        text = data.get('text', '')
        image_descriptions = data.get('image_descriptions', [])  # 图片描述列表
        
        if not text:
            return jsonify({'success': False, 'error': '请提供文字内容'})
        
        if not image_descriptions:
            return jsonify({'success': False, 'error': '请提供图片描述'})
        
        client = OpenAI(
            base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
            api_key=DASHSCOPE_API_KEY
        )
        
        prompt = f"""你是一位回忆录编辑助手。请分析以下文字内容，为每张图片建议最合适的插入位置。

文字内容：
{text}

待插入的图片：
{chr(10).join([f'{i+1}. {desc}' for i, desc in enumerate(image_descriptions)])}

请为每张图片指出：
1. 应该插入在哪段文字之后（引用具体的句子片段）
2. 简短说明为什么这个位置合适

请用JSON格式返回，格式如下：
[
  {{"image_index": 1, "insert_after": "具体句子片段", "reason": "原因说明"}},
  ...
]

只返回JSON，不要其他内容："""

        response = client.chat.completions.create(
            model='qwen-plus',
            messages=[{
                'role': 'user',
                'content': [{'type': 'text', 'text': prompt}]
            }],
            stream=False
        )
        
        result = response.choices[0].message.content
        # 清理思考过程标记
        if "<think>" in result:
            result = result.split("</think>")[-1].strip()
        
        # 尝试解析JSON
        import re
        json_match = re.search(r'\[.*\]', result, re.DOTALL)
        if json_match:
            suggestions = json.loads(json_match.group())
            return jsonify({'success': True, 'suggestions': suggestions})
        else:
            return jsonify({'success': False, 'error': '无法解析AI建议'})
    except Exception as e:
        print(f"图片位置建议错误: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/describe_image', methods=['POST'])
def describe_image():
    """使用多模态模型描述图片内容"""
    try:
        data = request.json
        image_url = data.get('image_url', '')
        
        if not image_url:
            return jsonify({'success': False, 'error': '请提供图片URL'})
        
        # 读取图片并转为base64
        if image_url.startswith('/api/images/'):
            filename = image_url.split('/')[-1]
            filepath = os.path.join(IMAGE_FOLDER, filename)
            with open(filepath, 'rb') as f:
                image_data = base64.b64encode(f.read()).decode('utf-8')
            image_url = f"data:image/jpeg;base64,{image_data}"
        
        client = OpenAI(
            base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
            api_key=DASHSCOPE_API_KEY
        )
        
        response = client.chat.completions.create(
            model='qwen-vl-plus',
            messages=[{
                'role': 'user',
                'content': [
                    {'type': 'text', 'text': '请简要描述这张图片的内容，用一两句话概括主要元素和场景。'},
                    {'type': 'image_url', 'image_url': {'url': image_url}}
                ]
            }],
            stream=False
        )
        
        result = response.choices[0].message.content
        if "<think>" in result:
            result = result.split("</think>")[-1].strip()
        
        return jsonify({'success': True, 'description': result})
    except Exception as e:
        print(f"图片描述错误: {e}")
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chapters/<chapter_id>/tags', methods=['POST'])
def add_tag(chapter_id):
    """为章节添加标签"""
    try:
        data = request.json
        tag = data.get('tag', '').strip()
        
        if not tag:
            return jsonify({'success': False, 'error': '标签不能为空'})
        
        memoir = load_memoir()
        
        for chapter in memoir['chapters']:
            if chapter['id'] == chapter_id:
                if 'tags' not in chapter:
                    chapter['tags'] = []
                if tag not in chapter['tags']:
                    chapter['tags'].append(tag)
                    save_memoir(memoir)
                return jsonify({'success': True, 'tags': chapter['tags']})
        
        return jsonify({'success': False, 'error': '章节不存在'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/chapters/<chapter_id>/tags/<tag>', methods=['DELETE'])
def remove_tag(chapter_id, tag):
    """移除章节标签"""
    try:
        memoir = load_memoir()
        
        for chapter in memoir['chapters']:
            if chapter['id'] == chapter_id:
                if 'tags' in chapter and tag in chapter['tags']:
                    chapter['tags'].remove(tag)
                    save_memoir(memoir)
                return jsonify({'success': True, 'tags': chapter.get('tags', [])})
        
        return jsonify({'success': False, 'error': '章节不存在'})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})

@app.route('/api/all_tags', methods=['GET'])
def get_all_tags():
    """获取所有已使用的标签"""
    memoir = load_memoir()
    all_tags = set()
    for chapter in memoir.get('chapters', []):
        for tag in chapter.get('tags', []):
            all_tags.add(tag)
    return jsonify({'tags': list(all_tags)})

@app.route('/api/timeline', methods=['GET'])
def generate_timeline():
    """生成大事年表"""
    try:
        memoir = load_memoir()
        chapters = memoir.get('chapters', [])
        
        if not chapters:
            return jsonify({'success': True, 'timeline': [], 'message': '暂无内容'})
        
        # 合并所有章节内容
        all_content = "\n\n".join([
            f"【{c.get('title', '未命名')}】（记录于{c.get('date', '')}）\n{c.get('content', '')}"
            for c in chapters
        ])
        
        client = OpenAI(
            base_url='https://dashscope.aliyuncs.com/compatible-mode/v1',
            api_key=DASHSCOPE_API_KEY
        )
        
        prompt = f"""你是一位回忆录整理助手。请仔细阅读以下回忆录内容，从中提取出重要的人生事件和时间节点，整理成一张大事年表。

回忆录内容：
{all_content}

请按照时间顺序整理，提取出：
1. 具体年份或时间段（如"1950年"、"60年代初"、"小学时期"等）
2. 重要事件（如出生、上学、工作、结婚、生子、退休等）
3. 简短描述（一两句话概括）

请用JSON数组格式返回，格式如下：
[
  {{"year": "年份或时间段", "event": "事件名称", "description": "简短描述"}},
  ...
]

注意：
- 如果内容中没有明确提到时间，可以根据上下文推断大致时期
- 如果完全无法确定时间，使用"不详"
- 按时间先后顺序排列
- 只返回JSON数组，不要其他内容"""

        response = client.chat.completions.create(
            model='qwen-plus',
            messages=[{
                'role': 'user',
                'content': [{'type': 'text', 'text': prompt}]
            }],
            stream=False
        )
        
        result = response.choices[0].message.content
        # 清理思考过程标记
        if "<think>" in result:
            result = result.split("</think>")[-1].strip()
        
        # 尝试解析JSON
        import re
        json_match = re.search(r'\[.*\]', result, re.DOTALL)
        if json_match:
            timeline = json.loads(json_match.group())
            return jsonify({'success': True, 'timeline': timeline})
        else:
            return jsonify({'success': False, 'error': '无法解析年表数据'})
    except Exception as e:
        print(f"生成年表错误: {e}")
        return jsonify({'success': False, 'error': str(e)})

# ==================== 形象预测 ====================

@app.route('/api/age_predict', methods=['POST'])
def age_predict():
    """形象预测 - 根据照片预测不同年龄的形象（使用 qwen-image-edit-plus 图生图）"""
    try:
        data = request.json
        image_url = data.get('image_url', '')
        current_age = int(data.get('current_age', 25))
        target_age = int(data.get('target_age', 50))

        if not image_url:
            return jsonify({'success': False, 'error': '请提供图片'})

        # 将本地图片转为 base64（DashScope 需要公网URL或base64）
        if image_url.startswith('/api/images/'):
            filename = image_url.split('/')[-1]
            filepath = os.path.join(IMAGE_FOLDER, filename)
            if not os.path.exists(filepath):
                return jsonify({'success': False, 'error': '图片不存在'})
            with open(filepath, 'rb') as f:
                img_data = base64.b64encode(f.read()).decode('utf-8')
            ext = filename.rsplit('.', 1)[-1].lower()
            mime = 'image/jpeg' if ext in ('jpg', 'jpeg') else f'image/{ext}'
            image_input = f"data:{mime};base64,{img_data}"
        else:
            image_input = image_url

        # 如果目标年龄和当前年龄一样，直接返回原图
        if target_age == current_age:
            return jsonify({
                'success': True,
                'image_url': image_url,
                'target_age': target_age
            })

        # 构建年龄变换提示词
        if target_age < current_age:
            prompt = (
                f"将照片中的人物变为{target_age}岁时的样子。"
                f"照片中的人物当前约{current_age}岁。要求："
                f"保持人物的五官特征（眼睛、鼻子、嘴巴的形状和比例）完全不变，"
                f"自然地将面容恢复到{target_age}岁的年轻状态，"
                f"皮肤更加光滑紧致，减少皱纹，头发更浓密颜色更深。"
                f"保持相同的背景环境，保持真实照片风格。"
            )
        else:
            prompt = (
                f"将照片中的人物变为{target_age}岁时的样子。"
                f"照片中的人物当前约{current_age}岁。要求："
                f"保持人物的五官特征（眼睛、鼻子、嘴巴的形状和比例）完全不变，"
                f"自然地将面容老化到{target_age}岁的状态，"
                f"增加符合{target_age}岁的皱纹和皮肤纹理变化，"
                f"头发适当变灰白。保持相同的背景环境，保持真实照片风格。"
            )

        # 调用 DashScope 图生图 API（同步模式）
        api_url = "https://dashscope.aliyuncs.com/api/v1/services/aigc/multimodal-generation/generation"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {DASHSCOPE_API_KEY}"
        }

        payload = {
            "model": "qwen-image-edit-plus",
            "input": {
                "messages": [
                    {
                        "role": "user",
                        "content": [
                            {"image": image_input},
                            {"text": prompt}
                        ]
                    }
                ]
            },
            "parameters": {
                "n": 1,
                "negative_prompt": "低分辨率，低画质，肢体畸形，画面过饱和，人脸无细节，过度光滑，画面具有AI感，变形，模糊",
                "prompt_extend": False,
                "watermark": False,
                "size": "1024*1024"
            }
        }

        # 同步请求（模型直接返回结果，等待时间较长）
        resp = http_requests.post(api_url, json=payload, headers=headers, timeout=180)
        result = resp.json()

        # 检查是否返回了异步 task_id（部分模型可能仍返回异步）
        task_id = result.get('output', {}).get('task_id')
        if task_id:
            # 异步模式：轮询等待结果
            poll_url = f"https://dashscope.aliyuncs.com/api/v1/tasks/{task_id}"
            poll_headers = {"Authorization": f"Bearer {DASHSCOPE_API_KEY}"}

            max_wait = 120
            start = time.time()
            while time.time() - start < max_wait:
                time.sleep(2)
                poll_resp = http_requests.get(poll_url, headers=poll_headers, timeout=30)
                poll_result = poll_resp.json()
                status = poll_result.get('output', {}).get('task_status', '')

                if status == 'SUCCEEDED':
                    result = poll_result
                    break
                elif status == 'FAILED':
                    error_msg = poll_result.get('output', {}).get('message', '生成失败')
                    return jsonify({'success': False, 'error': error_msg})
            else:
                return jsonify({'success': False, 'error': '生成超时，请稍后重试'})

        # 从结果中提取图片（兼容两种返回格式）
        output = result.get('output', {})
        remote_url = ''

        # 格式1: output.results[0].url（异步任务结果）
        results = output.get('results', [])
        if results and results[0].get('url'):
            remote_url = results[0]['url']

        # 格式2: output.choices[0].message.content[0].image（同步chat格式）
        if not remote_url:
            choices = output.get('choices', [])
            if choices:
                content_list = choices[0].get('message', {}).get('content', [])
                for item in content_list:
                    if isinstance(item, dict) and item.get('image'):
                        remote_url = item['image']
                        break

        if not remote_url:
            error_msg = result.get('message', '') or output.get('message', '') or str(result)
            return jsonify({'success': False, 'error': f'API调用失败: {error_msg}'})

        # 下载图片保存到本地
        img_resp = http_requests.get(remote_url, timeout=30)
        if img_resp.status_code != 200:
            return jsonify({'success': False, 'error': '下载生成图片失败'})

        img_id = str(uuid.uuid4())
        img_path = os.path.join(IMAGE_FOLDER, f'{img_id}.png')
        with open(img_path, 'wb') as f:
            f.write(img_resp.content)
        local_url = f'/api/images/{img_id}.png'

        # 保存预测记录
        memoir = load_memoir()
        if 'age_predictions' not in memoir:
            memoir['age_predictions'] = []
        prediction = {
            'id': str(uuid.uuid4()),
            'source_image': image_url,
            'current_age': current_age,
            'target_age': target_age,
            'result_image': local_url,
            'created_at': datetime.now().isoformat()
        }
        memoir['age_predictions'].append(prediction)
        save_memoir(memoir)

        return jsonify({
            'success': True,
            'image_url': local_url,
            'target_age': target_age,
            'prediction': prediction
        })
    except Exception as e:
        print(f"形象预测错误: {e}")
        return jsonify({'success': False, 'error': str(e)})


@app.route('/api/age_predictions', methods=['GET'])
def get_age_predictions():
    """获取所有形象预测记录"""
    memoir = load_memoir()
    return jsonify({'predictions': memoir.get('age_predictions', [])})


@app.route('/api/age_predictions/<prediction_id>', methods=['DELETE'])
def delete_age_prediction(prediction_id):
    """删除形象预测记录"""
    try:
        memoir = load_memoir()
        memoir['age_predictions'] = [
            p for p in memoir.get('age_predictions', [])
            if p['id'] != prediction_id
        ]
        save_memoir(memoir)
        return jsonify({'success': True})
    except Exception as e:
        return jsonify({'success': False, 'error': str(e)})


if __name__ == '__main__':
    print("=" * 50)
    print("  老年人回忆录记录助手 启动中...")
    print("  访问地址: http://localhost:7860")
    print("=" * 50)
    app.run(host='0.0.0.0', port=7860, debug=False)

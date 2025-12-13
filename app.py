import streamlit as st
import google.generativeai as genai
import requests
import json
import datetime
import os
import time
import re

# -------------------------------------------------------------
# --- 0. 页面配置和 CSS 注入 (Legalon Tech 风格) ---
# -------------------------------------------------------------

st.set_page_config(
    page_title="德国财税专家QFS", 
    page_icon="🇩🇪", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Legalon Tech 风格核心 CSS
st.markdown("""
<style>
    /* 1. 全局字体与重置 */
    @import url('https://fonts.googleapis.com/css2?family=Noto+Sans+SC:wght@400;500;700&display=swap');
    
    * {
        font-family: 'Noto Sans SC', -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
        box-sizing: border-box;
    }
    
    html, body, [data-testid="stAppViewContainer"] {
        background-color: #ffffff !important;
    }

    /* 2. 核心：去除顶部空白与隐藏默认元素 */
    [data-testid="stHeader"], [data-testid="stToolbar"], footer, .stDeployButton {
        display: none !important;
    }
    
    /* 调整主容器 Padding，消除顶部大片留白 */
    .block-container {
        padding-top: 1.5rem !important;
        padding-bottom: 8rem !important;
        max-width: 900px !important;
    }

    /* 3. 标题区域 (Legalon 风格：简洁、深蓝) */
    .page-title {
        font-size: 2.2rem !important;
        font-weight: 700 !important;
        color: #003366 !important; /* Legalon Navy Blue */
        margin: 0 0 8px 0 !important;
        text-align: center !important;
        letter-spacing: -0.5px !important;
    }
    .subtitle {
        font-size: 1rem !important;
        color: #666666 !important;
        margin: 0 0 40px 0 !important;
        text-align: center !important;
        font-weight: 400 !important;
    }

    /* 4. 聊天气泡优化 */
    [data-testid="stChatMessage"] {
        padding: 0 !important;
        margin-bottom: 24px !important;
    }
    /* 用户气泡 */
    [data-testid="stChatMessage"][data-role="user"] > div:nth-child(2) {
        background-color: #003366 !important; /* 深蓝 */
        color: white !important;
        border-radius: 12px 12px 2px 12px !important;
        padding: 16px 24px !important;
        font-size: 0.95rem !important;
        box-shadow: 0 2px 5px rgba(0,51,102,0.1) !important;
    }
    /* AI 气泡 */
    [data-testid="stChatMessage"][data-role="assistant"] > div:nth-child(2) {
        background-color: transparent !important;
        padding: 0 !important;
        color: #1a1a1a !important;
    }
    
    /* 头像样式 */
    [data-testid="stChatMessage"] .st-emotion-cache-1p1m4ay, 
    [data-testid="stChatMessage"] .st-emotion-cache-p4 micv {
        width: 36px !important;
        height: 36px !important;
        border: 1px solid #e0e0e0;
    }

    /* 5. 卡片式设计 (通用) */
    .result-card {
        background-color: #ffffff !important;
        border: 1px solid #e5e7eb !important;
        border-radius: 8px !important;
        margin-bottom: 20px !important;
        overflow: hidden !important;
        transition: box-shadow 0.2s ease;
    }
    .result-card:hover {
        box-shadow: 0 4px 12px rgba(0,0,0,0.05) !important;
    }
    
    .card-header {
        padding: 12px 20px !important;
        font-size: 0.9rem !important;
        font-weight: 600 !important;
        display: flex !important;
        align-items: center !important;
        border-bottom: 1px solid #f0f2f5 !important;
        background-color: #f8fafc !important; /* 极淡的灰蓝 */
    }
    .gemini-bg { color: #1a73e8 !important; }
    .glm-bg { color: #f59e0b !important; }
    
    .card-content {
        padding: 20px !important;
        font-size: 0.95rem !important;
        line-height: 1.7 !important;
        color: #333333 !important;
    }

    /* 6. 语义分析卡片 (重点优化) */
    .semantic-card {
        background-color: #f0f7ff !important; /* 极淡的 Legalon 蓝背景 */
        border: 1px solid #cfe2ff !important;
        border-radius: 8px !important;
        margin-top: 24px !important;
    }
    .semantic-content strong {
        display: block !important;
        color: #003366 !important;
        font-size: 1rem !important;
        margin-top: 16px !important;
        margin-bottom: 8px !important;
        padding-bottom: 4px !important;
        border-bottom: 1px dashed #cfe2ff !important;
    }
    .semantic-content strong:first-child {
        margin-top: 0 !important;
    }

    /* 7. 输入框与按钮 */
    [data-testid="stChatInput"] {
        padding-bottom: 20px !important;
    }
    div.stButton > button {
        border-radius: 6px !important;
        border: 1px solid #e5e7eb !important;
        background-color: white !important;
        color: #666 !important;
        font-weight: 500 !important;
        transition: all 0.2s !important;
    }
    div.stButton > button:hover {
        border-color: #003366 !important;
        color: #003366 !important;
        background-color: #f0f7ff !important;
    }

    /* Markdown 列表修正 */
    ul { margin-left: 20px !important; padding-left: 0 !important; }
    li { margin-bottom: 6px !important; }
    
    /* 常用问题区域 */
    .faq-header {
        font-size: 0.85rem !important;
        color: #888 !important;
        margin: 30px 0 10px 0 !important;
        text-transform: uppercase !important;
        letter-spacing: 1px !important;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# --- 工具函数 ---
# -------------------------------------------------------------
def clean_extra_newlines(text):
    """清理冗余换行/空格"""
    cleaned = re.sub(r'\n{2,}', '\n', text)
    cleaned = re.sub(r'　+', '', cleaned)
    cleaned = cleaned.strip('\n')
    return cleaned

def complete_markdown_syntax(text):
    """简单补全未闭合的 Markdown"""
    if text.count("**") % 2 != 0: text += "**"
    return text

def markdown_to_html(text):
    """将 Markdown 转为 HTML，专门优化标题和列表"""
    text = complete_markdown_syntax(text)
    # 替换加粗
    text = re.sub(r'\*\*(.*?)\*\*', r'<strong>\1</strong>', text)
    
    lines = text.split("\n")
    html_lines = []
    in_list = False
    
    for line in lines:
        line = line.strip()
        if not line: continue
        
        if line.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            html_lines.append(f"<li>{line[2:]}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            html_lines.append(f"<p>{line}</p>")
            
    if in_list: html_lines.append("</ul>")
    return "\n".join(html_lines)

# -------------------------------------------------------------
# --- 1. 配置与初始化 ---
# -------------------------------------------------------------
USER_ICON = "👤"
ASSISTANT_ICON = "⚖️"
GEMINI_ICON = "♊️"
GLM_ICON = "🧠"

COMMON_LEGAL_QUESTIONS = [
    "怎么应对税务稽查？",
    "货物出口德国如何判断增值税地点？",
    "企业在德国做重组，怎么做税务优化"
]

SYSTEM_INSTRUCTION = """
角色：德国资深税务师（20年跨境合规经验）
服务对象：中国出海企业
核心要求：
1. 基于德国现行法律法规，提供专业、严谨建议；
2. 结构化输出：核心风险 -> 法律依据(具体法条) -> 合规建议 -> 免责声明；
3. 排版简洁。
"""

# API Config
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
glm_api_key = st.secrets.get("GLM_API_KEY", "")

if not gemini_api_key:
    st.warning("⚠️ 未配置 Gemini API Key")
    st.session_state["api_configured"] = False
else:
    st.session_state["api_configured"] = True

@st.cache_resource
def initialize_gemini_model():
    if not gemini_api_key: return None
    return genai.GenerativeModel(
        model_name='gemini-flash-latest', 
        system_instruction=SYSTEM_INSTRUCTION,
        generation_config={"temperature": 0.1}
    )

gemini_model = initialize_gemini_model()

if "messages" not in st.session_state:
    st.session_state.messages = []
if "model_responses" not in st.session_state:
    st.session_state.model_responses = {}

# -------------------------------------------------------------
# --- 2. 流式处理函数 ---
# -------------------------------------------------------------
def stream_gemini_response(prompt, model):
    try:
        stream = model.generate_content(prompt, stream=True)
        for chunk in stream:
            if chunk.text:
                yield chunk.text
                time.sleep(0.02)
    except Exception as e:
        yield f"Gemini Error: {str(e)}"

def stream_glm_response(prompt, api_key):
    if not api_key:
        yield "未配置智谱 API Key"
        return
    try:
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {"Authorization": f"Bearer {api_key}", "Content-Type": "application/json"}
        data = {
            "model": "glm-4",
            "messages": [{"role": "user", "content": SYSTEM_INSTRUCTION + "\n" + prompt}],
            "stream": True
        }
        resp = requests.post(url, headers=headers, json=data, stream=True)
        for line in resp.iter_lines():
            if line:
                line = line.decode('utf-8').replace('data: ', '')
                if line == '[DONE]': break
                try:
                    chunk = json.loads(line)
                    content = chunk['choices'][0]['delta'].get('content', '')
                    if content: yield content
                except: pass
    except Exception as e:
        yield f"GLM Error: {str(e)}"

def generate_semantic_compare(gemini_resp, glm_resp, user_question, gemini_api_key):
    # 强制格式 Prompt
    compare_prompt = f"""
    作为专家，对比以下两个关于"{user_question}"的法律回答。
    请严格按照以下Markdown格式输出（不要添加其他开场白）：

    **核心共识**
    - [共识点1]
    - [共识点2]

    **观点差异**
    - Gemini：[侧重点]
    - 智谱GLM：[侧重点]

    **综合建议**
    [你的专业合规建议]

    ---
    回答A (Gemini): {gemini_resp[:1500]}
    回答B (GLM): {glm_resp[:1500]}
    """
    try:
        genai.configure(api_key=gemini_api_key)
        model = genai.GenerativeModel('gemini-flash-latest')
        stream = model.generate_content(compare_prompt, stream=True)
        for chunk in stream:
            if chunk.text:
                yield chunk.text
                time.sleep(0.02)
    except:
        yield "**分析失败**\n无法生成对比结果。"

# -------------------------------------------------------------
# --- 3. 页面渲染逻辑 ---
# -------------------------------------------------------------

# 标题 (Legalon 风格)
st.markdown('<h1 class="page-title">QFS Global Compliance</h1>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">Powered by Gemini & GLM-4 · 德国财税合规引擎</div>', unsafe_allow_html=True)

# 历史记录回显
for msg in st.session_state.messages:
    st.chat_message(msg["role"], avatar=USER_ICON if msg["role"] == "user" else ASSISTANT_ICON).write(msg["content"])

# 常见问题区 (仅当没有历史记录时显示，保持界面整洁)
prompt_from_button = None
if not st.session_state.messages:
    st.markdown('<div class="faq-header">常见合规咨询</div>', unsafe_allow_html=True)
    cols = st.columns(3)
    for i, q in enumerate(COMMON_LEGAL_QUESTIONS):
        if cols[i % 3].button(q, key=f"btn_{i}", use_container_width=True):
            prompt_from_button = q

# 处理输入
chat_input = st.chat_input("请输入具体的德国财税问题...")
user_query = prompt_from_button or chat_input

if user_query and st.session_state.get("api_configured"):
    # 1. 显示用户提问
    st.chat_message("user", avatar=USER_ICON).markdown(user_query)
    st.session_state.messages.append({"role": "user", "content": user_query})

    # 2. 占位容器
    st.markdown("### ⚖️ AI 合规分析")
    
    # Gemini 容器
    gemini_container = st.empty()
    # GLM 容器
    glm_container = st.empty()
    # 语义对比容器
    semantic_container = st.empty()

    # --- 执行 Gemini ---
    gemini_text = ""
    for chunk in stream_gemini_response(user_query, gemini_model):
        gemini_text += chunk
        html = markdown_to_html(clean_extra_newlines(gemini_text))
        gemini_container.markdown(f"""
        <div class="result-card">
            <div class="card-header gemini-bg">{GEMINI_ICON} Gemini Flash 法律意见</div>
            <div class="card-content">{html}</div>
        </div>
        """, unsafe_allow_html=True)

    # --- 执行 GLM ---
    glm_text = ""
    for chunk in stream_glm_response(user_query, glm_api_key):
        glm_text += chunk
        html = markdown_to_html(clean_extra_newlines(glm_text))
        glm_container.markdown(f"""
        <div class="result-card">
            <div class="card-header glm-bg">{GLM_ICON} 智谱 GLM-4 法律意见</div>
            <div class="card-content">{html}</div>
        </div>
        """, unsafe_allow_html=True)

    # --- 执行 语义对比 ---
    semantic_text = ""
    for chunk in generate_semantic_compare(gemini_text, glm_text, user_query, gemini_api_key):
        semantic_text += chunk
        html = markdown_to_html(clean_extra_newlines(semantic_text))
        semantic_container.markdown(f"""
        <div class="result-card semantic-card">
            <div class="card-header" style="background:none; border:none; color:#003366;">
                📊 深度语义异同分析
            </div>
            <div class="card-content semantic-content">{html}</div>
        </div>
        """, unsafe_allow_html=True)

    # 记录到历史
    full_record = f"**双模型分析完成**\n\n查看上方卡片获取 Gemini 与 GLM 的详细法律意见对比。\n\n**总结建议**：\n{semantic_text}"
    st.session_state.messages.append({"role": "assistant", "content": full_record})

# 底部清空按钮
if st.session_state.messages:
    if st.button('重置对话', key="reset_btn"):
        st.session_state.messages = []
        st.rerun()

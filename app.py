import streamlit as st
import google.generativeai as genai
import requests
import json
import datetime
import os
import time
import re

# -------------------------------------------------------------
# --- 0. 页面配置和 CSS 注入 (Kimi 风格 + Markdown 渲染优化) ---
# -------------------------------------------------------------

st.set_page_config(
    page_title="德国财税专家QFS", 
    page_icon="🇩🇪", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Moonshot Kimi 风格核心 CSS + Markdown 渲染样式
st.markdown("""
<style>
    /* 1. 全局重置 */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"], .stApp {
        padding: 0 !important;
        margin: 0 !important;
        background-color: #ffffff !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
    }

    /* 2. 隐藏默认元素 */
    header, [data-testid="stSidebar"], footer, .stDeployButton, [data-testid="stToolbar"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="stHeader"] {
        display: none !important;
    }

    /* 3. 主容器 */
    .main-container {
        max-width: 800px !important;
        width: 100% !important;
        margin: 0 auto !important;
        padding: 20px 24px 90px 24px !important;
    }

    /* 4. 标题区域 */
    .page-title {
        font-size: 1.8rem !important;
        font-weight: 600 !important;
        color: #1a1a1a !important;
        margin: 0 0 8px 0 !important;
        line-height: 1.4 !important;
    }
    .subtitle {
        font-size: 0.9rem !important;
        color: #666666 !important;
        margin: 0 0 32px 0 !important;
        font-weight: 400 !important;
    }

    /* 5. 聊天消息气泡 */
    [data-testid="stChatMessage"] {
        margin-bottom: 12px !important;
        padding: 0 !important;
        max-width: 100% !important;
    }
    [data-testid="stChatMessage"][data-role="user"] > div:nth-child(2) {
        background-color: #0f7bff !important;
        color: white !important;
        border-radius: 16px 16px 4px 16px !important;
        padding: 14px 20px !important;
        box-shadow: none !important;
        margin-left: 8px !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
    }
    [data-testid="stChatMessage"][data-role="assistant"] > div:nth-child(2) {
        background-color: #f5f7fa !important;
        border: none !important;
        border-radius: 16px 16px 16px 4px !important;
        padding: 14px 20px !important;
        box-shadow: none !important;
        margin-right: 8px !important;
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
        color: #1a1a1a !important;
    }
    [data-testid="stChatMessage"] img {
        width: 32px !important;
        height: 32px !important;
        border-radius: 50% !important;
        object-fit: cover !important;
    }

    /* 6. 常见问题按钮 */
    .faq-header {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        color: #1a1a1a !important;
        margin: 24px 0 16px 0 !important;
    }
    div.stButton > button {
        background-color: #f5f7fa !important;
        color: #1a1a1a !important;
        border: none !important;
        border-radius: 12px !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        padding: 12px 16px !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
        margin-bottom: 10px !important;
        text-align: left !important;
    }
    div.stButton > button:hover {
        background-color: #ebeef5 !important;
        color: #0f7bff !important;
        transform: none !important;
    }

    /* 7. 底部输入框 */
    [data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        background: white !important;
        padding: 16px 0 !important;
        box-shadow: 0 -1px 3px rgba(0, 0, 0, 0.05) !important;
        z-index: 999 !important;
        max-width: 800px !important;
        margin: 0 auto !important;
        width: 100% !important;
        border-top: 1px solid #f0f2f5 !important;
    }
    [data-testid="stChatInput"] textarea {
        border-radius: 16px !important;
        border: 1px solid #e5e9f2 !important;
        padding: 16px 20px !important;
        font-size: 0.95rem !important;
        background-color: #fafbfc !important;
        box-shadow: none !important;
        height: 60px !important;
        resize: none !important;
    }
    [data-testid="stChatInput"] textarea:focus {
        border-color: #0f7bff !important;
        background-color: white !important;
        box-shadow: 0 0 0 2px rgba(15, 123, 255, 0.1) !important;
        outline: none !important;
    }

    /* 8. 模型结果卡片 */
    .model-compare-header {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #1a1a1a !important;
        margin: 32px 0 16px 0 !important;
        padding-bottom: 8px !important;
        border-bottom: 1px solid #f0f2f5 !important;
    }
    .model-card {
        background-color: #fafbfc !important;
        padding: 20px !important;
        border-radius: 16px !important;
        border: 1px solid #f0f2f5 !important;
        box-shadow: none !important;
        margin-bottom: 20px !important;
    }
    .model-card-header {
        font-size: 0.95rem !important;
        font-weight: 600 !important;
        margin-bottom: 14px !important;
        display: flex !important;
        align-items: center !important;
        color: #1a1a1a !important;
    }
    .gemini-header {
        color: #4285f4 !important;
    }
    .glm-header {
        color: #ff6700 !important;
    }
    .model-card-content {
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
        color: #1a1a1a !important;
        white-space: pre-wrap !important;
        padding: 0 !important;
        margin: 0 !important;
        overflow-x: hidden !important;
    }

    /* 9. 语义总结卡片 + Markdown 渲染样式 */
    .semantic-compare-header {
        font-size: 1.05rem !important;
        font-weight: 600 !important;
        color: #1a1a1a !important;
        margin: 24px 0 16px 0 !important;
        padding-bottom: 8px !important;
        border-bottom: 1px solid #f0f2f5 !important;
    }
    .semantic-card {
        background-color: #e8f3ff !important;
        padding: 20px !important;
        border-radius: 16px !important;
        border: 1px solid #d1e7ff !important;
        box-shadow: none !important;
        margin-bottom: 16px !important;
    }
    .semantic-content {
        color: #1a1a1a !important;
        line-height: 1.6 !important;
        font-size: 0.95rem !important;
        padding: 0 !important;
        margin: 0 !important;
        overflow-x: hidden !important;
    }
    /* 关键：Markdown 列表样式（Kimi 风格） */
    ul {
        margin: 8px 0 16px 20px !important;
        padding: 0 !important;
    }
    li {
        margin: 6px 0 !important;
        line-height: 1.6 !important;
        color: #1a1a1a !important;
    }
    /* Markdown 加粗样式（Kimi 蓝色强调） */
    strong {
        color: #0f7bff !important;
        font-weight: 600 !important;
    }
    /* 解决空白行 */
    .semantic-content br, .model-card-content br {
        line-height: 1.4 !important;
        margin: 1px 0 !important;
    }
    p {
        margin: 6px 0 !important;
        padding: 0 !important;
    }

    /* 10. 清空按钮 */
    .clear-btn {
        background-color: #f5f7fa !important;
        color: #666666 !important;
        border: none !important;
        border-radius: 12px !important;
        padding: 8px 16px !important;
        font-size: 0.85rem !important;
        margin-top: 12px !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
    }
    .clear-btn:hover {
        background-color: #ebeef5 !important;
        color: #0f7bff !important;
    }

    /* 11. 加载光标 */
    @keyframes blink {
        0%, 100% { opacity: 1; }
        50% { opacity: 0; }
    }
    .blinking-cursor {
        animation: blink 1s infinite;
        margin-left: 4px;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# --- 工具函数：Markdown 渲染 + 冗余清理 ---
# -------------------------------------------------------------
def clean_extra_newlines(text):
    """清理冗余换行/空格"""
    cleaned = re.sub(r'\n{2,}', '\n', text)
    cleaned = re.sub(r'　+', '', cleaned)
    cleaned = re.sub(r'\t+', '', cleaned)
    cleaned = cleaned.strip('\n')
    cleaned = re.sub(r'\n+(- )', '\n- ', cleaned)
    return cleaned

def complete_markdown_syntax(text):
    """补全未闭合的 Markdown 语法"""
    # 补全加粗 **
    bold_count = text.count("**")
    if bold_count % 2 != 0:
        text += "**"
    # 补全代码块 `
    code_count = text.count("`")
    if code_count % 2 != 0:
        text += "`"
    # 补全列表
    if text.endswith("- "):
        text += "未完成的要点"
    return text

def markdown_to_html(text):
    """将 Markdown 转为可渲染的 HTML"""
    text = complete_markdown_syntax(text)
    # 替换加粗
    text = text.replace("**", "<strong>")
    # 处理列表
    lines = text.split("\n")
    html_lines = []
    in_list = False
    for line in lines:
        line = line.strip()
        if line.startswith("- "):
            if not in_list:
                html_lines.append("<ul>")
                in_list = True
            item = line[2:].strip()
            html_lines.append(f"<li>{item}</li>")
        else:
            if in_list:
                html_lines.append("</ul>")
                in_list = False
            if line.startswith("**") and line.endswith("**"):
                html_lines.append(f"<p><strong>{line.strip('**')}</strong></p>")
            elif line:
                html_lines.append(f"<p>{line}</p>")
    if in_list:
        html_lines.append("</ul>")
    # 清理空标签
    html = "\n".join(html_lines).replace("<p></p>", "").replace("<ul></ul>", "")
    return html

# -------------------------------------------------------------
# --- 1. 常量定义与基础配置 ---
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
1. 基于德国现行法律法规，提供专业、严谨、可落地的合规建议；
2. 结构化输出：核心风险点 → 法律依据 → 合规建议 → 免责声明；
3. 法律依据需标注具体法条/欧盟指令编号；
4. 排版简洁：单个换行分隔内容，禁止冗余空白；
5. 免责声明简明（不超过50字）。
"""

# -------------------------- 访问计数器 --------------------------
COUNTER_FILE = "visit_stats_qfs.json"

def update_daily_visits():
    try:
        today_str = datetime.date.today().isoformat()
        if "has_counted" in st.session_state:
            if os.path.exists(COUNTER_FILE):
                try:
                    with open(COUNTER_FILE, "r") as f:
                        return json.load(f).get("count", 0)
                except:
                    return 0
            return 0
        data = {"date": today_str, "count": 0}
        if os.path.exists(COUNTER_FILE):
            try:
                with open(COUNTER_FILE, "r") as f:
                    file_data = json.load(f)
                    if file_data.get("date") == today_str:
                        data = file_data
            except:
                pass 
        data["count"] += 1
        with open(COUNTER_FILE, "w") as f:
            json.dump(data, f)
        st.session_state["has_counted"] = True
        return data["count"]
    except Exception as e:
        return 0

daily_visits = update_daily_visits()
visit_text = f"今日访问: {daily_visits}"

# -------------------------------------------------------------
# --- 2. 流式输出核心函数 ---
# -------------------------------------------------------------
def stream_gemini_response(prompt, model):
    try:
        stream = model.generate_content(prompt, stream=True)
        for chunk in stream:
            if chunk.text:
                yield chunk.text
                time.sleep(0.04)
    except Exception as e:
        yield f"\n\n⚠️ Gemini调用失败：{str(e)[:100]}..."

def stream_glm_response(prompt, api_key, model_name="glm-4"):
    if not api_key:
        yield "⚠️ 未配置智谱GLM API Key，暂无法获取该模型分析结果。"
        return
    try:
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        full_prompt = f"""{SYSTEM_INSTRUCTION}
用户问题：{prompt}
额外要求：回答结构清晰，排版简洁，单个换行分隔，无冗余空白。"""
        data = {
            "model": model_name,
            "messages": [{"role": "user", "content": full_prompt}],
            "temperature": 0.1,
            "max_tokens": 4096,
            "stream": True
        }
        response = requests.post(url, headers=headers, json=data, stream=True, timeout=30)
        response.raise_for_status()
        for line in response.iter_lines():
            if line:
                line = line.decode('utf-8')
                if line.startswith('data: '):
                    line = line[6:]
                    if line == '[DONE]':
                        break
                    try:
                        chunk = json.loads(line)
                        if chunk.get('choices') and chunk['choices'][0].get('delta', {}).get('content'):
                            content = chunk['choices'][0]['delta']['content']
                            yield content
                            time.sleep(0.04)
                    except:
                        continue
    except requests.exceptions.RequestException as e:
        yield f"\n\n⚠️ 智谱GLM调用失败：{str(e)[:100]}..."
    except Exception as e:
        yield f"\n\n⚠️ 智谱GLM处理失败：{str(e)[:100]}..."

def generate_semantic_compare(gemini_resp, glm_resp, user_question, gemini_api_key):
    compare_prompt = f"""
作为德国财税分析专家，对比以下两个模型针对"{user_question}"的回答，总结语义异同：

### 对比要求：
1. 核心共识：3-4条核心观点共识，简洁明了；
2. 观点差异：分别描述两个模型的分析角度和侧重点；
3. 综合建议：具体、可落地的行动建议（不少于50字）；
4. 排版：单个换行分隔，无冗余空白，符合Kimi极简风格。

### Gemini回答：
{gemini_resp[:2000]}

### 智谱GLM回答：
{glm_resp[:2000]}

### 输出格式：
**核心共识**
- 要点1
- 要点2

**观点差异**
- Gemini：xxx
- 智谱GLM：xxx

**综合建议**
xxx
"""
    try:
        genai.configure(api_key=gemini_api_key)
        summary_model = genai.GenerativeModel(
            model_name='gemini-flash-latest',
            generation_config={
                "temperature": 0.1, 
                "max_output_tokens": 3000,
                "top_p": 0.95
            }
        )
        stream = summary_model.generate_content(compare_prompt, stream=True)
        for chunk in stream:
            if chunk.text:
                yield chunk.text
                time.sleep(0.03)
    except Exception as e:
        st.error(f"语义总结生成失败：{str(e)}")
        print(f"语义总结错误详情：{e}")
        yield f"""
**核心共识**
- 均认可{user_question}相关德国财税法规的核心适用原则
- 均强调合规操作和风险防控的必要性
- 均建议结合专业税务师咨询落地

**观点差异**
- Gemini：侧重法条字面解读、国际通用性和合规框架搭建
- 智谱GLM：侧重中企实操落地、本土化适配和流程简化

**综合建议**
针对{user_question}，建议先参考Gemini的合规框架确保符合德国法规要求，再结合智谱GLM的实操建议优化落地流程，关键节点咨询当地专业税务师，降低合规风险。
"""

# -------------------------------------------------------------
# --- 3. 模型初始化与会话状态 ---
# -------------------------------------------------------------
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
glm_api_key = st.secrets.get("GLM_API_KEY", "")

if not gemini_api_key:
    st.markdown(f"""
    <div style="
        background-color: #fff8f8; 
        color: #dc2626; 
        padding: 12px 16px; 
        border-radius: 12px; 
        margin: 0 0 20px 0;
        font-size: 0.9rem;
    ">
        ⚠️ 未配置Gemini API Key<br>
        请在 /workspaces/qfs/.streamlit/secrets.toml 中添加：<br>
        <code style="font-size: 0.85rem;">GEMINI_API_KEY = "你的Gemini密钥"</code>
    </div>
    """, unsafe_allow_html=True)
    st.session_state["api_configured"] = False
else:
    st.session_state["api_configured"] = True

@st.cache_resource(show_spinner="正在加载专业知识库...")
def initialize_gemini_model():
    if not gemini_api_key:
        return None
    generation_config = {
        "max_output_tokens": 4096,
        "temperature": 0.1,
        "top_p": 0.95
    }
    model = genai.GenerativeModel(
        model_name='gemini-flash-latest', 
        system_instruction=SYSTEM_INSTRUCTION,
        generation_config=generation_config
    )
    return model

gemini_model = initialize_gemini_model()

if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是您的德国财税专家QFS。请问您在中国企业出海过程中遇到了哪些财务、税务或商业资质方面的问题？"}
    ]
if "model_responses" not in st.session_state:
    st.session_state.model_responses = {}

# -------------------------------------------------------------
# --- 4. 主程序入口 (Markdown 渲染修复) ---
# -------------------------------------------------------------
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# 头部区域
st.markdown('<h1 class="page-title">🇩🇪 德国合规QFS</h1>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">资深税务师 · 跨境合规专家 · AI 咨询服务</div>', unsafe_allow_html=True)

# 常见问题
st.markdown('<div class="faq-header">💡 常见问题快速查询</div>', unsafe_allow_html=True)
cols = st.columns(1)
prompt_from_button = None
with cols[0]:
    for i, question in enumerate(COMMON_LEGAL_QUESTIONS):
        if st.button(question, key=f"q_{i}"):
            prompt_from_button = question

# 聊天区域
for msg in st.session_state.messages:
    icon = USER_ICON if msg["role"] == "user" else ASSISTANT_ICON
    st.chat_message(msg["role"], avatar=icon).write(msg["content"])

# 获取用户输入
chat_input_text = st.chat_input("请输入你的合规问题...")
user_input = prompt_from_button if prompt_from_button else chat_input_text

# 处理用户输入
if user_input and st.session_state.get("api_configured", False):
    st.chat_message("user", avatar=USER_ICON).write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # === 1. Gemini 流式输出（修复 Markdown 渲染） ===
    st.markdown('<div class="model-compare-header">🔍 模型分析结果</div>', unsafe_allow_html=True)
    st.markdown(f"""
    <div class="model-card">
        <div class="model-card-header gemini-header">
            {GEMINI_ICON} Gemini Flash
        </div>
        <div class="model-card-content" id="gemini-content">
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    gemini_placeholder = st.empty()
    gemini_full_response = ""
    for chunk in stream_gemini_response(user_input, gemini_model):
        gemini_full_response += chunk
        cleaned_gemini = clean_extra_newlines(gemini_full_response)
        display_gemini = markdown_to_html(cleaned_gemini)
        gemini_placeholder.markdown(f"""
        <div class="model-card">
            <div class="model-card-header gemini-header">
                {GEMINI_ICON} Gemini Flash
            </div>
            <div class="model-card-content">
                {display_gemini}<span class="blinking-cursor">|</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 最终渲染 Gemini
    final_gemini = clean_extra_newlines(gemini_full_response)
    final_display_gemini = markdown_to_html(final_gemini)
    gemini_placeholder.markdown(f"""
    <div class="model-card">
        <div class="model-card-header gemini-header">
            {GEMINI_ICON} Gemini Flash
        </div>
        <div class="model-card-content">
            {final_display_gemini}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # === 2. 智谱 GLM 流式输出（修复 Markdown 渲染） ===
    st.markdown(f"""
    <div class="model-card">
        <div class="model-card-header glm-header">
            {GLM_ICON} 智谱GLM-4
        </div>
        <div class="model-card-content" id="glm-content">
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    glm_placeholder = st.empty()
    glm_full_response = ""
    for chunk in stream_glm_response(user_input, glm_api_key):
        glm_full_response += chunk
        cleaned_glm = clean_extra_newlines(glm_full_response)
        display_glm = markdown_to_html(cleaned_glm)
        glm_placeholder.markdown(f"""
        <div class="model-card">
            <div class="model-card-header glm-header">
                {GLM_ICON} 智谱GLM-4
            </div>
            <div class="model-card-content">
                {display_glm}<span class="blinking-cursor">|</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 最终渲染 GLM
    final_glm = clean_extra_newlines(glm_full_response)
    final_display_glm = markdown_to_html(final_glm)
    glm_placeholder.markdown(f"""
    <div class="model-card">
        <div class="model-card-header glm-header">
            {GLM_ICON} 智谱GLM-4
        </div>
        <div class="model-card-content">
            {final_display_glm}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 存储结果
    st.session_state.model_responses[user_input] = {
        "gemini": gemini_full_response,
        "glm": glm_full_response
    }
    
    # === 3. 语义对比 流式输出（核心修复 Markdown 渲染） ===
    st.markdown('<div class="semantic-compare-header">📊 语义层面异同分析</div>', unsafe_allow_html=True)
    semantic_placeholder = st.empty()
    semantic_full_response = ""
    
    for chunk in generate_semantic_compare(gemini_full_response, glm_full_response, user_input, gemini_api_key):
        semantic_full_response += chunk
        cleaned_semantic = clean_extra_newlines(semantic_full_response)
        display_semantic = markdown_to_html(cleaned_semantic)
        semantic_placeholder.markdown(f"""
        <div class="semantic-card">
            <div class="semantic-content">
                {display_semantic}<span class="blinking-cursor">|</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 最终渲染语义总结
    final_semantic = clean_extra_newlines(semantic_full_response)
    final_display_semantic = markdown_to_html(final_semantic)
    semantic_placeholder.markdown(f"""
    <div class="semantic-card">
        <div class="semantic-content">
            {final_display_semantic}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 添加到聊天记录
    combined_response = f"""
### 双模型语义分析总结：
{final_semantic}

### 完整回答参考：
- Gemini 详细分析：{final_gemini[:200]}...
- 智谱GLM 详细分析：{final_glm[:200]}...
    """
    st.session_state.messages.append({"role": "assistant", "content": combined_response})

# 清空按钮
def clear_chat_history():
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是您的德国财税专家QFS。请问您在中国企业出海过程中遇到了哪些财务、税务或商业资质方面的问题？"}
    ]
    st.session_state.model_responses = {}

st.button(
    '🧹 清空聊天记录', 
    help="清除所有历史对话", 
    key="clear_btn",
    on_click=clear_chat_history,
 
)

st.markdown('</div>', unsafe_allow_html=True)

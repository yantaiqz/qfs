import streamlit as st
import google.generativeai as genai
import requests
import json
import datetime
import os
import time
import re

# -------------------------------------------------------------
# --- 0. 页面配置和 CSS 注入 (模仿legalontech.jp风格) ---
# -------------------------------------------------------------

st.set_page_config(
    page_title="德国财税专家QFS", 
    page_icon="🇩🇪", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# legalontech.jp 风格核心 CSS - 极简、专业、无冗余空白
st.markdown("""
<style>
    /* 1. 全局重置 - 彻底移除所有默认边距 */
    * {
        margin: 0;
        padding: 0;
        box-sizing: border-box;
    }
    
    /* 核心：移除所有顶部空白 */
    html, body {
        height: 100%;
        width: 100%;
        margin: 0 !important;
        padding: 0 !important;
    }
    
    [data-testid="stAppViewContainer"], [data-testid="stMain"], .stApp {
        padding: 0 !important;
        margin: 0 !important;
        background-color: #f9f9f9 !important; /* legalontech 浅灰背景 */
        font-family: 'Helvetica Neue', Arial, sans-serif !important;
    }

    /* 2. 隐藏所有 Streamlit 默认元素 */
    header, [data-testid="stSidebar"], footer, .stDeployButton, [data-testid="stToolbar"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"], [data-testid="stHeader"],
    [data-testid="stVerticalBlock"] > [data-testid="stVerticalBlock"]:first-child {
        display: none !important;
    }

    /* 3. 主容器 - legalontech 风格窄版居中 */
    .main-container {
        max-width: 900px !important;
        width: 100% !important;
        margin: 0 auto !important;
        padding: 0 24px !important;
        background-color: #ffffff !important;
        min-height: 100vh !important;
        box-shadow: 0 0 10px rgba(0,0,0,0.05) !important; /* 轻微阴影增强层次感 */
    }

    /* 4. 头部区域 - legalontech 极简风格 */
    .header-wrapper {
        padding: 32px 0 24px 0 !important;
        border-bottom: 1px solid #eaeaea !important; /* 细分隔线 */
        margin-bottom: 24px !important;
    }
    .page-title {
        font-size: 2rem !important;
        font-weight: 700 !important;
        color: #222222 !important; /* 深灰文字 */
        margin: 0 0 8px 0 !important;
        line-height: 1.3 !important;
    }
    .subtitle {
        font-size: 1rem !important;
        color: #666666 !important;
        margin: 0 !important;
        font-weight: 400 !important;
    }

    /* 5. 聊天消息气泡 - 专业简洁风格 */
    [data-testid="stChatMessage"] {
        margin-bottom: 16px !important;
        padding: 0 !important;
        max-width: 100% !important;
    }
    [data-testid="stChatMessage"][data-role="user"] > div:nth-child(2) {
        background-color: #2d3748 !important; /* 深色专业蓝 */
        color: white !important;
        border-radius: 8px !important;
        padding: 16px 20px !important;
        box-shadow: none !important;
        margin-left: 0 !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
    }
    [data-testid="stChatMessage"][data-role="assistant"] > div:nth-child(2) {
        background-color: #ffffff !important;
        border: 1px solid #eaeaea !important;
        border-radius: 8px !important;
        padding: 16px 20px !important;
        box-shadow: none !important;
        margin-right: 0 !important;
        font-size: 1rem !important;
        line-height: 1.6 !important;
        color: #333333 !important;
    }
    [data-testid="stChatMessage"] img {
        width: 36px !important;
        height: 36px !important;
        border-radius: 50% !important;
        object-fit: cover !important;
    }

    /* 6. 常见问题按钮 - legalontech 扁平风格 */
    .faq-section {
        margin: 24px 0 32px 0 !important;
    }
    .faq-header {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #222222 !important;
        margin: 0 0 16px 0 !important;
    }
    .faq-buttons {
        display: grid !important;
        grid-template-columns: repeat(auto-fit, minmax(280px, 1fr)) !important;
        gap: 12px !important;
    }
    div.stButton > button {
        background-color: #ffffff !important;
        color: #333333 !important;
        border: 1px solid #eaeaea !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 1rem !important;
        padding: 14px 18px !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
        box-shadow: none !important;
        text-align: left !important;
    }
    div.stButton > button:hover {
        background-color: #f5f5f5 !important;
        color: #2d3748 !important;
        border-color: #ddd !important;
    }

    /* 7. 底部输入框 - legalontech 固定底部样式 */
    [data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        background: white !important;
        padding: 16px 0 !important;
        box-shadow: 0 -1px 5px rgba(0,0,0,0.05) !important;
        z-index: 999 !important;
        max-width: 900px !important;
        margin: 0 auto !important;
        width: 100% !important;
        border-top: 1px solid #eaeaea !important;
    }
    [data-testid="stChatInput"] textarea {
        border-radius: 8px !important;
        border: 1px solid #eaeaea !important;
        padding: 16px 20px !important;
        font-size: 1rem !important;
        background-color: #ffffff !important;
        box-shadow: none !important;
        height: 64px !important;
        resize: none !important;
    }
    [data-testid="stChatInput"] textarea:focus {
        border-color: #2d3748 !important;
        background-color: white !important;
        box-shadow: 0 0 0 2px rgba(45, 55, 72, 0.1) !important;
        outline: none !important;
    }

    /* 8. 模型结果卡片 - legalontech 专业风格 */
    .model-results-section {
        margin: 32px 0 !important;
    }
    .model-compare-header {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        color: #222222 !important;
        margin: 0 0 20px 0 !important;
        padding-bottom: 12px !important;
        border-bottom: 1px solid #eaeaea !important;
    }
    .model-card {
        background-color: #ffffff !important;
        padding: 24px !important;
        border-radius: 8px !important;
        border: 1px solid #eaeaea !important;
        box-shadow: none !important;
        margin-bottom: 20px !important;
    }
    .model-card-header {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        margin-bottom: 16px !important;
        display: flex !important;
        align-items: center !important;
        color: #222222 !important;
    }
    .gemini-header {
        color: #4285f4 !important;
    }
    .glm-header {
        color: #ff6700 !important;
    }
    .model-card-content {
        font-size: 1rem !important;
        line-height: 1.7 !important;
        color: #333333 !important;
        white-space: pre-wrap !important;
    }

    /* 9. 语义总结卡片 - legalontech 强调风格 */
    .semantic-section {
        margin: 32px 0 80px 0 !important; /* 底部留空避免被输入框遮挡 */
    }
    .semantic-compare-header {
        font-size: 1.2rem !important;
        font-weight: 600 !important;
        color: #222222 !important;
        margin: 0 0 20px 0 !important;
        padding-bottom: 12px !important;
        border-bottom: 1px solid #eaeaea !important;
    }
    .semantic-card {
        background-color: #f8f9fa !important;
        padding: 24px !important;
        border-radius: 8px !important;
        border-left: 4px solid #2d3748 !important; /* 左侧强调线 */
        box-shadow: none !important;
    }
    .semantic-content {
        color: #333333 !important;
        line-height: 1.7 !important;
        font-size: 1rem !important;
    }
    
    /* Markdown 渲染样式 - legalontech 专业风格 */
    ul {
        margin: 12px 0 20px 24px !important;
        padding: 0 !important;
    }
    li {
        margin: 8px 0 !important;
        line-height: 1.7 !important;
        color: #333333 !important;
    }
    strong {
        color: #2d3748 !important;
        font-weight: 600 !important;
    }
    p {
        margin: 10px 0 !important;
        padding: 0 !important;
    }

    /* 10. 清空按钮 - 次要按钮风格 */
    .clear-btn-wrapper {
        margin: 24px 0 0 0 !important;
    }
    .clear-btn {
        background-color: #ffffff !important;
        color: #666666 !important;
        border: 1px solid #eaeaea !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-size: 0.9rem !important;
        transition: all 0.2s ease !important;
    }
    .clear-btn:hover {
        background-color: #f5f5f5 !important;
        color: #2d3748 !important;
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
# --- 工具函数：统一格式处理 + Markdown 渲染 ---
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

def standardize_model_output(text, model_name):
    """
    统一模型输出格式为标准化结构
    适配语义分析的格式：核心观点 → 分析角度 → 具体建议
    """
    # 清理基础格式
    text = clean_extra_newlines(text)
    text = complete_markdown_syntax(text)
    
    # 标准化输出结构
    standardized = f"""**核心观点**
{text if text else '暂无有效分析内容'}

**分析角度**
- {model_name}：聚焦德国财税法规的{'条文解读' if model_name == 'Gemini' else '实操落地'}维度
- 分析框架：基于德国《税收通则》(AO) 和《增值税法》(UStG) 等核心法规

**具体建议**
- 建议结合专业税务师进行个性化方案制定
- 确保所有操作符合德国反避税规则和欧盟相关指令"""
    
    return standardized

def markdown_to_html(text):
    """将 Markdown 转为可渲染的 HTML，适配标准化格式"""
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

# 更新系统指令，要求输出标准化格式
SYSTEM_INSTRUCTION = """
角色：德国资深税务师（20年跨境合规经验）
服务对象：中国出海企业
输出格式要求（必须严格遵守）：
**核心观点**
- 核心结论1
- 核心结论2

**分析角度**
- 法规依据：具体法条/指令编号
- 分析维度：合规风险/税务优化/实操落地

**具体建议**
- 可落地的行动建议1
- 可落地的行动建议2

其他要求：
1. 基于德国现行法律法规，提供专业、严谨的合规建议；
2. 法律依据需标注具体法条/欧盟指令编号；
3. 排版简洁，单个换行分隔，禁止冗余空白；
4. 免责声明简明（不超过50字）。
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
额外要求：严格按照指定格式输出，结构清晰，排版简洁。"""
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
    """生成标准化格式的语义对比分析"""
    compare_prompt = f"""
作为德国财税分析专家，对比以下两个模型针对"{user_question}"的回答，按照以下格式总结语义异同：

### 输出格式（必须严格遵守）：
**核心共识**
- 要点1
- 要点2
- 要点3

**观点差异**
- Gemini：分析角度和侧重点
- 智谱GLM：分析角度和侧重点

**综合建议**
具体、可落地的行动建议（不少于80字）

### Gemini回答：
{gemini_resp[:2000]}

### 智谱GLM回答：
{glm_resp[:2000]}

### 要求：
1. 核心共识提取3-4条核心观点共识
2. 观点差异清晰对比两个模型的分析角度
3. 综合建议需结合德国具体法规和实操场景
4. 排版简洁，无冗余空白，专业严谨
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
- 均需遵守德国反避税规则和欧盟ATAD指令

**观点差异**
- Gemini：侧重法条字面解读、国际通用性和合规框架搭建，关注欧盟层面的协调规则
- 智谱GLM：侧重中企实操落地、本土化适配和流程简化，关注具体申报流程和材料准备

**综合建议**
针对{user_question}，建议先参考Gemini的合规框架确保符合德国《税收通则》(AO)和《增值税法》(UStG)等核心法规要求，再结合智谱GLM的实操建议优化落地流程。关键节点需咨询德国当地税务师，确保转让定价符合BEPS规则，同时做好税务稽查的文档准备工作，降低合规风险。
"""

# -------------------------------------------------------------
# --- 3. 模型初始化与会话状态 ---
# -------------------------------------------------------------
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
glm_api_key = st.secrets.get("GLM_API_KEY", "")

# 容错提示（legalontech 风格）
if not gemini_api_key:
    st.markdown(f"""
    <div style="
        background-color: #fff5f5; 
        color: #c53030; 
        padding: 16px 20px; 
        border-radius: 8px; 
        margin: 24px 0;
        font-size: 1rem;
        border-left: 4px solid #e53e3e;
    ">
        ⚠️ 未配置Gemini API Key<br>
        请在 /workspaces/qfs/.streamlit/secrets.toml 中添加：<br>
        <code style="font-size: 0.9rem; background-color: #fef2f2; padding: 2px 6px; border-radius: 4px;">GEMINI_API_KEY = "你的Gemini密钥"</code>
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

# 会话状态初始化
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是您的德国财税专家QFS。请问您在中国企业出海过程中遇到了哪些财务、税务或商业资质方面的问题？"}
    ]
if "model_responses" not in st.session_state:
    st.session_state.model_responses = {}

# -------------------------------------------------------------
# --- 4. 主程序入口 (legalontech 风格布局) ---
# -------------------------------------------------------------
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# 头部区域（legalontech 风格）
st.markdown("""
<div class="header-wrapper">
    <h1 class="page-title">🇩🇪 德国财税合规专家</h1>
    <p class="subtitle">专注中国企业出海德国的税务合规与优化</p>
</div>
""", unsafe_allow_html=True)

# 常见问题区域
st.markdown("""
<div class="faq-section">
    <h2 class="faq-header">💡 常见问题快速查询</h2>
    <div class="faq-buttons">
""", unsafe_allow_html=True)

prompt_from_button = None
cols = st.columns(1)
with cols[0]:
    for i, question in enumerate(COMMON_LEGAL_QUESTIONS):
        if st.button(question, key=f"q_{i}"):
            prompt_from_button = question

st.markdown("""
    </div>
</div>
""", unsafe_allow_html=True)

# 聊天区域
for msg in st.session_state.messages:
    icon = USER_ICON if msg["role"] == "user" else ASSISTANT_ICON
    st.chat_message(msg["role"], avatar=icon).write(msg["content"])

# 获取用户输入
chat_input_text = st.chat_input("请输入你的合规问题...")
user_input = prompt_from_button if prompt_from_button else chat_input_text

# 处理用户输入
if user_input and st.session_state.get("api_configured", False):
    # 显示用户消息
    st.chat_message("user", avatar=USER_ICON).write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # === 1. Gemini 流式输出（标准化格式） ===
    st.markdown("""
    <div class="model-results-section">
        <h2 class="model-compare-header">🔍 模型分析结果</h2>
    """, unsafe_allow_html=True)
    
    # Gemini 卡片
    st.markdown(f"""
    <div class="model-card">
        <div class="model-card-header gemini-header">
            {GEMINI_ICON} Gemini Flash 分析结果
        </div>
        <div class="model-card-content" id="gemini-content">
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    gemini_placeholder = st.empty()
    gemini_full_response = ""
    for chunk in stream_gemini_response(user_input, gemini_model):
        gemini_full_response += chunk
        # 标准化输出格式
        standardized_gemini = standardize_model_output(gemini_full_response, "Gemini")
        cleaned_gemini = clean_extra_newlines(standardized_gemini)
        display_gemini = markdown_to_html(cleaned_gemini)
        
        gemini_placeholder.markdown(f"""
        <div class="model-card">
            <div class="model-card-header gemini-header">
                {GEMINI_ICON} Gemini Flash 分析结果
            </div>
            <div class="model-card-content">
                {display_gemini}<span class="blinking-cursor">|</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 最终渲染 Gemini（标准化格式）
    final_gemini = standardize_model_output(gemini_full_response, "Gemini")
    final_display_gemini = markdown_to_html(final_gemini)
    gemini_placeholder.markdown(f"""
    <div class="model-card">
        <div class="model-card-header gemini-header">
            {GEMINI_ICON} Gemini Flash 分析结果
        </div>
        <div class="model-card-content">
            {final_display_gemini}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # === 2. 智谱 GLM 流式输出（标准化格式） ===
    st.markdown(f"""
    <div class="model-card">
        <div class="model-card-header glm-header">
            {GLM_ICON} 智谱GLM-4 分析结果
        </div>
        <div class="model-card-content" id="glm-content">
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    glm_placeholder = st.empty()
    glm_full_response = ""
    for chunk in stream_glm_response(user_input, glm_api_key):
        glm_full_response += chunk
        # 标准化输出格式
        standardized_glm = standardize_model_output(glm_full_response, "智谱GLM")
        cleaned_glm = clean_extra_newlines(standardized_glm)
        display_glm = markdown_to_html(cleaned_glm)
        
        glm_placeholder.markdown(f"""
        <div class="model-card">
            <div class="model-card-header glm-header">
                {GLM_ICON} 智谱GLM-4 分析结果
            </div>
            <div class="model-card-content">
                {display_glm}<span class="blinking-cursor">|</span>
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 最终渲染 GLM（标准化格式）
    final_glm = standardize_model_output(glm_full_response, "智谱GLM")
    final_display_glm = markdown_to_html(final_glm)
    glm_placeholder.markdown(f"""
    <div class="model-card">
        <div class="model-card-header glm-header">
            {GLM_ICON} 智谱GLM-4 分析结果
        </div>
        <div class="model-card-content">
            {final_display_glm}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    st.markdown("</div>", unsafe_allow_html=True)  # 关闭 model-results-section
    
    # 存储结果
    st.session_state.model_responses[user_input] = {
        "gemini": gemini_full_response,
        "glm": glm_full_response
    }
    
    # === 3. 语义对比分析（标准化格式） ===
    st.markdown("""
    <div class="semantic-section">
        <h2 class="semantic-compare-header">📊 语义层面异同分析</h2>
    """, unsafe_allow_html=True)
    
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
    
    st.markdown("</div>", unsafe_allow_html=True)  # 关闭 semantic-section
    
    # 添加到聊天记录
    combined_response = f"""
### 双模型语义分析总结：
{final_semantic}

### 完整分析参考：
- Gemini 侧重德国财税法规的条文解读和国际通用性
- 智谱GLM 侧重中企出海的实操落地和本土化适配
    """
    st.session_state.messages.append({"role": "assistant", "content": combined_response})

# 清空按钮
st.markdown('<div class="clear-btn-wrapper">', unsafe_allow_html=True)
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

# 闭合主容器
st.markdown('</div>', unsafe_allow_html=True)

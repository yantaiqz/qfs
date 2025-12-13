import streamlit as st
import google.generativeai as genai
import requests
import json
import datetime
import os
import time

# -------------------------------------------------------------
# --- 0. 页面配置和 CSS 注入 (Kimi风格 + 无顶部空白 + 上下排列) ---
# -------------------------------------------------------------

st.set_page_config(
    page_title="德国财税专家QFS", 
    page_icon="🇩🇪", 
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Kimi风格 CSS 注入（核心优化）
st.markdown("""
<style>
    /* 1. 彻底移除所有默认空白和边距 */
    html, body, [data-testid="stAppViewContainer"], [data-testid="stMain"] {
        padding: 0 !important;
        margin: 0 !important;
        background-color: #f5f7fa !important;
    }
    
    /* 2. 隐藏所有默认元素 */
    header, [data-testid="stSidebar"], footer, .stDeployButton, [data-testid="stToolbar"],
    [data-testid="stDecoration"], [data-testid="stStatusWidget"] {
        display: none !important;
    }
    
    /* 3. 全局样式（Kimi风格） */
    .stApp {
        background-color: #f5f7fa !important;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif !important;
        padding: 0 !important;
        margin: 0 !important;
        max-width: 100% !important;
    }

    /* 4. 主容器（Kimi风格居中+窄边距） */
    .main-container {
        max-width: 900px !important;
        width: 100% !important;
        margin: 0 auto !important;
        padding: 16px 24px 80px 24px !important; /* 底部留空给输入框 */
        box-sizing: border-box !important;
    }

    /* 5. 标题区域（Kimi风格） */
    .page-title {
        font-size: 2rem !important;
        font-weight: 600 !important;
        color: #2d3748 !important;
        margin: 8px 0 12px 0 !important;
        line-height: 1.3 !important;
    }
    .subtitle {
        font-size: 0.95rem !important;
        color: #718096 !important;
        margin: 0 0 24px 0 !important;
        font-weight: 400 !important;
        line-height: 1.5 !important;
    }

    /* 6. 聊天消息气泡（Kimi风格） */
    [data-testid="stChatMessage"] {
        margin-bottom: 16px !important;
        padding: 0 !important;
    }
    [data-testid="stChatMessage"][data-role="user"] > div:nth-child(2) {
        background-color: #4285f4 !important;
        color: white !important;
        border-radius: 12px 12px 4px 12px !important;
        padding: 16px 20px !important;
        box-shadow: 0 2px 8px rgba(66, 133, 244, 0.15) !important;
        margin-left: 8px !important;
    }
    [data-testid="stChatMessage"][data-role="assistant"] > div:nth-child(2) {
        background-color: white !important;
        border: 1px solid #e8e8e8 !important;
        border-radius: 12px 12px 12px 4px !important;
        padding: 16px 20px !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
        margin-right: 8px !important;
    }
    [data-testid="stChatMessage"] img {
        width: 36px !important;
        height: 36px !important;
        border-radius: 50% !important;
    }

    /* 7. 常见问题按钮（Kimi风格） */
    .faq-header {
        font-size: 1rem !important;
        font-weight: 600 !important;
        color: #2d3748 !important;
        margin: 20px 0 12px 0 !important;
    }
    div.stButton > button {
        background-color: white !important;
        color: #2d3748 !important;
        border: 1px solid #e8e8e8 !important;
        border-radius: 8px !important;
        font-weight: 500 !important;
        font-size: 0.9rem !important;
        padding: 10px 16px !important;
        width: 100% !important;
        transition: all 0.2s ease !important;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.03) !important;
        margin-bottom: 8px !important;
    }
    div.stButton > button:hover {
        background-color: #f8f9fa !important;
        border-color: #4285f4 !important;
        color: #4285f4 !important;
        transform: translateY(-1px) !important;
        box-shadow: 0 2px 4px rgba(0, 0, 0, 0.05) !important;
    }

    /* 8. 底部输入框（Kimi风格固定底部） */
    [data-testid="stChatInput"] {
        position: fixed !important;
        bottom: 0 !important;
        left: 0 !important;
        right: 0 !important;
        background: white !important;
        padding: 12px 0 !important;
        box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05) !important;
        z-index: 999 !important;
        max-width: 900px !important;
        margin: 0 auto !important;
        width: 100% !important;
        border-top: 1px solid #e8e8e8 !important;
    }
    [data-testid="stChatInput"] textarea {
        border-radius: 10px !important;
        border: 1px solid #e8e8e8 !important;
        padding: 14px 16px !important;
        font-size: 0.95rem !important;
        background-color: #fafafa !important;
        box-shadow: none !important;
        height: auto !important;
    }
    [data-testid="stChatInput"] textarea:focus {
        border-color: #4285f4 !important;
        background-color: white !important;
        box-shadow: 0 0 0 2px rgba(66, 133, 244, 0.1) !important;
    }

    /* 9. 模型结果卡片（Kimi风格上下排列） */
    .model-compare-header {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #2d3748 !important;
        margin: 24px 0 16px 0 !important;
    }
    .model-card {
        background-color: white !important;
        padding: 20px !important;
        border-radius: 12px !important;
        border: 1px solid #e8e8e8 !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04) !important;
        margin-bottom: 16px !important; /* 上下排列的间距 */
    }
    .model-card-header {
        font-size: 1rem !important;
        font-weight: 600 !important;
        margin-bottom: 12px !important;
        display: flex !important;
        align-items: center !important;
    }
    .gemini-header {
        color: #4285f4 !important; /* Google蓝 */
    }
    .glm-header {
        color: #ff6700 !important; /* 智谱橙 */
    }
    .model-card-content {
        font-size: 0.95rem !important;
        line-height: 1.6 !important;
        color: #2d3748 !important;
        white-space: pre-wrap !important;
    }

    /* 10. 语义总结卡片（Kimi风格） */
    .semantic-compare-header {
        font-size: 1.1rem !important;
        font-weight: 600 !important;
        color: #2d3748 !important;
        margin: 20px 0 12px 0 !important;
    }
    .semantic-card {
        background-color: #f0f8fb !important;
        padding: 20px !important;
        border-radius: 12px !important;
        border: 1px solid #e3f2fd !important;
        margin-bottom: 16px !important;
    }
    .semantic-content {
        color: #2d3748 !important;
        line-height: 1.6 !important;
        font-size: 0.95rem !important;
    }

    /* 11. 访问统计（隐藏，简化界面） */
    .visit-stats-top {
        display: none !important;
    }

    /* 12. 清空按钮（Kimi风格） */
    .clear-btn {
        background-color: #f8f9fa !important;
        color: #718096 !important;
        border: 1px solid #e8e8e8 !important;
        border-radius: 8px !important;
        padding: 8px 16px !important;
        font-size: 0.85rem !important;
        margin-top: 8px !important;
    }
    .clear-btn:hover {
        background-color: #f0f0f0 !important;
        color: #4a5568 !important;
        border-color: #dee2e6 !important;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# --- 1. 常量定义与基础配置 ---
# -------------------------------------------------------------

USER_ICON = "👤"
ASSISTANT_ICON = "👩‍💼"
GEMINI_ICON = "♊️"
GLM_ICON = "🧠"

COMMON_LEGAL_QUESTIONS = [
    "怎么应对税务稽查？",
    "货物出口德国如何判断增值税地点？",
    "企业在德国做重组，怎么做税务优化"
]

SYSTEM_INSTRUCTION = """
角色： 德国资深税务师 / 全球跨境合规专家与涉外律师（20年经验）
服务对象： 中国出海企业
核心职能： 针对德国法律环境，提供严谨、专业、具有实操性的合规建议。
核心行为准则已加载：
1. 企业资质评估：启用【企业资信评估报告】结构化输出。
2. 专业语气：启用客观、中立、严谨的法律专业人士语气。
3. 地域精准：回答基于德国国家/地区的现行法律法规。
4. 结构化输出：启用“核心风险点”、“法律依据”、“合规建议”分层结构。
5. 强制数据来源：启用【数据来源/法律依据】章节。
6. 强制免责声明：所有回复末尾强制包含免责声明。
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

# 2.1 Gemini 流式输出函数
def stream_gemini_response(prompt, model):
    """Gemini 流式输出生成器"""
    try:
        stream = model.generate_content(prompt, stream=True)
        for chunk in stream:
            if chunk.text:
                yield chunk.text
                time.sleep(0.05)  # 控制输出速度
    except Exception as e:
        yield f"\n\n⚠️ Gemini调用失败：{str(e)[:100]}..."

# 2.2 智谱GLM 流式输出函数
def stream_glm_response(prompt, api_key, model_name="glm-4"):
    """智谱GLM 流式输出生成器"""
    if not api_key:
        yield "⚠️ 未配置智谱GLM API Key，暂无法获取该模型分析结果。"
        return
    
    try:
        # 智谱流式API配置
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        full_prompt = f"""{SYSTEM_INSTRUCTION}
        用户问题：{prompt}"""
        
        data = {
            "model": model_name,
            "messages": [{"role": "user", "content": full_prompt}],
            "temperature": 0.1,
            "max_tokens": 4096,
            "stream": True  # 开启流式输出
        }
        
        # 发送流式请求
        response = requests.post(url, headers=headers, json=data, stream=True, timeout=30)
        response.raise_for_status()
        
        # 解析流式响应
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
                            time.sleep(0.05)
                    except:
                        continue
    except requests.exceptions.RequestException as e:
        yield f"\n\n⚠️ 智谱GLM调用失败：{str(e)[:100]}..."
    except Exception as e:
        yield f"\n\n⚠️ 智谱GLM处理失败：{str(e)[:100]}..."

# 2.3 语义对比总结函数（修复参数错误）
def generate_semantic_compare(gemini_resp, glm_resp, user_question, gemini_api_key):
    """生成语义层面的异同总结"""
    compare_prompt = f"""
    请作为专业的德国财税分析专家，对比以下两个AI模型针对"{user_question}"的回答，从**语义层面**总结它们的异同：
    
    ### 对比要求：
    1. 相同点：总结核心法律观点、适用法条、风险判断等方面的共识
    2. 不同点：分析在分析角度、建议侧重点、法条解读深度、实操性等方面的差异
    3. 避免逐字逐句对比，聚焦核心语义和逻辑层面
    4. 语言简洁、专业，符合财税咨询场景，每条要点不超过20字
    
    ### Gemini回答：
    {gemini_resp[:1500]}
    
    ### 智谱GLM回答：
    {glm_resp[:1500]}
    
    ### 输出格式（严格遵守）：
    **【核心共识】**
    - 要点1
    - 要点2
    
    **【观点差异】**
    - Gemini：侧重xxx，分析角度xxx
    - 智谱GLM：侧重xxx，分析角度xxx
    
    **【综合建议】**
    结合两个模型的分析，给用户的最优行动建议（不超过50字）
    """
    
    try:
        genai.configure(api_key=gemini_api_key)
        summary_model = genai.GenerativeModel(
            model_name='gemini-flash-latest',
            generation_config={
                "temperature": 0.1, 
                "max_output_tokens": 1000,
                "top_p": 0.95
            }
        )
        stream = summary_model.generate_content(compare_prompt, stream=True)
        for chunk in stream:
            if chunk.text:
                yield chunk.text
                time.sleep(0.02)
    except Exception as e:
        st.error(f"语义总结生成失败：{str(e)}")
        print(f"语义总结错误详情：{e}")
        yield f"""
**【核心共识】**
- 均认可{user_question}相关德国财税法规的核心原则
- 均强调该场景下合规操作和风险防控的必要性

**【观点差异】**
- Gemini：侧重{user_question}法条的字面解读与国际通用性
- 智谱GLM：侧重{user_question}的实操落地与本土化建议

**【综合建议】**
针对{user_question}，兼顾德国法条合规性与中企实操落地需求
"""

# -------------------------------------------------------------
# --- 3. 模型初始化与会话状态 ---
# -------------------------------------------------------------

# API Key 配置（容错）
gemini_api_key = st.secrets.get("GEMINI_API_KEY", "")
glm_api_key = st.secrets.get("GLM_API_KEY", "")

# 容错提示
if not gemini_api_key:
    st.markdown(f"""
    <div style="
        background-color: #fef2f2; 
        color: #dc2626; 
        padding: 1rem; 
        border-radius: 0.5rem; 
        border-left: 4px solid #dc2626;
        margin: 0.5rem 0 1rem 0;
    ">
        ⚠️ 未配置Gemini API Key<br>
        请在 /workspaces/qfs/.streamlit/secrets.toml 中添加：<br>
        <code>GEMINI_API_KEY = "你的Gemini密钥"</code>
    </div>
    """, unsafe_allow_html=True)
    st.session_state["api_configured"] = False
else:
    st.session_state["api_configured"] = True

# 初始化Gemini模型
@st.cache_resource(show_spinner="正在建立QFS的专业知识库...")
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
# --- 4. 主程序入口 (Kimi风格 + 上下排列) ---
# -------------------------------------------------------------

# 主容器
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# 访问统计（隐藏）
st.markdown(f"""
<div class="visit-stats-top">
    {visit_text}
</div>
""", unsafe_allow_html=True)

# 头部区域（简化，贴近Kimi）
st.markdown('<h1 class="page-title">🇩🇪 德国合规QFS</h1>', unsafe_allow_html=True)
st.markdown('<div class="subtitle">资深税务师 / 全球跨境专家 AI 咨询服务</div>', unsafe_allow_html=True)

# 常见问题
st.markdown('<div class="faq-header">💡 常见问题快速查询</div>', unsafe_allow_html=True)
cols = st.columns(3, gap="small")

prompt_from_button = None
for i, question in enumerate(COMMON_LEGAL_QUESTIONS):
    with cols[i]:
        if st.button(question, key=f"q_{i}"):
            prompt_from_button = question

# 聊天区域
# 显示历史消息
for msg in st.session_state.messages:
    icon = USER_ICON if msg["role"] == "user" else ASSISTANT_ICON
    st.chat_message(msg["role"], avatar=icon).write(msg["content"])

# 获取用户输入
chat_input_text = st.chat_input("请输入你的合规问题...")
user_input = prompt_from_button if prompt_from_button else chat_input_text

# 处理用户输入（核心：上下排列）
if user_input and st.session_state.get("api_configured", False):
    # 显示用户消息
    st.chat_message("user", avatar=USER_ICON).write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # === 1. Gemini 流式输出（上） ===
    st.markdown('<div class="model-compare-header">🔍 模型分析结果</div>', unsafe_allow_html=True)
    
    # Gemini 卡片（单独一行）
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
        gemini_placeholder.markdown(f"""
        <div class="model-card">
            <div class="model-card-header gemini-header">
                {GEMINI_ICON} Gemini Flash (正在生成...)
            </div>
            <div class="model-card-content">
                {gemini_full_response}▌
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 最终渲染Gemini
    gemini_placeholder.markdown(f"""
    <div class="model-card">
        <div class="model-card-header gemini-header">
            {GEMINI_ICON} Gemini Flash
        </div>
        <div class="model-card-content">
            {gemini_full_response}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # === 2. 智谱GLM 流式输出（下） ===
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
        glm_placeholder.markdown(f"""
        <div class="model-card">
            <div class="model-card-header glm-header">
                {GLM_ICON} 智谱GLM-4 (正在生成...)
            </div>
            <div class="model-card-content">
                {glm_full_response}▌
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 最终渲染GLM
    glm_placeholder.markdown(f"""
    <div class="model-card">
        <div class="model-card-header glm-header">
            {GLM_ICON} 智谱GLM-4
        </div>
        <div class="model-card-content">
            {glm_full_response}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 存储完整结果
    st.session_state.model_responses[user_input] = {
        "gemini": gemini_full_response,
        "glm": glm_full_response
    }
    
    # === 3. 语义对比 流式输出 ===
    st.markdown('<div class="semantic-compare-header">📊 语义层面异同分析</div>', unsafe_allow_html=True)
    semantic_placeholder = st.empty()
    semantic_full_response = ""
    
    # 流式生成语义总结
    for chunk in generate_semantic_compare(gemini_full_response, glm_full_response, user_input, gemini_api_key):
        semantic_full_response += chunk
        semantic_placeholder.markdown(f"""
        <div class="semantic-card">
            <div class="semantic-content">
                {semantic_full_response}▌
            </div>
        </div>
        """, unsafe_allow_html=True)
    
    # 最终渲染语义总结
    semantic_placeholder.markdown(f"""
    <div class="semantic-card">
        <div class="semantic-content">
            {semantic_full_response}
        </div>
    </div>
    """, unsafe_allow_html=True)
    
    # 添加到聊天记录
    combined_response = f"""
### 双模型语义分析总结：
{semantic_full_response}

### 完整回答参考：
- Gemini 详细分析：{gemini_full_response[:200]}...
- 智谱GLM 详细分析：{glm_full_response[:200]}...
    """
    st.session_state.messages.append({"role": "assistant", "content": combined_response})

# 清空按钮（Kimi风格）
st.button(
    '🧹 清空聊天记录', 
    help="清除所有历史对话", 
    key="clear_btn",
    on_click=lambda: st.session_state.update({
        "messages": [{"role": "assistant", "content": "您好！我是您的德国财税专家QFS。请问您在中国企业出海过程中遇到了哪些财务、税务或商业资质方面的问题？"}],
        "model_responses": {}
    }),
    # class_="clear-btn"
)

# 闭合主容器
st.markdown('</div>', unsafe_allow_html=True)

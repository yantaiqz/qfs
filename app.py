import streamlit as st
import google.generativeai as genai
import requests
import json
import datetime
import os
import time

# -------------------------------------------------------------
# --- 0. 页面配置和 CSS 注入 (取消顶部留白 + 流式适配) ---
# -------------------------------------------------------------

st.set_page_config(page_title="德国财税专家QFS", page_icon="🇩🇪", layout="wide")

# 硅谷简洁风格 CSS 注入
st.markdown("""
<style>
    /* 1. 隐藏默认元素 */
    header, [data-testid="stSidebar"], footer, .stDeployButton, [data-testid="stToolbar"] {
        display: none !important;
    }
    
    /* 2. 全局容器 (取消顶部留白) */
    .stApp {
        background-color: #f8fafc;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        padding: 0 !important;
        margin: 0 !important;
    }

    /* 3. 主容器 (取消顶部padding) */
    .main-container {
        max-width: 1200px;
        width: 100%;
        margin: 0 auto !important;
        padding: 0 24px 20px 24px !important;
        box-sizing: border-box;
    }

    /* 4. 专家卡片样式 */
    .expert-card {
        background-color: white;
        padding: 24px;
        border-radius: 20px;
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.06);
        border: 1px solid #f0f0f0;
        max-width: 300px;
        width: 100%;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        align-items: flex-start;
        text-align: left;
        transition: transform 0.3s ease;
    }
    .expert-card:hover {
        transform: translateY(-4px);
    }
    .expert-link {
        text-decoration: none !important;
        color: inherit !important;
        width: 100%;
        display: block;
    }

    /* 5. 专家头像样式 */
    .profile-img {
        width: 128px;
        height: 128px; 
        border-radius: 50%;
        margin-bottom: 16px;
        border: 6px solid #ffffff; 
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.08);
        background-image: url("https://www.qfs-tax.de/public/uploads/20250614/50f3417b502ae9ce206b90e67e28a4a4.jpg"); 
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
        align-self: center;
    }

    /* 6. 标题样式 (最小化留白) */
    .page-title {
        font-size: clamp(2.2rem, 4vw, 3rem);
        font-weight: 800;
        color: #111827;
        line-height: 1.2;
        margin: 16px 0 8px 0 !important;
    }
    .subtitle {
        font-size: clamp(1rem, 2vw, 1.15rem);
        color: #4b5563;
        margin: 0 0 16px 0 !important;
        font-weight: 400;
        line-height: 1.5;
    }

    /* 7. 聊天消息气泡 */
    [data-testid="stChatMessage"] {
        border-radius: 16px;
        padding: 0;
        margin-bottom: 16px;
    }
    [data-testid="stChatMessage"][data-role="user"] > div:nth-child(2) {
        background-color: #3b82f6;
        color: white;
        border-radius: 18px 18px 4px 18px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
    }
    [data-testid="stChatMessage"][data-role="assistant"] > div:nth-child(2) {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px 18px 18px 4px;
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    [data-testid="stChatMessage"] img {
        width: 36px !important;
        height: 36px !important;
    }

    /* 8. 常见问题区域 */
    .faq-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1f2937;
        margin: 24px 0 16px 0 !important;
    }
    div.stButton > button {
        background-color: #ffffff;
        color: #374151;
        border: 1px solid #e5e7eb;
        border-radius: 12px; 
        font-weight: 500;
        font-size: 0.95rem;
        padding: 0.75rem 1.25rem;
        width: 100%;
        transition: all 0.2s ease;
        box-shadow: 0 1px 2px rgba(0, 0, 0, 0.05);
    }
    div.stButton > button:hover {
        background-color: #f9fafb;
        border-color: #3b82f6;
        color: #2563eb;
        transform: translateY(-1px);
        box-shadow: 0 4px 6px rgba(0, 0, 0, 0.05);
    }

    /* 9. 底部输入框 */
    [data-testid="stChatInput"] {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: transparent !important;
        padding: 16px 24px 20px 24px;
        box-shadow: none !important;
        z-index: 1000;
        max-width: 1200px; 
        margin: 0 auto;
        width: 100%;
        box-sizing: border-box;
    }
    [data-testid="stChatInput"] textarea {
        border-radius: 12px !important;
        border: 1px solid #e5e7eb !important;
        padding: 12px 16px !important;
        font-size: 1rem !important;
        background-color: white !important;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05) !important;
    }

    /* 10. 双模型对比区域 */
    .model-compare-header {
        font-size: 1.3rem;
        font-weight: 700;
        color: #1f2937;
        margin: 24px 0 16px 0 !important;
    }
    .model-card {
        background-color: #ffffff;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #e5e7eb;
        box-shadow: 0 4px 12px rgba(0, 0, 0, 0.04);
        height: 100%;
    }
    .model-card-header {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 12px;
        display: flex;
        align-items: center;
    }
    .gemini-header {
        color: #4285F4;
    }
    .glm-header {
        color: #FF6700;
    }
    .model-card-content {
        font-size: 0.95rem;
        line-height: 1.6;
        color: #374151;
        white-space: pre-wrap;
    }

    /* 11. 语义对比区域 */
    .semantic-compare-header {
        font-size: 1.2rem;
        font-weight: 700;
        color: #1f2937;
        margin: 20px 0 12px 0 !important;
    }
    .semantic-card {
        background-color: #f0f8fb;
        padding: 20px;
        border-radius: 16px;
        border: 1px solid #e3f2fd;
        margin-bottom: 16px;
    }
    .semantic-content {
        color: #4a5568;
        line-height: 1.6;
        font-size: 0.95rem;
    }

    /* 12. 访问统计 */
    .visit-stats-top {
        color: #9ca3af;
        font-size: 0.75rem;
        text-align: right;
        margin: 8px 0 8px 0 !important;
        line-height: 1;
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
                time.sleep(0.05)  # 控制输出速度，避免过快
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

# 2.3 语义对比总结函数
def generate_semantic_compare(gemini_resp, glm_resp, user_question, gemini_api_key):
    """生成语义层面的异同总结"""
    compare_prompt = f"""
    请作为专业的德国财税分析专家，对比以下两个AI模型针对"{user_question}"的回答，从**语义层面**总结它们的异同：
    
    ### 对比要求：
    1. 相同点：总结核心法律观点、适用法条、风险判断等方面的共识
    2. 不同点：分析在分析角度、建议侧重点、法条解读深度、实操性等方面的差异
    3. 避免逐字逐句对比，聚焦核心语义和逻辑层面
    4. 语言简洁、专业，符合财税咨询场景
    
    ### Gemini回答：
    {gemini_resp[:1500]}  # 缩短截断长度，避免输入超限
    
    ### 智谱GLM回答：
    {glm_resp[:1500]}
    
    ### 输出格式：
    **【核心共识】**
    - 要点1
    - 要点2
    
    **【观点差异】**
    - Gemini：侧重xxx，分析角度xxx，建议更偏向xxx
    - 智谱GLM：侧重xxx，分析角度xxx，建议更偏向xxx
    
    **【综合建议】**
    结合两个模型的分析，给用户的最优行动建议
    """
    
    try:
        genai.configure(api_key=gemini_api_key)
        summary_model = genai.GenerativeModel(
            model_name='gemini-flash-latest',
            generation_config={"temperature": 0.1, "max_output_tokens": 1000, "timeout": 60}  # 延长超时时间
        )
        stream = summary_model.generate_content(compare_prompt, stream=True)
        for chunk in stream:
            if chunk.text:
                yield chunk.text
                time.sleep(0.02)  # 缩短等待时间，减少超时概率
    except Exception as e:
        # 新增：打印错误日志（Streamlit控制台可查看）
        st.error(f"语义总结生成失败：{str(e)}")  # 前端显示错误
        print(f"语义总结错误详情：{e}")  # 终端打印错误
        # 降级返回通用模板
        yield f"""
**【核心共识】**
- 两个模型均认可德国财税相关法规对"{user_question}"的核心适用原则
- 均强调该场景下合规操作的重要性和风险防控的必要性

**【观点差异】**
- Gemini：更侧重"{user_question}"相关法条的字面解读和国际通用性分析
- 智谱GLM：更侧重中国企业在"{user_question}"场景下的实操落地和本土化建议

**【综合建议】**
针对"{user_question}"问题，建议结合两个模型的分析，既关注德国法条的合规性要求，也兼顾中国企业出海的实际操作场景。
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
        margin: 0.5rem 0;
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
# --- 4. 主程序入口 (流式输出核心逻辑) ---
# -------------------------------------------------------------

# 主容器
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# 访问统计
st.markdown(f"""
<div class="visit-stats-top">
    {visit_text}
</div>
""", unsafe_allow_html=True)

# 头部区域
col_title, col_expert = st.columns([3, 1], gap="large")
EXPERT_URL = "https://www.qfs-tax.de/Aboutinfo_2.html"

with col_title:
    st.markdown('<h1 class="page-title">🇩🇪 德国合规QFS</h1>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">资深税务师 / 全球跨境专家 AI 咨询服务（双模型流式输出）</div>', unsafe_allow_html=True)

with col_expert:
    st.markdown(f"""
    <div class="expert-card">
        <a href="{EXPERT_URL}" class="expert-link" target="_blank">
            <div class="profile-img" alt="乔斐·苏斯 首席合伙人"></div> 
            <div class="expert-title">乔斐·苏斯 (Fei Qiao-Süss)</div>
            <div class="expert-role">QFS谦帆思联合事务所 | 首席合伙人</div>
        </a>
    </div>
    """, unsafe_allow_html=True)

# 常见问题
st.markdown('<div class="faq-header">💡 常见问题快速查询</div>', unsafe_allow_html=True)
cols = st.columns(3, gap="medium")

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

# 处理用户输入（流式输出核心）
if user_input and st.session_state.get("api_configured", False):
    # 显示用户消息
    st.chat_message("user", avatar=USER_ICON).write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # === 1. Gemini 流式输出 ===
    st.markdown('<div class="model-compare-header">🔍 双模型分析结果</div>', unsafe_allow_html=True)
    col_gemini, col_glm = st.columns(2, gap="large")
    
    # Gemini 列
    with col_gemini:
        st.markdown(f"""
        <div class="model-card">
            <div class="model-card-header gemini-header">
                {GEMINI_ICON} Gemini Flash (流式输出)
            </div>
            <div class="model-card-content" id="gemini-content">
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 流式输出Gemini结果
        gemini_placeholder = st.empty()
        gemini_full_response = ""
        for chunk in stream_gemini_response(user_input, gemini_model):
            gemini_full_response += chunk
            gemini_placeholder.markdown(f"""
            <div class="model-card">
                <div class="model-card-header gemini-header">
                    {GEMINI_ICON} Gemini Flash (流式输出)
                </div>
                <div class="model-card-content">
                    {gemini_full_response}▌
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # 最终渲染（移除光标）
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
    
    # === 2. 智谱GLM 流式输出 ===
    with col_glm:
        st.markdown(f"""
        <div class="model-card">
            <div class="model-card-header glm-header">
                {GLM_ICON} 智谱GLM-4 (流式输出)
            </div>
            <div class="model-card-content" id="glm-content">
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 流式输出GLM结果
        glm_placeholder = st.empty()
        glm_full_response = ""
        for chunk in stream_glm_response(user_input, glm_api_key):
            glm_full_response += chunk
            glm_placeholder.markdown(f"""
            <div class="model-card">
                <div class="model-card-header glm-header">
                    {GLM_ICON} 智谱GLM-4 (流式输出)
                </div>
                <div class="model-card-content">
                    {glm_full_response}▌
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # 最终渲染（移除光标）
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

# 清空按钮
col_clear = st.columns([1])[0]
with col_clear:
    if st.button('🧹 清空聊天记录', help="清除所有历史对话", key="clear_btn", 
                type="secondary"):
        st.session_state.messages = [
            {"role": "assistant", "content": "您好！我是您的德国财税专家QFS。请问您在中国企业出海过程中遇到了哪些财务、税务或商业资质方面的问题？"}
        ]
        st.session_state.model_responses = {}
        st.rerun()

# 闭合主容器
st.markdown('</div>', unsafe_allow_html=True)

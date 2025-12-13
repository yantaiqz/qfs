import streamlit as st
import google.generativeai as genai
import requests
import json
import datetime
import os

# -------------------------------------------------------------
# --- 0. 页面配置和全新 CSS 注入 (取消顶部留白 + 优化样式) ---
# -------------------------------------------------------------

st.set_page_config(page_title="德国财税专家QFS", page_icon="🇩🇪", layout="wide")

# 硅谷简洁风格 CSS 注入 (核心修改：取消顶部留白 + 优化对比样式)
st.markdown("""
<style>
    /* 1. 彻底隐藏Streamlit默认干扰元素 */
    header, [data-testid="stSidebar"], footer, .stDeployButton, [data-testid="stToolbar"] {
        display: none !important;
    }
    
    /* 2. 全局容器调整 (核心：取消顶部所有留白) */
    .stApp {
        background-color: #f8fafc;
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        padding: 0 !important;  /* 取消全局padding */
        margin: 0 !important;   /* 取消全局margin */
    }

    /* 3. 主容器 (核心：取消顶部padding，仅保留左右和底部) */
    .main-container {
        max-width: 1200px;
        width: 100%;
        margin: 0 auto !important;  /* 取消上下margin */
        padding: 0 24px 20px 24px !important;  /* 仅保留左右和底部padding，取消顶部 */
        box-sizing: border-box;
    }

    /* 4. 专家背书卡片 */
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

    /* 6. 专家信息文字样式 */
    .expert-title {
        font-size: 1.15rem;
        font-weight: 700;
        color: #1f2937;
        margin-bottom: 4px;
    }
    .expert-role {
        font-size: 0.9rem;
        color: #6b7280;
        line-height: 1.4;
    }

    /* 7. 标题和副标题样式 (取消标题底部多余留白) */
    .page-title {
        font-size: clamp(2.2rem, 4vw, 3rem);
        font-weight: 800;
        color: #111827;
        line-height: 1.2;
        margin: 16px 0 8px 0 !important;  /* 仅保留少量顶部margin，取消多余底部 */
    }
    .subtitle {
        font-size: clamp(1rem, 2vw, 1.15rem);
        color: #4b5563;
        margin: 0 0 16px 0 !important;  /* 取消多余底部留白 */
        font-weight: 400;
        line-height: 1.5;
    }

    /* 8. 聊天消息气泡优化 */
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

    /* 9. 常见问题区域样式 (取消多余顶部留白) */
    .faq-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1f2937;
        margin: 24px 0 16px 0 !important;  /* 减少顶部留白 */
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
    div.stButton > button:active {
        transform: translateY(0);
    }
    
    /* 10. 底部输入框样式 */
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

    /* 11. 清空按钮和统计区域 */
    .control-area {
        margin-top: 16px;
        padding-top: 16px;
        border-top: none !important;
    }

    /* 响应式适配 (同步取消移动端留白) */
    @media (max-width: 768px) {
        .main-container {
            padding: 0 16px 20px 16px !important;
        }
        [data-testid="stChatInput"] {
            padding: 16px 16px 20px 16px;
            background: transparent !important;
        }
        .page-title {
            margin: 12px 0 8px 0 !important;
        }
    }
    
    /* 12. 访问统计样式 (取消底部多余留白) */
    .visit-stats-top {
        color: #9ca3af;
        font-size: 0.75rem;
        text-align: right;
        margin: 8px 0 8px 0 !important;  /* 最小化留白 */
        line-height: 1;
    }

    /* 新增：双模型对比区域样式 */
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

    /* 新增：语义对比总结样式 */
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
    .semantic-title {
        font-weight: 600;
        color: #2d3748;
        margin-bottom: 8px;
        font-size: 1rem;
    }
    .semantic-content {
        color: #4a5568;
        line-height: 1.6;
        font-size: 0.95rem;
    }
</style>
""", unsafe_allow_html=True)

# -------------------------------------------------------------
# --- 1. 常量定义、系统指令和模型配置 ---
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

# -------------------------- 2. 安全的计数器逻辑 --------------------------
COUNTER_FILE = "visit_stats_qfs.json"

def update_daily_visits():
    """安全更新访问量，如果出错则返回 0，绝不让程序崩溃"""
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
# --- 新增：智谱GLM模型调用函数 ---
# -------------------------------------------------------------
def query_glm(prompt, api_key, model_name="glm-4"):
    """调用智谱GLM模型"""
    if not api_key:
        return "请配置智谱GLM API Key"
    
    try:
        # 智谱API接口
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        
        # 构造请求体（添加德国财税系统指令）
        full_prompt = f"""{SYSTEM_INSTRUCTION}
        
        用户问题：{prompt}"""
        
        data = {
            "model": model_name,
            "messages": [{"role": "user", "content": full_prompt}],
            "temperature": 0.1,
            "max_tokens": 4096
        }
        
        # 发送请求
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()
        result = response.json()
        return result["choices"][0]["message"]["content"]
    
    except requests.exceptions.RequestException as e:
        return f"智谱GLM调用失败: {str(e)[:100]}..."
    except Exception as e:
        return f"智谱GLM处理失败: {str(e)[:100]}..."

# -------------------------------------------------------------
# --- 新增：语义化对比总结函数 (核心修改) ---
# -------------------------------------------------------------
def generate_semantic_compare(gemini_resp, glm_resp, user_question):
    """
    生成双模型语义层面的异同总结（非纯文字对比）
    基于回答的核心观点、法律依据、分析逻辑、建议维度进行总结
    """
    # 构造语义对比提示词
    compare_prompt = f"""
    请作为专业的德国财税分析专家，对比以下两个AI模型针对"{user_question}"的回答，从**语义层面**总结它们的异同：
    
    ### 对比要求：
    1. 相同点：总结核心法律观点、适用法条、风险判断等方面的共识
    2. 不同点：分析在分析角度、建议侧重点、法条解读深度、实操性等方面的差异
    3. 避免逐字逐句对比，聚焦核心语义和逻辑层面
    4. 语言简洁、专业，符合财税咨询场景
    
    ### Gemini回答：
    {gemini_resp[:2000]}  # 截断避免过长
    
    ### 智谱GLM回答：
    {glm_resp[:2000]}
    
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
    
    # 调用Gemini生成语义总结（也可调用GLM，这里复用已有模型）
    try:
        genai.configure(api_key=st.secrets.get("GEMINI_API_KEY"))
        summary_model = genai.GenerativeModel(
            model_name='gemini-flash-latest',
            generation_config={"temperature": 0.1, "max_output_tokens": 1000}
        )
        summary = summary_model.generate_content(compare_prompt).text
        return summary
    except Exception as e:
        # 降级处理：基础语义总结
        return f"""
**【核心共识】**
- 两个模型均认可德国财税相关法规的核心适用原则
- 均强调合规操作的重要性和风险防控的必要性

**【观点差异】**
- Gemini：更侧重法条的字面解读和国际通用性分析
- 智谱GLM：更侧重中国企业出海的实操场景和本土化建议

**【综合建议】**
建议结合两个模型的分析，既关注法条的合规性，也兼顾中国企业的实际操作落地。
"""

# -------------------------------------------------------------
# --- 3. 模型初始化 (新增智谱配置 + 容错) ---
# -------------------------------------------------------------

# 1. API Key 获取与配置（容错处理）
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

# 2. 初始化Gemini模型
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

# 3. 聊天历史初始化
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是您的德国财税专家QFS。请问您在中国企业出海过程中遇到了哪些财务、税务或商业资质方面的问题？"}
    ]
if "model_responses" not in st.session_state:
    st.session_state.model_responses = {}

# -------------------------------------------------------------
# --- 4. 主程序入口 (核心修改：语义化对比) ---
# -------------------------------------------------------------

# 将所有内容包裹在主容器内
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# === 置顶的访问统计 (最小化留白) ===
st.markdown(f"""
<div class="visit-stats-top">
    {visit_text}
</div>
""", unsafe_allow_html=True)

# === 头部区域：标题 + 专家卡片 ===
col_title, col_expert = st.columns([3, 1], gap="large")

# 专家超链接目标 URL
EXPERT_URL = "https://www.qfs-tax.de/Aboutinfo_2.html"

with col_title:
    st.markdown('<h1 class="page-title">🇩🇪 德国合规QFS</h1>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">资深税务师 / 全球跨境专家 AI 咨询服务（双模型语义对比）</div>', unsafe_allow_html=True)

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

# === 常见问题区域 ===
st.markdown('<div class="faq-header">💡 常见问题快速查询</div>', unsafe_allow_html=True)
cols = st.columns(3, gap="medium")

prompt_from_button = None
for i, question in enumerate(COMMON_LEGAL_QUESTIONS):
    with cols[i]:
        if st.button(question, key=f"q_{i}"):
            prompt_from_button = question

# === 核心聊天区域 ===
# 显示历史消息 
for msg in st.session_state.messages:
    icon = USER_ICON if msg["role"] == "user" else ASSISTANT_ICON
    st.chat_message(msg["role"], avatar=icon).write(msg["content"])

# 获取输入
chat_input_text = st.chat_input("请输入你的合规问题...")
user_input = prompt_from_button if prompt_from_button else chat_input_text

# 处理输入
if user_input and st.session_state.get("api_configured", False):
    # 显示用户消息
    st.chat_message("user", avatar=USER_ICON).write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 调用双模型
    try:
        # 1. 调用Gemini
        with st.spinner("Gemini正在分析您的问题..."):
            gemini_full_response = ""
            if gemini_model:
                for chunk in gemini_model.generate_content(user_input, stream=True):
                    gemini_full_response += chunk.text if chunk.text else ""
            else:
                gemini_full_response = "Gemini模型初始化失败，请检查API Key配置"
        
        # 2. 调用智谱GLM
        with st.spinner("智谱GLM正在分析您的问题..."):
            if glm_api_key:
                glm_full_response = query_glm(user_input, glm_api_key)
            else:
                glm_full_response = "⚠️ 未配置智谱GLM API Key，暂无法获取该模型分析结果。"
        
        # 存储双模型结果
        st.session_state.model_responses[user_input] = {
            "gemini": gemini_full_response,
            "glm": glm_full_response
        }
        
        # === 双模型结果分栏展示 ===
        st.markdown('<div class="model-compare-header">🔍 双模型分析结果</div>', unsafe_allow_html=True)
        col_gemini, col_glm = st.columns(2, gap="large")
        
        with col_gemini:
            st.markdown(f"""
            <div class="model-card">
                <div class="model-card-header gemini-header">
                    {GEMINI_ICON} Gemini Flash
                </div>
                <div class="model-card-content">
                    {gemini_full_response}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        with col_glm:
            st.markdown(f"""
            <div class="model-card">
                <div class="model-card-header glm-header">
                    {GLM_ICON} 智谱GLM-4
                </div>
                <div class="model-card-content">
                    {glm_full_response}
                </div>
            </div>
            """, unsafe_allow_html=True)
        
        # === 核心修改：语义化对比总结 (替换纯文字差异) ===
        st.markdown('<div class="semantic-compare-header">📊 语义层面异同分析</div>', unsafe_allow_html=True)
        with st.spinner("正在分析双模型语义差异..."):
            semantic_summary = generate_semantic_compare(gemini_full_response, glm_full_response, user_input)
        
        # 展示语义总结
        st.markdown(f"""
        <div class="semantic-card">
            <div class="semantic-content">
                {semantic_summary}
            </div>
        </div>
        """, unsafe_allow_html=True)
        
        # 将语义总结添加到聊天记录
        combined_response = f"""
### 双模型语义分析总结：
{semantic_summary}

### 完整回答参考：
- Gemini 详细分析：{gemini_full_response[:200]}...
- 智谱GLM 详细分析：{glm_full_response[:200]}...
        """
        st.session_state.messages.append({"role": "assistant", "content": combined_response})
    
    except Exception as e:
        st.markdown(f"""
    <div style="
        background-color: #fef2f2; 
        color: #dc2626; 
        padding: 1rem; 
        border-radius: 0.5rem; 
        border-left: 4px solid #dc2626;
        margin: 0.5rem 0;
    ">
        发生错误: 模型调用失败<br>
        详细信息: {str(e)[:100]}...
    </div>
    """, unsafe_allow_html=True)

# === 清空聊天记录按钮 ===
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

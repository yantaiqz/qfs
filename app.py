import streamlit as st
import google.generativeai as genai
import requests
import json
import datetime
import os

# -------------------------------------------------------------
# --- 0. 页面配置和全新 CSS 注入 (硅谷简洁风 V2.1 优化版) ---
# -------------------------------------------------------------

st.set_page_config(page_title="德国财税专家QFS", page_icon="🇩🇪", layout="wide")

# 硅谷简洁风格 CSS 注入 (优化间距、阴影、聊天气泡、响应式)
st.markdown("""
<style>
    /* 1. 彻底隐藏Streamlit默认干扰元素 */
    header, [data-testid="stSidebar"], footer, .stDeployButton, [data-testid="stToolbar"] {
        display: none !important;
    }
    
    /* 2. 全局容器调整 (移除底部留白，适配无白色底部) */
    .stApp {
        background-color: #f8fafc; /* 保持背景色一致 */
        font-family: 'Inter', -apple-system, BlinkMacSystemFont, sans-serif;
        padding: 0;
        margin: 0;
    }

    /* 3. 主容器 (关键：移除底部超大留白，适配输入框悬浮) */
    .main-container {
        max-width: 1200px;
        width: 100%;
        margin: 0 auto;
        padding: 32px 24px 20px 24px; /* 底部留白从90px减到20px */
        box-sizing: border-box;
    }

    /* 4. 专家背书卡片 (优化比例和阴影层次) */
    .expert-card {
        background-color: white;
        padding: 24px; /* 优化内边距 */
        border-radius: 20px; /* 更圆润的边角 */
        box-shadow: 0 10px 30px rgba(0, 0, 0, 0.06); /* 更自然的阴影 */
        border: 1px solid #f0f0f0; /* 轻量边框增强层次感 */
        max-width: 300px;
        width: 100%;
        margin: 0 auto;
        display: flex;
        flex-direction: column;
        align-items: flex-start; /* 左对齐更符合阅读习惯 */
        text-align: left;
        transition: transform 0.3s ease;
    }
    .expert-card:hover {
        transform: translateY(-4px); /* 悬停上浮效果 */
    }
    .expert-link {
        text-decoration: none !important;
        color: inherit !important;
        width: 100%;
        display: block;
    }

    /* 5. 专家头像样式 (优化比例和层次感) */
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
        align-self: center; /* 头像居中更美观 */
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

    /* 7. 标题和副标题样式 (优化层级) */
    .page-title {
        font-size: clamp(2.2rem, 4vw, 3rem); /* 响应式字号 */
        font-weight: 800;
        color: #111827;
        line-height: 1.2;
        margin-bottom: 8px;
    }
    .subtitle {
        font-size: clamp(1rem, 2vw, 1.15rem);
        color: #4b5563;
        margin-bottom: 32px;
        font-weight: 400;
        line-height: 1.5;
    }

    /* 8. 聊天消息气泡优化 (增强区分度) */
    [data-testid="stChatMessage"] {
        border-radius: 16px;
        padding: 0;
        margin-bottom: 16px;
    }
    /* 用户消息 */
    [data-testid="stChatMessage"][data-role="user"] > div:nth-child(2) {
        background-color: #3b82f6;
        color: white;
        border-radius: 18px 18px 4px 18px; /* 不对称圆角更自然 */
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(59, 130, 246, 0.15);
    }
    /* 助手消息 */
    [data-testid="stChatMessage"][data-role="assistant"] > div:nth-child(2) {
        background-color: #ffffff;
        border: 1px solid #e5e7eb;
        border-radius: 18px 18px 18px 4px; /* 不对称圆角 */
        padding: 16px 20px;
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.04);
    }
    /* 头像大小优化 */
    [data-testid="stChatMessage"] img {
        width: 36px !important;
        height: 36px !important;
    }

    /* 9. 常见问题区域样式 */
    .faq-header {
        font-size: 1.25rem;
        font-weight: 600;
        color: #1f2937;
        margin: 40px 0 16px 0;
    }
    /* 常见问题按钮样式 - 现代扁平化设计 */
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
    
    /* 10. 底部输入框样式 (核心修改：去掉白色背景，融入全局) */
    [data-testid="stChatInput"] {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: transparent !important; /* 去掉白色背景 */
        padding: 16px 24px 20px 24px; /* 调整内边距 */
        box-shadow: none !important; /* 去掉阴影 */
        z-index: 1000;
        max-width: 1200px; 
        margin: 0 auto;
        width: 100%;
        box-sizing: border-box;
    }
    /* 输入框内部样式 (适配透明背景) */
    [data-testid="stChatInput"] textarea {
        border-radius: 12px !important;
        border: 1px solid #e5e7eb !important;
        padding: 12px 16px !important;
        font-size: 1rem !important;
        background-color: white !important; /* 仅输入框本身保留白色，保证可读性 */
        box-shadow: 0 2px 8px rgba(0, 0, 0, 0.05) !important;
    }

    /* 11. 清空按钮和统计区域 (去掉边框/留白，融入背景) */
    .control-area {
        margin-top: 24px;
        padding-top: 16px;
        border-top: none !important; /* 去掉顶部边框 */
    }

    /* 响应式适配 (同步修改移动端) */
    @media (max-width: 768px) {
        .main-container {
            padding: 24px 16px 20px 16px; /* 移动端底部留白也减少 */
        }
        [data-testid="stChatInput"] {
            padding: 16px 16px 20px 16px;
            background: transparent !important;
        }
    }
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------
# --- 1. 常量定义、系统指令和模型配置 (保持核心逻辑) ---
# -------------------------------------------------------------

USER_ICON = "👤"
ASSISTANT_ICON = "👩‍💼"

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
COUNTER_FILE = "visit_stats.json"

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
# --- 3. 模型初始化 ---
# -------------------------------------------------------------

# 1. API Key 获取与配置
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("请配置 API Key")
    st.stop()
genai.configure(api_key=api_key)

# 2. 缓存模型初始化
@st.cache_resource(show_spinner="正在建立QFS的专业知识库...")
def initialize_model():
    generation_config = {
        "max_output_tokens": 4096,
        "temperature": 0.1,  # 降低随机性，提升回答严谨性
        "top_p": 0.95
    }
    
    model = genai.GenerativeModel(
        model_name='gemini-2.5-flash', 
        system_instruction=SYSTEM_INSTRUCTION,
        generation_config=generation_config
    )
    return model

model = initialize_model()

# 3. 聊天历史初始化
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是您的德国财税专家QFS。请问您在中国企业出海过程中遇到了哪些财务、税务或商业资质方面的问题？"}
    ]

# -------------------------------------------------------------
# --- 4. 主程序入口 (优化排版结构) ---
# -------------------------------------------------------------

# 将所有内容包裹在主容器内
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# === 头部区域：标题 + 专家卡片 (优化响应式布局) ===
col_title, col_expert = st.columns([3, 1], gap="large")

# 专家超链接目标 URL
EXPERT_URL = "https://www.qfs-tax.de/Aboutinfo_2.html"

with col_title:
    st.markdown('<h1 class="page-title">🇩🇪 德国合规QFS</h1>', unsafe_allow_html=True)
    st.markdown('<div class="subtitle">资深税务师 / 全球跨境专家 AI 咨询服务</div>', unsafe_allow_html=True)

with col_expert:
    # 专家卡片 (优化结构和样式)
    st.markdown(f"""
    <div class="expert-card">
        <a href="{EXPERT_URL}" class="expert-link" target="_blank">
            <div class="profile-img" alt="乔斐·苏斯 首席合伙人"></div> 
            <div class="expert-title">乔斐·苏斯 (Fei Qiao-Süss)</div>
            <div class="expert-role">QFS谦帆思联合事务所 | 首席合伙人</div>
        </a>
    </div>
    """, unsafe_allow_html=True)

# === 常见问题区域 (优化标题和布局) ===
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
if user_input:
    # 显示用户消息
    st.chat_message("user", avatar=USER_ICON).write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 调用 Gemini (流式输出)
    try:
        with st.chat_message("assistant", avatar=ASSISTANT_ICON):
            message_placeholder = st.empty()
            full_response = ""
            
            for chunk in model.generate_content(user_input, stream=True):
                full_response += chunk.text if chunk.text else ""
                message_placeholder.markdown(full_response + "▌")
        
            # 流式结束后替换占位符
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    except Exception as e:
        st.error(f"""
        发生错误: 调用Gemini API失败
        <br>请检查：1. API Key 是否有效 2. 配额是否充足
        <br>详细信息: {str(e)[:100]}...
        """, unsafe_allow_html=True)

# === 底部控制区域 (清空按钮 + 访问统计) ===
st.markdown('<div class="control-area">', unsafe_allow_html=True)
col_clear, col_stats = st.columns([1, 1])

with col_clear:
    # 清空聊天记录按钮
    if st.button('🧹 清空聊天记录', help="清除所有历史对话", key="clear_btn", 
                kwargs={"use_container_width": False}, 
                type="secondary"):
        st.session_state.messages = [
            {"role": "assistant", "content": "您好！我是您的德国财税专家QFS。请问您在中国企业出海过程中遇到了哪些财务、税务或商业资质方面的问题？"}
        ]
        st.rerun()

with col_stats:
    st.markdown(f'<div class="visit-stats">{visit_text}</div>', unsafe_allow_html=True)

st.markdown('</div>', unsafe_allow_html=True)  # 闭合控制区域

# 闭合主容器
st.markdown('</div>', unsafe_allow_html=True)

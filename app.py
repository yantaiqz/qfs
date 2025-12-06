import streamlit as st
import google.generativeai as genai
import requests
import json
import datetime
import os

# -------------------------------------------------------------
# --- 0. 页面配置和全新 CSS 注入 (硅谷简洁风 V2.0) ---
# -------------------------------------------------------------

st.set_page_config(page_title="德国财税专家QFS", page_icon="🇩🇪", layout="wide")

# 硅谷简洁风格 CSS 注入 (优化间距、阴影、聊天气泡)
st.markdown("""
<style>
    /* 1. 彻底隐藏Streamlit默认干扰元素 */
    header, [data-testid="stSidebar"], footer, .stDeployButton, [data-testid="stToolbar"] {
        display: none !important;
    }
    
    /* 2. 全局容器调整 */
    .stApp {
        background-color: #f8fafc; /* 柔和的浅灰色背景 */
        font-family: 'Inter', sans-serif;
        padding: 0;
        margin: 0;
    }

    /* 3. 头部卡片和主要内容的容器样式 */
    .main-container {
        max-width: 1000px; /* 限制内容最大宽度，居中 */
        margin: 0 auto;
        padding: 24px 20px 80px 20px; /* 顶部和底部增加留白 */
    }

    /* 4. 专家背书卡片 (强化阴影和圆角) */
    .expert-card {
        background-color: white;
        padding: 20px 15px; /* 略微减小左右边距 */
        border-radius: 16px; /* 更大的圆角 */
        box-shadow: 0 8px 25px rgba(0, 0, 0, 0.08); /* 更明显的硅谷风格阴影 */
        border: none; /* 移除边框，依赖阴影 */
        max-width: 280px; /* 略微放大卡片宽度 */
        margin-left: auto;
        margin-right: auto;
        display: flex;
        flex-direction: column;
        align-items: left;
        text-align: left;
    }
    .expert-link {
        text-decoration: none !important;
        color: inherit !important;
        cursor: pointer;
        transition: transform 0.2s, opacity 0.2s;
    }
    .expert-link:hover {
        transform: translateY(-2px); /* 悬停微动效果 */
        opacity: 0.95; 
    }

    /* 5. 专家头像样式 (已放大并支持剪裁) */
    .profile-img {
        width: 120px; /* 调整为更平衡的尺寸 */
        height: 120px; 
        border-radius: 50%;
        margin-bottom: 12px;
        border: 5px solid #ffffff; /* 白色内边框 */
        box-shadow: 0 0 0 1px #e5e7eb; /* 外部细边框 */
        
        /* 图片来源已更新为实际链接 */
        background-image: url("https://www.qfs-tax.de/public/uploads/20250614/50f3417b502ae9ce206b90e67e28a4a4.jpg"); 
        background-size: cover;
        background-position: center;
        background-repeat: no-repeat;
    }

    /* 6. 标题和副标题样式 */
    h1 {
        font-size: 2.8rem; /* 增大主标题 */
        font-weight: 900; /* 更粗的字体 */
        color: #1f2937;
        line-height: 1.1;
    }
    .subtitle {
        font-size: 1.1rem;
        color: #6b7280;
        margin-top: -10px;
        margin-bottom: 30px;
        font-weight: 400;
    }

    /* 7. 聊天消息气泡优化 */
    .stChatMessage {
        border-radius: 12px;
        padding: 15px;
        margin-bottom: 12px;
        box-shadow: 0 1px 3px rgba(0, 0, 0, 0.05); /* 消息气泡轻微阴影 */
    }
    /* 调整助手气泡颜色 */
    [data-testid="stChatMessage"]:nth-child(odd) > div:nth-child(2) {
        background-color: #f3f4f6; /* 助手气泡使用浅灰色背景 */
        border-radius: 12px;
    }
    
    /* 8. 常见问题按钮样式 - 更现代的圆角和点击效果 */
    div.stButton > button {
        background-color: #ffffff;
        color: #4b5563;
        border: 1px solid #d1d5db;
        border-radius: 8px; 
        font-weight: 600; /* 略微加粗 */
        padding: 0.6rem 1rem;
        box-shadow: none;
    }
    div.stButton > button:hover {
        background-color: #eff6ff; /* 悬停时淡蓝色背景 */
        border-color: #3b82f6;
        color: #1d4ed8;
    }
    
    /* 9. 底部固定输入框样式 (保持不变) */
    [data-testid="stChatInput"] {
        position: fixed;
        bottom: 0;
        left: 0;
        right: 0;
        background: white;
        padding: 15px 20px;
        box-shadow: 0 -2px 10px rgba(0, 0, 0, 0.05);
        z-index: 1000;
        max-width: 1000px; 
        margin: 0 auto;
    }
</style>
""", unsafe_allow_html=True)


# -------------------------------------------------------------
# --- 1. 常量定义、系统指令和模型配置 (保持不变) ---
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
企业资质评估：启用【企业资信评估报告】结构化输出。
专业语气：启用客观、中立、严谨的法律专业人士语气。
地域精准：回答基于德国国家/地区的现行法律法规。
结构化输出：启用“核心风险点”、“法律依据”、“合规建议”分层结构。
强制数据来源：启用【数据来源/法律依据】章节。
强制免责声明：所有回复末尾强制包含免责声明。
"""

# -------------------------- 2. 安全的计数器逻辑 (保持不变) --------------------------
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
# --- 3. 模型初始化 (保持不变) ---
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
        "max_output_tokens": 4096 
    }
    
    model = genai.GenerativeModel(
        model_name='gemini-2.5-pro', 
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
# --- 4. 主程序入口 ---
# -------------------------------------------------------------

# 将所有内容包裹在主容器内
st.markdown('<div class="main-container">', unsafe_allow_html=True)

# === 头部重构：标题和专家图片卡片 ===
col_title, col_expert = st.columns([2.5, 1])

# 专家超链接目标 URL
EXPERT_URL = "https://www.qfs-tax.de/Aboutinfo_2.html"

with col_title:
    st.title("🇩🇪 德国合规QFS")
    st.markdown('<div class="subtitle">资深税务师 / 全球跨境专家 AI 咨询服务</div>', unsafe_allow_html=True) # 简化副标题
    st.markdown('<div style="height: 10px;"></div>', unsafe_allow_html=True) 

with col_expert:
    # 专家图片卡片 (将 img 替换为 div)
    st.markdown(f"""
    <div class="expert-card">
        <a href="{EXPERT_URL}" class="expert-link" target="_blank">
            <div class="profile-img" alt="专家头像"></div> 
            <div class="expert-title">乔斐·苏斯 (Fei Qiao-Süss)</div>
            <div class="expert-role">QFS谦帆思联合事务所 | 首席合伙人</div>
        </a>
    </div>
    """, unsafe_allow_html=True) 


# --- 4. 常见问题按钮逻辑 ---

prompt_from_button = None
st.subheader("💡 常见问题快速查询")

# 优化为 3 列布局
cols = st.columns(3)

for i, question in enumerate(COMMON_LEGAL_QUESTIONS):
    with cols[i % 3]:
        if st.button(question, use_container_width=True, key=f"q_{i}"):
            prompt_from_button = question
            
st.markdown('<div style="height: 15px;"></div>', unsafe_allow_html=True)

# --- 5. 核心聊天逻辑 ---

# 1. 显示历史消息 
for msg in st.session_state.messages:
    icon = USER_ICON if msg["role"] == "user" else ASSISTANT_ICON
    st.chat_message(msg["role"], avatar=icon).write(msg["content"])

# 2. 获取输入（注意：输入框被 CSS 移动到了屏幕底部）
chat_input_text = st.chat_input("请输入你的合规问题...")

if prompt_from_button:
    user_input = prompt_from_button
elif chat_input_text:
    user_input = chat_input_text
else:
    user_input = None

# 3. 处理输入
if user_input:
    # 显示用户消息
    st.chat_message("user", avatar=USER_ICON).write(user_input)
    st.session_state.messages.append({"role": "user", "content": user_input})
    
    # 4. 调用 Gemini (流式输出)
    try:
        with st.chat_message("assistant", avatar=ASSISTANT_ICON):
            message_placeholder = st.empty()
            full_response = ""
            
            for chunk in model.generate_content(user_input, stream=True):
                full_response += chunk.text if chunk.text else ""
                message_placeholder.markdown(full_response + "▌")
        
            # 流式结束后，用最终内容替换占位符，去掉光标
            message_placeholder.markdown(full_response)
            st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    except Exception as e:
        st.error(f"发生错误: 调用Gemini API失败。请检查API Key配额。详细信息: {e}")
        
# --- 清空按钮和底部统计 ---

# 清空历史记录的函数
def clear_chat_history():
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是您的德国财税专家QFS。请问您在中国企业出海过程中遇到了哪些财务、法务或商业资质方面的问题？"}
    ]

st.markdown('<div style="height: 70px;"></div>', unsafe_allow_html=True) # 为底部的 Fixed Chat Input 留出空间

col_clear, col_stats = st.columns([1, 1])
with col_clear:
    if st.button('🧹 清空聊天记录', help="点击后将清除所有历史对话和文件上传记录"):
        clear_chat_history()
        st.rerun() 

with col_stats:
    st.markdown(f'<div class="visit-stats" style="text-align: right;">{visit_text}</div>', unsafe_allow_html=True)


# 闭合主容器
st.markdown('</div>', unsafe_allow_html=True)

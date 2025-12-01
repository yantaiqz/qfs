import streamlit as st
import google.generativeai as genai

# hide_streamlit_ui = """
# <style>
#  #MainMenu {visibility: hidden;} /* 隐藏三条杠菜单 */
# footer {visibility: hidden;}    /* 隐藏底部的 “Made with Streamlit” */
# header {visibility: hidden;}    /* 隐藏顶部工具栏 (包括 Rerun 按钮) */
# </style>
# """
# st.markdown(hide_streamlit_ui, unsafe_allow_html=True)

# -------------------------------------------------------------
# --- 1. 常量定义、系统指令和模型配置 (放在代码最顶部) ---
# -------------------------------------------------------------

# 定义头像常量
USER_ICON = "👤"
ASSISTANT_ICON = "👩‍💼"

# 定义常见法律问题
COMMON_LEGAL_QUESTIONS = [
    " 怎么应对税务稽查？",
    "货物出口德国如何判断增值税地点？",
    "企业在德国做重组，怎么做税务优化"
]

# 定义律师角色 (SYSTEM_INSTRUCTION，格式优化)
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

# -------------------------------------------------------------
# --- 2. 页面配置和模型初始化 (使用缓存和优化模型) ---
# -------------------------------------------------------------

st.set_page_config(page_title="德国财税专家QFS", page_icon="⚖️")
st.title("德国合规QFS：查法规、查外企")

# 确保您的聊天历史初始化代码已更新，以便 clear_chat_history 函数可以正常工作。
# ... (您的 if "messages" not in st.session_state: 应该和 clear_chat_history 内容保持一致)

# 移除 model listing 逻辑 (仅用于调试，影响生产性能)
# print("正在列出可用模型...") ... (已移除) ...

# 1. API Key 获取与配置
api_key = st.secrets.get("GEMINI_API_KEY")
if not api_key:
    st.error("请配置 API Key")
    st.stop()
genai.configure(api_key=api_key)

# 2. 缓存模型初始化（关键性能优化）
@st.cache_resource(show_spinner="正在建立QFS的专业知识库...")
def initialize_model():
    # 修正模型：升级到 gemini-2.5-flash 以提高可靠性
    # 修正 Token 限制：显式设置高 Token 限制
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


# 3. 聊天历史初始化（添加欢迎语）
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是您的德国财税专家QFS。请问您在中国企业出海过程中遇到了哪些财务、税务或商业资质方面的问题？"}
    ]
    
# --- 3. 常见问题按钮逻辑 (优化布局) ---

prompt_from_button = None
st.subheader("常见问题快速查询")

# 优化为 3 列布局，更好地适应移动端
cols = st.columns(3)

# 使用索引和循环来填充按钮，更简洁
for i, question in enumerate(COMMON_LEGAL_QUESTIONS):
    with cols[i % 3]: # 保证每行最多3个按钮
        if st.button(question, use_container_width=True, key=f"q_{i}"):
            prompt_from_button = question

# --- 4. 核心聊天逻辑 ---

# 1. 显示历史消息 (修正：添加头像参数)
for msg in st.session_state.messages:
    icon = USER_ICON if msg["role"] == "user" else ASSISTANT_ICON
    st.chat_message(msg["role"], avatar=icon).write(msg["content"])

# 2. 【核心逻辑】获取并合并输入
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
    
    # 4. 调用 Gemini (修正：使用流式输出，并添加错误捕捉)
    try:

        with st.chat_message("assistant", avatar=ASSISTANT_ICON):
        # 创建一个空的占位符来动态更新内容
            message_placeholder = st.empty()
            full_response = ""
            
        # 调用模型的流式接口
        for chunk in model.generate_content(user_input, stream=True):
            # 将每个块的内容追加到完整响应中
            full_response += chunk.text if chunk.text else ""
            # 更新占位符内容，末尾加一个光标效果
            message_placeholder.markdown(full_response + "▌")
        
        # 流式结束后，用最终内容替换占位符，去掉光标
        message_placeholder.markdown(full_response)
        st.session_state.messages.append({"role": "assistant", "content": full_response})
    
    except Exception as e:
        # 捕捉可能出现的 ResourceExhausted 或 NotFound 错误
        st.error(f"发生错误: 调用Gemini API失败。请检查API Key配额。详细信息: {e}")
        
# --- 清空历史记录的函数 ---
def clear_chat_history():
    # 恢复到初始的欢迎语状态
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是您的德国财税专家QFS。请问您在中国企业出海过程中遇到了哪些财务、法务或商业资质方面的问题？"}
    ]

# --- 清空按钮的 UI 放置 ---
# 使用 st.columns 放在右边或左边，这里放在主界面最上方
if st.button('🧹 清空聊天记录', help="点击后将清除所有历史对话和文件上传记录"):
    clear_chat_history()
    st.rerun() # 强制 Streamlit 立即重新运行脚本，刷新界面

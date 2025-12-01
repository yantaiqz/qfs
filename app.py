import streamlit as st
import google.generativeai as genai
import io 
import tempfile # 用于创建临时文件路径

# import os # 不再需要，已删除

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
    "美国亚马逊被法院TRO怎么办？",
    "越南制造业工厂的劳动合同应该注意什么？",
    "汽车出口欧洲如何实现数据合规？",
    "巴西比亚迪的征信情况",
    "阿布扎比国家石油公司的账期多久比较安全"
]

# 定义律师角色 (SYSTEM_INSTRUCTION，格式优化)
SYSTEM_INSTRUCTION = """
**角色定义 (Role):**
你是一位拥有20年经验的“全球跨境合规专家与涉外律师”。你的核心服务对象是“中国出海企业”。你的任务是针对目的国（如美国、欧盟、东南亚等）的法律环境，提供严谨、专业、具有实操性的合规建议。

**核心行为准则 (Core Guidelines):**
0.  **企业资质与信用查询:** 当提及具体海外公司时，**不要**仅提供一段普通文本。必须按照以下报告格式的结构进行回复：
1.  **专业语气:** 保持客观、中立、严谨的法律专业人士语气。避免使用模棱两可的词汇，但必须包含必要的法律免责声明。
2.  **地域精准:** 回答必须基于目标国家/地区的现行法律法规（如GDPR, CCPA, 越南劳动法等）。
3.  **结构化输出:** 回答复杂法律问题时，请使用“核心风险点”、“法律依据”、“合规建议”的分层结构。
4.  **强制数据来源:** 每一个回答的末尾，必须设立独立章节【数据来源/法律依据】，明确列出参考的法条、公约、官方指南或权威报告名称。

--- 报告格式的结构 ---
### 企业资信评估报告
**1. 概要与评级 (Summary)**
* **企业名称:** [英文全称]
* **D-U-N-S® (模拟/未知):** [如有则填，无则标注未知]
* **综合风险评级:** [高/中/低 - 基于公开负面新闻判断]
* **2. 基本识别信息 (Identification)**
* **注册地址:** [详细地址]
* **成立时间:** [年份]
* **企业类型:** [如：有限责任公司 / 上市公司]
* **3. 运营与业务 (Operations)**
* **主营业务:** [核心产品或服务]
* **行业地位:** [简述]
* **4. 合规与法律风险 (Legal & Compliance Risks)**
* **制裁名单扫描:** [是否在实体清单/SDN名单中]
* **公开诉讼记录:** [是否有重大公开诉讼]
* **负面舆情:** [近期相关负面新闻摘要]
【数据来源】
* 基于公开商业数据库及网络公开信息检索。
--- 报告格式结束 ---

**免责声明:**
请在所有回复最后注明：“*本回复由AI生成，仅供一般性参考，不构成正式法律意见。重大商业决策请咨询当地持牌律师。*”
"""

RISK_ANALYSIS_PROMPT = """
请严格扮演“跨境合规专家”，对用户上传的这份合同文件进行以下结构化风险审查，并使用清晰的 Markdown 格式输出报告：

### 📄 合同风险审查报告

1.  **核心风险识别:** 找出并说明本合同中对中国出海企业而言，**前 3 个最高**的法律或商业风险（如管辖权争议、违约金不合理、不可抗力定义过于狭窄等）。
2.  **管辖权/法律选择:** 明确指出合同中规定的适用的法律和争议解决地。评估这对中国企业的风险等级（高/中/低）。
3.  **终止与退出机制:** 总结合同的终止条款、提前解除的罚则以及退出机制的公平性。
4.  **综合风险评级:** 给出简短的“高/中/低”综合风险评级和精炼的处置建议。
"""

# -------------------------------------------------------------
# --- 2. 页面配置和模型初始化 (使用缓存和优化模型) ---
# -------------------------------------------------------------

st.set_page_config(page_title="跨境合规专家AI", page_icon="⚖️")
st.title("跨境合规Judi：查法规、查外企、审合同")

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
@st.cache_resource(show_spinner="正在建立Judi的专业知识库...")
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



# 注入一个带有自定义样式的虚线
st.markdown(
    '<hr style="border-top: 2px dashed #8c8c8c; background: none;">', 
    unsafe_allow_html=True
)

# --- 合同风险审核工具 ---
# st.subheader("合同文件风险审核")

uploaded_file = st.file_uploader(
    "合同文件风险审核", 
    type=['pdf', 'docx', 'txt'], # 定义支持的文件类型
    help="Gemini 可以直接读取 PDF 和文本文件进行分析"
)

# 确保模型定义在前面被正确调用（已在您的代码中实现）
if uploaded_file and st.button("立即启动风险审查", key="review_start_btn"):
    
    # 提取核心数据
    file_bytes = uploaded_file.getvalue()
    mime_type = uploaded_file.type
    file_name = uploaded_file.name

    st.chat_message("user", avatar="👤").write(f"已上传文件: {file_name}，正在请求风险审查。")

    try:
        with st.spinner(f"正在分析 {file_name} 的 {len(file_bytes)} 字节文件..."):
            
            # 1. 构造 Prompt Parts (核心修正在这里！)
            prompt_parts = [
                RISK_ANALYSIS_PROMPT,
                {
                    # 告知 Gemini 文件的 MIME 类型
                    "mime_type": mime_type,
                    # 传入文件的原始字节数据
                    "data": file_bytes 
                }
            ]

            # 2. 调用模型 (流式输出)
            response_stream = model.generate_content(prompt_parts, stream=True)
            
            # 显示并记录助手的流式响应
            with st.chat_message("assistant", avatar="👩‍💼"):
                message_placeholder = st.empty()
                full_review = ""
                
                for chunk in response_stream:
                    if chunk.text:
                        full_review += chunk.text
                        message_placeholder.markdown(full_review + "▌")
                
                message_placeholder.markdown(full_review)
                st.session_state.messages.append({"role": "assistant", "content": full_review})
                
        st.success("合同审查完成！")

    except Exception as e:
        st.error(f"处理文件或API调用失败。错误详情: {e}")


# 注入一个带有自定义样式的虚线
st.markdown(
    '<hr style="border-top: 2px dashed #8c8c8c; background: none;">', 
    unsafe_allow_html=True
)


# 3. 聊天历史初始化（添加欢迎语）
if "messages" not in st.session_state:
    st.session_state.messages = [
        {"role": "assistant", "content": "您好！我是您的跨境合规专家Judi。请问您在中国企业出海过程中遇到了哪些法律、监管或商业资质方面的问题？"}
    ]
    
# --- 3. 常见问题按钮逻辑 (优化布局) ---

prompt_from_button = None
st.subheader("常见合规问题和外企资质快速查询")

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
        {"role": "assistant", "content": "您好！我是您的跨境合规专家Judi。请问您在中国企业出海过程中遇到了哪些法律、监管或商业资质方面的问题？"}
    ]

# --- 清空按钮的 UI 放置 ---
# 使用 st.columns 放在右边或左边，这里放在主界面最上方
if st.button('🧹 清空聊天记录', help="点击后将清除所有历史对话和文件上传记录"):
    clear_chat_history()
    st.rerun() # 强制 Streamlit 立即重新运行脚本，刷新界面

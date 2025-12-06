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

import requests
import json
import datetime
import os


# -------------------------- 新增：配置 --------------------------
VISITOR_DB_FILE = "visitor_stats.json"
# 使用 st.session_state 存储当前会话信息，避免在一次 session 内重复查询 IP
if 'session_data' not in st.session_state:
    st.session_state.session_data = {}

# -------------------------- 新增：获取地理位置函数 --------------------------

def get_visitor_ip_and_location():
    """尝试获取用户的IP地址和地理位置。"""
    
    # 尝试从 Streamlit Cloud 或代理头中获取IP
    # 注意：这在本地运行时会失败，仅在部署后有效
    try:
        # 实际部署时，你可能需要根据部署环境查看不同的请求头
        # 这是一个常见的代理头，但在Streamlit Cloud上可能不可用
        ip_request = requests.get('https://api.ipify.org?format=json', timeout=5)
        ip_data = ip_request.json()
        ip_address = ip_data.get('ip', 'Unknown')
    except Exception:
        ip_address = '127.0.0.1' # 本地或获取失败时的默认值

    if ip_address == '127.0.0.1' and 'location_cache' not in st.session_state.session_data:
        # 避免在本地调试时频繁调用API
        return {'ip': 'Localhost', 'country': 'Local', 'region': 'Local'}

    # 使用第三方IP查询服务获取地理位置
    if 'location_cache' not in st.session_state.session_data:
        try:
            geo_request = requests.get(f'https://ipinfo.io/{ip_address}/json', timeout=5)
            geo_data = geo_request.json()
            country = geo_data.get('country', 'N/A')
            region = geo_data.get('region', 'N/A')
            st.session_state.session_data['location_cache'] = {
                'ip': ip_address,
                'country': country,
                'region': region
            }
        except Exception:
            st.session_state.session_data['location_cache'] = {
                'ip': ip_address, 
                'country': 'Unknown', 
                'region': 'Unknown'
            }
            
    return st.session_state.session_data['location_cache']

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



import json
import datetime
import os
# -------------------------- 2. 安全的计数器逻辑 --------------------------
COUNTER_FILE = "visit_stats.json"

def update_daily_visits():
    """安全更新访问量，如果出错则返回 0，绝不让程序崩溃"""
    try:
        today_str = datetime.date.today().isoformat()
        
        # 1. 检查 Session，防止刷新页面重复计数
        if "has_counted" in st.session_state:
            if os.path.exists(COUNTER_FILE):
                try:
                    with open(COUNTER_FILE, "r") as f:
                        return json.load(f).get("count", 0)
                except:
                    return 0
            return 0

        # 2. 读取或初始化数据
        data = {"date": today_str, "count": 0}
        
        if os.path.exists(COUNTER_FILE):
            try:
                with open(COUNTER_FILE, "r") as f:
                    file_data = json.load(f)
                    if file_data.get("date") == today_str:
                        data = file_data
            except:
                pass # 文件损坏则从0开始
        
        # 3. 计数 +1
        data["count"] += 1
        
        # 4. 写入文件 (最容易报错的地方，加了try保护)
        with open(COUNTER_FILE, "w") as f:
            json.dump(data, f)
        
        st.session_state["has_counted"] = True
        return data["count"]
        
    except Exception as e:
        # 如果发生任何错误（如权限不足），静默失败，不影响页面显示
        return 0


# -------- 每日访问统计 (即使报错也不崩溃) --------
daily_visits = update_daily_visits()
# visit_text = f"Daily Visits: {daily_visits}" if selected_lang == "English" else f"今日访问: {daily_visits}"
visit_text = f"今日访问: {daily_visits}"

# -------------------------- 3. 访问记录数据库操作 --------------------------

def load_visitor_db():
    """加载用户访问数据库，如果文件不存在则返回空字典"""
    if os.path.exists(VISITOR_DB_FILE):
        try:
            with open(VISITOR_DB_FILE, "r") as f:
                return json.load(f)
        except json.JSONDecodeError:
            print(f"警告：{VISITOR_DB_FILE} 文件内容损坏，将重新创建。")
            return {}
    return {}

def save_visitor_db(db):
    """保存用户访问数据库"""
    try:
        with open(VISITOR_DB_FILE, "w") as f:
            json.dump(db, f, indent=4)
        return True
    except Exception as e:
        print(f"错误：保存数据库失败: {e}")
        return False

def record_user_visit():
    """记录和更新当前用户的访问信息"""
    
    # 使用会话状态标记，确保每个 Session 只执行一次复杂的记录逻辑
    if "visitor_recorded" in st.session_state:
        return st.session_state.visitor_db.get(st.session_state.session_data['location_cache']['ip'], {})

    # 1. 获取用户位置信息
    user_info = get_visitor_ip_and_location()
    user_ip = user_info['ip']
    
    # 2. 加载数据库
    db = load_visitor_db()
    current_time_str = datetime.datetime.now().isoformat()
    
    # 3. 检查并更新记录
    if user_ip in db:
        # 用户已存在：更新最后访问时间和访问次数
        db[user_ip]['visits'] += 1
        db[user_ip]['last_visit'] = current_time_str
        db[user_ip]['country'] = user_info['country'] # 确保更新地理信息 (防止IP切换)
        db[user_ip]['region'] = user_info['region']
    else:
        # 新用户：创建新记录
        db[user_ip] = {
            'first_visit': current_time_str,
            'last_visit': current_time_str,
            'visits': 1,
            'country': user_info['country'],
            'region': user_info['region']
        }

    # 4. 保存数据库，并在 Session State 中缓存 DB 和标记
    save_visitor_db(db)
    st.session_state.visitor_db = db
    st.session_state.visitor_recorded = True
    
    return db[user_ip]

# -------------------------- 运行记录逻辑 --------------------------

# 在脚本运行之初调用记录函数
if 'visitor_recorded' not in st.session_state:
    user_visit_record = record_user_visit()
else:
    # 如果已记录，从缓存中读取当前用户的记录
    user_ip = st.session_state.session_data.get('location_cache', {}).get('ip', 'Localhost')
    user_visit_record = st.session_state.visitor_db.get(user_ip, {})


# --- 页面展示示例 ---
st.sidebar.markdown('---')
st.sidebar.subheader("👤 当前访问者信息")
st.sidebar.json({
    "IP": st.session_state.session_data.get('location_cache', {}).get('ip', 'N/A'),
    "国家/地区": user_visit_record.get('country', 'N/A'),
    "首次访问": user_visit_record.get('first_visit', 'N/A'),
    "末次访问": user_visit_record.get('last_visit', 'N/A'),
    "访问次数": user_visit_record.get('visits', 0)
})


st.markdown(f"""
<div style="text-align: center; color: #64748b; font-size: 0.7rem; margin-top: 10px; padding-bottom: 20px;">
    {visit_text}
</div>
""", unsafe_allow_html=True)


# -------------------------------------------------------------
# --- 2. 页面配置和模型初始化 (使用缓存和优化模型) ---
# -------------------------------------------------------------

st.set_page_config(page_title="德国财税专家QFS", page_icon="🇩🇪")
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

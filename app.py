import streamlit as st
import google.generativeai as genai
import requests  # 智谱API使用HTTP请求
import os
import difflib
import time

# --- 页面配置 ---
st.set_page_config(
    page_title="Legal AI Dual-Core | 法律双模助手",
    page_icon="⚖️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# --- CSS样式：打造 Kimi 风格极简界面 ---
# 调整智谱相关配色和图标
st.markdown("""
<style>
    /* 全局字体和背景 */
    .stApp {
        background-color: #F9F9F9;
        font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
    }
    
    /* 标题样式 */
    h1 {
        font-weight: 600;
        color: #333;
        text-align: center;
        margin-bottom: 1.5rem;
    }
    
    /* 输入框美化 */
    .stTextInput > div > div > input {
        border-radius: 20px;
        border: 1px solid #E0E0E0;
        padding: 10px 20px;
        box-shadow: 0 2px 5px rgba(0,0,0,0.05);
    }
    .stTextInput > div > div > input:focus {
        border-color: #6C5CE7;
        box-shadow: 0 2px 8px rgba(108, 92, 231, 0.2);
    }

    /* 按钮美化 */
    .stButton > button {
        border-radius: 20px;
        background-color: #333;
        color: white;
        border: none;
        padding: 0.5rem 2rem;
        font-weight: 500;
        transition: all 0.3s ease;
    }
    .stButton > button:hover {
        background-color: #000;
        transform: translateY(-1px);
        box-shadow: 0 4px 10px rgba(0,0,0,0.1);
    }

    /* 结果卡片样式 */
    .result-card {
        background-color: white;
        padding: 25px;
        border-radius: 15px;
        box-shadow: 0 4px 15px rgba(0,0,0,0.03);
        height: 100%;
        border: 1px solid #F0F0F0;
    }
    
    .model-header {
        font-size: 1.1rem;
        font-weight: 600;
        margin-bottom: 15px;
        display: flex;
        align-items: center;
    }
    
    /* 差异高亮颜色 */
    .diff-add { background-color: #e6ffec; color: #248043; padding: 2px 4px; border-radius: 4px; }
    .diff-del { background-color: #ffebe9; color: #cf222e; text-decoration: line-through; padding: 2px 4px; border-radius: 4px; opacity: 0.8; }
    .diff-text { line-height: 1.8; color: #444; font-size: 0.95rem; }

    /* 隐藏顶部红线和Footer */
    header {visibility: hidden;}
    footer {visibility: hidden;}
</style>
""", unsafe_allow_html=True)

# --- 侧边栏：API Key 配置 ---
with st.sidebar:
    st.header("⚙️ API 设置")
    st.info("请输入您的 API Key 以开始使用。")
    
    gemini_key = st.text_input("Gemini API Key", type="password")
    # 替换豆包配置为智谱配置
    glm_key = st.text_input("智谱 GLM API Key", type="password", help="从智谱开放平台获取：https://open.bigmodel.cn/")
    glm_model = st.selectbox(
        "智谱模型选择",
        options=["glm-4", "glm-4v", "glm-3-turbo"],
        index=0,
        help="选择要调用的智谱模型版本"
    )
    
    st.markdown("---")
    use_mock = st.checkbox("使用模拟模式 (无 Key 体验)", value=True, help="如果没有API Key，勾选此项查看界面效果")

# --- 核心逻辑函数 ---

def query_gemini(prompt, api_key):
    """调用 Google Gemini 模型"""
    if not api_key: return "请配置 Gemini API Key"
    try:
        genai.configure(api_key=api_key)
        model = genai.GenerativeModel('gemini-pro')
        # 添加法律系统提示词
        full_prompt = f"你是一名专业的中国法律顾问。请用专业、严谨、简洁的语言回答以下问题，并引用相关法律法规（如有）。\n\n用户问题：{prompt}"
        response = model.generate_content(full_prompt)
        return response.text
    except Exception as e:
        return f"Gemini 调用失败: {str(e)}"

def query_glm(prompt, api_key, model_name):
    """调用智谱 GLM 模型（替换原豆包调用逻辑）"""
    if not api_key: return "请配置智谱 GLM API Key"
    try:
        # 智谱API接口地址
        url = "https://open.bigmodel.cn/api/paas/v4/chat/completions"
        headers = {
            "Content-Type": "application/json",
            "Authorization": f"Bearer {api_key}"
        }
        # 构造请求体
        full_prompt = f"你是一名资深的中国律师。请针对以下问题提供法律咨询意见，确保引用法条准确，逻辑清晰。\n\n用户问题：{prompt}"
        data = {
            "model": model_name,
            "messages": [{"role": "user", "content": full_prompt}],
            "temperature": 0.7,  # 可控随机性
            "max_tokens": 2048   # 最大生成长度
        }
        # 发送请求
        response = requests.post(url, headers=headers, json=data, timeout=30)
        response.raise_for_status()  # 抛出HTTP错误
        result = response.json()
        return result["choices"][0]["message"]["content"]
    except requests.exceptions.RequestException as e:
        return f"智谱 GLM 调用失败: {str(e)}"
    except Exception as e:
        return f"智谱 GLM 处理失败: {str(e)}"

def mock_response(model_name, query):
    """模拟返回结果 (用于演示 UI)"""
    time.sleep(1.5)
    base = f"针对关于“{query}”的法律咨询，{model_name}认为：\n\n"
    if model_name == "Gemini":
        return base + "根据《中华人民共和国民法典》第五百七十七条，当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。建议您首先保留证据，包括合同原件、聊天记录等。"
    else:
        return base + "依据《民法典》第五百七十七条及第五百八十四条相关规定，违约方需赔偿守约方的实际损失，包括合同履行后可获得的利益，但不得超过违约方订立合同时预见到或者应当预见到的因违约可能造成的损失。建议优先协商，协商不成可诉讼，注意3年诉讼时效。"

def generate_diff_html(text1, text2):
    """
    生成两个文本的对比 HTML。
    这里使用 difflib 比较文本，并生成简单的 HTML 片段。
    """
    d = difflib.Differ()
    # 按行分割或按句分割效果更好，这里简化为按字/词分割演示
    diff = d.compare(text1.splitlines(), text2.splitlines())
    
    html_content = '<div class="diff-text">'
    for line in diff:
        if line.startswith('  '): # 共有
            html_content += f'<div>{line[2:]}</div>'
        elif line.startswith('- '): # Text 1 独有
            html_content += f'<div class="diff-del">Gemini: {line[2:]}</div>'
        elif line.startswith('+ '): # Text 2 独有
            html_content += f'<div class="diff-add">智谱 GLM: {line[2:]}</div>'
    html_content += '</div>'
    return html_content

# --- 页面布局 ---

# 1. 顶部区域
st.title("⚖️ 法律智能双询")
st.caption("同时咨询 Gemini 与 智谱 GLM，对比法律意见，辅助专业决策")

st.write("") # Spacer

# 2. 输入区域 (居中容器)
col_spacer1, col_input, col_spacer2 = st.columns([1, 6, 1])
with col_input:
    user_query = st.text_input("", placeholder="请输入具体的法律问题，例如：二手房买卖违约如何计算赔偿？")
    submit_btn = st.button("开始咨询", use_container_width=True)

# 3. 结果区域
if submit_btn and user_query:
    if not use_mock and (not gemini_key or not glm_key):
        st.error("请先在左侧侧边栏配置 API Key，或勾选“模拟模式”。")
    else:
        st.write("---")
        
        # 使用 Spinner 提升体验
        with st.spinner("正在检索法律法规并生成意见..."):
            # 并发处理模拟 (实际生产中可以使用 asyncio 或 ThreadPoolExecutor)
            if use_mock:
                res_gemini = mock_response("Gemini", user_query)
                res_glm = mock_response("智谱 GLM", user_query)  # 替换豆包为智谱
            else:
                # 实际调用
                # 简单起见这里串行调用，实际建议用并发
                res_gemini = query_gemini(user_query, gemini_key)
                res_glm = query_glm(user_query, glm_key, glm_model)  # 调用智谱API

        # 4. 双栏展示结果
        col1, col2 = st.columns(2)
        
        with col1:
            st.markdown(
                f"""
                <div class="result-card">
                    <div class="model-header" style="color: #4285F4;">
                        <img src="https://www.gstatic.com/lamda/images/gemini_sparkle_v002_d4735304ff6292a690345.svg" width="20" style="vertical-align: middle; margin-right: 8px;">
                        Gemini Pro
                    </div>
                    <div style="font-size: 0.95rem; line-height: 1.6; color: #333;">
                        {res_gemini}
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )
            
        with col2:
            st.markdown(
                f"""
                <div class="result-card">
                    <div class="model-header" style="color: #FF6700;">  <!-- 智谱品牌色 -->
                        <span style="font-size: 20px; margin-right: 8px;">🧠</span>
                        智谱 GLM ({glm_model})
                    </div>
                    <div style="font-size: 0.95rem; line-height: 1.6; color: #333;">
                        {res_glm}
                    </div>
                </div>
                """, 
                unsafe_allow_html=True
            )

        # 5. 差异化可视化分析
        st.write("")
        st.subheader("🔍 观点差异分析")
        
        with st.expander("点击展开：详细文本差异比对", expanded=True):
            # 简单的差异分析 Prompt
            # 在实际高级应用中，这里应该调用第三次 LLM 来总结两个回答的逻辑差异
            # 这里我们展示视觉上的差异
            
            diff_html = generate_diff_html(res_gemini, res_glm)  # 替换豆包结果为智谱
            
            st.markdown("""
            <div style="background-color: #fff; padding: 20px; border-radius: 10px; border: 1px solid #eee;">
                <p style="font-size: 0.8rem; color: #888; margin-bottom: 10px;">
                    <span style="background-color: #ffebe9; color: #cf222e; padding: 2px 5px; border-radius: 4px;">红色</span> 代表 Gemini 独有的表述，
                    <span style="background-color: #e6ffec; color: #248043; padding: 2px 5px; border-radius: 4px;">绿色</span> 代表 智谱 GLM 独有的表述。
                </p>
            """, unsafe_allow_html=True)
            
            st.markdown(diff_html, unsafe_allow_html=True)
            st.markdown("</div>", unsafe_allow_html=True)

# 6. 空状态/引导页
if not user_query:
    st.markdown("""
    <div style="text-align: center; margin-top: 50px; color: #888;">
        <p>支持合同审查、法条检索、案例分析等场景</p>
    </div>
    """, unsafe_allow_html=True)

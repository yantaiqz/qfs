import streamlit as st
import google.generativeai as genai
from volcengine.ark import Ark
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
# 使用素雅的配色、大圆角、隐藏多余的 Streamlit 元素
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
    doubao_key = st.text_input("Doubao (Ark) API Key", type="password")
    doubao_ep = st.text_input("Doubao Endpoint ID", placeholder="ep-202xxx...", help="火山引擎在线推理的接入点ID")
    
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

def query_doubao(prompt, api_key, endpoint_id):
    """调用字节跳动豆包 (Volcengine Ark) 模型"""
    if not api_key or not endpoint_id: return "请配置豆包 API Key 和 Endpoint"
    try:
        client = Ark(api_key=api_key)
        full_prompt = f"你是一名资深的中国律师。请针对以下问题提供法律咨询意见，确保引用法条准确，逻辑清晰。\n\n用户问题：{prompt}"
        completion = client.chat.completions.create(
            model=endpoint_id,
            messages=[{"role": "user", "content": full_prompt}],
        )
        return completion.choices[0].message.content
    except Exception as e:
        return f"豆包调用失败: {str(e)}"

def mock_response(model_name, query):
    """模拟返回结果 (用于演示 UI)"""
    time.sleep(1.5)
    base = f"针对关于“{query}”的法律咨询，{model_name}认为：\n\n"
    if model_name == "Gemini":
        return base + "根据《中华人民共和国民法典》第五百七十七条，当事人一方不履行合同义务或者履行合同义务不符合约定的，应当承担继续履行、采取补救措施或者赔偿损失等违约责任。建议您首先保留证据，包括合同原件、聊天记录等。"
    else:
        return base + "依据《民法典》相关规定，违约方需承担责任。建议优先协商解决。若协商不成，可依据合同约定向人民法院提起诉讼或申请仲裁。注意诉讼时效问题，一般为三年。"

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
            html_content += f'<div class="diff-add">Doubao: {line[2:]}</div>'
    html_content += '</div>'
    return html_content

# --- 页面布局 ---

# 1. 顶部区域
st.title("⚖️ 法律智能双询")
st.caption("同时咨询 Gemini 与 豆包，对比法律意见，辅助专业决策")

st.write("") # Spacer

# 2. 输入区域 (居中容器)
col_spacer1, col_input, col_spacer2 = st.columns([1, 6, 1])
with col_input:
    user_query = st.text_input("", placeholder="请输入具体的法律问题，例如：二手房买卖违约如何计算赔偿？")
    submit_btn = st.button("开始咨询", use_container_width=True)

# 3. 结果区域
if submit_btn and user_query:
    if not use_mock and (not gemini_key or not doubao_key):
        st.error("请先在左侧侧边栏配置 API Key，或勾选“模拟模式”。")
    else:
        st.write("---")
        
        # 使用 Spinner 提升体验
        with st.spinner("正在检索法律法规并生成意见..."):
            # 并发处理模拟 (实际生产中可以使用 asyncio 或 ThreadPoolExecutor)
            if use_mock:
                res_gemini = mock_response("Gemini", user_query)
                res_doubao = mock_response("Doubao", user_query)
            else:
                # 实际调用
                # 简单起见这里串行调用，实际建议用并发
                res_gemini = query_gemini(user_query, gemini_key)
                res_doubao = query_doubao(user_query, doubao_key, doubao_ep)

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
                    <div class="model-header" style="color: #0452E8;">
                        <span style="font-size: 20px; margin-right: 8px;">🍬</span>
                        豆包 (Doubao)
                    </div>
                    <div style="font-size: 0.95rem; line-height: 1.6; color: #333;">
                        {res_doubao}
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
            
            diff_html = generate_diff_html(res_gemini, res_doubao)
            
            st.markdown("""
            <div style="background-color: #fff; padding: 20px; border-radius: 10px; border: 1px solid #eee;">
                <p style="font-size: 0.8rem; color: #888; margin-bottom: 10px;">
                    <span style="background-color: #ffebe9; color: #cf222e; padding: 2px 5px; border-radius: 4px;">红色</span> 代表 Gemini 独有的表述，
                    <span style="background-color: #e6ffec; color: #248043; padding: 2px 5px; border-radius: 4px;">绿色</span> 代表 豆包 独有的表述。
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

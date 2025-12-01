import streamlit as st
import pandas as pd

st.title('我的 Streamlit 网页端应用')
st.write('数据加载成功!')
st.dataframe(pd.DataFrame({'A': [1], 'B': [2]}))

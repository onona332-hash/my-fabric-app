import streamlit as st
import google.generativeai as genai
from PIL import Image

st.title("🧵 魔法の洋裁ログ (複数枚対応版)")

# APIキー設定
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("APIキーの設定を確認してください。")
    st.stop()

tab1, tab2 = st.tabs(["スクショで登録", "在庫一覧"])

with tab1:
    st.header("楽天のスクショを解析")
    
    # 【変更点】 accept_multiple_files=True にして複数枚選べるようにします
    uploaded_files = st.file_uploader("スクショを全部選んでね（複数可）", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
    
    if uploaded_files:
        images = []
        for uploaded_file in uploaded_files:
            img = Image.open(uploaded_file)
            images.append(img)
        
        # 画面にプレビューを表示
        st.write(f"{len(images)}枚の画像を読み込みました。")
        
        if st.button("AIでまとめて解析する"):
            with st.spinner("すべての画像から情報を集めています..."):
                # プロンプト（AIへの指示）
                prompt = """
                複数の画像（楽天のスクショ）を送ります。
                これらをすべて確認して、一つの生地の情報としてまとめて抽出してください。
                情報が分散していても、組み合わせて回答してください。
                
                【生地名】: 
                【素材】: 
                【生地幅】: 
                【価格】: 
                【ショップ名】:
                """
                # 画像リストとプロンプトを一緒に渡す
                response = model.generate_content([prompt] + images)
                
                st.subheader("解析結果")
                st.write(response.text)
                st.success("バラバラの情報が一つにまとまりました！")

with tab2:
    st.write("次は、これをスプレッドシートに保存しましょう。")

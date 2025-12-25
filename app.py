import streamlit as st
import google.generativeai as genai
from PIL import Image

# アプリのタイトル
st.title("🧵 魔法の洋裁ログ (Gemini版)")

# 1. APIキーの設定（StreamlitのSecretsから読み込み）
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("APIキーが設定されていません。Settings > Secrets を確認してください。")
    st.stop()

# タブ分け
tab1, tab2 = st.tabs(["スクショで登録", "在庫一覧"])

with tab1:
    st.header("楽天のスクショを解析")
    
    # 画像のアップロード
    uploaded_file = st.file_uploader("生地のスクショを選択してね", type=['png', 'jpg', 'jpeg'])
    
    if uploaded_file:
        image = Image.open(uploaded_file)
        st.image(image, caption='アップロードされた画像', use_container_width=True)
        
        if st.button("AIで解析する"):
            with st.spinner("Geminiが読み取り中..."):
                # Geminiへの指示（プロンプト）
                prompt = """
                この画像から生地の情報を抽出して、以下の形式で日本語で回答してください。
                【生地名】: 
                【素材】: 
                【生地幅】: 
                【価格】: 
                """
                response = model.generate_content([prompt, image])
                
                st.subheader("解析結果")
                st.write(response.text)
                st.success("この内容をスプレッドシートに保存する機能は、次に作りましょう！")

with tab2:
    st.write("（ここに在庫リストが表示される予定です）")

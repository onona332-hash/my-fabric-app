import streamlit as st
import google.generativeai as genai
from PIL import Image

st.title("🧵 魔法の洋裁ログ (安定版)")

# APIキー設定
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    model = genai.GenerativeModel('gemini-1.5-flash')
except:
    st.error("APIキーの設定を確認してください。")
    st.stop()

tab1, tab2 = st.tabs(["情報取得", "在庫一覧"])

with tab1:
    st.header("生地情報を取得")
    
    method = st.radio("どうやって読み込みますか？", ["テキストを貼り付ける", "カメラ・写真から読み込む"])

    # テキスト貼り付け（URLの代わりに、ページの内容をコピペ！）
    if method == "テキストを貼り付ける":
        st.subheader("📋 商品説明などを貼り付け")
        text_input = st.text_area("楽天の「商品仕様」や「商品説明」をコピーしてここに貼り付けてください", height=200)
        
        if text_input and st.button("AIで解析する"):
            with st.spinner("AIが文字を分析しています..."):
                prompt = f"""
                以下のテキストから生地の情報を抽出して整理してください。
                【生地名】: 
                【素材】: 
                【生地幅】: 
                【価格】: 
                【ショップ名】:
                
                テキスト:
                {text_input}
                """
                response = model.generate_content(prompt)
                st.subheader("解析結果")
                st.write(response.text)

    # 写真からの読み込み（カメラ・スクショ）
    elif method == "カメラ・写真から読み込む":
        st.subheader("📸 写真・スクショをアップロード")
        uploaded_files = st.file_uploader(
            "実物のタグやスクショを選んでね（複数可）", 
            type=['png', 'jpg', 'jpeg'], 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            images = []
            for uploaded_file in uploaded_files:
                img = Image.open(uploaded_file)
                images.append(img)
            
            if st.button("AIで写真を解析する"):
                with st.spinner("画像を解析中..."):
                    prompt = "画像から生地の名前、素材、幅、価格、ショップ名を抽出して整理してください。"
                    response = model.generate_content([prompt] + images)
                    st.subheader("解析結果")
                    st.write(response.text)

with tab2:
    st.write("解析できたら、次はスプレッドシートへ保存しましょう！")

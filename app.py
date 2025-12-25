import streamlit as st
import google.generativeai as genai
from PIL import Image

st.title("🧵 魔法の洋裁ログ (URL & カメラ対応)")

# APIキー設定
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    # シンプルなモデル設定に戻しました
    model = genai.GenerativeModel('gemini-1.5-flash')
except Exception as e:
    st.error(f"APIキーの設定を確認してください。")
    st.stop()

# タブ分け
tab1, tab2 = st.tabs(["情報取得", "在庫一覧"])

with tab1:
    st.header("生地情報を取得")
    
    method = st.radio("どうやって情報を読み込みますか？", ["URLから読み込む", "スクショ/実物写真から読み込む"])

    # URLからの読み込み
    if method == "URLから読み込む":
        st.subheader("🔗 商品URLを貼り付け")
        url_input = st.text_input("ここに楽天などのURLを入力してください")
        
        if url_input and st.button("URLを解析する"):
            with st.spinner("AIがページを分析しています..."):
                # URLをテキストとしてGeminiに渡し、内容を推測・解析させます
                prompt = f"""
                以下のURLは生地の商品ページです。
                このページの内容から、生地の情報を抽出してください。
                【生地名】: 
                【素材】: 
                【生地幅】: 
                【価格】: 
                【ショップ名】:
                
                URL: {url_input}
                """
                response = model.generate_content(prompt)
                st.subheader("解析結果")
                st.write(response.text)

    # 写真からの読み込み
    elif method == "スクショ/実物写真から読み込む":
        st.subheader("📸 写真をアップロード")
        uploaded_files = st.file_uploader(
            "写真を選んでね（複数可）", 
            type=['png', 'jpg', 'jpeg'], 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            images = []
            for uploaded_file in uploaded_files:
                img = Image.open(uploaded_file)
                images.append(img)
            
            if st.button("AIで解析する"):
                with st.spinner("画像を解析中..."):
                    prompt = "画像から生地の名前、素材、幅、価格、ショップ名を抽出してください。"
                    response = model.generate_content([prompt] + images)
                    st.subheader("解析結果")
                    st.write(response.text)

with tab2:
    st.write("次はスプレッドシート連携ですね！")

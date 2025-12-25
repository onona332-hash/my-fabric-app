import streamlit as st
import google.generativeai as genai
from PIL import Image
import requests # URLから画像をダウンロードするために使います

st.title("🧵 魔法の洋裁ログ (URL & カメラ対応)")

# APIキー設定
try:
    api_key = st.secrets["GEMINI_API_KEY"]
    genai.configure(api_key=api_key)
    # Webブラウジング機能を持つモデルを使用
    model = genai.GenerativeModel('gemini-1.5-flash', tools=[genai.GenerativeModel.from_pretrained("models/gemini-1.5-flash").tools[0]])
except Exception as e:
    st.error(f"APIキーの設定を確認してください: {e}")
    st.stop()

# タブ分け
tab1, tab2 = st.tabs(["情報取得", "在庫一覧"])

with tab1:
    st.header("生地情報を取得")
    
    # 選択肢の追加
    method = st.radio("どうやって情報を読み込みますか？", ["URLから読み込む", "スクショ/実物写真から読み込む"])

    # URLからの読み込み
    if method == "URLから読み込む":
        st.subheader("🔗 楽天などの商品URLを貼り付け")
        url_input = st.text_input("ここに商品ページのURLを入力してください")
        
        if url_input and st.button("URLを解析する"):
            with st.spinner("GeminiがWebページを読み取り中..."):
                prompt = f"""
                このWebページから生地の情報を抽出してください。
                特に以下の情報を探してください。
                【生地名】: 
                【素材】: 
                【生地幅】: 
                【価格】: 
                【ショップ名】:
                URL: {url_input}
                """
                
                try:
                    # GeminiのWebブラウジング機能を使ってURLを直接解析
                    response = model.generate_content(prompt)
                    st.subheader("解析結果")
                    st.write(response.text)
                    st.success("Webページから情報を取得しました！")
                except Exception as e:
                    st.error(f"URLの解析中にエラーが発生しました。URLが正しいか、公開されているか確認してください。エラー: {e}")

    # スクショ/実物写真からの読み込み
    elif method == "スクショ/実物写真から読み込む":
        st.subheader("📸 スクショや実物タグの写真をアップロード")
        uploaded_files = st.file_uploader(
            "生地のスクショや実物のタグ写真を選択してね（複数可）", 
            type=['png', 'jpg', 'jpeg'], 
            accept_multiple_files=True
        )
        
        if uploaded_files:
            images = []
            for uploaded_file in uploaded_files:
                img = Image.open(uploaded_file)
                images.append(img)
            
            st.write(f"{len(images)}枚の画像を読み込みました。")
            
            if st.button("AIでまとめて解析する（画像）"):
                with st.spinner("すべての画像から情報を集めています..."):
                    prompt = """
                    複数の画像を送ります。楽天のスクショや、実物の生地タグの写真などです。
                    これらをすべて確認して、一つの生地の情報としてまとめて抽出してください。
                    情報が分散していても、組み合わせて回答してください。
                    特に以下の情報を探してください。
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
                    st.success("画像から情報を取得しました！")

with tab2:
    st.write("次は、この解析結果をスプレッドシートに保存しましょう！")


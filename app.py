import streamlit as st
import google.generativeai as genai
from PIL import Image

# ページ設定は必ず最初に行う
st.set_page_config(page_title="洋裁在庫ログ", layout="centered")

st.title("🧵 魔法の洋裁ログ")

# 1. APIキーの読み込みチェック
if "GEMINI_API_KEY" not in st.secrets:
    st.error("StreamlitのSecretsに 'GEMINI_API_KEY' が設定されていません。")
    st.stop()

# 2. AIの初期設定
try:
    genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
    # モデル名をフルパスで指定（404回避のため）
    model = genai.GenerativeModel('models/gemini-1.5-flash')
except Exception as e:
    st.error(f"初期設定エラー: {e}")
    st.stop()

tab1, tab2 = st.tabs(["情報取得", "在庫一覧"])

with tab1:
    method = st.radio("入力方法を選択", ["テキスト貼り付け", "画像アップロード"])

    # --- テキスト解析 ---
    if method == "テキスト貼り付け":
        text_input = st.text_area("商品説明（楽天のスペック表など）を貼り付けてください", height=200)
        if st.button("AIで解析する") and text_input:
            with st.spinner("AIが文章を読み取っています..."):
                try:
                    prompt = f"以下のテキスタイル情報を【生地名、素材、生地幅、価格】の項目で整理して回答してください:\n\n{text_input}"
                    response = model.generate_content(prompt)
                    st.success("解析に成功しました！")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"解析エラーが発生しました。APIキーが有効か確認してください。\n詳細: {e}")

    # --- 画像解析 ---
    else:
        uploaded_files = st.file_uploader("生地のスクショやタグの写真をアップ", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if st.button("画像から情報を抽出") and uploaded_files:
            with st.spinner("画像を解析中..."):
                try:
                    # 1枚目の画像を代表として解析
                    img = Image.open(uploaded_files[0])
                    prompt = "この画像から生地情報を抽出してください（生地名、素材、幅、価格）。日本語で回答してください。"
                    
                    # 最新の呼び出し形式
                    response = model.generate_content([prompt, img])
                    
                    st.success("画像の読み取りに成功しました！")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"画像解析エラー: {e}")

with tab2:
    st.info("解析が成功したら、次はここへ自動保存する機能を追加しましょう！")

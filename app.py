import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="洋裁在庫ログ", layout="centered")
st.title("🧵 魔法の洋裁ログ")

# APIキー設定
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secretsにキーが設定されていません。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- ここが修正ポイント ---
# モデル名を最もシンプルに指定します
model = genai.GenerativeModel('gemini-1.5-flash')

tab1, tab2 = st.tabs(["情報取得", "在庫一覧"])

with tab1:
    method = st.radio("入力方法", ["テキスト貼り付け", "画像アップ"])

    if method == "テキスト貼り付け":
        text_input = st.text_area("商品説明を貼り付けてください", height=150)
        if st.button("AIで解析") and text_input:
            with st.spinner("解析中..."):
                try:
                    # 指示を英語と日本語のミックスにすることで、認識率を上げます
                    prompt = f"Please extract fabric info from this text in Japanese. (生地名、素材、生地幅、価格):\n\n{text_input}"
                    response = model.generate_content(prompt)
                    st.success("解析完了！")
                    st.info(response.text)
                except Exception as e:
                    st.error(f"エラー: {e}")

    else:
        uploaded_files = st.file_uploader("写真を選択", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if st.button("画像から解析") and uploaded_files:
            with st.spinner("画像を解析中..."):
                try:
                    # 画像解析の際、1枚ずつ慎重に処理するように変更
                    img = Image.open(uploaded_files[0])
                    prompt = "生地の情報を抽出してください（生地名、素材、幅、価格）。"
                    # model.generate_content([prompt, img]) の形式で呼び出し
                    response = model.generate_content([prompt, img])
                    st.success("解析完了！")
                    st.info(response.text)
                except Exception as e:
                    st.error(f"画像解析エラー: {e}")

with tab2:
    st.write("解析が動いたら、次はスプレッドシートへの保存ですね！")

import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="洋裁在庫ログ", layout="centered")
st.title("🧵 魔法の洋裁ログ")

# APIキー設定
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secretsに GEMINI_API_KEY が設定されていません。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# エラーを回避するため、あえて「models/」を頭に付けた正式な形式で指定します
# もしこれでもダメな場合は 'models/gemini-1.5-pro' も試せるようにします
model = genai.GenerativeModel('models/gemini-1.5-flash')

tab1, tab2 = st.tabs(["情報取得", "在庫一覧"])

with tab1:
    method = st.radio("入力方法", ["テキスト貼り付け", "画像アップ"])

    if method == "テキスト貼り付け":
        text_input = st.text_area("商品説明を貼り付けてください", height=150)
        if st.button("AIで解析"):
            if not text_input:
                st.warning("テキストを入力してください")
            else:
                with st.spinner("解析中..."):
                    try:
                        prompt = f"以下のテキストから生地名、素材、生地幅、価格を抽出し、日本語で整理してください:\n\n{text_input}"
                        response = model.generate_content(prompt)
                        st.success("解析が完了しました！")
                        st.info(response.text)
                    except Exception as e:
                        # 404エラーが出た場合に備え、別のモデル名でのヒントを表示
                        st.error(f"エラーが発生しました。APIキーを作成したサイトで「Gemini 1.5 Flash」が利用可能か確認してください。: {e}")

    else:
        uploaded_files = st.file_uploader("写真を選択", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if st.button("画像から解析"):
            if not uploaded_files:
                st.warning("画像を選択してください")
            else:
                with st.spinner("画像を解析中..."):
                    try:
                        imgs = [Image.open(f) for f in uploaded_files]
                        prompt = "画像から生地情報を抽出してください（生地名、素材、幅、価格）。"
                        response = model.generate_content([prompt] + imgs)
                        st.success("解析が完了しました！")
                        st.info(response.text)
                    except Exception as e:
                        st.error(f"画像解析でエラーが発生しました: {e}")

with tab2:
    st.write("解析ができるようになったら、次はいよいよ保存ボタンを付けましょう！")

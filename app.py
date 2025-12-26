import streamlit as st
import google.generativeai as genai
from PIL import Image

st.set_page_config(page_title="洋裁在庫ログ", layout="centered")
st.title("🧵 魔法の洋裁ログ")

if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secretsにキーが設定されていません。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])
model = genai.GenerativeModel('gemini-1.5-flash')

tab1, tab2 = st.tabs(["情報取得", "在庫一覧"])

with tab1:
    method = st.radio("入力方法を選択", ["テキスト貼り付け", "画像アップロード"])

    if method == "テキスト貼り付け":
        text_input = st.text_area("商品説明を貼り付けてください", height=200)
        if st.button("AIで解析する") and text_input:
            with st.spinner("計算中..."):
                try:
                    # --- ここで「計算」を指示に含めます ---
                    prompt = f"""
                    以下のテキストから生地情報を抽出してください。
                    特に「購入数（数量）」と「1個あたりの長さ（50cm単位など）」を見つけて、
                    合計で何cm購入したかを計算して出力してください。
                    
                    出力形式：
                    【生地名】: 
                    【素材】: 
                    【生地幅】: 
                    【購入合計の長さ】: （例：100cm(2個分) など）
                    【価格】: 
                    
                    テキスト:
                    {text_input}
                    """
                    response = model.generate_content(prompt)
                    st.success("解析完了！")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"エラー: {e}")

    else:
        # 画像アップロード側も同様に「計算」を指示に含めると便利です
        uploaded_files = st.file_uploader("写真を選択", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if st.button("画像から解析") and uploaded_files:
            with st.spinner("画像を解析中..."):
                try:
                    img = Image.open(uploaded_files[0])
                    prompt = "画像から生地名、素材、幅、価格、そして【購入合計の長さ】（数量から計算）を抽出してください。"
                    response = model.generate_content([prompt, img])
                    st.success("解析成功！")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"画像解析エラー: {e}")

with tab2:
    st.info("解析が動くようになったので、いよいよ次はこの結果を自動で表にしましょう！")

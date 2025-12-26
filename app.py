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

# --- 404エラー対策：動くモデルを自動選択 ---
def get_working_model():
    try:
        # 使えるモデルのリストを取得
        available_names = [m.name for m in genai.list_models()]
        # 優先順に試す
        for target in ["models/gemini-1.5-flash", "models/gemini-1.5-flash-latest", "models/gemini-pro"]:
            if target in available_names:
                return genai.GenerativeModel(target)
    except:
        pass
    return genai.GenerativeModel("gemini-1.5-flash") # デフォルト

model = get_working_model()

tab1, tab2 = st.tabs(["情報取得", "在庫一覧"])

with tab1:
    method = st.radio("入力方法を選択", ["テキスト貼り付け", "画像アップロード"])

    if method == "テキスト貼り付け":
        text_input = st.text_area("商品説明を貼り付けてください", height=200)
        if st.button("AIで解析する") and text_input:
            with st.spinner("単価と長さを計算中..."):
                try:
                    # 合体させた計算ルール付きプロンプト
                    prompt = f"""
                    以下のテキストから生地情報を抽出し、指定のルールで計算して整理してください。

                    【計算ルール】:
                    1. 「数量」と「販売単位（50cmなど）」を掛け合わせて【合計の長さ】を出す。
                    2. 「表示価格（単価）」と「数量」を掛け合わせて【購入合計価格】を出す。
                    3. 購入合計価格と合計の長さから【1mあたりの価格】を算出する。
                       （例：50cmで869円なら、1mあたり1,738円）

                    出力形式：
                    【生地名】: 
                    【素材】: 
                    【生地幅】: 
                    【購入合計の長さ】: ●cm（数量●個分）
                    【購入合計価格】: ●円
                    【1mあたりの価格】: ●円/m
                    【ショップ名】:

                    テキスト:
                    {text_input}
                    """
                    response = model.generate_content(prompt)
                    st.success("解析成功！")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"解析エラー: {e}")

    else:
        uploaded_files = st.file_uploader("写真を選択", type=['png', 'jpg', 'jpeg'], accept_multiple_files=True)
        if st.button("画像から解析") and uploaded_files:
            with st.spinner("画像を解析中..."):
                try:
                    img = Image.open(uploaded_files[0])
                    # 画像側にも計算ルールを適用
                    prompt = "この画像から生地情報を抽出し、購入合計価格と1mあたりの価格を計算して日本語で整理してください。"
                    response = model.generate_content([prompt, img])
                    st.success("画像解析成功！")
                    st.markdown(response.text)
                except Exception as e:
                    st.error(f"画像解析エラー: {e}")

with tab2:
    st.info("計算結果が正しければ、次はいよいよスプレッドシートへの保存ボタンを作りましょう！")

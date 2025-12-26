import streamlit as st
import google.generativeai as genai

st.set_page_config(page_title="洋裁在庫ログ", layout="centered")
st.title("🧵 魔法の洋裁ログ")

# APIキーの読み込み
if "GEMINI_API_KEY" not in st.secrets:
    st.error("Secretsに 'GEMINI_API_KEY' が設定されていません。")
    st.stop()

genai.configure(api_key=st.secrets["GEMINI_API_KEY"])

# --- モデルを自動で選ぶ関数（404エラー対策） ---
def get_available_model():
    candidates = ['gemini-1.5-flash-latest', 'gemini-1.5-flash', 'gemini-pro']
    available_models = []
    try:
        for m in genai.list_models():
            if 'generateContent' in m.supported_generation_methods:
                available_models.append(m.name)
        for cand in candidates:
            full_name = f"models/{cand}"
            if full_name in available_models:
                return genai.GenerativeModel(full_name)
    except:
        pass
    return genai.GenerativeModel('models/gemini-pro')

model = get_available_model()

# --- 入力画面 ---
text_input = st.text_area("商品説明を貼り付けてください", height=250)

if st.button("AIで解析する") and text_input:
    with st.spinner("単価と長さを計算中..."):
        try:
            # ご指定の計算ルールとプロンプト
            prompt = f"""
            以下のテキストから生地情報を抽出し、指定のルールで計算して整理してください。

            【計算ルール】:
            1. 「数量」と「販売単位（50cmなど）」を掛け合わせて【合計の長さ】を出す。
            2. 「表示価格」と「数量」を掛け合わせて【購入合計価格】を出す。
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
            st.success("解析が完了しました！")
            st.markdown(response.text)
        except Exception as e:
            st.error(f"解析エラー: {e}")

st.divider()
st.info("計算結果が正しければ、次はこの情報をスプレッドシートへ保存しましょう！")

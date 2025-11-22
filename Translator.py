import gradio as gr
import urllib.parse
import urllib.request
import json

# 언어 코드 목록
languages = {
    "Auto (자동 감지)": "auto",
    "English": "en",
    "Korean": "ko",
    "Japanese": "ja",
    "Chinese (Simplified)": "zh-CN",
    "Spanish": "es",
    "French": "fr",
    "German": "de",
    "Russian": "ru",
    "Italian": "it",
    "Portuguese": "pt",
    "Vietnamese": "vi",
    "Thai": "th",
    "Arabic": "ar",
    "Indonesian": "id",
}

# 번역 함수
def translate_text(text, src_lang, target_lang):
    if not text.strip():
        return "⚠️ 번역할 내용을 입력하세요."
    try:
        query = urllib.parse.quote(text)
        src_code = languages[src_lang]
        tgt_code = languages[target_lang]
        url = f"https://translate.googleapis.com/translate_a/single?client=gtx&sl={src_code}&tl={tgt_code}&dt=t&q={query}"

        with urllib.request.urlopen(url) as response:
            data = json.loads(response.read().decode("utf-8"))
            translated_text = data[0][0][0]
            return translated_text
    except Exception as e:
        return f"❌ 오류: {e}"

# Gradio UI
demo = gr.Interface(
    fn=translate_text,
    inputs=[
        gr.Textbox(label="번역할 문장 입력", placeholder="예: Hello World"),
        gr.Dropdown(list(languages.keys()), value="Auto (자동 감지)", label="원본 언어 선택"),
        gr.Dropdown(list(languages.keys()), value="Korean", label="번역할 언어 선택"),
    ],
    outputs=gr.Textbox(label="번역 결과"),
    title="Gradio 번역기",
    flagging_mode="never"  # 🚩 Flag 버튼 제거
)

demo.launch()

import requests
import datetime
import gradio as gr

def generate_image(prompt):
    # Pollinations API 요청
    url = f"https://image.pollinations.ai/prompt/{prompt}"
    img_data = requests.get(url).content

    # 파일 이름 자동 생성 (시간 기반)
    t = str(datetime.datetime.today())
    name = t.replace(':','').replace('.','').replace('-','').replace(' ','')
    filename = f"image{name}.png"

    # 이미지 저장
    with open(filename, "wb") as f:
        f.write(img_data)

    return filename  # Gradio가 자동으로 이미지를 표시함

# Gradio 인터페이스 설정
interface = gr.Interface(
    fn=generate_image,
    inputs=gr.Textbox(label="프롬프트를 입력하세요"),
    outputs=gr.Image(label="생성된 이미지"),
    title="Pollinations.AI 이미지 생성기",
    description="텍스트 프롬프트를 입력하면 Pollinations.AI를 통해 이미지를 생성합니다."
)

if __name__ == "__main__":
    interface.launch()

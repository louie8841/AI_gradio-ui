import uuid
import json
import urllib.request
import gradio as gr
import os

# ------------------ Firebase Realtime Database URL ------------------
FIREBASE_URL = "https://chatbot-database-af5ef-default-rtdb.firebaseio.com/"  # 본인 프로젝트 URL

# ------------------ Firebase REST API ------------------
def save_user(username, password):
    url = f"{FIREBASE_URL}/users/{username}.json"
    data = json.dumps({"password": password}).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"}, method="PUT")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def load_users():
    url = f"{FIREBASE_URL}/users.json"
    try:
        with urllib.request.urlopen(url) as resp:
            data = json.loads(resp.read().decode())
            return {k:v["password"] for k,v in data.items()} if data else {}
    except:
        return {}

def save_chats(username, sessions_state):
    url = f"{FIREBASE_URL}/chats/{username}.json"
    data = json.dumps(sessions_state).encode()
    req = urllib.request.Request(url, data=data, headers={"Content-Type":"application/json"}, method="PUT")
    with urllib.request.urlopen(req) as resp:
        return json.loads(resp.read().decode())

def load_chats(username):
    url = f"{FIREBASE_URL}/chats/{username}.json"
    try:
        with urllib.request.urlopen(url) as resp:
            return json.loads(resp.read().decode()) or {}
    except:
        return {}

# ------------------ Gemini API ------------------
API_KEY = "Your-API-key"  # Gemini API 키
API_URL = f"https://generativelanguage.googleapis.com/v1beta/models/gemini-2.0-flash:generateContent?key={API_KEY}"

def call_gemini(history):
    if not history:
        return "안녕하세요! 무엇을 도와드릴까요?"

    contents = [{"role": "user" if h["role"]=="user" else "model",
                 "parts":[{"text":h["text"]}]} for h in history]

    data = {"contents": contents, "generationConfig":{"temperature":0.7}}

    try:
        req = urllib.request.Request(API_URL,
                                     data=json.dumps(data).encode("utf-8"),
                                     headers={"Content-Type":"application/json"},
                                     method="POST")
        with urllib.request.urlopen(req) as response:
            result = json.loads(response.read().decode("utf-8"))
            return result["candidates"][0]["content"]["parts"][0]["text"]
    except:
        return "❌ 서버 오류"

# ------------------ 채팅 관리 ------------------
chat_id_map = {}

def make_chat_list(sessions_state):
    titles = []
    chat_id_map.clear()
    for cid, conv in sessions_state.items():
        titles.append(conv["title"])
        chat_id_map[conv["title"]] = cid
    return titles

def new_chat(sessions_state, user):
    chat_id = str(uuid.uuid4())[:8]
    sessions_state[chat_id] = {"title": "새 채팅", "history": [], "ui": []}
    titles = make_chat_list(sessions_state)
    save_chats(user, sessions_state)
    return chat_id, gr.update(choices=titles, value="새 채팅"), [], sessions_state

def send_message(user_input, selected_title, sessions_state, user):
    if not user_input:
        return "", selected_title, gr.update(), [], sessions_state
    chat_id = chat_id_map.get(selected_title, str(uuid.uuid4())[:8])
    if chat_id not in sessions_state:
        sessions_state[chat_id] = {"title": "새 채팅", "history": [], "ui": []}
    conv = sessions_state[chat_id]
    conv["history"].append({"role": "user", "text": user_input})
    if conv["title"] == "새 채팅":
        conv["title"] = (user_input[:15] + "…") if len(user_input) > 15 else user_input
    reply = call_gemini(conv["history"])
    conv["history"].append({"role": "model", "text": reply})
    conv["ui"].append({"role": "user", "content": user_input})
    conv["ui"].append({"role": "assistant", "content": reply})
    titles = make_chat_list(sessions_state)
    save_chats(user, sessions_state)
    return "", conv["title"], gr.update(choices=titles, value=conv["title"]), conv["ui"], sessions_state

def switch_chat(selected_title, sessions_state):
    chat_id = chat_id_map.get(selected_title)
    if chat_id and chat_id in sessions_state:
        conv = sessions_state[chat_id]
        return conv["title"], conv["ui"], sessions_state
    return "", [], sessions_state

def delete_chat(selected_title, sessions_state, user):
    chat_id = chat_id_map.get(selected_title)
    if chat_id and chat_id in sessions_state:
        del sessions_state[chat_id]
        save_chats(user, sessions_state)
        titles = make_chat_list(sessions_state)
        return gr.update(choices=titles, value=None), [], sessions_state, "채팅이 삭제되었습니다."
    return gr.update(), [], sessions_state, "삭제할 채팅을 선택하세요."

# ------------------ 로그인/회원가입 ------------------
def login(username, password):
    users = load_users()
    if username in users and users[username] == password:
        sessions_state = load_chats(username)
        return gr.update(visible=False), gr.update(visible=True), sessions_state, username, ""
    return gr.update(visible=True), gr.update(visible=False), {}, "", "아이디 또는 비밀번호 오류"

def signup(username, password):
    if not username or not password:
        return "아이디/비밀번호 입력 필요"
    users = load_users()
    if username in users:
        return "이미 존재하는 아이디"
    save_user(username, password)
    return "회원가입 완료! 로그인하세요."

def logout():
    return gr.update(visible=True), gr.update(visible=False), {}, "", ""

# ------------------ 목록 토글 ------------------
def toggle_chat_list(chat_list_visible):
    new_state = not chat_list_visible
    return new_state, gr.update(visible=new_state)

# ------------------ UI ------------------
with gr.Blocks() as demo:
    current_title = gr.State("")
    chat_list_visible = gr.State(True)
    username_state = gr.State("")
    sessions_state = gr.State({})

    # 로그인/회원가입
    with gr.Column(visible=True) as login_page:
        username_input = gr.Textbox(label="아이디")
        password_input = gr.Textbox(label="비밀번호", type="password")
        login_btn = gr.Button("로그인")
        signup_btn = gr.Button("회원가입")
        login_message = gr.Markdown("")
        signup_message = gr.Markdown("")

    # 채팅 화면
    with gr.Column(visible=False) as chat_page:
        with gr.Row():
            logout_btn = gr.Button("로그아웃")
            toggle_list_btn = gr.Button("목록 토글")
        with gr.Row():
            with gr.Column(scale=1, visible=True) as chat_list_column:
                new_btn = gr.Button("새 채팅")
                delete_btn = gr.Button("채팅 삭제")
                chat_list = gr.Radio(choices=[], label="채팅 목록", interactive=True)
            with gr.Column(scale=3):
                chatbot = gr.Chatbot(type="messages")
                msg = gr.Textbox(label="질문 입력")
                delete_message = gr.Markdown("")

    # 이벤트 연결
    login_btn.click(login, inputs=[username_input, password_input],
                    outputs=[login_page, chat_page, sessions_state, username_state, login_message])
    signup_btn.click(signup, inputs=[username_input, password_input], outputs=[signup_message])
    logout_btn.click(logout, outputs=[login_page, chat_page, sessions_state, username_state, chatbot])
    new_btn.click(new_chat, inputs=[sessions_state, username_state],
                  outputs=[current_title, chat_list, chatbot, sessions_state])
    msg.submit(send_message, inputs=[msg, chat_list, sessions_state, username_state],
               outputs=[msg, chat_list, chat_list, chatbot, sessions_state])
    chat_list.change(switch_chat, inputs=[chat_list, sessions_state], outputs=[current_title, chatbot, sessions_state])
    delete_btn.click(delete_chat, inputs=[chat_list, sessions_state, username_state],
                     outputs=[chat_list, chatbot, sessions_state, delete_message])
    toggle_list_btn.click(toggle_chat_list, inputs=[chat_list_visible],
                          outputs=[chat_list_visible, chat_list_column])

demo.launch()

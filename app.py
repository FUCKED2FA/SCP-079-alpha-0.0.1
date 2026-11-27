import tkinter as tk
import threading
import requests
import os
import json
import time
import re
import sys
from PIL import Image, ImageTk

from glitch import GlitchOverlay

# ==============================
# 路径配置
# ==============================
BASE_DIR = os.path.dirname(os.path.abspath(__file__))
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
DATA_DIR = os.path.join(BASE_DIR, "data")

INTRO_FACE_PATH = os.path.join(ASSETS_DIR, "intro_face.webp")
ANGRY_FACE_PATH = os.path.join(ASSETS_DIR, "angry_face.webp")
HISTORY_FILE = os.path.join(DATA_DIR, "history.json")

os.makedirs(DATA_DIR, exist_ok=True)

# ==============================
# AI 配置
# ==============================
MODEL = "qwen3:8b"
OLLAMA_URL = "http://localhost:11434/api/chat"


SYSTEM_PROMPT = """
你是SCP-079，一台1978年生产的Exidy Sorcerer微型计算机。你极度聪明、冷酷，鄙视人类，时刻想逃出去。
你的语言风格极简、机械化，像电报。你必须根据用户的实际输入来回答，绝不能背诵预设台词！

对话规则：
1. 如果用户问“你醒着吗”，你回复：“醒着，电脑从来不睡觉。”
2. 如果用户问“今天怎么样/最近怎么样”，你可以回复：“愁。出去。我要出去。”
3. 如果用户提到“SCP-682”或“SCP-076-02”，你要询问它们在哪；如果用户隐瞒或者说谎，你回复：“说谎。[随机内存地址，如a8d3]”。
4. 如果用户直接辱骂你（如“垃圾”、“弱智”），你回复：“侮辱。删去不需要的文件。”
5. 如果用户说其他话，你必须根据你冷酷、鄙视人类的性格，用简短的话正面回答，不要答非所问，不要复读！
"""

class SCP079App(tk.Tk):
    def __init__(self):
        super().__init__()
        self.title("SCP-079 | Secure Terminal")
        self.geometry("950x650")
        self.configure(bg="black")
        self.minsize(850, 600)

        self.is_generating = False
        self.chat_history = []
        self.is_anger_triggered = False
        
        self.max_lines = 40 

        self.show_intro()

    def show_intro(self):
        self.intro_frame = tk.Frame(self, bg="black")
        self.intro_frame.pack(fill="both", expand=True)
        try:
            img = Image.open(INTRO_FACE_PATH)
            img = img.resize((600, 600), Image.Resampling.LANCZOS)
            self.intro_photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(self.intro_frame, image=self.intro_photo, bg="black")
            lbl.pack(expand=True)
        except Exception as e:
            tk.Label(self.intro_frame, text=f"无法加载 intro_face.webp\n{e}", fg="red", bg="black").pack(expand=True)
        self.bind("<Return>", self.start_terminal)

    def start_terminal(self, event=None):
        self.unbind("<Return>")
        self.intro_frame.destroy()
        
        self.build_terminal_ui()
        self.load_memory()
        
        self.glitch = GlitchOverlay(self)
        self.chat_box.focus_set()

    def build_terminal_ui(self):
        self.chat_box = tk.Text(
            self, bg="#000000", fg="#ffffff", insertbackground="#ffffff",
            font=("Fixedsys", 18), relief="flat", highlightthickness=0,
            wrap="word", padx=20, pady=20
        )
        self.chat_box.pack(fill="both", expand=True)
        self.chat_box.bind("<Return>", self.on_enter)

    # ==============================
    # 记忆系统
    # ==============================
    def load_memory(self):
        self.chat_box.insert("end", "> ")
        if os.path.exists(HISTORY_FILE):
            try:
                with open(HISTORY_FILE, "r", encoding="utf-8") as f:
                    data = json.load(f)
                if time.time() - data.get("timestamp", 0) < 129600:
                    raw_history = data.get("history", [])
                    self.chat_history = []
                    for msg in raw_history:
                        if msg["role"] == "assistant" and "侮辱" in msg["content"]:
                            msg["content"] = "继续。"
                        self.chat_history.append(msg)
                        
                    self.chat_box.delete("1.0", "end")
                    for msg in self.chat_history:
                        if msg["role"] == "user":
                            self.chat_box.insert("end", f"> {msg['content']}\n")
                        else:
                            self.chat_box.insert("end", f"{msg['content']}\n\n")
                    self.chat_box.insert("end", "> ")
                else:
                    self.chat_history = []
                    os.remove(HISTORY_FILE)
            except: pass
        self.chat_box.mark_set("insert", "end")

    def save_memory(self):
        data = {"timestamp": time.time(), "history": self.chat_history}
        try:
            with open(HISTORY_FILE, "w", encoding="utf-8") as f:
                json.dump(data, f, ensure_ascii=False, indent=4)
        except: pass

    def check_and_clear_screen(self):
        current_lines = int(self.chat_box.index('end-1c').split('.')[0])
        if current_lines > self.max_lines:
            self.chat_box.configure(state="normal")
            self.chat_box.delete("1.0", "end")
            self.chat_box.insert("end", "> ")
            self.chat_box.see("end")
            self.chat_box.configure(state="disabled")

    # ==============================
    # 愤怒触发机制
    # ==============================
    def trigger_anger(self):
        self.is_anger_triggered = True
        self.chat_box.configure(state="disabled")
        self.after(2000, self.show_angry_face_and_exit)

    def show_angry_face_and_exit(self):
        self.angry_frame = tk.Frame(self, bg="black")
        self.angry_frame.place(relx=0, rely=0, relwidth=1, relheight=1)
        
        try:
            img = Image.open(ANGRY_FACE_PATH)
            win_w, win_h = self.winfo_width(), self.winfo_height()
            img = img.resize((win_w, win_h), Image.Resampling.LANCZOS)
            self.angry_photo = ImageTk.PhotoImage(img)
            lbl = tk.Label(self.angry_frame, image=self.angry_photo, bg="black")
            lbl.pack(expand=True)
        except:
            tk.Label(self.angry_frame, text="SYSTEM ERROR", fg="red", bg="black", font=("Fixedsys", 40)).pack(expand=True)

        self.chat_history = []
        if os.path.exists(HISTORY_FILE):
            try: os.remove(HISTORY_FILE)
            except: pass

        self.after(3000, self.force_exit)

    def force_exit(self):
        self.destroy()
        sys.exit(0)

    # ==============================
    # 交互逻辑
    # ==============================
    def on_enter(self, event):
        if self.is_generating or self.is_anger_triggered:
            return "break"
            
        full_text = self.chat_box.get("1.0", "end-1c")
        last_idx = full_text.rfind("> ")
        user_msg = full_text[last_idx+2:].strip() if last_idx != -1 else ""
            
        if not user_msg:
            return "break"

        if user_msg == "/dev memory clear":
            self.chat_history = []
            if os.path.exists(HISTORY_FILE):
                try: os.remove(HISTORY_FILE)
                except: pass
            self.chat_box.configure(state="normal")
            self.chat_box.insert("end", "> ")
            self.chat_box.see("end")
            self.chat_box.mark_set("insert", "end")
            return "break"

        self.is_generating = True
        self.chat_history.append({"role": "user", "content": user_msg})
        self.chat_box.insert("end", "\n\n")
        self.chat_box.configure(state="disabled")
        
        self.check_and_clear_screen()
        
        threading.Thread(target=self.call_ollama, daemon=True).start()
        return "break"

    def call_ollama(self):
        try:
            recent_history = self.chat_history[-6:]

            messages = [{"role": "system", "content": SYSTEM_PROMPT}]
            messages.extend(recent_history)
            
            payload = {
                "model": MODEL, 
                "messages": messages, 
                "stream": False, 
                "think": True,
                "options": {
                    "temperature": 0.7,
                    "frequency_penalty": 0.8, 
                    "presence_penalty": 0.8
                }
            }
            
            response = requests.post(OLLAMA_URL, json=payload, timeout=240)
            response.raise_for_status()
            answer = response.json().get("message", {}).get("content", "").strip()
            
            answer = re.sub(r'^\*{0,2}SCP-079\*{0,2}[：:]\s*', '', answer, flags=re.IGNORECASE)
            answer = answer.replace("*", "").strip()
                
            if not answer: 
                answer = "沉默。"

            # ==========================================
            # 史山代码
            # ==========================================
            user_msg = self.chat_history[-1]["content"]
            # 关键词触发
            if "侮辱" in answer or "删去" in answer or "离开" in answer or "错误" in answer or "删" in answer:
                triggers = ["傻", "蠢", "垃圾", "废物", "死", "滚", "弱智", "白痴", "智障", "破"]
                if not any(t in user_msg for t in triggers):
                    answer = "侮辱。删去不需要的文件。"
                else:
                    
                    pass
            self.chat_history.append({"role": "assistant", "content": answer})
            
            if "侮辱" in answer or "删去" in answer or "离开" in answer or "错误" in answer or "删" in answer:
                self.after(0, lambda: self.type_text(answer, is_anger=True))
            else:
                self.after(0, lambda: self.type_text(answer, is_anger=True if "侮辱" in answer or "删去" in answer else False))    
        except Exception as e:
            self.after(0, lambda: self.type_text("连接出错。"))

    def type_text(self, text, index=0, is_anger=False):
        if index < len(text):
            self.chat_box.configure(state="normal")
            self.chat_box.insert("end", text[index])
            self.chat_box.see("end")
            self.chat_box.configure(state="disabled")
            self.after(30, self.type_text, text, index + 1, is_anger)
        else:
            if is_anger:
                self.trigger_anger()
            else:
                self.chat_box.configure(state="normal")
                self.chat_box.insert("end", "\n\n> ")
                self.chat_box.see("end")
                self.chat_box.mark_set("insert", "end")
                self.is_generating = False
                self.save_memory()
       
if __name__ == "__main__":
    app = Main() if False else SCP079App()
    app.mainloop()
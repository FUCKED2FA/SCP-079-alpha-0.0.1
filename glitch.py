import tkinter as tk
import random

class GlitchOverlay(tk.Toplevel):
    def __init__(self, master):
        super().__init__(master)
        self.master = master
        self.overrideredirect(True)
        self.attributes('-topmost', True)
        try:
            self.attributes('-transparentcolor', 'black')
            self.attributes('-disabled', True) 
        except:
            pass 
        #窗口设置   
        self.configure(bg='black')
        self.canvas = tk.Canvas(self, bg='black', highlightthickness=0)
        self.canvas.pack(fill='both', expand=True)
        self.master.bind('<Configure>', self.sync_geometry)
        self.sync_geometry()
        self.update_effect()

    def sync_geometry(self, event=None):
        
        self.geometry(f"{self.master.winfo_width()}x{self.master.winfo_height()}+{self.master.winfo_rootx()}+{self.master.winfo_rooty()}")

    def update_effect(self):
        w = self.master.winfo_width()
        h = self.master.winfo_height()
        
        
        if w <= 1 or h <= 1:
            self.after(100, self.update_effect)
            return

        self.canvas.delete("all")
        
        
        for y in range(0, h, random.randint(3, 8)):
            color = random.choice(["#0a1a0a", "#051005", ""])
            if color:
                self.canvas.create_line(0, y, w, y, fill=color)

        
        for _ in range(150):
            x = random.randint(0, w)
            y = random.randint(0, h)
            self.canvas.create_line(x, y, x+random.randint(1,3), y, fill=random.choice(["#1a4a1a", "#35ff65", "#000000"]))

        
        if random.random() > 0.8:
            bx = random.randint(0, w)
            by = random.randint(0, h)
            bw = random.randint(20, 100)
            bh = random.randint(5, 20)
            self.canvas.create_rectangle(bx, by, bx+bw, by+bh, fill="#12351a", outline="")

        
        self.after(random.randint(50, 150), self.update_effect)#循环
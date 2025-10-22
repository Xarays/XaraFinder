import tkinter as tk
import random

class Aquarium:
    def __init__(self, parent):
        self.window = tk.Toplevel(parent)
        self.window.title("🐠 Секретный аквариум создателей")
        self.window.geometry("900x700")
        self.window.configure(bg="#001122")
        self.window.resizable(False, False)
        self.window.attributes('-topmost', True)

        header = tk.Frame(self.window, bg="#58a6ff", height=60)
        header.pack(fill=tk.X)
        tk.Label(header, text="🐠 Аквариум создателей: Kara7s (Xarays) & Nakish_",
                 font=("Segoe UI", 14, "bold"), bg="#58a6ff", fg="white").pack(pady=15)

        self.canvas = tk.Canvas(self.window, width=900, height=600, bg="#001122", highlightthickness=0)
        self.canvas.pack()

        self.creator_fishes = [
            {"name": "Kara7s", "x": 200, "y": 300, "color": "#FF6B6B", "size": 35, "speed_x": 2, "speed_y": 1},
            {"name": "Xarays", "x": 400, "y": 200, "color": "#4ECDC4", "size": 32, "speed_x": -2, "speed_y": 0},
            {"name": "Nakish_", "x": 600, "y": 400, "color": "#FFE66D", "size": 38, "speed_x": 1, "speed_y": -1},
            {"name": "Fancy_Legend", "x": 300, "y": 100, "color": "#FFE66D", "size": 40, "speed_x": 1, "speed_y": -2},
            {"name": "botinok", "x": 700, "y": 200, "color": "#FFE66D", "size": 42, "speed_x": 2, "speed_y": -1}
        ]

        self.fishes = []
        for _ in range(10): self.create_fish()
        self.bubbles = []; self.animate()

        close_btn = tk.Button(self.window, text="Закрыть аквариум", command=self.window.destroy,
                              bg="#f85149", fg="white", font=("Arial", 10), pady=5)
        close_btn.pack(pady=10)

    def create_fish(self):
        colors = ["#FF6B6B", "#4ECDC4", "#FFE66D", "#6A0572", "#FF9A8B", "#95E1D3", "#FCE38A"]
        x = random.randint(50, 850); y = random.randint(50, 550); color = random.choice(colors)
        size = random.randint(20, 40); speed_x = random.choice([-3, -2, -1, 1, 2, 3]); speed_y = random.choice([-1, 0, 1])
        fish = {"body": None, "tail": None, "eye": None, "label": None, "x": x, "y": y, "size": size,
                "speed_x": speed_x, "speed_y": speed_y, "color": color, "name": None}
        self.fishes.append(fish)

    def draw_fish(self, fish, is_creator=False):
        direction = 1 if fish["speed_x"] > 0 else -1; size = fish["size"]
        body = self.canvas.create_oval(fish["x"] - size, fish["y"] - size // 2, fish["x"] + size, fish["y"] + size // 2,
                                       fill=fish["color"], outline="")
        tail_x = fish["x"] - direction * size
        tail_points = [tail_x, fish["y"], tail_x - direction * size, fish["y"] - size // 2, tail_x - direction * size, fish["y"] + size // 2]
        tail = self.canvas.create_polygon(tail_points, fill=fish["color"], outline="")
        eye_x = fish["x"] + direction * size // 2
        eye = self.canvas.create_oval(eye_x - 2, fish["y"] - 2, eye_x + 2, fish["y"] + 2, fill="black")
        label = None
        if is_creator and fish["name"]:
            label = self.canvas.create_text(fish["x"], fish["y"] - size - 10, text=fish["name"], fill=fish["color"], font=("Arial", 10, "bold"))
        return body, tail, eye, label

    def animate(self):
        self.canvas.delete("all")
        self.canvas.create_rectangle(0, 550, 900, 600, fill="#2d1b00", outline="")
        for x in range(50, 900, 80):
            height = random.randint(80, 200)
            self.canvas.create_line(x, 550, x, 550 - height, fill="#00AA00", width=3)
            for y in range(550 - height, 550, 20):
                self.canvas.create_line(x, y, x + random.randint(10, 30), y - random.randint(5, 15), fill="#00CC00", width=2)
        if random.random() < 0.1:
            self.bubbles.append({"x": random.randint(50, 850), "y": 550, "size": random.randint(5, 15), "speed": random.uniform(1, 3)})
        new_bubbles = []
        for bubble in self.bubbles:
            bubble["y"] -= bubble["speed"]
            if bubble["y"] > 0:
                new_bubbles.append(bubble)
                self.canvas.create_oval(bubble["x"] - bubble["size"], bubble["y"] - bubble["size"],
                                        bubble["x"] + bubble["size"], bubble["y"] + bubble["size"], fill="#88FFFF", outline="")
        self.bubbles = new_bubbles
        for fish in self.fishes:
            fish["x"] += fish["speed_x"]; fish["y"] += fish["speed_y"]
            if fish["x"] < 20 or fish["x"] > 880: fish["speed_x"] *= -1
            if fish["y"] < 20 or fish["y"] > 530: fish["speed_y"] *= -1
            if random.random() < 0.02: fish["speed_y"] = random.choice([-1, 0, 1])
            fish["body"], fish["tail"], fish["eye"], _ = self.draw_fish(fish)
        for fish in self.creator_fishes:
            fish["x"] += fish["speed_x"]; fish["y"] += fish["speed_y"]
            if fish["x"] < 50 or fish["x"] > 850: fish["speed_x"] *= -1
            if fish["y"] < 50 or fish["y"] > 500: fish["speed_y"] *= -1
            if random.random() < 0.01: fish["speed_y"] = random.choice([-1, 0, 1])
            fish["body"], fish["tail"], fish["eye"], fish["label"] = self.draw_fish(fish, True)
        self.window.after(50, self.animate)
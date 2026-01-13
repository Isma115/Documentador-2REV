import tkinter as tk
from tkinter import filedialog, messagebox
import os

class ProjectLoaderApp:
    def __init__(self, root):
        self.root = root
        self.root.title("Project Loader")
        self.root.geometry("800x600")
        self.root.configure(bg="#1E1E1E")  # Dark background

        # Custom Styles
        self.bg_color = "#1E1E1E"
        self.fg_color = "#FFFFFF"
        self.accent_color = "#007ACC"  # VS Code-like blue
        self.button_bg = "#3C3C3C"
        self.button_fg = "#000000"
        self.font_style = ("Segoe UI", 10)
        self.header_font = ("Segoe UI", 12, "bold")
        
        # Configure window to take up most of the screen
        screen_width = root.winfo_screenwidth()
        screen_height = root.winfo_screenheight()
        # Set to ~90% of screen size
        width = int(screen_width * 0.9)
        height = int(screen_height * 0.9)
        # Center the window roughly
        x = (screen_width - width) // 2
        y = (screen_height - height) // 2
        self.root.geometry(f"{width}x{height}+{x}+{y}")
        self.top_bar = tk.Frame(root, bg=self.bg_color, height=50)
        self.top_bar.pack(side=tk.TOP, fill=tk.X, padx=10, pady=10)

        # Load Folder Button
        self.load_btn = tk.Button(
            self.top_bar,
            text="Cargar Proyecto",
            command=self.load_project,
            bg=self.accent_color,
            fg=self.button_fg,
            font=self.header_font,
            relief="flat",
            padx=15,
            pady=5,
            cursor="hand2"
        )
        self.load_btn.pack(side=tk.LEFT)

        # Path Label
        self.path_label = tk.Label(
            self.top_bar,
            text="Ningún proyecto cargado",
            bg=self.bg_color,
            fg="#AAAAAA",
            font=self.font_style
        )
        self.path_label.pack(side=tk.LEFT, padx=15)

        # Main Content Area (Empty for now)
        self.content_frame = tk.Frame(root, bg=self.bg_color)
        self.content_frame.pack(expand=True, fill=tk.BOTH)

    def load_project(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.path_label.config(text=f"Proyecto: {folder_selected}", fg=self.fg_color)
            # Future logic to handle the loaded project can go here
            print(f"Project loaded: {folder_selected}")

if __name__ == "__main__":
    root = tk.Tk()
    app = ProjectLoaderApp(root)
    root.mainloop()

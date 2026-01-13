import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class CodeEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Python Code Editor")
        self.geometry("1100x700")
        
        # Configure Grid Layout
        # Column 0: Editor (Flexible)
        # Column 1: Side Panel (Fixed width mostly, but we can use weight=0)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0, minsize=250)
        self.grid_rowconfigure(0, weight=0) # Top bar (optional)
        self.grid_rowconfigure(1, weight=1) # Main content

        # --- Variables ---
        self.current_project_path = None

        # --- Top Bar (Menu/Actions) ---
        self.top_bar = ctk.CTkFrame(self, height=40, corner_radius=0)
        self.top_bar.grid(row=0, column=0, columnspan=2, sticky="ew")
        
        self.load_btn = ctk.CTkButton(
            self.top_bar, 
            text="Open Folder", 
            command=self.load_project,
            width=100,
            height=30
        )
        self.load_btn.pack(side="left", padx=10, pady=5)

        self.path_label = ctk.CTkLabel(
            self.top_bar, 
            text="No Project Opened",
            text_color="gray"
        )
        self.path_label.pack(side="left", padx=5)

        # --- Main Editor Area (Left) ---
        self.editor_frame = ctk.CTkFrame(self, corner_radius=0)
        self.editor_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 2), pady=0)
        
        # Text Editor
        self.code_editor = ctk.CTkTextbox(
            self.editor_frame,
            font=("Consolas", 14), # Monospaced font
            corner_radius=0,
            activate_scrollbars=True
        )
        self.code_editor.pack(fill="both", expand=True)
        self.code_editor.insert("0.0", "# Welcome to Python Editor\n# Open a folder to start coding.")

        # --- Side Panel (Right) ---
        self.side_panel = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.side_panel.grid(row=1, column=1, sticky="nsew")
        
        # Header for the list
        self.list_header = ctk.CTkLabel(
            self.side_panel, 
            text="Project Files", 
            font=("Segoe UI", 13, "bold")
        )
        self.list_header.pack(pady=10, padx=10, anchor="w")

        # Scrollable List for files
        self.file_list_frame = ctk.CTkScrollableFrame(
            self.side_panel, 
            label_text=None,
            fg_color="transparent"
        )
        self.file_list_frame.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Placeholder items
        self.add_placeholder_item("No files to show")

    def load_project(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.current_project_path = folder_selected
            self.path_label.configure(text=f"{folder_selected}")
            self.populate_file_list(folder_selected)

    def populate_file_list(self, folder_path):
        # Clear existing items
        for widget in self.file_list_frame.winfo_children():
            widget.destroy()
            
        try:
            items = sorted(os.listdir(folder_path))
            for item in items:
                # Simple file/folder differentiation logic
                full_path = os.path.join(folder_path, item)
                if os.path.isdir(full_path):
                    self.add_file_item(f"📁 {item}")
                else:
                    self.add_file_item(f"📄 {item}")
        except Exception as e:
            print(f"Error loading files: {e}")
            self.add_placeholder_item("Error loading files")

    def add_file_item(self, text):
        lbl = ctk.CTkLabel(
            self.file_list_frame, 
            text=text, 
            anchor="w",
            cursor="hand2"
        )
        lbl.pack(fill="x", pady=2, padx=5)
        # Bind click event later for opening files

    def add_placeholder_item(self, text):
        lbl = ctk.CTkLabel(self.file_list_frame, text=text, text_color="gray")
        lbl.pack(pady=20)

if __name__ == "__main__":
    app = CodeEditorApp()
    app.mainloop()


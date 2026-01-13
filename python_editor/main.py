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
            text="Code Assets", 
            font=("Segoe UI", 13, "bold")
        )
        self.list_header.pack(pady=(10, 5), padx=10, anchor="w")

        # Search Bar
        self.search_entry = ctk.CTkEntry(
            self.side_panel,
            placeholder_text="Search files...",
            height=30
        )
        self.search_entry.pack(fill="x", padx=10, pady=(0, 10))
        self.search_entry.bind("<KeyRelease>", self.filter_file_list)

        # Virtual List for assets
        from virtual_list import VirtualList
        self.file_list = VirtualList(self.side_panel, item_height=40)
        self.file_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Placeholder items
        self.file_list.set_data(["No files to show"])

    def load_project(self):
        folder_selected = filedialog.askdirectory()
        if folder_selected:
            self.current_project_path = folder_selected
            self.path_label.configure(text=f"{folder_selected}")
            self.load_assets(folder_selected)

    def load_assets(self, folder_path):
        import asset_extractor
        self.all_assets = asset_extractor.scan_project_assets(folder_path)
        self.populate_asset_list()

    def populate_asset_list(self, filter_text=""):
        if not hasattr(self, 'all_assets') or not self.all_assets:
            self.file_list.set_data(["No code assets found"])
            return

        filtered_assets = []
        for asset in self.all_assets:
            if filter_text.lower() in asset.name.lower():
                filtered_assets.append(asset)
        
        if not filtered_assets:
            self.file_list.set_data(["No matches found"])
        else:
            self.file_list.set_data(filtered_assets)

    def filter_file_list(self, event=None):
        if hasattr(self, 'all_assets'):
            filter_text = self.search_entry.get()
            self.populate_asset_list(filter_text)




if __name__ == "__main__":
    app = CodeEditorApp()
    app.mainloop()


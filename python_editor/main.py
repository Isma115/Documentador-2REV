import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os
import json
import asset_extractor

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
        self.CONFIG_FILE = "config.json"
        self.current_project_path = None
        
        # Load Settings
        self.load_settings()

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
        
        self.create_btn = ctk.CTkButton(
            self.top_bar,
            text="Create Compound",
            command=self.create_compound_asset_window,
            width=120,
            height=30,
            fg_color="#00695C", 
            hover_color="#004D40"
        )
        self.create_btn.pack(side="left", padx=5, pady=5)

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

        # Sort Options
        self.sort_var = ctk.StringVar(value="Name")
        self.sort_menu = ctk.CTkOptionMenu(
            self.side_panel,
            values=["Name", "Type"],
            command=self.on_sort_change,
            height=25,
            width=100
        )
        self.sort_menu.pack(pady=(0, 5), padx=10, anchor="e")

        # Virtual List for assets
        from virtual_list import VirtualList
        self.file_list = VirtualList(self.side_panel, item_height=40)
        self.file_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Placeholder items
        self.file_list.set_data(["No files to show"])

        # Auto-load project if exists
        if self.current_project_path and os.path.exists(self.current_project_path):
            self.path_label.configure(text=f"{self.current_project_path}")
            # Use after to ensure UI is ready
            self.after(100, lambda: self.load_assets(self.current_project_path))

    def load_settings(self):
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, "r") as f:
                    settings = json.load(f)
                    self.current_project_path = settings.get("last_directory")
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            settings = {"last_directory": self.current_project_path}
            with open(self.CONFIG_FILE, "w") as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def load_project(self):
        folder_selected = filedialog.askdirectory(initialdir=self.current_project_path)
        if folder_selected:
            self.current_project_path = folder_selected
            self.path_label.configure(text=f"{folder_selected}")
            self.load_assets(folder_selected)
            self.save_settings()

    def load_assets(self, folder_path):
        # import asset_extractor # Imported globally now
        self.all_assets = asset_extractor.scan_project_assets(folder_path)
        self.load_custom_assets(folder_path)  # Load saved compound assets
        self.populate_asset_list()

    def populate_asset_list(self, filter_text=""):
        if not hasattr(self, 'all_assets') or not self.all_assets:
            self.file_list.set_data(["No code assets found"])
            return

        filtered_assets = []
        for asset in self.all_assets:
            if filter_text.lower() in asset.name.lower():
                filtered_assets.append(asset)
        
        # Apply Sorting
        sort_by = self.sort_var.get()
        filtered_assets = self.sort_assets(filtered_assets, sort_by)

        if not filtered_assets:
            self.file_list.set_data(["No matches found"])
        else:
            self.file_list.set_data(filtered_assets)

    def sort_assets(self, assets, sort_by):
        if sort_by == "Name":
            return sorted(assets, key=lambda x: x.name.lower())
        elif sort_by == "Type":
            return sorted(assets, key=lambda x: (x.asset_type, x.name.lower()))
        return assets

    def on_sort_change(self, choice):
        self.filter_file_list()

    def filter_file_list(self, event=None):
        if hasattr(self, 'all_assets'):
            filter_text = self.search_entry.get()
            self.populate_asset_list(filter_text)


    def create_compound_asset_window(self):
        if not hasattr(self, 'all_assets') or not self.all_assets:
            return

        window = ctk.CTkToplevel(self)
        window.title("Create Compound Asset")
        
        # Geometry and Centering
        width = 900
        height = 700
        
        self.update_idletasks()
        main_x = self.winfo_x()
        main_y = self.winfo_y()
        main_width = self.winfo_width()
        main_height = self.winfo_height()
        
        x = main_x + (main_width // 2) - (width // 2)
        y = main_y + (main_height // 2) - (height // 2)
        
        window.geometry(f"{width}x{height}+{x}+{y}")
        window.grab_set()
        window.focus_set()
        
        # --- Name Entry ---
        name_frame = ctk.CTkFrame(window, fg_color="transparent")
        name_frame.pack(fill="x", padx=20, pady=(10, 5))
        
        ctk.CTkLabel(name_frame, text="Asset Name:", font=("Arial", 12, "bold")).pack(side="left")
        name_entry = ctk.CTkEntry(name_frame, width=300)
        name_entry.pack(side="left", padx=10)
        
        # --- Lists Container ---
        lists_frame = ctk.CTkFrame(window, fg_color="transparent")
        lists_frame.pack(fill="both", expand=True, padx=20, pady=10)
        lists_frame.grid_columnconfigure(0, weight=1)
        lists_frame.grid_columnconfigure(1, weight=0)
        lists_frame.grid_columnconfigure(2, weight=1)
        lists_frame.grid_rowconfigure(1, weight=1)
        
        # --- Left Panel: Available Assets ---
        ctk.CTkLabel(lists_frame, text="Available Assets", font=("Arial", 11, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 5))
        
        left_search = ctk.CTkEntry(lists_frame, placeholder_text="Search...", height=28)
        left_search.grid(row=0, column=0, sticky="e", pady=(0, 5))

        from virtual_list import VirtualList
        available_list = VirtualList(lists_frame, item_height=35, command_double_click=lambda item: add_selected(item))
        available_list.grid(row=1, column=0, sticky="nsew", padx=(0, 5))
        
        # --- Center Buttons ---
        btn_frame = ctk.CTkFrame(lists_frame, fg_color="transparent", width=60)
        btn_frame.grid(row=1, column=1, padx=10)
        
        # --- Right Panel: Selected Assets ---
        ctk.CTkLabel(lists_frame, text="Selected Assets", font=("Arial", 11, "bold")).grid(row=0, column=2, sticky="w", pady=(0, 5))
        
        selected_list = VirtualList(lists_frame, item_height=35, command_double_click=lambda item: remove_selected(item))
        selected_list.grid(row=1, column=2, sticky="nsew", padx=(5, 0))
        
        # Selected items storage
        selected_assets = []
        
        def refresh_available():
            filter_text = left_search.get().lower()
            filtered = [a for a in self.all_assets if filter_text in a.name.lower() and a not in selected_assets]
            available_list.set_data(filtered)
        
        def refresh_selected():
            selected_list.set_data(selected_assets[:])
        
        def add_selected(item=None):
            if item is None:
                item = available_list.get_clicked_item()
            if item and item not in selected_assets:
                selected_assets.append(item)
                refresh_available()
                refresh_selected()
        
        def remove_selected(item=None):
            if item is None:
                item = selected_list.get_clicked_item()
            if item and item in selected_assets:
                selected_assets.remove(item)
                refresh_available()
                refresh_selected()
        
        add_btn = ctk.CTkButton(btn_frame, text="→", width=40, command=add_selected, fg_color="#00695C", hover_color="#004D40")
        add_btn.pack(pady=5)
        
        remove_btn = ctk.CTkButton(btn_frame, text="←", width=40, command=remove_selected, fg_color="#B71C1C", hover_color="#7F0000")
        remove_btn.pack(pady=5)
        
        left_search.bind("<KeyRelease>", lambda e: refresh_available())
        
        # Initial population
        refresh_available()
        refresh_selected()
        
        # --- Documentation ---
        doc_label = ctk.CTkLabel(window, text="Documentation:", font=("Arial", 12, "bold"))
        doc_label.pack(anchor="w", padx=20, pady=(10, 5))
        
        doc_textbox = ctk.CTkTextbox(window, height=120)
        doc_textbox.pack(fill="x", padx=20, pady=(0, 10))
        
        # --- Create Button ---
        def create():
            name = name_entry.get().strip()
            if not name:
                return
            
            documentation = doc_textbox.get("0.0", "end").strip()
            
            # Create "activos" folder if needed
            if self.current_project_path:
                activos_folder = os.path.join(self.current_project_path, "activos")
                os.makedirs(activos_folder, exist_ok=True)
                
                # Prepare data for JSON
                asset_data = {
                    "name": name,
                    "asset_type": "Compound",
                    "documentation": documentation,
                    "children": [{"name": a.name, "file_path": a.file_path, "line_number": a.line_number} for a in selected_assets]
                }
                
                # Save JSON
                json_path = os.path.join(activos_folder, f"{name}.json")
                with open(json_path, "w", encoding="utf-8") as f:
                    json.dump(asset_data, f, indent=2, ensure_ascii=False)
            
            # Create new asset object
            new_asset = asset_extractor.CodeAsset(
                name=name,
                asset_type="Compound",
                file_path=os.path.join(activos_folder, f"{name}.json") if self.current_project_path else "Virtual",
                line_number=0,
                children=selected_assets,
                documentation=documentation
            )
            
            self.all_assets.insert(0, new_asset)
            self.populate_asset_list()
            window.destroy()
        
        ctk.CTkButton(
            window,
            text="Create Asset",
            command=create,
            fg_color="#00695C",
            hover_color="#004D40",
            height=35
        ).pack(pady=15)


    def load_custom_assets(self, folder_path):
        """Load custom compound assets from the 'activos' folder."""
        activos_folder = os.path.join(folder_path, "activos")
        if not os.path.exists(activos_folder):
            return
        
        for filename in os.listdir(activos_folder):
            if filename.endswith(".json"):
                json_path = os.path.join(activos_folder, filename)
                try:
                    with open(json_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    
                    # Reconstruct children as CodeAsset objects (simplified)
                    children = []
                    for child_data in data.get("children", []):
                        child = asset_extractor.CodeAsset(
                            name=child_data.get("name", "Unknown"),
                            asset_type="Reference",
                            file_path=child_data.get("file_path", ""),
                            line_number=child_data.get("line_number", 0)
                        )
                        children.append(child)
                    
                    asset = asset_extractor.CodeAsset(
                        name=data.get("name", filename),
                        asset_type="Compound",
                        file_path=json_path,
                        line_number=0,
                        children=children,
                        documentation=data.get("documentation", "")
                    )
                    self.all_assets.insert(0, asset)
                except Exception as e:
                    print(f"Error loading custom asset {filename}: {e}")


if __name__ == "__main__":
    app = CodeEditorApp()
    app.mainloop()


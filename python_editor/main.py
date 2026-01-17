import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os
import json
import asset_extractor
from syntax_highlighter import SyntaxHighlighter

ctk.set_appearance_mode("Dark")
ctk.set_default_color_theme("blue")

class TreeNode:
    """Wrapper for assets to display in tree with depth and expansion state."""
    def __init__(self, asset, depth=0, is_expanded=False):
        self.asset = asset
        self.depth = depth
        self.is_expanded = is_expanded
        self.is_compound = getattr(asset, 'asset_type', '') == 'Compound'
        # Use original asset name without modification for consistent display
        self.name = asset.name if hasattr(asset, 'name') else str(asset)
        self.asset_type = getattr(asset, 'asset_type', 'default')
        # Copy other relevant properties from asset for consistent rendering
        self.file_path = getattr(asset, 'file_path', '')
        self.line_number = getattr(asset, 'line_number', 0)
    
    def __repr__(self):
        return self.name

class CodeEditorApp(ctk.CTk):
    def __init__(self):
        super().__init__()

        # Window Setup
        self.title("Python Code Editor")
        # Maximize window after UI is ready
        self.after(10, lambda: self.state('zoomed'))
        
        # Configure Grid Layout
        # Column 0: Editor (Flexible)
        # Column 1: Sub-assets Tree Panel (hidden by default)
        # Column 2: Side Panel (Assets list)
        self.grid_columnconfigure(0, weight=1)
        self.grid_columnconfigure(1, weight=0, minsize=0)  # Sub-assets panel (dynamic)
        self.grid_columnconfigure(2, weight=0, minsize=250)
        self.grid_rowconfigure(0, weight=0)  # Top bar
        self.grid_rowconfigure(1, weight=1)  # Main content
        
        # Track current compound asset being viewed
        self.current_compound_asset = None
        self.navigation_stack = []  # Stack for recursive navigation
        self.expanded_nodes = set()  # Track which nodes are expanded (by asset id)

        # --- Variables ---
        self.CONFIG_FILE = "config.json"
        self.current_project_path = None
        self.editor_font_size = 14  # Default font size for zoom
        
        # Load Settings (may override font_size)
        self.load_settings()

        # --- Top Bar (Menu/Actions) ---
        self.top_bar = ctk.CTkFrame(self, height=40, corner_radius=0)
        self.top_bar.grid(row=0, column=0, columnspan=3, sticky="ew")
        
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
            font=("Consolas", self.editor_font_size), # Monospaced font
            corner_radius=0,
            activate_scrollbars=True
        )
        self.code_editor.pack(fill="both", expand=True)
        self.code_editor.insert("0.0", "# Welcome to Python Editor\n# Open a folder to start coding.")
        
        # Bind zoom shortcuts (Ctrl + Plus/Minus)
        self.code_editor.bind("<Control-plus>", self.zoom_in)
        self.code_editor.bind("<Control-minus>", self.zoom_out)
        self.code_editor.bind("<Control-equal>", self.zoom_in)  # For keyboards where + is Shift+=
        self.code_editor.bind("<Control-KP_Add>", self.zoom_in)  # Numpad +
        self.code_editor.bind("<Control-KP_Subtract>", self.zoom_out)  # Numpad -

        # Initialize Syntax Highlighter
        self.syntax_highlighter = SyntaxHighlighter(self.code_editor)

        # --- Sub-assets Tree Panel (Middle - Hidden by default) ---
        self.subassets_panel = ctk.CTkFrame(self, width=250, corner_radius=0)
        # Initially hidden - will be shown when clicking compound asset
        
        # Sub-assets header
        self.subassets_header_frame = ctk.CTkFrame(self.subassets_panel, fg_color="transparent")
        self.subassets_header_frame.pack(fill="x", padx=5, pady=5)
        
        self.subassets_title = ctk.CTkLabel(
            self.subassets_header_frame,
            text="Sub-Assets",
            font=("Segoe UI", 12, "bold"),
            text_color="#00E676"
        )
        self.subassets_title.pack(side="left", padx=5)
        
        # Back button (hidden by default)
        self.back_subassets_btn = ctk.CTkButton(
            self.subassets_header_frame,
            text="←",
            width=25,
            height=25,
            command=self.navigate_back_subassets,
            fg_color="#1565C0",
            hover_color="#0D47A1"
        )
        # Initially hidden
        
        self.close_subassets_btn = ctk.CTkButton(
            self.subassets_header_frame,
            text="✕",
            width=25,
            height=25,
            command=self.hide_subassets_panel,
            fg_color="#B71C1C",
            hover_color="#7F0000"
        )
        self.close_subassets_btn.pack(side="right", padx=5)
        
        # Sub-assets tree list
        from virtual_list import VirtualList
        self.subassets_list = VirtualList(
            self.subassets_panel, 
            item_height=40, 
            command_click=self.on_subasset_click
        )
        self.subassets_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # --- Side Panel (Right) ---
        self.side_panel = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.side_panel.grid(row=1, column=2, sticky="nsew")
        
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
        self.file_list = VirtualList(self.side_panel, item_height=40, command_click=self.on_asset_click)
        self.file_list.pack(fill="both", expand=True, padx=5, pady=5)
        
        # Placeholder items
        self.file_list.set_data(["No files to show"])

        # Auto-load project if exists
        if self.current_project_path and os.path.exists(self.current_project_path):
            self.path_label.configure(text=f"{self.current_project_path}")
            # Use after to ensure UI is ready
            self.after(100, lambda: self.load_assets(self.current_project_path))

    def zoom_in(self, event=None):
        """Increase editor font size (zoom in)."""
        if self.editor_font_size < 40:  # Max font size limit
            self.editor_font_size += 2
            self.code_editor.configure(font=("Consolas", self.editor_font_size))
            self.save_settings()  # Persist zoom level
        return "break"  # Prevent default behavior

    def zoom_out(self, event=None):
        """Decrease editor font size (zoom out)."""
        if self.editor_font_size > 8:  # Min font size limit
            self.editor_font_size -= 2
            self.code_editor.configure(font=("Consolas", self.editor_font_size))
            self.save_settings()  # Persist zoom level
        return "break"  # Prevent default behavior

    def load_settings(self):
        try:
            if os.path.exists(self.CONFIG_FILE):
                with open(self.CONFIG_FILE, "r") as f:
                    settings = json.load(f)
                    self.current_project_path = settings.get("last_directory")
                    self.editor_font_size = settings.get("editor_font_size", 14)
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            settings = {
                "last_directory": self.current_project_path,
                "editor_font_size": self.editor_font_size
            }
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

    def on_asset_click(self, asset):
        """Handle click on an asset in the list."""
        if not hasattr(asset, 'name'):
            return  # Not a valid asset
        
        # Check if it's a compound asset (user-created)
        if getattr(asset, 'asset_type', '') == 'Compound':
            self.show_subassets_panel(asset)
        else:
            self.show_asset_code(asset)
    
    def show_subassets_panel(self, compound_asset, push_to_stack=True):
        """Show the sub-assets panel for a compound asset."""
        # Push current asset to stack for back navigation
        if push_to_stack and self.current_compound_asset is not None:
            self.navigation_stack.append(self.current_compound_asset)
        
        self.current_compound_asset = compound_asset
        
        # Update title with compound asset name
        self.subassets_title.configure(text=f"◆ {compound_asset.name}")
        
        # Show/hide back button based on stack
        if self.navigation_stack:
            self.back_subassets_btn.pack(side="left", padx=(5, 0))
        else:
            self.back_subassets_btn.pack_forget()
        
        # Show the panel
        self.subassets_panel.grid(row=1, column=1, sticky="nsew", padx=(2, 2))
        self.grid_columnconfigure(1, weight=0, minsize=250)
        
        # Build and populate the tree
        self.refresh_tree_view()
    
    def refresh_tree_view(self):
        """Rebuild the tree view based on current compound asset and expansion state."""
        if not self.current_compound_asset:
            return
        
        tree_nodes = self.build_tree_list(self.current_compound_asset, depth=0)
        if tree_nodes:
            self.subassets_list.set_data(tree_nodes)
        else:
            self.subassets_list.set_data(["No sub-assets found"])
    
    def build_tree_list(self, compound_asset, depth=0):
        """Build a flat list of TreeNodes representing the expanded tree."""
        nodes = []
        children = getattr(compound_asset, 'children', [])
        
        for child in children:
            is_compound = getattr(child, 'asset_type', '') == 'Compound'
            is_expanded = is_compound and id(child) in self.expanded_nodes
            node = TreeNode(child, depth, is_expanded)
            nodes.append(node)
            
            # If this child is compound AND expanded, add its children recursively
            if is_expanded:
                child_nodes = self.build_tree_list(child, depth + 1)
                nodes.extend(child_nodes)
        
        return nodes
    
    def toggle_node_expansion(self, asset):
        """Toggle expansion state of a compound asset node."""
        asset_id = id(asset)
        if asset_id in self.expanded_nodes:
            self.expanded_nodes.discard(asset_id)
        else:
            self.expanded_nodes.add(asset_id)
        self.refresh_tree_view()
    
    def hide_subassets_panel(self):
        """Hide the sub-assets panel and clear navigation."""
        self.current_compound_asset = None
        self.navigation_stack.clear()
        self.expanded_nodes.clear()
        self.back_subassets_btn.pack_forget()
        self.subassets_panel.grid_forget()
        self.grid_columnconfigure(1, weight=0, minsize=0)
    
    def navigate_back_subassets(self):
        """Navigate back to the previous compound asset."""
        if self.navigation_stack:
            previous_asset = self.navigation_stack.pop()
            self.show_subassets_panel(previous_asset, push_to_stack=False)
    
    def on_subasset_click(self, clicked_item):
        """Handle click on a sub-asset in the tree."""
        # Handle TreeNode wrapper
        if isinstance(clicked_item, TreeNode):
            asset = clicked_item.asset
        else:
            asset = clicked_item
        
        if not hasattr(asset, 'name'):
            return
        
        # Check if this sub-asset is also a compound asset
        if getattr(asset, 'asset_type', '') == 'Compound':
            # Toggle expansion in-place
            self.toggle_node_expansion(asset)
        else:
            self.show_asset_code(asset)
    
    def extract_asset_code(self, asset):
        """Extract only the code of a specific asset from its file."""
        if not hasattr(asset, 'file_path') or not asset.file_path:
            return None
        
        if not os.path.exists(asset.file_path):
            return None
        
        try:
            with open(asset.file_path, 'r', encoding='utf-8', errors='ignore') as f:
                lines = f.readlines()
            
            if not hasattr(asset, 'line_number') or asset.line_number <= 0:
                return ''.join(lines)
            
            start_line = asset.line_number - 1  # 0-indexed
            if start_line >= len(lines):
                return None
            
            # Get the starting indentation level
            first_line = lines[start_line]
            base_indent = len(first_line) - len(first_line.lstrip())
            
            # Find the end of this asset (when indentation returns to base level or less)
            end_line = start_line + 1
            for i in range(start_line + 1, len(lines)):
                line = lines[i]
                stripped = line.strip()
                
                # Skip empty lines and comments
                if not stripped or stripped.startswith('#'):
                    end_line = i + 1
                    continue
                
                current_indent = len(line) - len(line.lstrip())
                
                # If we return to base indentation or less, we've exited the block
                if current_indent <= base_indent and stripped:
                    break
                
                end_line = i + 1
            
            # Extract the code block
            return ''.join(lines[start_line:end_line])
            
        except Exception as e:
            return f"# Error extracting code: {e}"
    
    def show_asset_code(self, asset):
        """Display only the code of an asset in the main editor."""
        if not hasattr(asset, 'file_path') or not asset.file_path:
            return
        
        # Extract only the asset's code
        code = self.extract_asset_code(asset)
        
        if code is None:
            self.code_editor.delete("0.0", "end")
            self.code_editor.insert("0.0", f"# Could not load code for {asset.name}")
            return
        
        # Clear editor and insert content
        self.code_editor.delete("0.0", "end")
        self.code_editor.insert("0.0", code)
        
        # Highlight the first line (definition)
        self.code_editor.tag_remove("highlight", "0.0", "end")
        self.code_editor.tag_add("highlight", "1.0", "1.end")
        self.code_editor.tag_config("highlight", background="#3D5A80")
        
        # Apply syntax highlighting
        self.syntax_highlighter.highlight(code, asset.file_path)


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
                    "children": [{"name": a.name, "file_path": a.file_path, "line_number": a.line_number, "asset_type": a.asset_type} for a in selected_assets]
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
                    
                    # Reconstruct children as CodeAsset objects
                    children = []
                    for child_data in data.get("children", []):
                        child_type = child_data.get("asset_type", "Reference")
                        child_path = child_data.get("file_path", "")
                        
                        # Detect compound by .json extension (for legacy files without asset_type)
                        if child_path.endswith(".json") and os.path.exists(child_path):
                            child_type = "Compound"
                        
                        # Check if child is a compound asset - load its children
                        child_children = []
                        if child_type == "Compound" and child_path.endswith(".json") and os.path.exists(child_path):
                            try:
                                with open(child_path, "r", encoding="utf-8") as cf:
                                    child_json = json.load(cf)
                                # Recursively load nested children
                                for nested_data in child_json.get("children", []):
                                    nested = asset_extractor.CodeAsset(
                                        name=nested_data.get("name", "Unknown"),
                                        asset_type=nested_data.get("asset_type", "Reference"),
                                        file_path=nested_data.get("file_path", ""),
                                        line_number=nested_data.get("line_number", 0)
                                    )
                                    child_children.append(nested)
                            except:
                                pass
                        
                        child = asset_extractor.CodeAsset(
                            name=child_data.get("name", "Unknown"),
                            asset_type=child_type,
                            file_path=child_path,
                            line_number=child_data.get("line_number", 0),
                            children=child_children
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


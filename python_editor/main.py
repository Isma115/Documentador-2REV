import customtkinter as ctk
import tkinter as tk
from tkinter import filedialog
import os
import json
import asset_extractor
from syntax_highlighter import SyntaxHighlighter
from html_editor import HTMLDocEditor

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
        self.docs_folder_path = None  # Carpeta donde se guardan las documentaciones
        self.current_asset = None  # Activo actualmente seleccionado
        self.view_mode = "code"  # "code" o "docs" - modo de visualización actual
        
        # Load Settings (may override font_size)
        self.load_settings()

        # --- Top Bar (Menu/Actions) ---
        self.top_bar = ctk.CTkFrame(self, height=55, corner_radius=0)
        self.top_bar.grid(row=0, column=0, columnspan=3, sticky="ew")
        
        self.load_btn = ctk.CTkButton(
            self.top_bar, 
            text="Open Folder", 
            command=self.load_project,
            width=140,
            height=40,
            font=("Segoe UI", 14, "bold")
        )
        self.load_btn.pack(side="left", padx=10, pady=8)
        
        self.create_btn = ctk.CTkButton(
            self.top_bar,
            text="Create Compound",
            command=self.create_compound_asset_window,
            width=170,
            height=40,
            font=("Segoe UI", 14, "bold"),
            fg_color="#00695C", 
            hover_color="#004D40"
        )
        self.create_btn.pack(side="left", padx=5, pady=8)
        
        # AI Prompt Copy Button
        self.ai_prompt_btn = ctk.CTkButton(
            self.top_bar,
            text="📋 AI Prompt",
            command=self.copy_as_ai_prompt,
            width=140,
            height=40,
            font=("Segoe UI", 14, "bold"),
            fg_color="#6A1B9A",
            hover_color="#4A148C"
        )
        self.ai_prompt_btn.pack(side="left", padx=5, pady=8)
        
        # Docs Folder Button
        self.docs_folder_btn = ctk.CTkButton(
            self.top_bar,
            text="📁 Docs Folder",
            command=self.select_docs_folder,
            width=150,
            height=40,
            font=("Segoe UI", 14, "bold"),
            fg_color="#1565C0",
            hover_color="#0D47A1"
        )
        self.docs_folder_btn.pack(side="left", padx=5, pady=8)

        self.path_label = ctk.CTkLabel(
            self.top_bar, 
            text="No Project Opened",
            text_color="gray",
            font=("Segoe UI", 14)
        )
        self.path_label.pack(side="left", padx=10)

        # --- Main Editor Area (Left) ---
        self.editor_frame = ctk.CTkFrame(self, corner_radius=0)
        self.editor_frame.grid(row=1, column=0, sticky="nsew", padx=(0, 2), pady=0)
        
        # --- Tab Bar for Code/Docs toggle ---
        self.tab_bar = ctk.CTkFrame(self.editor_frame, height=50, fg_color="#1E1E1E")
        self.tab_bar.pack(fill="x", pady=(0, 2))
        
        self.code_tab_btn = ctk.CTkButton(
            self.tab_bar,
            text="💻 Código",
            command=lambda: self.switch_view_mode("code"),
            width=130,
            height=38,
            font=("Segoe UI", 14, "bold"),
            fg_color="#2D2D2D",
            hover_color="#3D3D3D",
            corner_radius=5
        )
        self.code_tab_btn.pack(side="left", padx=5, pady=6)
        
        self.docs_tab_btn = ctk.CTkButton(
            self.tab_bar,
            text="📝 Documentación",
            command=lambda: self.switch_view_mode("docs"),
            width=160,
            height=38,
            font=("Segoe UI", 14, "bold"),
            fg_color="#1E1E1E",
            hover_color="#3D3D3D",
            corner_radius=5
        )
        self.docs_tab_btn.pack(side="left", padx=2, pady=6)
        
        # Save docs button (only visible in docs mode)
        self.save_docs_btn = ctk.CTkButton(
            self.tab_bar,
            text="💾 Guardar",
            command=self.save_current_documentation,
            width=120,
            height=38,
            font=("Segoe UI", 14, "bold"),
            fg_color="#00695C",
            hover_color="#004D40",
            corner_radius=5
        )
        # Initially hidden
        
        # Asset name label
        self.asset_name_label = ctk.CTkLabel(
            self.tab_bar,
            text="",
            font=("Segoe UI", 14),
            text_color="#888888"
        )
        self.asset_name_label.pack(side="right", padx=10, pady=6)
        
        # --- Code Editor (Read-Only) ---
        self.code_editor = ctk.CTkTextbox(
            self.editor_frame,
            font=("Consolas", self.editor_font_size),
            corner_radius=0,
            activate_scrollbars=True,
            state="disabled"  # SOLO LECTURA
        )
        self.code_editor.pack(fill="both", expand=True)
        
        # --- Documentation Editor (Hidden by default) - Using HTML Editor ---
        self.docs_editor = HTMLDocEditor(self.editor_frame)
        # Initially hidden - will be shown when switching to docs mode
        
        # Set initial welcome message
        self.code_editor.configure(state="normal")
        self.code_editor.insert("0.0", "# Bienvenido al Visor de Código\n# Abre una carpeta para comenzar.\n# El código es solo lectura.")
        self.code_editor.configure(state="disabled")
        
        # Bind zoom shortcuts (Ctrl + Plus/Minus)
        self.code_editor.bind("<Control-plus>", self.zoom_in)
        self.code_editor.bind("<Control-minus>", self.zoom_out)
        self.code_editor.bind("<Control-equal>", self.zoom_in)
        self.code_editor.bind("<Control-KP_Add>", self.zoom_in)
        self.code_editor.bind("<Control-KP_Subtract>", self.zoom_out)

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
            font=("Segoe UI", 15, "bold"),
            text_color="#00E676"
        )
        self.subassets_title.pack(side="left", padx=8)
        
        # Back button (hidden by default)
        self.back_subassets_btn = ctk.CTkButton(
            self.subassets_header_frame,
            text="←",
            width=35,
            height=35,
            font=("Segoe UI", 16, "bold"),
            command=self.navigate_back_subassets,
            fg_color="#1565C0",
            hover_color="#0D47A1"
        )
        # Initially hidden
        
        self.close_subassets_btn = ctk.CTkButton(
            self.subassets_header_frame,
            text="✕",
            width=35,
            height=35,
            font=("Segoe UI", 16, "bold"),
            command=self.hide_subassets_panel,
            fg_color="#B71C1C",
            hover_color="#7F0000"
        )
        self.close_subassets_btn.pack(side="right", padx=8)
        
        # Sub-assets tree list
        from virtual_list import VirtualList
        self.subassets_list = VirtualList(
            self.subassets_panel, 
            item_height=50, 
            command_click=self.on_subasset_click
        )
        self.subassets_list.pack(fill="both", expand=True, padx=8, pady=8)
        
        # --- Side Panel (Right) ---
        self.side_panel = ctk.CTkFrame(self, width=250, corner_radius=0)
        self.side_panel.grid(row=1, column=2, sticky="nsew")
        
        # Header for the list
        self.list_header = ctk.CTkLabel(
            self.side_panel, 
            text="Code Assets", 
            font=("Segoe UI", 16, "bold")
        )
        self.list_header.pack(pady=(12, 8), padx=12, anchor="w")

        # Search Bar
        self.search_entry = ctk.CTkEntry(
            self.side_panel,
            placeholder_text="Search files...",
            height=40,
            font=("Segoe UI", 14)
        )
        self.search_entry.pack(fill="x", padx=12, pady=(0, 12))
        self.search_entry.bind("<KeyRelease>", self.filter_file_list)

        # Sort Options
        self.sort_var = ctk.StringVar(value="Name")
        self.sort_menu = ctk.CTkOptionMenu(
            self.side_panel,
            values=["Name", "Type"],
            command=self.on_sort_change,
            height=35,
            width=120,
            font=("Segoe UI", 13)
        )
        self.sort_menu.pack(pady=(0, 8), padx=12, anchor="e")

        # Virtual List for assets
        from virtual_list import VirtualList
        self.file_list = VirtualList(self.side_panel, item_height=50, command_click=self.on_asset_click)
        self.file_list.pack(fill="both", expand=True, padx=8, pady=8)
        
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
                    self.docs_folder_path = settings.get("docs_folder_path")
        except Exception as e:
            print(f"Error loading settings: {e}")

    def save_settings(self):
        try:
            settings = {
                "last_directory": self.current_project_path,
                "editor_font_size": self.editor_font_size,
                "docs_folder_path": self.docs_folder_path
            }
            with open(self.CONFIG_FILE, "w") as f:
                json.dump(settings, f)
        except Exception as e:
            print(f"Error saving settings: {e}")

    def select_docs_folder(self):
        """Permite al usuario seleccionar la carpeta de documentación."""
        folder_selected = filedialog.askdirectory(
            initialdir=self.docs_folder_path or self.current_project_path,
            title="Seleccionar Carpeta de Documentación"
        )
        if folder_selected:
            self.docs_folder_path = folder_selected
            self.save_settings()
            # Mostrar confirmación
            self.show_notification(f"Carpeta de docs: {os.path.basename(folder_selected)}")
    
    def show_notification(self, message, color="#1B5E20"):
        """Muestra una notificación temporal."""
        notif = ctk.CTkToplevel(self)
        notif.overrideredirect(True)
        
        self.update_idletasks()
        x = self.winfo_x() + (self.winfo_width() // 2) - 150
        y = self.winfo_y() + 60
        notif.geometry(f"300x40+{x}+{y}")
        
        frame = ctk.CTkFrame(notif, fg_color=color, corner_radius=8)
        frame.pack(fill="both", expand=True, padx=2, pady=2)
        
        ctk.CTkLabel(frame, text=message, text_color="white", font=("Arial", 11)).pack(expand=True)
        
        notif.after(2000, notif.destroy)
    
    def get_asset_doc_id(self, asset):
        """Genera un ID único para el archivo de documentación de un activo."""
        import hashlib
        # Crear un identificador basado en nombre, ruta y línea
        identifier = f"{asset.name}_{getattr(asset, 'file_path', '')}_{getattr(asset, 'line_number', 0)}"
        hash_short = hashlib.md5(identifier.encode()).hexdigest()[:8]
        # Limpiar nombre para usar en archivo
        safe_name = "".join(c if c.isalnum() or c in '-_' else '_' for c in asset.name)
        return f"{safe_name}_{hash_short}"
    
    def get_asset_doc_path(self, asset):
        """Obtiene la ruta completa del archivo de documentación para un activo."""
        if not self.docs_folder_path:
            return None
        doc_id = self.get_asset_doc_id(asset)
        return os.path.join(self.docs_folder_path, f"{doc_id}.md")
    
    def load_asset_documentation(self, asset):
        """Carga la documentación de un activo desde el archivo."""
        doc_path = self.get_asset_doc_path(asset)
        if not doc_path or not os.path.exists(doc_path):
            return ""
        try:
            with open(doc_path, 'r', encoding='utf-8') as f:
                return f.read()
        except Exception as e:
            print(f"Error loading documentation: {e}")
            return ""
    
    def save_asset_documentation(self, asset, content):
        """Guarda la documentación de un activo en el archivo."""
        if not self.docs_folder_path:
            self.show_notification("Primero selecciona una carpeta de documentación", "#B71C1C")
            return False
        
        # Crear carpeta si no existe
        try:
            os.makedirs(self.docs_folder_path, exist_ok=True)
        except Exception as e:
            print(f"Error creating docs folder: {e}")
            self.show_notification(f"Error creando carpeta: {e}", "#B71C1C")
            return False
        
        doc_path = self.get_asset_doc_path(asset)
        if not doc_path:
            self.show_notification("No se pudo generar ruta de documentación", "#B71C1C")
            return False
            
        try:
            with open(doc_path, 'w', encoding='utf-8') as f:
                f.write(content)
            return True
        except Exception as e:
            print(f"Error saving documentation to {doc_path}: {e}")
            self.show_notification(f"Error: {str(e)[:30]}", "#B71C1C")
            return False
    
    def save_current_documentation(self):
        """Guarda la documentación del activo actualmente seleccionado."""
        if not self.current_asset:
            self.show_notification("No hay activo seleccionado", "#B71C1C")
            return
        
        # Obtener HTML del editor
        content = self.docs_editor.get_html()
        if self.save_asset_documentation(self.current_asset, content):
            self.show_notification("✓ Documentación guardada")
        else:
            self.show_notification("Error al guardar", "#B71C1C")
    
    def refresh_documentation_view(self):
        """Actualiza la vista de documentación con el activo actual."""
        if not self.current_asset:
            self.docs_editor.set_content("Sin activo seleccionado\n\nSelecciona un activo de código para ver/editar su documentación.")
            return
        
        doc_content = self.load_asset_documentation(self.current_asset)
        if doc_content:
            # Si es HTML, cargarlo con load_html
            if doc_content.strip().startswith("<!DOCTYPE") or doc_content.strip().startswith("<html"):
                self.docs_editor.load_html(doc_content)
            else:
                self.docs_editor.set_content(doc_content)
        else:
            # Plantilla inicial
            template = f"{self.current_asset.name}\n\nDescripción\n\nEscribe aquí la documentación de este activo.\n\nNotas\n\n"
            self.docs_editor.set_content(template)
    
    def switch_view_mode(self, mode):
        """Cambia entre modo código y modo documentación."""
        if mode == self.view_mode:
            return
        
        self.view_mode = mode
        
        if mode == "code":
            # Mostrar código, ocultar documentación
            self.docs_editor.pack_forget()
            self.code_editor.pack(fill="both", expand=True)
            self.save_docs_btn.pack_forget()
            # Actualizar estilos de pestañas
            self.code_tab_btn.configure(fg_color="#2D2D2D")
            self.docs_tab_btn.configure(fg_color="#1E1E1E")
        else:
            # Mostrar documentación, ocultar código
            self.code_editor.pack_forget()
            self.docs_editor.pack(fill="both", expand=True)
            self.save_docs_btn.pack(side="left", padx=10, pady=3)
            # Actualizar estilos de pestañas
            self.code_tab_btn.configure(fg_color="#1E1E1E")
            self.docs_tab_btn.configure(fg_color="#2D2D2D")
            
            # Cargar documentación del activo actual
            self.refresh_documentation_view()

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
        
        # Siempre actualizar el activo actual (para documentación)
        self.current_asset = asset
        self.asset_name_label.configure(text=f"📄 {asset.name}")
        
        # Check if it's a compound asset (user-created)
        if getattr(asset, 'asset_type', '') == 'Compound':
            self.show_subassets_panel(asset)
            # Si estamos en modo docs, actualizar la documentación
            if self.view_mode == "docs":
                self.refresh_documentation_view()
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
        """Display only the code of an asset in the main editor (read-only)."""
        if not hasattr(asset, 'file_path') or not asset.file_path:
            return
        
        # Actualizar el activo actual
        self.current_asset = asset
        self.asset_name_label.configure(text=f"📄 {asset.name}")
        
        # Extract only the asset's code (siempre lo extraemos para tenerlo listo)
        code = self.extract_asset_code(asset)
        
        # Actualizar el editor de código (aunque esté oculto)
        self.code_editor.configure(state="normal")
        self.code_editor.delete("0.0", "end")
        if code is None:
            self.code_editor.insert("0.0", f"# Could not load code for {asset.name}")
        else:
            self.code_editor.insert("0.0", code)
            # Highlight the first line (definition)
            self.code_editor.tag_remove("highlight", "0.0", "end")
            self.code_editor.tag_add("highlight", "1.0", "1.end")
            self.code_editor.tag_config("highlight", background="#3D5A80")
            # Apply syntax highlighting
            self.syntax_highlighter.highlight(code, asset.file_path)
        self.code_editor.configure(state="disabled")
        
        # Si estamos en modo documentación, actualizar también la documentación
        if self.view_mode == "docs":
            self.refresh_documentation_view()

    def get_current_asset_extension(self):
        """Obtiene la extensión del archivo del activo actualmente mostrado."""
        # Intentar detectar la extensión desde el código mostrado o usar 'python' por defecto
        code = self.code_editor.get("0.0", "end-1c")
        if not code.strip():
            return "python"
        
        # Detectar por indicadores comunes en el código
        if "def " in code or "class " in code or "import " in code:
            return "python"
        elif "function " in code or "const " in code or "let " in code or "var " in code:
            return "javascript"
        elif "public class" in code or "private " in code or "void " in code:
            return "java"
        elif "#include" in code or "int main" in code:
            return "cpp"
        elif "<html" in code.lower() or "<!doctype" in code.lower():
            return "html"
        elif "{" in code and "}" in code and ":" in code and ";" not in code:
            return "json"
        
        return "python"  # Default
    
    def get_full_asset_code(self):
        """Obtiene el código completo del editor (activo actualmente visible)."""
        return self.code_editor.get("0.0", "end-1c")
    
    def extract_all_compound_code(self, compound_asset, depth=0):
        """Extrae recursivamente todo el código de un activo compuesto y sus hijos."""
        code_blocks = []
        indent = "  " * depth
        
        # Añadir encabezado del activo compuesto
        asset_name = compound_asset.name if hasattr(compound_asset, 'name') else str(compound_asset)
        code_blocks.append(f"\n{'#' * (depth + 2)} {asset_name}")
        
        # Añadir documentación si existe
        doc = getattr(compound_asset, 'documentation', '')
        if doc:
            code_blocks.append(f"\n> Documentación: {doc}")
        
        children = getattr(compound_asset, 'children', [])
        
        for child in children:
            child_name = child.name if hasattr(child, 'name') else str(child)
            child_type = getattr(child, 'asset_type', 'Unknown')
            
            if child_type == 'Compound':
                # Recursivamente extraer código de sub-compuestos
                child_code = self.extract_all_compound_code(child, depth + 1)
                code_blocks.append(child_code)
            else:
                # Extraer código del activo simple
                asset_code = self.extract_asset_code(child)
                
                if asset_code:
                    # Detectar extensión del archivo
                    file_path = getattr(child, 'file_path', '')
                    ext = os.path.splitext(file_path)[1].lstrip('.') if file_path else 'python'
                    if not ext:
                        ext = 'python'
                    
                    code_blocks.append(f"\n### {child_name} ({child_type})")
                    code_blocks.append(f"```{ext}\n{asset_code}\n```")
                else:
                    code_blocks.append(f"\n### {child_name} ({child_type})")
                    code_blocks.append(f"_[No se pudo extraer el código de este activo]_")
        
        return "\n".join(code_blocks)
    
    def get_compound_asset_code(self):
        """Obtiene todo el código del activo compuesto actualmente seleccionado."""
        if not self.current_compound_asset:
            return None
        
        return self.extract_all_compound_code(self.current_compound_asset)
    
    def copy_as_ai_prompt(self):
        """Muestra popup para describir la mejora y copia el código como prompt de IA."""
        # Verificar si hay un activo compuesto activo (con el panel de sub-activos visible)
        is_compound_mode = self.current_compound_asset is not None
        
        if is_compound_mode:
            # Extraer código de todo el árbol de activos
            code = self.get_compound_asset_code()
            compound_name = self.current_compound_asset.name if hasattr(self.current_compound_asset, 'name') else "Activo Compuesto"
        else:
            # Usar el código del editor actual
            code = self.get_full_asset_code()
            compound_name = None
        
        if not code or not code.strip():
            # Mostrar mensaje de error si no hay código
            error_window = ctk.CTkToplevel(self)
            error_window.title("Error")
            error_window.geometry("350x120")
            error_window.grab_set()
            
            # Centrar ventana
            self.update_idletasks()
            x = self.winfo_x() + (self.winfo_width() // 2) - 175
            y = self.winfo_y() + (self.winfo_height() // 2) - 60
            error_window.geometry(f"350x120+{x}+{y}")
            
            error_msg = "No hay activo compuesto seleccionado.\nPrimero selecciona un activo compuesto de la lista." if is_compound_mode else "No hay código en el editor."
            
            ctk.CTkLabel(
                error_window, 
                text=error_msg,
                font=("Arial", 12)
            ).pack(pady=20)
            
            ctk.CTkButton(
                error_window,
                text="Aceptar",
                command=error_window.destroy,
                width=80
            ).pack()
            return
        
        # Crear popup para descripción
        popup = ctk.CTkToplevel(self)
        popup.title("Generar Prompt de IA")
        
        # Geometría y centrado
        width = 500
        height = 400
        
        self.update_idletasks()
        main_x = self.winfo_x()
        main_y = self.winfo_y()
        main_width = self.winfo_width()
        main_height = self.winfo_height()
        
        x = main_x + (main_width // 2) - (width // 2)
        y = main_y + (main_height // 2) - (height // 2)
        
        popup.geometry(f"{width}x{height}+{x}+{y}")
        popup.grab_set()
        popup.focus_set()
        
        # Indicador del modo
        if is_compound_mode:
            mode_label = ctk.CTkLabel(
                popup,
                text=f"📦 Activo Compuesto: {compound_name}",
                font=("Arial", 11),
                text_color="#00E676"
            )
            mode_label.pack(pady=(10, 0), padx=20, anchor="w")
        
        # Título descriptivo
        ctk.CTkLabel(
            popup,
            text="Describe la mejora o corrección que necesitas:",
            font=("Arial", 13, "bold")
        ).pack(pady=(10, 10), padx=20, anchor="w")
        
        # Campo de texto para descripción
        description_textbox = ctk.CTkTextbox(popup, height=150)
        description_textbox.pack(fill="x", padx=20, pady=(0, 10))
        description_textbox.focus_set()
        
        # Info text
        info_msg = "El prompt se copiará con TODO el código del activo compuesto\ny sus sub-activos. La IA devolverá solo los fragmentos modificados." if is_compound_mode else "El prompt se copiará al portapapeles con el código completo\ny la instrucción de devolver solo los fragmentos modificados."
        
        ctk.CTkLabel(
            popup,
            text=info_msg,
            font=("Arial", 10),
            text_color="gray"
        ).pack(pady=(0, 15))
        
        # Frame para botones
        btn_frame = ctk.CTkFrame(popup, fg_color="transparent")
        btn_frame.pack(pady=10)
        
        def accept():
            description = description_textbox.get("0.0", "end-1c").strip()
            if not description:
                # Resaltar el campo si está vacío
                description_textbox.configure(border_color="#B71C1C")
                return
            
            # Formatear el prompt según el modo
            if is_compound_mode:
                prompt = f"""Necesito que analices y modifiques el siguiente conjunto de código según las instrucciones proporcionadas.

## Activo Compuesto: {compound_name}

El siguiente contenido incluye múltiples archivos/funciones/clases que forman parte de este activo:

{code}

## Descripción de la mejora/corrección solicitada:
{description}

## Instrucciones importantes:
- Devuelve ÚNICAMENTE los fragmentos de código que han sido modificados
- Para cada fragmento modificado, indica claramente:
  1. El nombre del activo/archivo afectado
  2. La ubicación (número de línea o nombre de función/clase afectada)
  3. El código original (antes)
  4. El código modificado (después)
- NO devuelvas el código completo, solo las partes que cambian
- Si hay múltiples modificaciones en diferentes archivos, sepáralas claramente por archivo"""
            else:
                extension = self.get_current_asset_extension()
                prompt = f"""Necesito que analices y modifiques el siguiente código según las instrucciones proporcionadas.

## Código actual:
```{extension}
{code}
```

## Descripción de la mejora/corrección solicitada:
{description}

## Instrucciones importantes:
- Devuelve ÚNICAMENTE los fragmentos de código que han sido modificados
- Para cada fragmento modificado, indica claramente:
  1. La ubicación (número de línea o nombre de función/clase afectada)
  2. El código original (antes)
  3. El código modificado (después)
- NO devuelvas el código completo, solo las partes que cambian
- Si hay múltiples modificaciones, sepáralas claramente"""
            
            # Copiar al portapapeles
            self.clipboard_clear()
            self.clipboard_append(prompt)
            self.update()  # Necesario para que el portapapeles persista
            
            popup.destroy()
            
            # Mostrar confirmación breve
            confirm = ctk.CTkToplevel(self)
            confirm.title("")
            confirm.geometry("250x80")
            confirm.overrideredirect(True)  # Sin barra de título
            
            # Centrar
            cx = main_x + (main_width // 2) - 125
            cy = main_y + (main_height // 2) - 40
            confirm.geometry(f"250x80+{cx}+{cy}")
            
            confirm_frame = ctk.CTkFrame(confirm, fg_color="#1B5E20", corner_radius=10)
            confirm_frame.pack(fill="both", expand=True, padx=2, pady=2)
            
            ctk.CTkLabel(
                confirm_frame,
                text="✓ Prompt copiado al portapapeles",
                font=("Arial", 12, "bold"),
                text_color="white"
            ).pack(expand=True)
            
            # Auto-cerrar después de 1.5 segundos
            confirm.after(1500, confirm.destroy)
        
        def cancel():
            popup.destroy()
        
        ctk.CTkButton(
            btn_frame,
            text="Aceptar",
            command=accept,
            width=100,
            fg_color="#00695C",
            hover_color="#004D40"
        ).pack(side="left", padx=10)
        
        ctk.CTkButton(
            btn_frame,
            text="Cancelar",
            command=cancel,
            width=100,
            fg_color="#757575",
            hover_color="#616161"
        ).pack(side="left", padx=10)

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
        
        ctk.CTkLabel(name_frame, text="Asset Name:", font=("Segoe UI", 15, "bold")).pack(side="left")
        name_entry = ctk.CTkEntry(name_frame, width=350, height=40, font=("Segoe UI", 14))
        name_entry.pack(side="left", padx=15)
        
        # --- Lists Container ---
        lists_frame = ctk.CTkFrame(window, fg_color="transparent")
        lists_frame.pack(fill="both", expand=True, padx=20, pady=10)
        lists_frame.grid_columnconfigure(0, weight=1)
        lists_frame.grid_columnconfigure(1, weight=0)
        lists_frame.grid_columnconfigure(2, weight=1)
        lists_frame.grid_rowconfigure(1, weight=1)
        
        # --- Left Panel: Available Assets ---
        ctk.CTkLabel(lists_frame, text="Available Assets", font=("Segoe UI", 14, "bold")).grid(row=0, column=0, sticky="w", pady=(0, 8))
        
        left_search = ctk.CTkEntry(lists_frame, placeholder_text="Search...", height=38, font=("Segoe UI", 13))
        left_search.grid(row=0, column=0, sticky="e", pady=(0, 8))

        from virtual_list import VirtualList
        available_list = VirtualList(lists_frame, item_height=50, command_double_click=lambda item: add_selected(item))
        available_list.grid(row=1, column=0, sticky="nsew", padx=(0, 8))
        
        # --- Center Buttons ---
        btn_frame = ctk.CTkFrame(lists_frame, fg_color="transparent", width=60)
        btn_frame.grid(row=1, column=1, padx=10)
        
        # --- Right Panel: Selected Assets ---
        ctk.CTkLabel(lists_frame, text="Selected Assets", font=("Segoe UI", 14, "bold")).grid(row=0, column=2, sticky="w", pady=(0, 8))
        
        selected_list = VirtualList(lists_frame, item_height=50, command_double_click=lambda item: remove_selected(item))
        selected_list.grid(row=1, column=2, sticky="nsew", padx=(8, 0))
        
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
        
        add_btn = ctk.CTkButton(btn_frame, text="→", width=50, height=45, font=("Segoe UI", 18, "bold"), command=add_selected, fg_color="#00695C", hover_color="#004D40")
        add_btn.pack(pady=8)
        
        remove_btn = ctk.CTkButton(btn_frame, text="←", width=50, height=45, font=("Segoe UI", 18, "bold"), command=remove_selected, fg_color="#B71C1C", hover_color="#7F0000")
        remove_btn.pack(pady=8)
        
        left_search.bind("<KeyRelease>", lambda e: refresh_available())
        
        # Initial population
        refresh_available()
        refresh_selected()
        
        # --- Documentation ---
        doc_label = ctk.CTkLabel(window, text="Documentation:", font=("Segoe UI", 15, "bold"))
        doc_label.pack(anchor="w", padx=20, pady=(10, 8))
        
        doc_textbox = ctk.CTkTextbox(window, height=140, font=("Segoe UI", 14))
        doc_textbox.pack(fill="x", padx=20, pady=(0, 15))
        
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
            height=45,
            font=("Segoe UI", 15, "bold")
        ).pack(pady=18)


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


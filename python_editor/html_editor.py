"""
Editor de Documentación HTML WYSIWYG
Editor estilo Word con barra de herramientas y vista previa en tiempo real.
"""
import customtkinter as ctk
import tkinter as tk
from tkinter import colorchooser, simpledialog
import re


class HTMLDocEditor(ctk.CTkFrame):
    """Editor de documentación HTML con formato visual en tiempo real."""
    
    def __init__(self, parent, **kwargs):
        super().__init__(parent, **kwargs)
        
        self.configure(fg_color="transparent")
        
        # Variables de estado
        self.current_font_size = 12
        
        # Crear la interfaz
        self._create_toolbar()
        self._create_editor()
        self._setup_tags()
        self._bind_shortcuts()
    
    def _create_toolbar(self):
        """Crea la barra de herramientas de formato."""
        self.toolbar = ctk.CTkFrame(self, height=40, fg_color="#2D2D2D", corner_radius=5)
        self.toolbar.pack(fill="x", padx=2, pady=(2, 5))
        
        # --- Grupo: Formato de texto ---
        format_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        format_frame.pack(side="left", padx=5, pady=3)
        
        self.bold_btn = ctk.CTkButton(
            format_frame, text="B", width=30, height=28,
            font=("Arial", 12, "bold"),
            command=lambda: self.toggle_format("bold"),
            fg_color="#3D3D3D", hover_color="#4D4D4D"
        )
        self.bold_btn.pack(side="left", padx=1)
        
        self.italic_btn = ctk.CTkButton(
            format_frame, text="I", width=30, height=28,
            font=("Arial", 12, "italic"),
            command=lambda: self.toggle_format("italic"),
            fg_color="#3D3D3D", hover_color="#4D4D4D"
        )
        self.italic_btn.pack(side="left", padx=1)
        
        self.underline_btn = ctk.CTkButton(
            format_frame, text="U", width=30, height=28,
            font=("Arial", 12, "underline"),
            command=lambda: self.toggle_format("underline"),
            fg_color="#3D3D3D", hover_color="#4D4D4D"
        )
        self.underline_btn.pack(side="left", padx=1)
        
        self.strike_btn = ctk.CTkButton(
            format_frame, text="S̶", width=30, height=28,
            command=lambda: self.toggle_format("strikethrough"),
            fg_color="#3D3D3D", hover_color="#4D4D4D"
        )
        self.strike_btn.pack(side="left", padx=1)
        
        # Separador visual
        sep1 = ctk.CTkFrame(self.toolbar, width=2, height=24, fg_color="#555555")
        sep1.pack(side="left", padx=8, pady=5)
        
        # --- Grupo: Encabezados ---
        heading_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        heading_frame.pack(side="left", padx=5, pady=3)
        
        self.h1_btn = ctk.CTkButton(
            heading_frame, text="H1", width=35, height=28,
            font=("Arial", 11, "bold"),
            command=lambda: self.apply_heading("h1"),
            fg_color="#3D3D3D", hover_color="#4D4D4D"
        )
        self.h1_btn.pack(side="left", padx=1)
        
        self.h2_btn = ctk.CTkButton(
            heading_frame, text="H2", width=35, height=28,
            font=("Arial", 10, "bold"),
            command=lambda: self.apply_heading("h2"),
            fg_color="#3D3D3D", hover_color="#4D4D4D"
        )
        self.h2_btn.pack(side="left", padx=1)
        
        self.h3_btn = ctk.CTkButton(
            heading_frame, text="H3", width=35, height=28,
            font=("Arial", 9, "bold"),
            command=lambda: self.apply_heading("h3"),
            fg_color="#3D3D3D", hover_color="#4D4D4D"
        )
        self.h3_btn.pack(side="left", padx=1)
        
        # Separador visual
        sep2 = ctk.CTkFrame(self.toolbar, width=2, height=24, fg_color="#555555")
        sep2.pack(side="left", padx=8, pady=5)
        
        # --- Grupo: Listas ---
        list_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        list_frame.pack(side="left", padx=5, pady=3)
        
        self.ul_btn = ctk.CTkButton(
            list_frame, text="•", width=30, height=28,
            font=("Arial", 14),
            command=lambda: self.insert_list_item("ul"),
            fg_color="#3D3D3D", hover_color="#4D4D4D"
        )
        self.ul_btn.pack(side="left", padx=1)
        
        self.ol_btn = ctk.CTkButton(
            list_frame, text="1.", width=30, height=28,
            font=("Arial", 11),
            command=lambda: self.insert_list_item("ol"),
            fg_color="#3D3D3D", hover_color="#4D4D4D"
        )
        self.ol_btn.pack(side="left", padx=1)
        
        # Separador visual
        sep3 = ctk.CTkFrame(self.toolbar, width=2, height=24, fg_color="#555555")
        sep3.pack(side="left", padx=8, pady=5)
        
        # --- Grupo: Insertar ---
        insert_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        insert_frame.pack(side="left", padx=5, pady=3)
        
        self.link_btn = ctk.CTkButton(
            insert_frame, text="🔗", width=30, height=28,
            command=self.insert_link,
            fg_color="#3D3D3D", hover_color="#4D4D4D"
        )
        self.link_btn.pack(side="left", padx=1)
        
        self.code_btn = ctk.CTkButton(
            insert_frame, text="</>", width=35, height=28,
            font=("Consolas", 10),
            command=lambda: self.toggle_format("code"),
            fg_color="#3D3D3D", hover_color="#4D4D4D"
        )
        self.code_btn.pack(side="left", padx=1)
        
        # Separador visual
        sep4 = ctk.CTkFrame(self.toolbar, width=2, height=24, fg_color="#555555")
        sep4.pack(side="left", padx=8, pady=5)
        
        # --- Grupo: Colores ---
        color_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        color_frame.pack(side="left", padx=5, pady=3)
        
        self.text_color_btn = ctk.CTkButton(
            color_frame, text="A", width=30, height=28,
            font=("Arial", 12, "bold"),
            text_color="#FF5555",
            command=self.choose_text_color,
            fg_color="#3D3D3D", hover_color="#4D4D4D"
        )
        self.text_color_btn.pack(side="left", padx=1)
        
        self.bg_color_btn = ctk.CTkButton(
            color_frame, text="🎨", width=30, height=28,
            command=self.choose_bg_color,
            fg_color="#3D3D3D", hover_color="#4D4D4D"
        )
        self.bg_color_btn.pack(side="left", padx=1)

        # Separador visual
        sep5 = ctk.CTkFrame(self.toolbar, width=2, height=24, fg_color="#555555")
        sep5.pack(side="left", padx=8, pady=5)

        # --- Grupo: Tamaño de fuente ---
        font_size_frame = ctk.CTkFrame(self.toolbar, fg_color="transparent")
        font_size_frame.pack(side="left", padx=5, pady=3)

        self.decrease_font_btn = ctk.CTkButton(
            font_size_frame, text="A-", width=30, height=28,
            font=("Arial", 10, "bold"),
            command=lambda: self.change_font_size(-1),
            fg_color="#3D3D3D", hover_color="#4D4D4D"
        )
        self.decrease_font_btn.pack(side="left", padx=1)

        self.increase_font_btn = ctk.CTkButton(
            font_size_frame, text="A+", width=30, height=28,
            font=("Arial", 14, "bold"),
            command=lambda: self.change_font_size(1),
            fg_color="#3D3D3D", hover_color="#4D4D4D"
        )
        self.increase_font_btn.pack(side="left", padx=1)
        
        # --- Grupo: Limpiar formato ---
        self.clear_btn = ctk.CTkButton(
            self.toolbar, text="✕", width=30, height=28,
            command=self.clear_format,
            fg_color="#5D3D3D", hover_color="#7D4D4D"
        )
        self.clear_btn.pack(side="right", padx=5, pady=3)
    
    def _create_editor(self):
        """Crea el área de edición principal."""
        # Frame contenedor del editor
        editor_container = ctk.CTkFrame(self, fg_color="#1E1E1E", corner_radius=5)
        editor_container.pack(fill="both", expand=True, padx=2, pady=2)
        
        # Usamos tk.Text directamente para mejor control de tags
        self.editor = tk.Text(
            editor_container,
            wrap="word",
            font=("Segoe UI", 12),
            bg="#1E1E1E",
            fg="#FFFFFF",
            insertbackground="#FFFFFF",
            selectbackground="#3D5A80",
            selectforeground="#FFFFFF",
            padx=15,
            pady=15,
            relief="flat",
            undo=True
        )
        
        # Scrollbar
        scrollbar = ctk.CTkScrollbar(editor_container, command=self.editor.yview)
        scrollbar.pack(side="right", fill="y", padx=(0, 2), pady=2)
        
        self.editor.configure(yscrollcommand=scrollbar.set)
        self.editor.pack(fill="both", expand=True, padx=2, pady=2)
    
    def _setup_tags(self):
        """Configura los tags de formato para el editor."""
        # Formato de texto básico
        self.editor.tag_configure("bold", font=("Segoe UI", 12, "bold"))
        self.editor.tag_configure("italic", font=("Segoe UI", 12, "italic"))
        self.editor.tag_configure("underline", underline=True)
        self.editor.tag_configure("strikethrough", overstrike=True)
        
        # Encabezados
        self.editor.tag_configure("h1", font=("Segoe UI", 24, "bold"), foreground="#00E676")
        self.editor.tag_configure("h2", font=("Segoe UI", 20, "bold"), foreground="#4FC3F7")
        self.editor.tag_configure("h3", font=("Segoe UI", 16, "bold"), foreground="#FFB74D")
        
        # Código
        self.editor.tag_configure("code", font=("Consolas", 11), background="#2D2D2D", foreground="#CE9178")
        
        # Listas
        self.editor.tag_configure("list_item", lmargin1=20, lmargin2=35)
        
        # Link
        self.editor.tag_configure("link", foreground="#64B5F6", underline=True)
        
        # Combinaciones de formato
        self.editor.tag_configure("bold_italic", font=("Segoe UI", 12, "bold italic"))
    
    def _bind_shortcuts(self):
        """Configura los atajos de teclado."""
        self.editor.bind("<Control-b>", lambda e: self.toggle_format("bold"))
        self.editor.bind("<Control-i>", lambda e: self.toggle_format("italic"))
        self.editor.bind("<Control-u>", lambda e: self.toggle_format("underline"))
        self.editor.bind("<Control-Key-1>", lambda e: self.apply_heading("h1"))
        self.editor.bind("<Control-Key-2>", lambda e: self.apply_heading("h2"))
        self.editor.bind("<Control-Key-3>", lambda e: self.apply_heading("h3"))
    
    def _get_clean_selection(self):
        """Obtiene índices de selección ajustados para evitar bugs visuales."""
        try:
            sel_start = self.editor.index("sel.first")
            sel_end = self.editor.index("sel.last")
            
            # Si el final de la selección es el salto de línea, retroceder un caracter
            # Para evitar que el estilos de fondo/tamaño se extiendan a toda la linea visual
            if self.editor.get(f"{sel_end}-1c") == "\n":
                return sel_start, f"{sel_end}-1c"
                
            return sel_start, sel_end
        except tk.TclError:
            return None, None

    def toggle_format(self, format_type):
        """Aplica o quita formato al texto seleccionado."""
        sel_start, sel_end = self._get_clean_selection()
        if not sel_start: return "break"
        
        # Verificar si ya tiene el tag en el rango
        # Comprobar el primer caracter
        current_tags = self.editor.tag_names(sel_start)
        
        if format_type in current_tags:
            # Quitar formato
            self.editor.tag_remove(format_type, sel_start, sel_end)
        else:
            # Aplicar formato
            self.editor.tag_add(format_type, sel_start, sel_end)
        return "break"
    
    def apply_heading(self, heading_type):
        """Aplica estilo de encabezado a la línea actual."""
        try:
            # Los encabezados son elementos de bloque, se aplican a toda la línea
            current_line = self.editor.index("insert linestart")
            line_end = self.editor.index("insert lineend")
            
            # 1. Limpiar tags existentes en la linea que puedan conflictuar
            # Eliminamos tags de tamaño y formato básico para que mande el estilo del Header
            for tag in self.editor.tag_names(current_line):
                if tag in ["bold", "italic", "underline", "strikethrough"] or \
                   tag.startswith("size_") or \
                   tag.startswith("color_") or \
                   tag.startswith("bg_") or \
                   tag in ["h1", "h2", "h3"]:
                    self.editor.tag_remove(tag, current_line, line_end)
            
            # 2. Aplicar el nuevo encabezado
            self.editor.tag_add(heading_type, current_line, line_end)
            
            # 3. Asegurar que el tag tiene prioridad visual
            # Como los tags de tamaño se crean dinámicamente, podrían tapar al Header
            # así que elevamos el header para asegurar que se vea
            self.editor.tag_raise(heading_type)
            
        except tk.TclError:
            pass
        return "break"
    
    def insert_list_item(self, list_type):
        """Inserta un elemento de lista."""
        marker = "• " if list_type == "ul" else "1. "
        
        # Insertar al inicio de la línea o en la posición actual
        current_pos = self.editor.index("insert")
        line_start = self.editor.index("insert linestart")
        
        # Comprobar si ya es lista para no duplicar
        line_text = self.editor.get(line_start, f"{line_start} lineend")
        if line_text.strip().startswith(("•", "1.")):
            return # Ya es lista
            
        # Si estamos al inicio de la línea, insertar marcador
        if current_pos == line_start:
            self.editor.insert("insert", marker)
        else:
            # Nueva línea con marcador
            self.editor.insert("insert", f"\n{marker}")
        
        # Aplicar formato de lista
        new_line_start = self.editor.index("insert linestart")
        new_line_end = self.editor.index("insert lineend")
        self.editor.tag_add("list_item", new_line_start, new_line_end)
    
    def insert_link(self):
        """Inserta un enlace."""
        sel_start, sel_end = self._get_clean_selection()
        
        if sel_start:
            selected_text = self.editor.get(sel_start, sel_end)
        else:
            selected_text = ""
            sel_start = self.editor.index("insert")
            sel_end = sel_start
        
        # Pedir URL
        url = simpledialog.askstring("Insertar Enlace", "URL:", parent=self.winfo_toplevel())
        if url:
            if selected_text:
                # Aplicar formato de link al texto seleccionado
                self.editor.tag_add("link", sel_start, sel_end)
                self.editor.tag_bind("link", "<Button-1>", lambda e: self._open_link(url))
            else:
                # Insertar la URL como texto
                self.editor.insert("insert", url)
                end_pos = self.editor.index("insert")
                start_pos = f"{end_pos} - {len(url)} chars"
                self.editor.tag_add("link", start_pos, end_pos)
    
    def _open_link(self, url):
        """Abre un enlace en el navegador."""
        import webbrowser
        webbrowser.open(url)
    
    def choose_text_color(self):
        """Abre el selector de color para el texto."""
        color = colorchooser.askcolor(title="Color de Texto", parent=self.winfo_toplevel())
        if color[1]:
            sel_start, sel_end = self._get_clean_selection()
            if not sel_start: return

            # Crear un tag único para este color
            tag_name = f"color_{color[1].replace('#', '')}"
            self.editor.tag_configure(tag_name, foreground=color[1])
            
            # Limpiar colores anteriores en la selección
            for tag in self.editor.tag_names():
                if tag.startswith("color_"):
                    self.editor.tag_remove(tag, sel_start, sel_end)
            
            self.editor.tag_add(tag_name, sel_start, sel_end)
    
    def choose_bg_color(self):
        """Abre el selector de color para el fondo."""
        color = colorchooser.askcolor(title="Color de Fondo", parent=self.winfo_toplevel())
        if color[1]:
            sel_start, sel_end = self._get_clean_selection()
            if not sel_start: return
                
            # Crear un tag único para este color
            tag_name = f"bg_{color[1].replace('#', '')}"
            self.editor.tag_configure(tag_name, background=color[1])
            
            # Limpiar fondos anteriores
            for tag in self.editor.tag_names():
                if tag.startswith("bg_"):
                    self.editor.tag_remove(tag, sel_start, sel_end)
            
            self.editor.tag_add(tag_name, sel_start, sel_end)
    
    def change_font_size(self, delta):
        """Cambia el tamaño de fuente del texto seleccionado."""
        sel_start, sel_end = self._get_clean_selection()
        if not sel_start: return
        
        # Definir tamaños soportados
        sizes = [10, 12, 14, 16, 18, 20, 24, 28, 32]
        
        # Encontrar tamaño actual predominante
        current_tags = self.editor.tag_names(sel_start)
        current_size = 12 # Default
        
        for tag in current_tags:
            if tag.startswith("size_"):
                try:
                    current_size = int(tag.split("_")[1])
                    break
                except ValueError:
                    pass
        
        # Calcular nuevo indice
        try:
            idx = sizes.index(current_size)
        except ValueError:
            idx = 1 # 12 by default
        
        new_idx = idx + delta
        if new_idx < 0: new_idx = 0
        if new_idx >= len(sizes): new_idx = len(sizes) - 1
            
        new_size = sizes[new_idx]
        
        # Eliminar tags de tamaño anteriores
        for size in sizes:
            self.editor.tag_remove(f"size_{size}", sel_start, sel_end)
        
        # Aplicar nuevo tamaño si es diferente del default
        if new_size != 12:
            tag_name = f"size_{new_size}"
            self.editor.tag_configure(tag_name, font=("Segoe UI", new_size))
            self.editor.tag_add(tag_name, sel_start, sel_end)

    def clear_format(self):
        """Elimina todo el formato del texto seleccionado."""
        sel_start, sel_end = self._get_clean_selection()
        if not sel_start: return
        
        # Obtener todos los tags y removerlos
        for tag in self.editor.tag_names():
            if tag != "sel":  # No remover el tag de selección
                self.editor.tag_remove(tag, sel_start, sel_end)
    
    def get_content(self):
        """Obtiene el contenido del editor como texto plano."""
        return self.editor.get("1.0", "end-1c")
    
    def set_content(self, content):
        """Establece el contenido del editor."""
        self.editor.delete("1.0", "end")
        self.editor.insert("1.0", content)
    
    def get_html(self):
        """Convierte el contenido formateado a HTML."""
        html_parts = []
        html_parts.append("<!DOCTYPE html>\n<html>\n<head>\n")
        html_parts.append('<meta charset="UTF-8">\n')
        html_parts.append("<style>\n")
        html_parts.append("body { font-family: 'Segoe UI', sans-serif; background: #1E1E1E; color: #FFFFFF; padding: 20px; }\n")
        html_parts.append("h1 { color: #00E676; }\n")
        html_parts.append("h2 { color: #4FC3F7; }\n")
        html_parts.append("h3 { color: #FFB74D; }\n")
        html_parts.append("code { font-family: Consolas, monospace; background: #2D2D2D; color: #CE9178; padding: 2px 5px; }\n")
        html_parts.append("a { color: #64B5F6; }\n")
        html_parts.append("</style>\n</head>\n<body>\n")
        
        # Procesar el contenido línea por línea
        content = self.editor.get("1.0", "end-1c")
        lines = content.split("\n")
        
        for i, line in enumerate(lines):
            line_start = f"{i+1}.0"
            line_end = f"{i+1}.end"
            
            # Verificar tags de la línea
            tags = self.editor.tag_names(line_start)
            
            if "h1" in tags:
                html_parts.append(f"<h1>{self._escape_html(line)}</h1>\n")
            elif "h2" in tags:
                html_parts.append(f"<h2>{self._escape_html(line)}</h2>\n")
            elif "h3" in tags:
                html_parts.append(f"<h3>{self._escape_html(line)}</h3>\n")
            elif line.startswith("• "):
                html_parts.append(f"<li>{self._escape_html(line[2:])}</li>\n")
            elif line.startswith(("1. ", "2. ", "3. ", "4. ", "5. ", "6. ", "7. ", "8. ", "9. ")):
                html_parts.append(f"<li>{self._escape_html(line[3:])}</li>\n")
            else:
                # Procesar formato inline
                formatted_line = self._process_inline_formatting(line, i+1)
                if formatted_line.strip():
                    html_parts.append(f"<p>{formatted_line}</p>\n")
                else:
                    html_parts.append("<br>\n")
        
        html_parts.append("</body>\n</html>")
        return "".join(html_parts)
        
    def _escape_html(self, text):
        """Escapa caracteres especiales de HTML."""
        return text.replace("&", "&amp;").replace("<", "&lt;").replace(">", "&gt;")
    
    def _process_inline_formatting(self, line, line_num):
        """Procesa el formato inline de una línea."""
        result = []
        i = 0
        
        while i < len(line):
            char_index = f"{line_num}.{i}"
            tags = self.editor.tag_names(char_index)
            
            # Encontrar caracteres consecutivos con los mismos tags
            j = i + 1
            while j < len(line):
                next_tags = self.editor.tag_names(f"{line_num}.{j}")
                if set(tags) != set(next_tags):
                    break
                j += 1
            
            # Obtener el texto
            text = self._escape_html(line[i:j])
            
            # Aplicar formato
            if "bold" in tags:
                text = f"<strong>{text}</strong>"
            if "italic" in tags:
                text = f"<em>{text}</em>"
            if "underline" in tags:
                text = f"<u>{text}</u>"
            if "strikethrough" in tags:
                text = f"<s>{text}</s>"
            if "code" in tags:
                text = f"<code>{text}</code>"
            if "link" in tags:
                text = f"<a href='#'>{text}</a>"
            
            # Colores y Tamaño
            style_parts = []
            for tag in tags:
                if tag.startswith("color_"):
                    color = f"#{tag[6:]}"
                    style_parts.append(f"color:{color}")
                elif tag.startswith("bg_"):
                    color = f"#{tag[3:]}"
                    style_parts.append(f"background:{color}")
                elif tag.startswith("size_"):
                    size = tag[5:]
                    style_parts.append(f"font-size:{size}px")
            
            if style_parts:
                style_str = ";".join(style_parts)
                text = f"<span style='{style_str}'>{text}</span>"
            
            result.append(text)
            i = j
        
        return "".join(result)
    
    def load_html(self, html_content):
        """Carga contenido HTML y lo convierte a formato visual."""
        from html.parser import HTMLParser
        
        class DocHTMLParser(HTMLParser):
            def __init__(self, editor):
                super().__init__()
                self.editor = editor
                self.current_tags = []
                self.tag_stack = [] 
                self.ignore_content = False
                self.separator_pending = False # Track if we need a newline before next content
                self.block_tags = ['p', 'h1', 'h2', 'h3', 'div', 'li']
                self.editor.delete("1.0", "end")
                
            def handle_starttag(self, tag, attrs):
                if tag in ['head', 'script', 'style', 'title']:
                    self.ignore_content = True
                    return

                if self.ignore_content:
                    return
                
                # Handle pending separator (New Block Start)
                if tag in self.block_tags and self.separator_pending:
                    self.editor.insert("end", "\n")
                    self.separator_pending = False
                elif tag == 'br':
                    # BR consumes pending separator and adds its own newline
                    if self.separator_pending:
                        self.editor.insert("end", "\n")
                        self.separator_pending = False
                    self.editor.insert("end", "\n")
                    # BR does not set separator_pending True, it is self-contained
                    return

                attrs_dict = dict(attrs)
                added_tags = []
                
                if tag in ['strong', 'b']:
                    if "bold" not in self.current_tags:
                        self.current_tags.append("bold")
                        added_tags.append("bold")
                elif tag in ['em', 'i']:
                    if "italic" not in self.current_tags:
                        self.current_tags.append("italic")
                        added_tags.append("italic")
                elif tag == 'u':
                    if "underline" not in self.current_tags:
                        self.current_tags.append("underline")
                        added_tags.append("underline")
                elif tag == 's':
                    if "strikethrough" not in self.current_tags:
                        self.current_tags.append("strikethrough")
                        added_tags.append("strikethrough")
                elif tag == 'code':
                    if "code" not in self.current_tags:
                        self.current_tags.append("code")
                        added_tags.append("code")
                elif tag == 'a':
                    if "link" not in self.current_tags:
                        self.current_tags.append("link")
                        added_tags.append("link")
                elif tag in ['h1', 'h2', 'h3']:
                    if tag not in self.current_tags:
                        self.current_tags.append(tag)
                        added_tags.append(tag)
                elif tag == 'li':
                    if "list_item" not in self.current_tags:
                        self.current_tags.append("list_item")
                        added_tags.append("list_item")
                    self.editor.insert("end", "• ") # Bullet, newline handled by separator logic
                elif tag == 'span':
                    style = attrs_dict.get('style', '')
                    if 'color' in style:
                        match = re.search(r'color\s*:\s*(#[0-9a-fA-F]+)', style)
                        if match:
                            color = match.group(1)
                            tag_name = f"color_{color.replace('#', '')}"
                            self.editor.tag_configure(tag_name, foreground=color)
                            self.current_tags.append(tag_name)
                            added_tags.append(tag_name)
                    if 'background' in style:
                        match = re.search(r'background\s*:\s*(#[0-9a-fA-F]+)', style)
                        if match:
                            color = match.group(1)
                            tag_name = f"bg_{color.replace('#', '')}"
                            self.editor.tag_configure(tag_name, background=color)
                            self.current_tags.append(tag_name)
                            added_tags.append(tag_name)
                    if 'font-size' in style:
                        match = re.search(r'font-size\s*:\s*(\d+)px', style)
                        if match:
                            size = match.group(1)
                            tag_name = f"size_{size}"
                            self.editor.tag_configure(tag_name, font=("Segoe UI", int(size)))
                            self.current_tags.append(tag_name)
                            added_tags.append(tag_name)
                
                # Push the list of tags added by this element to the stack
                # BUT ONLY if it's not a void element (elements without end tag)
                if tag not in ['br', 'img', 'hr', 'meta', 'link']:
                    self.tag_stack.append(added_tags)
                            
            def handle_endtag(self, tag):
                if tag in ['head', 'script', 'style', 'title']:
                    self.ignore_content = False
                    return

                if self.ignore_content:
                    return

                # Void elements: handled in starttag or ignored here
                if tag in ['br', 'img', 'hr', 'meta', 'link']:
                    return

                # Pop the tags added by the closing element
                if self.tag_stack:
                    tags_to_remove = self.tag_stack.pop()
                    for t in tags_to_remove:
                        if t in self.current_tags:
                            self.current_tags.remove(t)
                
                # End of Block: Set pending separator
                if tag in self.block_tags:
                    self.separator_pending = True

            def handle_data(self, data):
                if self.ignore_content: return
                
                # Ignore structural newlines (pure whitespace with \n)
                # This corresponds to formatting newlines between tags in get_html
                if not data.strip() and '\n' in data:
                    return

                if data:
                    # If we have text content and a separator is pending, insert it now
                    if self.separator_pending:
                        self.editor.insert("end", "\n")
                        self.separator_pending = False
                        
                    tags = tuple(self.current_tags)
                    self.editor.insert("end", data, tags)

        # Usar el parser
        parser = DocHTMLParser(self.editor)
        parser.feed(html_content)
        
        # Limpiar líneas vacías excesivas al inicio
        content = self.editor.get("1.0", "end")
        if content.startswith("\n"):
             self.editor.delete("1.0", "2.0")
    
    def focus_editor(self):
        """Da foco al editor."""
        self.editor.focus_set()

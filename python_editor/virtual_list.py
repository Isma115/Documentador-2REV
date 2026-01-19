import customtkinter as ctk
import tkinter as tk

class VirtualList(ctk.CTkFrame):
    """
    A virtual list that uses native canvas elements instead of embedded widgets.
    This eliminates clipping issues during scroll.
    """
    def __init__(self, master, item_height=50, use_checkboxes=False, command_click=None, command_double_click=None, **kwargs):
        super().__init__(master, **kwargs)
        self.data = []
        self.item_height = item_height
        self.use_checkboxes = use_checkboxes
        self.command_click = command_click
        self.command_double_click = command_double_click
        self.selected_items = set()
        self.total_height = 0
        self.last_clicked_item = None
        
        # Colors for different asset types
        self.type_colors = {
            'Function': {'bg': '#E3F2FD', 'text': '#0D47A1', 'hover': '#BBDEFB'},
            'Class': {'bg': '#FFEBEE', 'text': '#B71C1C', 'hover': '#FFCDD2'},
            'Region': {'bg': '#FFF3E0', 'text': '#E65100', 'hover': '#FFE0B2'},
            'Component': {'bg': '#E8F5E9', 'text': '#1B5E20', 'hover': '#C8E6C9'},
            'Variable': {'bg': '#FCE4EC', 'text': '#880E4F', 'hover': '#F8BBD0'},
            'Constant': {'bg': '#FCE4EC', 'text': '#880E4F', 'hover': '#F8BBD0'},
            'Compound': {'bg': '#E0F2F1', 'text': '#00695C', 'hover': '#B2DFDB'},
            'default': {'bg': '#3D3D3D', 'text': '#FFFFFF', 'hover': '#4D4D4D'}
        }
        
        # Canvas for drawing
        self.canvas = tk.Canvas(
            self, 
            bg="#2B2B2B",
            highlightthickness=0,
            bd=0
        )
        
        # Scrollbar
        self.scrollbar = ctk.CTkScrollbar(self, command=self._on_scrollbar)
        self.scrollbar.pack(side="right", fill="y")
        
        self.canvas.pack(side="left", fill="both", expand=True)
        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Bindings
        self.canvas.bind("<Configure>", self._on_configure)
        self.canvas.bind("<MouseWheel>", self._on_mousewheel)
        self.canvas.bind("<Button-4>", self._on_mousewheel)  # Linux
        self.canvas.bind("<Button-5>", self._on_mousewheel)  # Linux
        self.canvas.bind("<Button-1>", self._on_click)
        self.canvas.bind("<Double-Button-1>", self._on_double_click)
        self.canvas.bind("<Motion>", self._on_motion)
        self.canvas.bind("<Leave>", self._on_leave)
        
        # State
        self.hover_index = -1
        self._needs_redraw = False

    def set_data(self, data):
        """Set the data to display in the list."""
        self.data = data if data else []
        self.total_height = len(self.data) * self.item_height
        self.canvas.configure(scrollregion=(0, 0, self.canvas.winfo_width(), self.total_height))
        self.canvas.yview_moveto(0)
        self._redraw()

    def get_selected_items(self):
        return list(self.selected_items)
    
    def get_clicked_item(self):
        return self.last_clicked_item
    
    def set_clicked_item(self, item):
        self.last_clicked_item = item

    def toggle_selection(self, item):
        if item in self.selected_items:
            self.selected_items.remove(item)
        else:
            self.selected_items.add(item)

    def _on_scrollbar(self, *args):
        """Handle scrollbar interaction."""
        self.canvas.yview(*args)
        self._redraw()

    def _on_configure(self, event):
        """Handle canvas resize."""
        self.canvas.configure(scrollregion=(0, 0, event.width, self.total_height))
        self._redraw()

    def _on_mousewheel(self, event):
        """Handle mouse wheel scroll."""
        if not self.data or self.total_height <= 0:
            return
        
        if hasattr(event, 'delta') and event.delta:
            delta = event.delta
            if abs(delta) >= 120:
                scroll_amount = int(-1 * (delta / 120))
            else:
                scroll_amount = -1 if delta > 0 else 1
            self.canvas.yview_scroll(scroll_amount, "units")
        elif event.num == 4:
            self.canvas.yview_scroll(-1, "units")
        elif event.num == 5:
            self.canvas.yview_scroll(1, "units")
        
        self._redraw()

    def _on_click(self, event):
        """Handle click on an item."""
        idx = self._get_index_at_y(event.y)
        if 0 <= idx < len(self.data):
            item = self.data[idx]
            self.set_clicked_item(item)
            if self.use_checkboxes:
                self.toggle_selection(item)
            if self.command_click:
                self.command_click(item)
            self._redraw()

    def _on_double_click(self, event):
        """Handle double-click on an item."""
        idx = self._get_index_at_y(event.y)
        if 0 <= idx < len(self.data):
            item = self.data[idx]
            self.last_clicked_item = item # Update last clicked
            if self.command_double_click:
                self.command_double_click(item)
            self._redraw()

    def _on_motion(self, event):
        """Handle mouse motion for hover effect."""
        new_hover = self._get_index_at_y(event.y)
        if new_hover != self.hover_index:
            self.hover_index = new_hover
            self._redraw()

    def _on_leave(self, event):
        """Handle mouse leaving the canvas."""
        if self.hover_index != -1:
            self.hover_index = -1
            self._redraw()

    def _get_index_at_y(self, canvas_y):
        """Get the data index at a given canvas y coordinate."""
        if not self.data:
            return -1
        # Convert canvas y to scroll position
        scroll_top = self.canvas.canvasy(0)
        actual_y = scroll_top + canvas_y
        idx = int(actual_y // self.item_height)
        return idx if 0 <= idx < len(self.data) else -1

    def _get_item_colors(self, item, is_hovered, is_selected):
        """Get colors for an item based on its type and state."""
        asset_type = getattr(item, 'asset_type', 'default')
        colors = self.type_colors.get(asset_type, self.type_colors['default'])
        
        if is_hovered:
            bg = colors['hover']
        else:
            bg = colors['bg']
        
        text_color = colors['text']
        border_color = '#00E676' if is_selected else text_color
        
        return bg, text_color, border_color

    def _get_display_text(self, item, is_selected):
        """Get the display text for an item."""
        if hasattr(item, 'name'):
            if self.use_checkboxes:
                prefix = "☑" if is_selected else "☐"
                return f"  {prefix} {item.name}"
            return f"  {item.name}"
        return f"  {str(item)}"

    def _redraw(self):
        """Redraw all visible items using native canvas elements."""
        self.canvas.delete("all")
        
        if not self.data:
            return
        
        canvas_width = self.canvas.winfo_width()
        canvas_height = self.canvas.winfo_height()
        
        if canvas_width <= 1 or canvas_height <= 1:
            return
        
        # Get visible range
        scroll_top = self.canvas.canvasy(0)
        scroll_bottom = scroll_top + canvas_height
        
        start_idx = max(0, int(scroll_top // self.item_height))
        end_idx = min(len(self.data), int(scroll_bottom // self.item_height) + 1)
        
        # Dimensions
        margin_left = 12
        margin_right = 18
        item_width = canvas_width - margin_left - margin_right
        item_actual_height = self.item_height - 8
        corner_radius = 8
        
        for idx in range(start_idx, end_idx):
            item = self.data[idx]
            
            # Check if item has depth (for tree nodes)
            item_depth = getattr(item, 'depth', 0) if hasattr(item, 'depth') else 0
            depth_margin = item_depth * 30  # 30 pixels per depth level for better visibility
            
            # Calculate position with depth margin
            y_top = idx * self.item_height + 3
            y_bottom = y_top + item_actual_height
            x_left = margin_left + depth_margin
            x_right = margin_left + item_width  # Keep right edge fixed
            
            # Get colors
            is_hovered = (idx == self.hover_index)
            is_selected = item in self.selected_items
            bg_color, text_color, border_color = self._get_item_colors(item, is_hovered, is_selected)
            
            # Draw rounded rectangle (using polygon for simplicity)
            self._draw_rounded_rect(
                x_left, y_top, x_right, y_bottom,
                corner_radius, bg_color, border_color
            )
            
            # Draw text
            display_text = self._get_display_text(item, is_selected)
            text_y = (y_top + y_bottom) / 2
            self.canvas.create_text(
                x_left + 12, text_y,
                text=display_text,
                anchor="w",
                fill=text_color,
                font=("Segoe UI", 14, "bold")
            )

    def _draw_rounded_rect(self, x1, y1, x2, y2, radius, fill, outline):
        """Draw a rounded rectangle on the canvas."""
        # Create rounded rectangle using arcs and lines
        points = [
            x1 + radius, y1,       # Top edge start
            x2 - radius, y1,       # Top edge end
            x2, y1,                # Top right corner control
            x2, y1 + radius,       # Right edge start
            x2, y2 - radius,       # Right edge end
            x2, y2,                # Bottom right corner control
            x2 - radius, y2,       # Bottom edge start
            x1 + radius, y2,       # Bottom edge end
            x1, y2,                # Bottom left corner control
            x1, y2 - radius,       # Left edge start
            x1, y1 + radius,       # Left edge end
            x1, y1,                # Top left corner control
            x1 + radius, y1        # Back to start
        ]
        
        self.canvas.create_polygon(
            points, 
            fill=fill, 
            outline=outline, 
            width=2,
            smooth=True
        )

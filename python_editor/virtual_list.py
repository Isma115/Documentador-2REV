import customtkinter as ctk
import tkinter as tk

class VirtualList(ctk.CTkFrame):
    def __init__(self, master, item_height=35, **kwargs):
        super().__init__(master, **kwargs)
        self.data = []
        self.item_height = item_height
        
        # Color setup (match CTK theme roughly)
        self.bg_color = self._apply_appearance_mode(self._fg_color)
        
        # Canvas for scrolling
        # Scrollbar (Pack first to ensure it gets space)
        # Canvas for scrolling
        self.canvas = tk.Canvas(
            self, 
            bg="#2B2B2B", # Approximation of dark ctk background
            highlightthickness=0,
            bd=0
        )
        
        # Scrollbar (Pack first to ensure it gets space)
        self.scrollbar = ctk.CTkScrollbar(self, command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
        
        self.canvas.pack(side="left", fill="both", expand=True)

        self.canvas.configure(yscrollcommand=self.scrollbar.set)
        
        # Bindings
        self.canvas.bind("<Configure>", self.on_resize)
        self.canvas.bind("<MouseWheel>", self.on_mousewheel) # Windows/MacOS
        # Linux might need Button-4/5
        
        # State
        self.visible_widgets = {} # index -> widget
        self.current_start_idx = -1
        self.current_end_idx = -1
        
        # Theme autodetect workaround (simple)
        self.text_color = "white"

    def set_data(self, data):
        """
        data: list of objects to render. 
        Each object should ideally have a string representation.
        """
        self.data = data
        self.total_height = len(data) * self.item_height
        self.canvas.configure(scrollregion=(0, 0, 0, self.total_height))
        self.refresh_view()

    def on_resize(self, event):
        self.refresh_view()
        
    def on_mousewheel(self, event):
        # Cross-platform scrolling
        # Windows/MacOS: event.delta
        # Linux: Button-4/Button-5 events (handled separately usually, but often mapped to MouseWheel in newer Tk)
        
        # On macOS, delta is often larger or handled differently.
        # We generally want to scroll the canvas yview.
        try:
            if event.delta:
                # MacOS/Windows
                # Different scaling: Windows usually 120, Mac variable.
                # Canvas yview_scroll expects 'units' or 'pages'.
                # Negative delta usually means scroll down (content moves up)
                
                # Normalize a bit
                delta = event.delta
                if abs(delta) >= 120:
                     # Classic mouse wheel step
                    scrolling = int(-1*(delta/120))
                else:
                    # Touchpad or weak scroll
                    scrolling = int(-1 * delta)
                
                self.canvas.yview_scroll(scrolling, "units")
            elif event.num == 4:
                # Linux scroll up
                self.canvas.yview_scroll(-1, "units")
            elif event.num == 5:
                # Linux scroll down
                self.canvas.yview_scroll(1, "units")
                
            self.refresh_view()
        except Exception:
            pass

    def on_scroll(self, *args):
        # Connect to scrollbar
        self.canvas.yview(*args)
        self.refresh_view()

    def refresh_view(self):
        if not self.data:
            self.canvas.delete("all")
            return

        # Calculate visible range
        canvas_height = self.canvas.winfo_height()
        if canvas_height <= 1: return

        # Get vertical scroll position (0.0 to 1.0)
        y_view = self.canvas.yview()
        top_y = y_view[0] * self.total_height
        bottom_y = y_view[1] * self.total_height
        
        start_idx = int(top_y // self.item_height)
        end_idx = int(bottom_y // self.item_height) + 1
        
        # Clamp
        start_idx = max(0, start_idx)
        end_idx = min(len(self.data), end_idx)
        
        # Optimize: If range didn't change heavily, only update edges?
        # For simplicity in V1, we'll reconcile.

        # Identify which indices we need
        needed_indices = set(range(start_idx, end_idx))
        current_indices = set(self.visible_widgets.keys())
        
        # Destroy widgets no longer needed
        to_remove = current_indices - needed_indices
        for idx in to_remove:
            widget = self.visible_widgets.pop(idx)
            widget.destroy()
            
        # Metrics
        canvas_width = self.canvas.winfo_width()
        # Increase margin to avoid right-side clipping (scrollbar overlap or DPI issues)
        # 10px left, 15px right (total 25 reduction) -> reduced from 40
        item_width = max(1, canvas_width - 25) 
        item_actual_height = self.item_height - 6 # Slightly less gap (6px instead of 8)
        x_pos = 10 # 10px left margin
        
        # Update/Create loop
        # We iterate over needed_indices to ensure everyone is correct (size/pos)
        # Note: canvas.itemconfigure is efficient
        
        for idx in needed_indices:
            y_pos = idx * self.item_height + 3 # 3px top padding/centering in slot

            if idx in self.visible_widgets:
                # Update existing
                self.canvas.itemconfigure(f"row_{idx}", width=item_width, height=item_actual_height)
                self.canvas.coords(f"row_{idx}", x_pos, y_pos)
            else:
                # Create new
                item = self.data[idx]
                
                # Use CTkButton for the "Box" look - it handles borders/bg/text robustness better than Frame
                # We disable hover effect if not desired, or keep it for interactivity
                btn = ctk.CTkButton(
                    self.canvas,
                    text="", # Set in configure
                    height=item_actual_height,
                    corner_radius=6,
                    border_width=2,
                    anchor="w", # Left align text
                    font=("Segoe UI", 12, "bold")
                )
                
                # Configure Content
                self.configure_item_button(btn, item)

                # Add to canvas
                self.canvas.create_window(
                    x_pos, y_pos, 
                    window=btn, 
                    anchor="nw", 
                    width=item_width, 
                    height=item_actual_height,
                    tags=f"row_{idx}"
                )
                self.visible_widgets[idx] = btn

    def configure_item_button(self, btn, item):
        display_text = str(item)
        
        # Default colors
        fg_color = "transparent"
        text_color = "white"
        hover_color = "#333333" # Fallback
        
        if hasattr(item, 'name'):
            display_text = f"  {item.name}" # Add indent for look
            
            if item.asset_type == 'Function':
                fg_color = "#E3F2FD"
                text_color = "#0D47A1"
                hover_color = "#BBDEFB"
            elif item.asset_type == 'Class':
                fg_color = "#FFEBEE"
                text_color = "#B71C1C"
                hover_color = "#FFCDD2"
            elif item.asset_type == 'Region':
                fg_color = "#FFF3E0"
                text_color = "#E65100"
                hover_color = "#FFE0B2"
            elif item.asset_type == 'Component':
                fg_color = "#E8F5E9"
                text_color = "#1B5E20"
                hover_color = "#C8E6C9"
            elif item.asset_type == 'Variable' or item.asset_type == 'Constant':
                fg_color = "#FCE4EC"
                text_color = "#880E4F"
                hover_color = "#F8BBD0"
        
        btn.configure(
            text=display_text,
            fg_color=fg_color,
            text_color=text_color,
            border_color=text_color,
            hover_color=hover_color
        )
        
        # Bind scrolling to the button as well
        btn.bind("<MouseWheel>", self.on_mousewheel)


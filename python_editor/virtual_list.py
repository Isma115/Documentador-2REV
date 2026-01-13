import customtkinter as ctk
import tkinter as tk

class VirtualList(ctk.CTkFrame):
    def __init__(self, master, item_height=25, **kwargs):
        super().__init__(master, **kwargs)
        self.data = []
        self.item_height = item_height
        
        # Color setup (match CTK theme roughly)
        self.bg_color = self._apply_appearance_mode(self._fg_color)
        
        # Canvas for scrolling
        self.canvas = tk.Canvas(
            self, 
            bg="#2B2B2B", # Approximation of dark ctk background
            highlightthickness=0,
            bd=0
        )
        self.canvas.pack(side="left", fill="both", expand=True)

        # Scrollbar
        self.scrollbar = ctk.CTkScrollbar(self, command=self.canvas.yview)
        self.scrollbar.pack(side="right", fill="y")
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
            
        # Create new widgets
        to_create = needed_indices - current_indices
        for idx in to_create:
            item = self.data[idx]
            y_pos = idx * self.item_height
            
            # Create the rendering widget
            # We use a simple Frame+Label combo for speed/look
            # Or just a Label
            # We need to rely on the `render_item` internal method
            
            # Using a Frame to hold the label allows for better width management
            frame = ctk.CTkFrame(
                self.canvas, 
                fg_color="transparent", 
                height=self.item_height,
                corner_radius=0
            )
            
            # Content
            self.create_item_widget(frame, item)

            # Add to canvas
            # We use `create_window` to place widgets on canvas
            # Width=window_width
            self.canvas.create_window(
                0, y_pos, 
                window=frame, 
                anchor="nw", 
                width=self.canvas.winfo_width(), 
                height=self.item_height,
                tags=f"row_{idx}"
            )
            self.visible_widgets[idx] = frame

    def create_item_widget(self, parent, item):
        # This can be overridden or callbacks used
        # For now, custom implementation hardcoded for Assets
        
        display_text = str(item)
        if hasattr(item, 'name'):
            # It's an Asset
             # Different icons/text based on type
            icon = "📝"
            if item.asset_type == 'Class':
                icon = "📦"
            elif item.asset_type == 'Function':
                icon = "ƒ "
            elif item.asset_type == 'Variable':
                icon = "🔧"
            elif item.asset_type == 'Constant':
                icon = "💎"

            display_text = f"{icon} {item.name}"
            # Add file path in smaller text? Maybe too crowded.
            # display_text += f" ({os.path.basename(item.file_path)})"

        lbl = ctk.CTkLabel(
            parent, 
            text=display_text, 
            anchor="w",
            font=("Segoe UI", 13)
        )
        lbl.pack(fill="both", expand=True, padx=5)
        
        # Bind events to children so scrolling works over them too
        parent.bind("<MouseWheel>", self.on_mousewheel)
        lbl.bind("<MouseWheel>", self.on_mousewheel)
        
        # Create tooltip/click events here if needed
        # lbl.bind("<Button-1>", lambda e: self.on_item_click(item))

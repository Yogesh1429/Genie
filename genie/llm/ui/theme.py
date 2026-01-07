import tkinter as tk
from tkinter import ttk, messagebox
from pathlib import Path

THEMES = {
	"light": {
		# "bg": "#EAF2FF", "card": "#F5F9E3", "primary": "#2563EB",
		"bg": "#EAF2FF", "card": "#F1F3DC", "primary": "#2563EB",
		"primary_hover": "#1D4ED8", "secondary": "#A7C7FF",
		"accent": "#60A5FA", "text": "#0F172A", "subtle": "#64748B",
		"border": "#CFE3FF", "success": "#10b981", "warning": "#f59e0b",
		"error": "#ef4444"
	},
	"dark": {
		"bg": "#111827", "card": "#1f2937", "primary": "#818cf8",
		"primary_hover": "#a5b4fc", "secondary": "#34d399",
		"accent": "#fb7185", "text": "#f9fafb", "subtle": "#9ca3af",
		"border": "#374151", "success": "#34d399", "warning": "#fbbf24",
		"error": "#f87171"
	}
}

def setup_styles(colors: dict):
	style = ttk.Style()
	style.theme_use("clam")
	style.configure("Card.TFrame", background=colors["card"], relief="flat")
	style.configure("GridBorder.TFrame", background=colors["border"], relief="flat")
	style.configure("GridWrap.TFrame", background=colors["card"], relief="flat")
	style.configure("Title.TLabel", font=("Segoe UI", 24, "bold"), background=colors["card"], foreground=colors["text"]) 
	style.configure("Sub.TLabel", font=("Segoe UI", 9), background=colors["card"], foreground=colors["subtle"]) 
	style.configure("Section.TLabel", font=("Segoe UI", 12, "bold"), background=colors["card"], foreground=colors["text"]) 
	style.configure("Accent.TButton", font=("Segoe UI", 10, "bold"), background=colors["primary"], foreground="white", bordercolor=colors["primary"], lightcolor=colors["primary"], darkcolor=colors["primary"], focuscolor=colors["primary"], padding=(10, 5))
	style.map("Accent.TButton", background=[("active", colors["primary_hover"])])
	style.configure("Normal.TButton", font=("Segoe UI", 9), background=colors["border"], foreground=colors["text"], bordercolor=colors["border"], lightcolor=colors["border"], darkcolor=colors["border"], padding=(9, 5))
	style.map("Normal.TButton", background=[("active", colors["subtle"])])
	# Inputs
	style.configure("TCombobox", fieldbackground=colors["card"], background=colors["card"], foreground=colors["text"], arrowcolor=colors["primary"], bordercolor=colors["border"], lightcolor=colors["border"], darkcolor=colors["border"], relief="flat", padding=6)
	style.map("TCombobox", fieldbackground=[("readonly", colors["card"])], background=[("readonly", colors["card"])])
	style.configure("TEntry", fieldbackground=colors["card"], foreground=colors["text"], bordercolor=colors["border"], lightcolor=colors["border"], darkcolor=colors["border"], insertcolor=colors["text"], relief="flat", padding=6)
	style.configure("Flat.Vertical.TScrollbar", background=colors["border"], troughcolor=colors["card"], bordercolor=colors["card"], lightcolor=colors["card"], darkcolor=colors["card"], arrowsize=10, relief="flat", gripcount=0)
	style.map("Flat.Vertical.TScrollbar", background=[("active", colors["primary_hover"])], troughcolor=[("active", colors["card"])])
	# Treeview
	style.configure("Grid.Treeview", background=colors["card"], fieldbackground=colors["card"], foreground=colors["text"], bordercolor=colors["border"], borderwidth=0, relief="flat", rowheight=22)
	try:
		style.layout("Grid.Treeview", [("Treeview.treearea", {"sticky": "nswe"})])
	except Exception:
		pass
	style.map("Grid.Treeview", background=[("selected", colors["primary"])], foreground=[("selected", "white")])
	style.configure("Grid.Treeview.Heading", background=colors["card"], foreground=colors["text"], bordercolor=colors["border"], lightcolor=colors["border"], darkcolor=colors["border"], borderwidth=1, relief="solid", font=("Segoe UI", 10, "bold"))
	
	style.map(
		"Grid.Treeview.Heading",
		background=[("active", colors["primary_hover"])],
		foreground=[("active", "white")],
	)
	try:
		style.layout("Grid.Treeview.Heading", [("Treeheading.cell", {"sticky": "nswe", "children": [("Treeheading.padding", {"sticky": "nswe", "children": [("Treeheading.image", {"side": "right", "sticky": ""}), ("Treeheading.text", {"sticky": "we"})]})]})])
	except Exception:
		pass

def set_theme(self, mode):
	self.colors = THEMES[mode]
	self.current_theme.set(mode)
	setup_styles(self.colors)
	update_all_colors(self)
	patch_messagebox_for_theme(self)

def patch_messagebox_for_theme(self):
	if not hasattr(self, "_orig_messagebox"):
		self._orig_messagebox = dict(
			showinfo=messagebox.showinfo,
			showwarning=messagebox.showwarning,
			showerror=messagebox.showerror,
			askyesno=messagebox.askyesno,
		)
	# Apply dark-mode patch or restore originals
	if (self.current_theme.get() or "").lower() == "dark":
		messagebox.showinfo = lambda title, msg: self._dark_dialog("info", title, msg)
		messagebox.showwarning = lambda title, msg: self._dark_dialog("warning", title, msg)
		messagebox.showerror = lambda title, msg: self._dark_dialog("error", title, msg)
		messagebox.askyesno = lambda title, msg: self._dark_dialog("askyesno", title, msg)
	else:
		for k, v in self._orig_messagebox.items():
			setattr(messagebox, k, v)

def toggle_theme(self, *_):
	new = "dark" if self.current_theme.get() == "light" else "light"
	set_theme(self, new)
	set_label_icon(self, new)

def set_label_icon(self, theme: str):
	try:
		app_dir = Path(__file__).resolve().parent
		if theme == "dark":
			png_path = app_dir / "Genie_dark.png"
		else:
			png_path = app_dir / "Genie_light.png"
		print(f"icon _path--> {png_path}")
		self.title_icon_img = tk.PhotoImage(file=str(png_path))
		self.title_label.configure(image=self.title_icon_img)        
        
	except Exception:
		pass

def set_window_icon(root: tk.Tk, theme: str):
	try:
		app_dir = Path(__file__).resolve().parent
		# ico_path = app_dir / "Genie.ico"
		if theme == "dark":
			png_path = app_dir / "Genie_dark.png"
		else:
			png_path = app_dir / "Genie_light.png"
		png_path_window = app_dir / "Genie_light.png"
		print(f"png_path--> {png_path}")
		# if ico_path.exists():
		# 	root.iconbitmap(default=str(ico_path))
		# 	return
		if png_path.exists():
			_icon_image = tk.PhotoImage(file=str(png_path))
			_icon_image_window = tk.PhotoImage(file=str(png_path_window))
			root.iconphoto(True, _icon_image_window)
			# root.title_label.configure(image=_icon_image)
			return _icon_image
		print("using default icon")
		img = tk.PhotoImage(width=16, height=16)
		img.put("#3B82F6", to=(0, 0, 16, 16))
		img.put("#FFFFFF", to=(3, 3, 13, 13))
		img.put("#3B82F6", to=(7, 7, 9, 9))
		_icon_image = img
		root.iconphoto(True, _icon_image)
	except Exception:
		pass
	
def update_all_colors(self):
	self.root.configure(bg=self.colors["bg"])
	self.canvas.configure(bg=self.colors["bg"], highlightthickness=0)
	self.model_list.configure(bg=self.colors["card"], fg=self.colors["text"], highlightbackground=self.colors["border"], highlightcolor=self.colors["border"], highlightthickness=1, bd=0, selectbackground=self.colors["primary"], selectforeground="white", activestyle="none")

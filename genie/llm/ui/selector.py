import tkinter as tk
from tkinter import ttk, messagebox
import logging

from .theme import THEMES, set_window_icon, setup_styles, set_label_icon, patch_messagebox_for_theme, toggle_theme, update_all_colors
from .controller import Controller
from ..core.config_loader import ConfigLoader
import os


# Setup logging for LLM Provider Selector
# try:
#     from ...log_setup import setup_logging
#     setup_logging()
# except ImportError:
#     logging.basicConfig(level=logging.INFO, format='%(asctime)s - %(name)s - %(levelname)s - %(message)s')

logger = logging.getLogger('genie.llm.ui.selector')

class LLMProviderSelector:
	def __init__(self, root, encryption_key=None):
		logger.info("Initializing LLM Provider Selector")
		self.root = root
		# self.root.title("🤖 LLM Manager")
		self.root.title("LLM Manager")
		self.base_width = 900
		self.base_height = 580
		self.bedrock_height = 650
		self.root.geometry(f"{self.base_width}x{self.base_height}")
		self.root.minsize(self.base_width, self.base_height)
		self.current_theme = tk.StringVar(value="dark")
		self.colors = THEMES["dark"]
		self.icon_image = set_window_icon(self.root, "dark")		

		setup_styles(self.colors)
		# Load external configuration
		cfg = os.getenv('APP_PROVIDERS_FILE')
		self.config_loader = ConfigLoader(config_file = cfg)
		self.ctrl = Controller(encryption_key=encryption_key, config_loader=self.config_loader)
		self.build_ui()
		# self.icon_image = set_label_icon(self.title_label, "dark")
		# self._patch_messagebox()
		patch_messagebox_for_theme(self)
		self.populate_initial()
		self.refresh_saved_configs()
		logger.info("LLM Provider Selector initialized successfully")

	def _dark_dialog(self, kind, title, message):
		dlg = tk.Toplevel(self.root)
		dlg.title(title or "")
		dlg.transient(self.root)
		dlg.grab_set()
		dlg.configure(bg=self.colors["card"])
		dlg.resizable(False, False)

		outer = ttk.Frame(dlg, style="Card.TFrame")
		outer.pack(fill="both", expand=True, padx=16, pady=12)

		row = ttk.Frame(outer, style="Card.TFrame")
		row.pack(fill="x", pady=(0, 10))

		bitmap_map = {
			"info": "info",
			"warning": "warning",
			"error": "error",
			"askyesno": "question",
			"askokcancel": "question",
			"askretrycancel": "question",
			"askyesnocancel": "question",
			"askquestion": "question",
		}
		bm = bitmap_map.get(kind, "info")

		tk.Label(row, bitmap=bm, bg=self.colors["card"], fg=self.colors["accent"]).pack(side="left", padx=(0, 10))

		ttk.Label(row, text=message, style="Sub.TLabel", wraplength=420).pack(side="left", fill="x", expand=True)

		result = {"val": None}
		def close(val=None):
			result["val"] = val
			try:
				dlg.destroy()
			except Exception:
				pass

		btns = ttk.Frame(outer, style="Card.TFrame")
		btns.pack(fill="x")
		if kind == "askyesno":
			ttk.Button(btns, text="No", style="Normal.TButton", command=lambda: close(False)).pack(side="right", padx=4)
			ttk.Button(btns, text="Yes", style="Accent.TButton", command=lambda: close(True)).pack(side="right", padx=4)
			dlg.bind("<Return>", lambda e: close(True))
			dlg.bind("<Escape>", lambda e: close(False))
		else:
			ttk.Button(btns, text="OK", style="Accent.TButton", command=lambda: close()).pack(side="right", padx=4)
			dlg.bind("<Return>", lambda e: close())
			dlg.bind("<Escape>", lambda e: close())

		# Center over parent
		dlg.update_idletasks()
		try:
			px = self.root.winfo_rootx() + (self.root.winfo_width() - dlg.winfo_width()) // 2
			py = self.root.winfo_rooty() + (self.root.winfo_height() - dlg.winfo_height()) // 2
			dlg.geometry(f"+{max(px, 0)}+{max(py, 0)}")
		except Exception:
			pass

		self.root.wait_window(dlg)
		return result["val"] if kind == "askyesno" else None

	def build_ui(self):
		self.root.configure(bg=self.colors["bg"])
		self.root.bind_all("<Control-d>", lambda e: toggle_theme(self))

		self.canvas = tk.Canvas(self.root, bg=self.colors["bg"], highlightthickness=0)
		self.canvas.pack(fill="both", expand=True, padx=30, pady=30)
		self.card = ttk.Frame(self.canvas, style="Card.TFrame")
		self.card_window = self.canvas.create_window((0, 0), window=self.card, anchor="nw")
		self.canvas.bind("<Configure>", lambda e: self.canvas.itemconfig(self.card_window, width=e.width))

		self.title_label = ttk.Label(self.card, text="LLM Manager", image=self.icon_image, compound="left", style="Title.TLabel")
		self.title_label.pack(pady=(20, 5))
        
		# ttk.Label(self.card, text="🤖 LLM Manager", style="Title.TLabel").pack(pady=(20, 5))
		ttk.Label(self.card, text="Securely configure your LLM provider for GenIE", style="Sub.TLabel").pack()

		self.profile_var = tk.StringVar()
		self.provider_var = tk.StringVar()
		self.model_var = tk.StringVar()
		self.endpoint_var = tk.StringVar()
		self.key_var = tk.StringVar()
		self.aws_key_id_var = tk.StringVar()
		self.aws_secret_key_var = tk.StringVar()
		self.show_key = tk.BooleanVar()

		# Two-pane layout: left form, right saved configs grid
		self.content_row = ttk.Frame(self.card, style="Card.TFrame")
		self.content_row.pack(fill="both", expand=True, padx=0, pady=(10, 0))

		self.left_pane = ttk.Frame(self.content_row, style="Card.TFrame")
		self.left_pane.pack(side="left", fill="both", expand=True, padx=(0, 0))

		self.right_pane = ttk.Frame(self.content_row, style="Card.TFrame", width=480)
		self.right_pane.pack_propagate(False)
		self.right_pane.pack(side="right", fill="both", pady=(10, 0))

		# Left: form fields
		self.add_section("🌐 API Provider", self.provider_var, readonly=True, parent=self.left_pane)
		self.add_endpoint_section(parent=self.left_pane)
		self.add_section("🧠 Available Models [Select default model]", self.model_var, readonly=True, parent=self.left_pane)
		self.add_section("🔑 API Key", self.key_var, secret=True, parent=self.left_pane)
		self.add_aws_creds_section(parent=self.left_pane)

		# Left: action bar (Save / Test / Clear)
		self.left_actions = ttk.Frame(self.left_pane, style="Card.TFrame")
		self.left_actions.pack(fill="x", padx=40, pady=(8, 0))
		ttk.Button(self.left_actions, text="Save", style="Accent.TButton", width=10, command=self.save).pack(side="left", padx=4)
		ttk.Button(self.left_actions, text="Test", style="Normal.TButton", width=8, command=self.test_api).pack(side="left", padx=4)
		ttk.Button(self.left_actions, text="Clear", style="Normal.TButton", width=10, command=self.clear).pack(side="left", padx=4)

		# Right: saved configurations grid and action bar
		self.add_saved_configs_section(parent=self.right_pane)

		self.bottom_spacer = ttk.Frame(self.card, style="Card.TFrame")
		self.bottom_spacer.pack(fill="both", expand=True)

		# Bottom status label
		# self.status_lbl = ttk.Label(self.card, text="✅ Ready", font=("Segoe UI", 9), background=self.colors["card"]) 
		self.status_lbl = ttk.Label(self.card, text="✅ Ready", style="Sub.TLabel", anchor='e') 		
		self.status_lbl.pack(side="bottom", pady=(0, 10), padx=(0, 20),anchor='e')
		update_all_colors(self)

	def add_section(self, label, var, readonly=False, secret=False, apply=False, parent=None):
		container = parent or self.card
		frame = ttk.Frame(container, style="Card.TFrame")
		frame.pack(fill="x", padx=40, pady=(10, 5))
		if " — " in label:
			main_label, sub_label = label.split(" — ", 1)
			head = ttk.Frame(frame, style="Card.TFrame")
			head.pack(fill="x")
			ttk.Label(head, text=main_label, style="Section.TLabel").pack(side="left", anchor="w")
			ttk.Label(head, text=f" — {sub_label}", style="Sub.TLabel").pack(side="left", anchor="w")
		elif " [" in label and label.endswith("]"):
			idx = label.rfind(" [")
			main_label = label[:idx]
			sub_label = label[idx:]
			head = ttk.Frame(frame, style="Card.TFrame")
			head.pack(fill="x")
			ttk.Label(head, text=main_label, style="Section.TLabel").pack(side="left", anchor="w")
			ttk.Label(head, text=sub_label, style="Sub.TLabel").pack(side="left", anchor="w")
		else:
			ttk.Label(frame, text=label, style="Section.TLabel").pack(anchor="w")
		inner = ttk.Frame(frame, style="Card.TFrame")
		inner.pack(fill="x", pady=(2, 0))
		if secret:
			entry = ttk.Entry(inner, textvariable=var, show="•", width=45)
			entry.pack(side="left", fill="x", expand=True)
			eye = ttk.Button(inner, text="👁", width=3, style="Normal.TButton", command=lambda: self.toggle_secret(entry, eye))
			eye.pack(side="left", padx=5)
			self.key_entry = entry
			self.key_eye = eye
			if label.startswith("🔑"):
				self.api_key_frame = frame
			if apply:
				ttk.Button(inner, text="Apply", style="Normal.TButton", width=6, command=self.apply_enc).pack(side="left")
		else:
			if label.startswith(("🏢", "🌐", "🔌")):
				cmb = ttk.Combobox(inner, textvariable=var, state="readonly", width=40)
				cmb.pack(fill="x", expand=True)
				self.provider_combo = cmb
			elif label.startswith(("🧠",)):
				list_container = ttk.Frame(inner, style="Card.TFrame")
				list_container.pack(fill="both", expand=True)
				yscroll = ttk.Scrollbar(list_container, orient="vertical", style="Flat.Vertical.TScrollbar")
				self.model_list = tk.Listbox(list_container, height=6, selectmode="browse", exportselection=False, activestyle="none", borderwidth=0, highlightthickness=1)
				self.model_list.pack(side="left", fill="both", expand=True)
				yscroll.config(command=self.model_list.yview)
				self.model_list.config(yscrollcommand=yscroll.set)
				self.model_list.configure(bg=self.colors["card"], fg=self.colors["text"], highlightbackground=self.colors["border"], highlightcolor=self.colors["border"], highlightthickness=1, bd=0, selectbackground=self.colors["primary"], selectforeground="white", activestyle="none")
				yscroll.pack(side="right", fill="y")
				self.model_list.bind("<<ListboxSelect>>", self.on_model_select)
			else:
				entry = ttk.Entry(inner, textvariable=var, width=45)
				entry.pack(fill="x", expand=True)

	def add_endpoint_section(self, parent=None):
		container = parent or self.card
		frame = ttk.Frame(container, style="Card.TFrame")
		frame.pack(fill="x", padx=40, pady=(4, 0))
		ttk.Label(frame, text="🔗 Endpoint URL", style="Section.TLabel").pack(anchor="w")
		inner = ttk.Frame(frame, style="Card.TFrame")
		inner.pack(fill="x", pady=(2, 0))
		entry = ttk.Entry(inner, textvariable=self.endpoint_var, state="readonly")
		entry.pack(fill="x", expand=True)

	def add_aws_creds_section(self, parent=None):
		container = parent or self.card
		frame = ttk.Frame(container, style="Card.TFrame")
		ttk.Label(frame, text="🔐 AWS Credentials (for Bedrock)", style="Section.TLabel").pack(anchor="w")
		inner = ttk.Frame(frame, style="Card.TFrame")
		inner.pack(fill="x", pady=(2, 0))
		left = ttk.Frame(inner, style="Card.TFrame")
		left.pack(fill="x", pady=(2, 0))
		ttk.Label(left, text="Key ID", style="Sub.TLabel").pack(anchor="w")
		ak_entry = ttk.Entry(left, textvariable=self.aws_key_id_var, width=45)
		ak_entry.pack(fill="x", expand=True)
		self.aws_key_entry = ak_entry
		right = ttk.Frame(inner, style="Card.TFrame")
		right.pack(fill="x", pady=(6, 0))
		ttk.Label(right, text="Secret Key", style="Sub.TLabel").pack(anchor="w")
		sk_entry = ttk.Entry(right, textvariable=self.aws_secret_key_var, show="•", width=45)
		sk_entry.pack(side="left", fill="x", expand=True)
		sk_eye = ttk.Button(right, text="👁", width=3, style="Normal.TButton", command=lambda: self.toggle_secret(sk_entry, sk_eye))
		sk_eye.pack(side="left", padx=5)
		self.aws_secret_entry = sk_entry
		self.aws_secret_eye = sk_eye
		self.aws_creds_frame = frame

	def add_saved_configs_section(self, parent=None):
		container = parent or self.card
		frame = ttk.Frame(container, style="Card.TFrame")
		frame.pack(fill="both", expand=True, padx=30, pady=(10, 5))
		head = ttk.Frame(frame, style="Card.TFrame")
		head.pack(fill="x")
		ttk.Label(head, text="💾 Saved Configurations", style="Section.TLabel").pack(side="left", anchor="w")
		ttk.Label(head, text=" — select to load/delete", style="Sub.TLabel").pack(side="left", anchor="w")

		# Treeview grid wrapped with a visible border that follows theme colors
		self.grid_border = ttk.Frame(frame, style="GridBorder.TFrame")
		self.grid_border.pack(fill="both", expand=True)
		grid_wrap = ttk.Frame(self.grid_border, style="GridWrap.TFrame")
		grid_wrap.pack(fill="both", expand=True, padx=1, pady=1)
		self.grid_wrap = grid_wrap
		# Include provider_id as a hidden data column
		columns = ("provider_id", "provider", "model")
		self.saved_tree = ttk.Treeview(grid_wrap, columns=columns, show="headings", height=8, style="Grid.Treeview")
		# Ensure no highlight border from native theme
		try:
			self.saved_tree.configure(takefocus=False)
		except Exception:
			pass
		self.saved_tree.heading("provider_id", text="Provider ID")
		self.saved_tree.heading("provider", text="Provider")
		self.saved_tree.heading("model", text="Model")
		# Hide provider_id in display but keep data by controlling displaycolumns
		self.saved_tree["displaycolumns"] = ("provider", "model")
		self.saved_tree.column("provider_id", width=0, minwidth=0, stretch=False)
		self.saved_tree.column("provider", width=60, anchor="w")
		self.saved_tree.column("model", width=180, anchor="w")
		scrollbar = ttk.Scrollbar(grid_wrap, orient="vertical", style="Flat.Vertical.TScrollbar")
		def _on_tree_yscroll(first, last):
			# Update scrollbar and show only when needed
			scrollbar.set(first, last)
			try:
				f1, f2 = float(first), float(last)
				if f1 <= 0.0 and f2 >= 1.0:
					if scrollbar.winfo_ismapped():
						scrollbar.pack_forget()
				else:
					if not scrollbar.winfo_ismapped():
						scrollbar.pack(side="right", fill="y")
			except Exception:
				pass
		self.saved_tree.configure(yscrollcommand=_on_tree_yscroll)
		self.saved_tree.pack(side="left", fill="both", expand=True)
		scrollbar.config(command=self.saved_tree.yview)
		# Defer initial evaluation until geometry is ready
		self.root.after(0, lambda: _on_tree_yscroll(*self.saved_tree.yview()))
		self.saved_tree.bind("<<TreeviewSelect>>", self.on_saved_select)
		self.saved_tree.bind("<Double-1>", lambda e: self.load())

		# Action bar under grid
		actions = ttk.Frame(frame, style="Card.TFrame")
		actions.pack(fill="x", pady=(8, 0))
		ttk.Button(actions, text="Load", style="Normal.TButton", width=10, command=self.load).pack(side="left", padx=2)
		ttk.Button(actions, text="Delete", style="Normal.TButton", width=10, command=self.delete_selected).pack(side="left", padx=2)
		ttk.Button(actions, text="▲ Up", style="Normal.TButton", width=8, command=lambda: self.move_saved(-1)).pack(side="right", padx=2)
		ttk.Button(actions, text="▼ Down", style="Normal.TButton", width=8, command=lambda: self.move_saved(1)).pack(side="right", padx=2)

	def populate_initial(self):
		self.provider_combo["values"] = list(self.ctrl.providers.keys())
		self.provider_combo.bind("<<ComboboxSelected>>", self.on_provider_change)

	def on_provider_change(self, *_):
		provider = self.provider_var.get()
		models = self.ctrl.providers.get(provider, [])
		if hasattr(self, "model_list"):
			self.model_list.delete(0, tk.END)
			for m in models:
				self.model_list.insert(tk.END, m)
			if models:
				try:
					self.model_list.selection_clear(0, tk.END)
					self.model_list.selection_set(0)
					self.model_list.activate(0)
					self.model_list.see(0)
				except Exception:
					pass
		endpoint = self.ctrl.name_to_endpoint.get(provider, "")
		self.endpoint_var.set(endpoint)
		self.model_var.set(models[0] if models else "")
		if hasattr(self, "key_entry"):
			prov_lower = (provider or "").lower()
			is_ollama = "ollama" in prov_lower or "bedrock" in prov_lower
			try:
				if "bedrock" in prov_lower and hasattr(self, "api_key_frame"):
					self.api_key_frame.pack_forget()
					self.key_var.set("")
					self.aws_key_id_var.set("")
					self.aws_secret_key_var.set("")
				else:
					if hasattr(self, "api_key_frame") and not self.api_key_frame.winfo_ismapped():
						self.api_key_frame.pack(fill="x", padx=40, pady=(10, 5))
					self.key_entry.config(state="disabled" if is_ollama else "normal")
					if is_ollama:
						self.key_var.set("")
					if hasattr(self, "key_eye"):
						self.key_eye.config(state="disabled" if is_ollama else "normal")
			except Exception:
				pass
		if hasattr(self, "aws_creds_frame") and hasattr(self, "aws_key_entry") and hasattr(self, "aws_secret_entry"):
			is_bedrock = "bedrock" in (provider or "").lower()
		try:
			if is_bedrock:
				if not self.aws_creds_frame.winfo_ismapped():
					self.aws_creds_frame.pack(fill="x", padx=40, pady=(10, 0))
				self.aws_key_entry.config(state="normal")
				self.aws_secret_entry.config(state="normal")
				if hasattr(self, "aws_secret_eye"):
					self.aws_secret_eye.config(state="normal")
				# Ensure left actions remain below creds section
				if hasattr(self, "left_actions"):
					self.left_actions.pack_forget()
					self.left_actions.pack(fill="x", padx=40, pady=(8, 0))
				self.root.geometry(f"{self.base_width}x{self.bedrock_height}")
			else:
				self.aws_creds_frame.pack_forget()
				self.aws_key_entry.config(state="disabled")
				self.aws_secret_entry.config(state="disabled")
				if hasattr(self, "aws_secret_eye"):
					self.aws_secret_eye.config(state="disabled")
				# Re-pack left actions below left fields
				if hasattr(self, "left_actions"):
					self.left_actions.pack_forget()
					self.left_actions.pack(fill="x", padx=40, pady=(8, 0))
				self.root.geometry(f"{self.base_width}x{self.base_height}")
		except Exception:
			pass

	def on_model_select(self, *_):
		if not hasattr(self, "model_list"):
			return
		sel = self.model_list.curselection()
		if not sel:
			return
		index = sel[0]
		value = self.model_list.get(index)
		self.model_var.set(value)

	def _select_model_in_list(self, model: str):
		if not hasattr(self, "model_list") or not model:
			return
		try:
			items = self.model_list.get(0, tk.END)
			if model in items:
				idx = items.index(model)
				self.model_list.selection_clear(0, tk.END)
				self.model_list.selection_set(idx)
				self.model_list.activate(idx)
				self.model_list.see(idx)
				self.model_var.set(model)
		except Exception:
			pass

	def on_saved_select(self, *_):
		try:
			if hasattr(self, "saved_tree"):
				selection = self.saved_tree.selection()
				if not selection:
					return
				item_id = selection[0]
				provider_id = self.saved_tree.set(item_id, "provider_id") or (
					self.saved_tree.item(item_id, "values")[0] if self.saved_tree.item(item_id, "values") else ""
				)
				if provider_id:
					self.profile_var.set(str(provider_id))
		except Exception:
			pass

	def toggle_secret(self, entry, btn):
		if entry.cget("show") == "•":
			entry.config(show="")
			btn.config(text="🙈")
		else:
			entry.config(show="•")
			btn.config(text="👁")

	def status(self, msg, typ="info"):
		self.status_lbl.config(text=f"{'✅' if typ == 'success' else '⚠️'} {msg}", anchor='e')
		self.root.after(4000, lambda: self.status_lbl.config(text="✅ Ready  ", anchor='e'))

	def refresh_saved_configs(self):
		try:
			if hasattr(self, "saved_tree"):
				for iid in self.saved_tree.get_children():
					self.saved_tree.delete(iid)
				all_cfgs = self.ctrl.list_profiles()
				for cfg in all_cfgs:
					# Stored key (may be legacy profile name); we keep it as row id
					save_key = cfg.get("profile_name", "")
					pid = cfg.get("provider_id", save_key)
					prov = cfg.get("provider", pid)
					model = cfg.get("model", "")
					self.saved_tree.insert("", "end", iid=save_key or pid, values=(pid, prov, model))
		except Exception:
			pass

	def _collect_current_config(self) -> dict | None:
		provider_name = self.provider_var.get()
		provider_id = self.ctrl.name_to_id.get(provider_name, provider_name)
		cfg = dict(
			provider_id=provider_id,
			provider=provider_name,
			base_url=self.endpoint_var.get(),
			model=self.model_var.get(),
		)
		provider_lower = (cfg["provider"] or "").lower()
		if "bedrock" in provider_lower:
			cfg["aws_access_key_id"] = self.aws_key_id_var.get()
			cfg["aws_secret_access_key"] = self.aws_secret_key_var.get()
		else:
			if "ollama" not in provider_lower:
				cfg["api_key"] = self.key_var.get()
		if not cfg["provider"]:
			messagebox.showerror("Error", "Select a provider")
			return None
			
		if not cfg["model"]:
			messagebox.showerror("Error", "Select a default model")
			return None
		if ("ollama" not in provider_lower and "bedrock" not in provider_lower) and not cfg.get("api_key"):
			messagebox.showerror("Error", "Enter an API key for this provider")
			return None
		if "bedrock" in provider_lower:
			ak = cfg.get("aws_access_key_id", "").strip()
			sk = cfg.get("aws_secret_access_key", "").strip()
			if not ak or not sk:
				messagebox.showerror("Error", "AWS Key ID and Secret Key are required for Bedrock")
				return None
		return cfg

	def save(self):
		# Use provider_id as the key
		cfg = self._collect_current_config()
		if not cfg:
			return
		name = cfg.get("provider_id", "").strip()
		if not name:
			messagebox.showerror("Error", "Select a provider")
			return
		# Confirm overwrite if provider already saved
		existing = self.ctrl.load_config(name)
		if existing is not None:
			prov_disp = cfg.get("provider", name)
			if not messagebox.askyesno("Replace saved config?", f"A configuration for '{prov_disp}' already exists.\n\nDo you want to replace it?"):
				self.status("Save cancelled", "info")
				return
		if self.ctrl.save_config(cfg):
			self.status("Saved profile", "success")
			self.refresh_saved_configs()
			messagebox.showinfo("Success", f"🔒 Saved provider '{name}'")
		else:
			self.status("Save failed", "error")

	def load(self):
		# Use selected provider_id; if not set, try current grid selection or a single saved profile fallback
		name = (self.profile_var.get() or "").strip()
		cfg = None
		if not name and hasattr(self, "saved_tree"):
			try:
				selection = self.saved_tree.selection()
				if selection:
					item_id = selection[0]
					pid = self.saved_tree.set(item_id, "provider_id") or (
						self.saved_tree.item(item_id, "values")[0] if self.saved_tree.item(item_id, "values") else ""
					)
					name = (pid or "").strip()
			except Exception:
				pass
		if not name:
			try:
				profiles = self.ctrl.list_profiles()
				if len(profiles) == 1:
					name = profiles[0]
			except Exception:
				pass
		if name:
			cfg = self.ctrl.load_config(name)
		if not cfg:
			messagebox.showwarning("Warning", "Select a saved configuration from the list")
			return
		prov_name = cfg.get("provider", "")
		prov_id = cfg.get("provider_id", "")
		self.provider_var.set(prov_name or prov_id)
		self.on_provider_change()
		model = cfg.get("model", "")
		if model:
			self._select_model_in_list(model)
		self.key_var.set(cfg.get("api_key", ""))
		if "bedrock" in (prov_name or prov_id).lower():
			self.aws_key_id_var.set(cfg.get("aws_access_key_id", ""))
			self.aws_secret_key_var.set(cfg.get("aws_secret_access_key", ""))
		else:
			self.aws_key_id_var.set("")
			self.aws_secret_key_var.set("")
		self.status("Loaded successfully", "success")

	def delete_selected(self):
		name = (self.profile_var.get() or "").strip()
		provider_label = name
		try:
			if hasattr(self, "saved_tree"):
				selection = self.saved_tree.selection()
				if (not name) and selection:
					item_id = selection[0]
					pid = self.saved_tree.set(item_id, "provider_id") or (
						self.saved_tree.item(item_id, "values")[0] if self.saved_tree.item(item_id, "values") else ""
					)
					name = str(pid).strip()
					provider_label = self.saved_tree.set(item_id, "provider") or name
			elif name and hasattr(self, "saved_tree") and self.saved_tree.exists(name):
				provider_label = self.saved_tree.set(name, "provider") or name
		except Exception:
			pass
		if not name:
			messagebox.showwarning("Warning", "Select a saved configuration to delete")
			return
		# Fallback: if provider_label is still the id, try to resolve via grid rows
		if hasattr(self, "saved_tree") and provider_label == name:
			try:
				for iid in self.saved_tree.get_children(""):
					if (self.saved_tree.set(iid, "provider_id") or "").strip() == name:
						prov_txt = self.saved_tree.set(iid, "provider")
						if prov_txt:
							provider_label = prov_txt
						break
			except Exception:
				pass
		if messagebox.askyesno("Confirm Delete", f"Delete saved configuration '{provider_label}'?"):
			if self.ctrl.delete_config(name):
				self.status("Configuration Deleted!", "success")
				self.refresh_saved_configs()
				self.clear_fields_only()
			else:
				self.status("Delete failed", "error")

	def clear_fields_only(self):
		self.model_var.set("")
		self.endpoint_var.set("")
		self.key_var.set("")
		self.aws_key_id_var.set("")
		self.aws_secret_key_var.set("")
		if hasattr(self, "model_list"):
			self.model_list.delete(0, tk.END)
			self.model_list.selection_clear(0, tk.END)
		if hasattr(self, "api_key_frame"):
			try:
				if not self.api_key_frame.winfo_ismapped():
					self.api_key_frame.pack(fill="x", padx=40, pady=(10, 5))
				if hasattr(self, "key_entry"):
					self.key_entry.config(state="normal")
				if hasattr(self, "key_eye"):
					self.key_eye.config(state="normal")
				# Ensure left actions are positioned after API key section
				if hasattr(self, "left_actions"):
					self.left_actions.pack_forget()
					self.left_actions.pack(fill="x", padx=40, pady=(8, 0))
			except Exception:
				pass
		if hasattr(self, "aws_creds_frame"):
			self.aws_creds_frame.pack_forget()
			# Re-pack left actions after removing creds to keep it at bottom
			if hasattr(self, "left_actions"):
				self.left_actions.pack_forget()
				self.left_actions.pack(fill="x", padx=40, pady=(8, 0))
		self.root.geometry(f"{self.base_width}x{self.base_height}")

	def clear(self):
		self.profile_var.set("")
		self.provider_var.set("")
		self.clear_fields_only()
		self.status("Cleared", "info")

	def test_api(self):
		provider = self.provider_var.get().strip()
		endpoint = self.endpoint_var.get().strip()
		api_key = self.key_var.get().strip()
		prov_lower = (provider or "").lower()
		is_no_key = ("ollama" in prov_lower) or ("bedrock" in prov_lower)
		if "bedrock" in prov_lower:
			ak = self.aws_key_id_var.get().strip()
			sk = self.aws_secret_key_var.get().strip()
			if not provider or not endpoint or not ak or not sk:
				messagebox.showwarning("Missing Info", "For Bedrock, select a provider, set region in Endpoint, and enter AWS Key ID and Secret Key.")
				return
		elif not provider or not endpoint or (not is_no_key and not api_key):
			msg = "Please select a provider, ensure endpoint is shown, and enter an API key."
			if is_no_key:
				msg = "Please select a provider and ensure endpoint is shown. API key is not required for this provider."
			messagebox.showwarning("Missing Info", msg)
			return
		ok, detail = self.ctrl.probe_api(
			provider, endpoint, api_key,
			self.aws_key_id_var.get().strip(),
			self.aws_secret_key_var.get().strip(),
		)
		if ok:
			self.status("API key looks valid", "success")
			messagebox.showinfo("Success", detail)
		else:
			self.status("API responded with error", "error")
			messagebox.showerror("Error", detail)

	def move_saved(self, delta: int):
		try:
			if not hasattr(self, "saved_tree"):
				return
			sel = self.saved_tree.selection()
			if not sel:
				self.status("Select a configuration first", "info")
				return
			iid = sel[0]

			items = list(self.saved_tree.get_children(""))
			if not items or iid not in items:
				return
			cur_idx = items.index(iid)
			n = len(items)
			new_idx = max(0, min(n - 1, cur_idx + int(delta)))
			if new_idx == cur_idx:
				self.status("Already at edge", "info")
				return

			pid = self.saved_tree.set(iid, "provider_id") or (
				self.saved_tree.item(iid, "values")[0] if self.saved_tree.item(iid, "values") else ""
			)
			if not pid:
				self.status("Unable to determine selected id", "error")
				return

			if hasattr(self.ctrl, "move_config"):
				step = 1 if new_idx > cur_idx else -1
				while cur_idx != new_idx:
					if not self.ctrl.move_config(str(pid), step):
						break
					cur_idx += step
				self.refresh_saved_configs()
				for row in self.saved_tree.get_children(""):
					if (self.saved_tree.set(row, "provider_id") or "") == str(pid):
						self.saved_tree.selection_set(row)
						self.saved_tree.see(row)
						break
				self.status("Order updated", "success")
			else:
				self.saved_tree.move(iid, "", new_idx)
				self.saved_tree.selection_set(iid)
				self.saved_tree.see(iid)
				self.status("Reordered (not persisted)", "info")
		except Exception:
			self.status("Move failed", "error")

# -------------------------------------------------------------
# if __name__ == "__main__":
# 	root = tk.Tk()
# 	LLMProviderSelector(root)
# 	root.mainloop()

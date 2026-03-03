import time
import tkinter as tk
from tkinter import scrolledtext
from tkinter import ttk


CARD_BG = '#FFFFFF'
APP_BG = '#EEF2F7'
CARD_BORDER = '#D9E2EC'
CARD_TEXT = '#1F2937'
MUTED_TEXT = '#6B7280'
ACCENT_BG = '#DDEEFF'
PRIMARY_BG = '#3B82F6'
SUCCESS_GREEN = '#22C55E'
OFF_GRAY = '#9CA3AF'
WARNING_BG = '#FFF3E0'
WARNING_TEXT = '#B45309'
BASE_FONT = ('TkDefaultFont', 12)
TITLE_FONT = ('TkDefaultFont', 16, 'bold')
CARD_TITLE_FONT = ('TkDefaultFont', 14, 'bold')
BODY_FONT = ('TkDefaultFont', 12)
SMALL_FONT = ('TkDefaultFont', 11)
LOG_FONT = ('Consolas', 11)


def create_main_window(root, urls, hotkey_initial, handlers):
	root.configure(bg=APP_BG)
	root.option_add('*Font', 'TkDefaultFont 12')

	style = ttk.Style(root)
	try:
		style.theme_use('clam')
	except Exception:
		pass
	style.configure('Main.TFrame', background=APP_BG)
	style.configure(
		'Card.TFrame',
		background=CARD_BG,
		relief='solid',
		borderwidth=1,
		bordercolor=CARD_BORDER,
	)
	style.configure('Primary.TButton', background=PRIMARY_BG, foreground='white', borderwidth=0, padding=(16, 8))
	style.map(
		'Primary.TButton',
		background=[('disabled', '#9CA3AF'), ('active', '#2563EB')],
		foreground=[('disabled', '#F3F4F6')],
	)
	style.configure('Secondary.TButton', background='#E5E7EB', foreground=CARD_TEXT, borderwidth=0, padding=(14, 8))
	style.map('Secondary.TButton', background=[('active', '#D1D5DB')])
	style.configure('Accent.TButton', background=ACCENT_BG, foreground=CARD_TEXT, borderwidth=0, padding=(12, 6))
	style.map('Accent.TButton', background=[('active', '#CDE1FF')])
	style.configure('Ghost.TButton', background=CARD_BG, foreground=CARD_TEXT, borderwidth=0, padding=(8, 4))
	style.map('Ghost.TButton', background=[('active', '#EEF2F7')])
	style.configure('Icon.TButton', background=CARD_BG, foreground=CARD_TEXT, borderwidth=0, padding=(6, 2))
	style.map('Icon.TButton', background=[('active', '#EEF2F7')])
	style.configure('Modern.TEntry', fieldbackground='white', foreground=CARD_TEXT, bordercolor='#CBD5E1', lightcolor='#CBD5E1', darkcolor='#CBD5E1')
	style.map('Modern.TEntry', fieldbackground=[('readonly', '#F8FAFC')])

	main_view = tk.Frame(root, bg=APP_BG)
	main_view.pack(fill=tk.BOTH, expand=True)

	viewport_canvas = tk.Canvas(main_view, bg=APP_BG, highlightthickness=0, bd=0)
	viewport_scrollbar = ttk.Scrollbar(main_view, orient=tk.VERTICAL, command=viewport_canvas.yview)
	viewport_canvas.configure(yscrollcommand=viewport_scrollbar.set)
	viewport_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
	viewport_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

	main_frame = tk.Frame(viewport_canvas, bg=APP_BG, padx=16, pady=14)
	viewport_window_id = viewport_canvas.create_window((0, 0), window=main_frame, anchor='nw')

	main_frame.bind(
		'<Configure>',
		lambda _: viewport_canvas.configure(scrollregion=viewport_canvas.bbox('all')),
	)
	viewport_canvas.bind(
		'<Configure>',
		lambda event: viewport_canvas.itemconfig(viewport_window_id, width=event.width),
	)

	def on_mousewheel(event):
		delta = event.delta
		if delta == 0:
			return
		viewport_canvas.yview_scroll(int(-delta / 120), 'units')

	def on_mousewheel_linux_up(_event):
		viewport_canvas.yview_scroll(-1, 'units')

	def on_mousewheel_linux_down(_event):
		viewport_canvas.yview_scroll(1, 'units')

	root.bind_all('<MouseWheel>', on_mousewheel)
	root.bind_all('<Button-4>', on_mousewheel_linux_up)
	root.bind_all('<Button-5>', on_mousewheel_linux_down)

	monitor_items_ref = {'value': urls if isinstance(urls, list) else []}
	poe_sess_var = tk.StringVar()
	hotkey_var = tk.StringVar(value=hotkey_initial)
	name_var = tk.StringVar()
	url_var = tk.StringVar()
	status_var = tk.StringVar(value='準備就緒 | 未啟動')
	show_session_ref = {'value': False}
	hotkey_capture_ref = {
		'capturing': False,
		'binding_id': None,
	}

	def create_card(parent):
		card_outer = tk.Frame(parent, bg=APP_BG)
		card_outer.pack(fill=tk.X, pady=7)
		card = ttk.Frame(card_outer, style='Card.TFrame', padding=(0, 0))
		card.pack(fill=tk.X, padx=2, pady=1)
		return card

	def create_title(parent, text):
		return tk.Label(
			parent,
			text=text,
			bg=CARD_BG,
			fg=CARD_TEXT,
			font=CARD_TITLE_FONT,
		)

	def on_add_monitor_item():
		if callable(handlers.get('on_add_url_item')):
			handlers['on_add_url_item']()

	def on_hotkey_apply():
		if callable(handlers.get('on_apply_hotkey')):
			handlers['on_apply_hotkey']()
		refresh_hotkey_button_text()

	def on_toggle_session_visibility():
		show_session_ref['value'] = not show_session_ref['value']
		if show_session_ref['value']:
			poe_entry.config(show='')
			show_btn_text.set('🙈')
		else:
			poe_entry.config(show='•')
			show_btn_text.set('👁')

	def refresh_hotkey_button_text():
		value = hotkey_var.get().strip()
		if value == '':
			value = '尚未設定'
		hotkey_btn_text.set(f'設定熱鍵（目前：{value}）')

	def format_hotkey_from_event(event):
		modifiers = []
		state = int(event.state)
		if state & 0x0004:
			modifiers.append('ctrl')
		if state & 0x0008:
			modifiers.append('alt')
		if state & 0x0001:
			modifiers.append('shift')

		key_name = str(event.keysym).lower()
		if key_name in {
			'shift_l', 'shift_r',
			'control_l', 'control_r',
			'alt_l', 'alt_r',
			'mode_switch', 'iso_level3_shift',
			'meta_l', 'meta_r',
		}:
			return ''
		if key_name == 'space':
			key_name = 'space'
		if key_name == 'escape':
			key_name = 'esc'
		if key_name.startswith('kp_'):
			key_name = key_name.replace('kp_', 'num')

		parts = [*modifiers, key_name]
		parts = [part for part in parts if part != '']
		return '+'.join(parts)

	def stop_hotkey_capture():
		if hotkey_capture_ref['binding_id'] is not None:
			root.unbind('<KeyPress>', hotkey_capture_ref['binding_id'])
		hotkey_capture_ref['capturing'] = False
		hotkey_capture_ref['binding_id'] = None
		hotkey_hint_var.set('範例：ctrl+alt+t, f12, shift+z')
		record_hotkey_btn.config(state=tk.NORMAL)

	def on_hotkey_keypress(event):
		combo = format_hotkey_from_event(event)
		if combo == '':
			return
		hotkey_var.set(combo)
		refresh_hotkey_button_text()
		stop_hotkey_capture()
		on_hotkey_apply()

	def start_hotkey_capture():
		if hotkey_capture_ref['capturing']:
			return
		hotkey_capture_ref['capturing'] = True
		hotkey_hint_var.set('錄製中：請直接按下你要設定的快捷鍵組合')
		record_hotkey_btn.config(state=tk.DISABLED)
		bind_id = root.bind('<KeyPress>', on_hotkey_keypress)
		hotkey_capture_ref['binding_id'] = bind_id

	def set_monitor_items(items):
		monitor_items_ref['value'] = items if isinstance(items, list) else []
		render_monitor_rows()

	def render_monitor_rows():
		for child in rows_container.winfo_children():
			child.destroy()

		items = monitor_items_ref['value']
		if len(items) == 0:
			empty_label = tk.Label(
				rows_container,
				text='尚未新增想要live search的網址',
				bg=CARD_BG,
				fg=MUTED_TEXT,
				font=BODY_FONT,
				pady=10,
			)
			empty_label.pack(fill=tk.X)
		else:
			for index, item in enumerate(items):
				render_monitor_row(rows_container, index, item)

		rows_container.update_idletasks()
		rows_canvas.config(scrollregion=rows_canvas.bbox('all'))

	def render_monitor_row(parent, index, item):
		enabled = bool(item.get('enabled', True))
		name = str(item.get('name', '')).strip()
		if name == '':
			name = str(item.get('url', '')).strip()

		status_color = SUCCESS_GREEN if enabled else OFF_GRAY
		status_text = 'live search中' if enabled else '未啟動'

		row = tk.Frame(parent, bg=CARD_BG, pady=5)
		row.pack(fill=tk.X)

		indicator = tk.Canvas(row, width=16, height=16, bg=CARD_BG, bd=0, highlightthickness=0)
		indicator.create_oval(3, 3, 13, 13, fill=status_color, outline=status_color)
		indicator.pack(side=tk.LEFT, padx=(4, 6))

		status_label = tk.Label(
			row,
			text=status_text,
			bg=CARD_BG,
			fg=status_color,
			font=('TkDefaultFont', 12, 'bold'),
			width=8,
			anchor='w',
		)
		status_label.pack(side=tk.LEFT)

		name_label = tk.Label(
			row,
			text=name,
			bg=CARD_BG,
			fg=CARD_TEXT,
			font=BODY_FONT,
			anchor='w',
		)
		name_label.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(8, 0))

		toggle_btn = ttk.Button(
			row,
			text='關閉' if enabled else '啟用',
			command=lambda: handlers['on_toggle_url_item'](index),
			cursor='hand2',
			style='Secondary.TButton',
		)
		toggle_btn.pack(side=tk.RIGHT, padx=(6, 0))

		delete_btn = ttk.Button(
			row,
			text='🗑',
			command=lambda: handlers['on_remove_url_item'](index),
			cursor='hand2',
			style='Icon.TButton',
		)
		delete_btn.pack(side=tk.RIGHT)

		copy_btn = ttk.Button(
			row,
			text='⧉',
			command=lambda: handlers['on_copy_url_item'](index),
			cursor='hand2',
			style='Icon.TButton',
		)
		copy_btn.pack(side=tk.RIGHT)

		edit_btn = ttk.Button(
			row,
			text='✎',
			command=lambda: handlers['on_edit_url_item'](index),
			cursor='hand2',
			style='Icon.TButton',
		)
		edit_btn.pack(side=tk.RIGHT)

		ttk.Separator(parent, orient=tk.HORIZONTAL).pack(fill=tk.X, padx=4, pady=2)

	header_card = create_card(main_frame)
	header_inner = tk.Frame(header_card, bg=CARD_BG, padx=14, pady=14)
	header_inner.pack(fill=tk.X)
	tk.Label(
		header_inner,
		text='POE 交易搶道具助手',
		bg=CARD_BG,
		fg=CARD_TEXT,
		font=TITLE_FONT,
	).pack(anchor='center')
	tk.Label(
		header_inner,
		text='新增你的 live search 網址 → 設定熱鍵 → 啟動 → 看到好貨就按熱鍵搶！\n完全自動掃描多個分頁，精準點擊 Travel to Hideout',
		bg=CARD_BG,
		fg=MUTED_TEXT,
		font=SMALL_FONT,
		justify='center',
	).pack(pady=(6, 0))

	url_card = create_card(main_frame)
	url_inner = tk.Frame(url_card, bg=CARD_BG, padx=12, pady=10)
	url_inner.pack(fill=tk.BOTH, expand=True)
	create_title(url_inner, 'Live Search 網址').pack(anchor='w', pady=(0, 8))

	add_row = tk.Frame(url_inner, bg=CARD_BG)
	add_row.pack(fill=tk.X, pady=(0, 8))
	name_entry = ttk.Entry(add_row, textvariable=name_var, width=24, style='Modern.TEntry')
	name_entry.pack(side=tk.LEFT, padx=(0, 6))
	name_entry.insert(0, '')
	url_entry = ttk.Entry(add_row, textvariable=url_var, style='Modern.TEntry')
	url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 6))
	add_btn = ttk.Button(
		add_row,
		text='＋ 新增想要live search的網址',
		command=on_add_monitor_item,
		cursor='hand2',
		style='Accent.TButton',
	)
	add_btn.pack(side=tk.RIGHT)

	header_row = tk.Frame(url_inner, bg=CARD_BG)
	header_row.pack(fill=tk.X)
	tk.Label(header_row, text='狀態', bg=CARD_BG, fg=MUTED_TEXT, width=10, anchor='w').pack(side=tk.LEFT, padx=(4, 0))
	tk.Label(header_row, text='自訂名稱', bg=CARD_BG, fg=MUTED_TEXT, anchor='w').pack(side=tk.LEFT, fill=tk.X, expand=True)
	tk.Label(header_row, text='操作', bg=CARD_BG, fg=MUTED_TEXT, anchor='e').pack(side=tk.RIGHT)
	ttk.Separator(url_inner, orient=tk.HORIZONTAL).pack(fill=tk.X, pady=(4, 4))

	rows_wrap = tk.Frame(url_inner, bg=CARD_BG)
	rows_wrap.pack(fill=tk.BOTH, expand=True)

	rows_canvas = tk.Canvas(rows_wrap, bg=CARD_BG, highlightthickness=0, bd=0, height=190)
	rows_scrollbar = ttk.Scrollbar(rows_wrap, orient=tk.VERTICAL, command=rows_canvas.yview)
	rows_canvas.configure(yscrollcommand=rows_scrollbar.set)
	rows_canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
	rows_scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

	rows_container = tk.Frame(rows_canvas, bg=CARD_BG)
	rows_window_id = rows_canvas.create_window((0, 0), window=rows_container, anchor='nw')
	rows_container.bind(
		'<Configure>',
		lambda _: rows_canvas.configure(scrollregion=rows_canvas.bbox('all')),
	)
	rows_canvas.bind(
		'<Configure>',
		lambda event: rows_canvas.itemconfig(rows_window_id, width=event.width),
	)

	controls_row = tk.Frame(url_inner, bg=CARD_BG)
	controls_row.pack(fill=tk.X, pady=(8, 0))

	ttk.Button(
		controls_row,
		text='我的最愛',
		command=handlers['on_favorites'],
		cursor='hand2',
		style='Secondary.TButton',
	).pack(side=tk.LEFT)

	ttk.Button(
		controls_row,
		text='重新載入所有啟用網址',
		command=handlers['on_refresh_tabs'],
		cursor='hand2',
		style='Secondary.TButton',
	).pack(side=tk.RIGHT)

	hotkey_card = create_card(main_frame)
	hotkey_inner = tk.Frame(hotkey_card, bg=CARD_BG, padx=12, pady=10)
	hotkey_inner.pack(fill=tk.X)
	create_title(hotkey_inner, '自訂熱鍵').pack(anchor='w')
	hotkey_btn_text = tk.StringVar()
	record_hotkey_btn = ttk.Button(
		hotkey_inner,
		textvariable=hotkey_btn_text,
		command=start_hotkey_capture,
		cursor='hand2',
		style='Accent.TButton',
	)
	record_hotkey_btn.pack(fill=tk.X, pady=(8, 4))
	hotkey_hint_var = tk.StringVar(value='範例：ctrl+alt+t, f12, shift+z')
	tk.Label(
		hotkey_inner,
		textvariable=hotkey_hint_var,
		bg=CARD_BG,
		fg=MUTED_TEXT,
		anchor='w',
	).pack(fill=tk.X)
	refresh_hotkey_button_text()

	sess_card = create_card(main_frame)
	sess_inner = tk.Frame(sess_card, bg=CARD_BG, padx=12, pady=10)
	sess_inner.pack(fill=tk.X)
	create_title(sess_inner, 'POESESSID（從瀏覽器 Cookie 貼上）').pack(anchor='w')
	tk.Label(
		sess_inner,
		text='只在本機使用，請勿分享給他人。',
		bg=CARD_BG,
		fg=MUTED_TEXT,
		anchor='w',
	).pack(fill=tk.X, pady=(4, 8))

	sess_entry_row = tk.Frame(sess_inner, bg=CARD_BG)
	sess_entry_row.pack(fill=tk.X)
	poe_entry = ttk.Entry(sess_entry_row, textvariable=poe_sess_var, show='•', style='Modern.TEntry')
	poe_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 8))
	show_btn_text = tk.StringVar(value='👁')
	ttk.Button(
		sess_entry_row,
		textvariable=show_btn_text,
		command=on_toggle_session_visibility,
		cursor='hand2',
		style='Secondary.TButton',
	).pack(side=tk.RIGHT)

	warning_card = create_card(main_frame)
	warning_inner = tk.Frame(warning_card, bg=WARNING_BG, padx=12, pady=10)
	warning_inner.pack(fill=tk.X)
	tk.Label(
		warning_inner,
		text='安全性警告',
		bg=WARNING_BG,
		fg=WARNING_TEXT,
		font=('TkDefaultFont', 12, 'bold'),
		anchor='w',
	).pack(fill=tk.X)
	tk.Label(
		warning_inner,
		text='⚠ 重要：POESESSID 是您的帳戶憑證，請絕對不要分享給任何人，防止帳戶被盜！',
		bg=WARNING_BG,
		fg=WARNING_TEXT,
		anchor='w',
	).pack(fill=tk.X, pady=(6, 0))

	control_card = create_card(main_frame)
	control_inner = tk.Frame(control_card, bg=CARD_BG, padx=12, pady=10)
	control_inner.pack(fill=tk.X)
	create_title(control_inner, '控制中心').pack(anchor='w', pady=(0, 8))

	control_row = tk.Frame(control_inner, bg=CARD_BG)
	control_row.pack(fill=tk.X)
	start_btn = ttk.Button(
		control_row,
		text='🚀 啟動（開啟 Chrome）',
		command=handlers['on_start'],
		cursor='hand2',
		style='Primary.TButton',
	)
	start_btn.pack(side=tk.LEFT, padx=(0, 10))

	stop_btn = ttk.Button(
		control_row,
		text='停止',
		command=handlers['on_stop'],
		cursor='hand2',
		style='Secondary.TButton',
		state=tk.DISABLED,
	)
	stop_btn.pack(side=tk.LEFT, padx=(0, 10))

	ttk.Button(
		control_row,
		text='手動掃描一次',
		command=handlers['on_manual_scan'],
		cursor='hand2',
		style='Secondary.TButton',
	).pack(side=tk.LEFT)

	log_card = create_card(main_frame)
	log_inner = tk.Frame(log_card, bg=CARD_BG, padx=12, pady=10)
	log_inner.pack(fill=tk.BOTH, expand=True)
	create_title(log_inner, '操作記錄').pack(anchor='w')
	log_text = scrolledtext.ScrolledText(
		log_inner,
		height=10,
		state=tk.DISABLED,
		font=LOG_FONT,
		bg='white',
		fg='black',
	)
	log_text.pack(fill=tk.BOTH, expand=True, pady=(8, 0))

	status_bar = tk.Label(
		root,
		textvariable=status_var,
		bg='#E5E7EB',
		fg=CARD_TEXT,
		anchor='w',
		padx=10,
		pady=5,
	)
	status_bar.pack(side=tk.BOTTOM, fill=tk.X)

	set_monitor_items(monitor_items_ref['value'])

	def append_log(message):
		log_text.configure(state=tk.NORMAL)
		log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
		log_text.see(tk.END)
		log_text.configure(state=tk.DISABLED)

	def get_entry_url():
		return url_var.get().strip()

	def get_entry_name():
		return name_var.get().strip()

	def clear_entry():
		url_var.set('')
		name_var.set('')

	def set_entry_url(value):
		url_var.set(value)

	def set_status(text):
		status_var.set(text)

	def set_start_enabled(enabled):
		start_btn.config(state=tk.NORMAL if enabled else tk.DISABLED)

	def set_stop_enabled(enabled):
		stop_btn.config(state=tk.NORMAL if enabled else tk.DISABLED)

	return {
		'append_log': append_log,
		'set_urls': set_monitor_items,
		'get_entry_url': get_entry_url,
		'get_entry_name': get_entry_name,
		'clear_entry': clear_entry,
		'set_entry_url': set_entry_url,
		'get_selected_index': lambda: None,
		'set_status': set_status,
		'set_start_enabled': set_start_enabled,
		'set_stop_enabled': set_stop_enabled,
		'get_hotkey_var': lambda: hotkey_var,
		'get_poe_sessid': lambda: poe_sess_var.get().strip(),
	}

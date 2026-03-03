import time
import tkinter as tk
from tkinter import ttk, scrolledtext


def create_main_window(root, urls, hotkey_initial, handlers):
	"""
	handlers: on_add_url, on_remove_url, on_refresh_tabs, on_apply_hotkey, on_start, on_stop
	回傳一個 object 提供：append_log, set_urls, get_entry_url, clear_entry, get_selected_index,
	set_status, set_start_enabled, set_stop_enabled, get_hotkey_var
	"""
	root.configure(bg='white')

	main_frame = ttk.Frame(root, padding=15)
	main_frame.pack(fill=tk.BOTH, expand=True)

	ttk.Label(main_frame, text='POE 交易搶道具助手', font=('Microsoft YaHei', 18, 'bold')).pack(pady=10)
	ttk.Label(
		main_frame,
		text='新增你的 live search 網址 → 設定熱鍵 → 啟動 → 看到好貨就按熱鍵搶！\n完全自動掃描多個分頁，精準點擊 Travel to Hideout',
		font=('Microsoft YaHei', 10),
		foreground='gray',
	).pack(pady=(0, 15))

	url_frame = ttk.LabelFrame(main_frame, text='監控的 Live Search 網址', padding=10)
	url_frame.pack(fill=tk.BOTH, expand=True, pady=10)

	add_frame = ttk.Frame(url_frame)
	add_frame.pack(fill=tk.X, pady=(0, 8))
	url_entry = ttk.Entry(add_frame, width=70)
	url_entry.pack(side=tk.LEFT, fill=tk.X, expand=True, padx=(0, 5))
	ttk.Button(add_frame, text='＋ 新增網址', command=handlers['on_add_url']).pack(side=tk.RIGHT)

	list_frame = ttk.Frame(url_frame)
	list_frame.pack(fill=tk.BOTH, expand=True)
	url_listbox = tk.Listbox(list_frame, height=8, font=('Microsoft YaHei', 10), bg='white', fg='black')
	scrollbar = ttk.Scrollbar(list_frame, orient=tk.VERTICAL, command=url_listbox.yview)
	url_listbox.config(yscrollcommand=scrollbar.set)
	url_listbox.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)
	scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

	for u in urls:
		url_listbox.insert(tk.END, u)

	btn_frame = ttk.Frame(url_frame)
	btn_frame.pack(fill=tk.X, pady=8)
	ttk.Button(btn_frame, text='移除選取', command=handlers['on_remove_url']).pack(side=tk.LEFT, padx=(0, 5))
	ttk.Button(btn_frame, text='重新載入所有網址', command=handlers['on_refresh_tabs']).pack(side=tk.LEFT)
	ttk.Button(btn_frame, text='我的最愛', command=handlers['on_favorites']).pack(side=tk.LEFT, padx=(5, 0))

	hotkey_frame = ttk.LabelFrame(main_frame, text='自訂熱鍵（搶道具時按這個）', padding=10)
	hotkey_frame.pack(fill=tk.X, pady=10)
	ttk.Label(hotkey_frame, text='熱鍵格式範例：ctrl+alt+t 、 f12 、 shift+z', font=('Microsoft YaHei', 9)).pack(anchor=tk.W)
	hk_entry_frame = ttk.Frame(hotkey_frame)
	hk_entry_frame.pack(fill=tk.X, pady=5)
	hotkey_var = tk.StringVar(value=hotkey_initial)
	ttk.Entry(hk_entry_frame, textvariable=hotkey_var, width=30, font=('Microsoft YaHei', 11)).pack(side=tk.LEFT, padx=(0, 10))
	ttk.Button(hk_entry_frame, text='套用熱鍵', command=handlers['on_apply_hotkey']).pack(side=tk.LEFT)

	sess_frame = ttk.LabelFrame(main_frame, text='POESESSID（從瀏覽器 Cookie 貼上）', padding=10)
	sess_frame.pack(fill=tk.X, pady=10)
	ttk.Label(sess_frame, text='只在本機使用，請勿分享給他人。', font=('Microsoft YaHei', 9)).pack(anchor=tk.W)
	sess_entry_frame = ttk.Frame(sess_frame)
	sess_entry_frame.pack(fill=tk.X, pady=5)
	poe_sess_var = tk.StringVar()
	ttk.Entry(sess_entry_frame, textvariable=poe_sess_var, width=50, font=('Microsoft YaHei', 10)).pack(side=tk.LEFT, padx=(0, 10))

	control_frame = ttk.Frame(main_frame)
	control_frame.pack(pady=15)
	start_btn = ttk.Button(control_frame, text='啟動（開啟 Chrome）', command=handlers['on_start'], style='Accent.TButton')
	start_btn.pack(side=tk.LEFT, padx=10)
	stop_btn = ttk.Button(control_frame, text='停止', command=handlers['on_stop'], state=tk.DISABLED)
	stop_btn.pack(side=tk.LEFT, padx=10)
	manual_btn = ttk.Button(control_frame, text='手動掃描一次', command=handlers['on_manual_scan'])
	manual_btn.pack(side=tk.LEFT, padx=10)

	log_frame = ttk.LabelFrame(main_frame, text='操作記錄（這裡會顯示搶到沒有）', padding=10)
	log_frame.pack(fill=tk.BOTH, expand=True, pady=10)
	log_text = scrolledtext.ScrolledText(log_frame, height=12, state=tk.DISABLED, font=('Consolas', 10), bg='white', fg='black')
	log_text.pack(fill=tk.BOTH, expand=True)

	status_var = tk.StringVar(value='準備就緒 | 未啟動')
	ttk.Label(root, textvariable=status_var, relief=tk.SUNKEN, anchor=tk.W, padding=5).pack(side=tk.BOTTOM, fill=tk.X)

	style = ttk.Style()
	try:
		style.theme_use('clam')
	except Exception:
		pass
	style.configure('Accent.TButton', foreground='white', background='#0078D4')

	def append_log(message):
		log_text.configure(state=tk.NORMAL)
		log_text.insert(tk.END, f"[{time.strftime('%H:%M:%S')}] {message}\n")
		log_text.see(tk.END)
		log_text.configure(state=tk.DISABLED)

	def set_urls(url_list):
		url_listbox.delete(0, tk.END)
		for u in url_list:
			url_listbox.insert(tk.END, u)

	def get_entry_url():
		return url_entry.get().strip()

	def clear_entry():
		url_entry.delete(0, tk.END)

	def set_entry_url(value):
		url_entry.delete(0, tk.END)
		url_entry.insert(0, value)

	def get_selected_index():
		sel = url_listbox.curselection()
		return sel[0] if sel else None

	def set_status(text):
		status_var.set(text)

	def set_start_enabled(enabled):
		start_btn.config(state=tk.NORMAL if enabled else tk.DISABLED)

	def set_stop_enabled(enabled):
		stop_btn.config(state=tk.NORMAL if enabled else tk.DISABLED)

	return {
		'append_log': append_log,
		'set_urls': set_urls,
		'get_entry_url': get_entry_url,
		'clear_entry': clear_entry,
		'set_entry_url': set_entry_url,
		'get_selected_index': get_selected_index,
		'set_status': set_status,
		'set_start_enabled': set_start_enabled,
		'set_stop_enabled': set_stop_enabled,
		'get_hotkey_var': lambda: hotkey_var,
		'get_poe_sessid': lambda: poe_sess_var.get().strip(),
	}

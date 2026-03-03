import queue
import tkinter as tk
from tkinter import messagebox

from src import config
from src import browser
from src import scanner
from src import hotkey
from src.ui import main_window
from src.ui import log_queue


def run():
	root = tk.Tk()
	root.title('POE 交易搶道具助手')
	cfg = config.load_config()
	urls = config.load_urls()
	favorites = cfg.get('favorites', [])
	if not isinstance(favorites, list):
		favorites = []
	root.geometry(f"{cfg.get('windowWidth', 900)}x{cfg.get('windowHeight', 700)}")
	root.resizable(True, True)

	event_queue = queue.Queue()
	driver = [None]
	current_hotkey = [cfg.get('hotkey', config.DEFAULT_HOTKEY)]
	selector = cfg.get('buttonSelector', config.DEFAULT_SELECTOR)
	ui = [None]

	def put_log(message):
		event_queue.put(log_queue.make_log_event(message))

	def do_trigger_scan():
		if driver[0] is None:
			put_log('瀏覽器未啟動')
			return
		put_log('開始掃描所有分頁...')
		_success, message = scanner.scan_and_click_travel_to_hideout(driver[0], selector)
		put_log(message)

	def on_log(message):
		if ui[0]:
			ui[0]['append_log'](message)

	def on_trigger_scan():
		do_trigger_scan()

	def poll():
		log_queue.process_queue(event_queue, on_log, on_trigger_scan)
		root.after(log_queue.POLL_MS, poll)

	handlers = {
		'on_add_url': lambda: handle_add_url(ui[0], urls, put_log),
		'on_remove_url': lambda: handle_remove_url(ui[0], urls, put_log),
		'on_refresh_tabs': lambda: handle_refresh_tabs(ui[0], driver, urls, put_log),
		'on_apply_hotkey': lambda: handle_apply_hotkey(ui[0], current_hotkey, driver, event_queue, put_log),
		'on_start': lambda: handle_start(ui[0], driver, urls, current_hotkey, selector, event_queue, put_log),
		'on_stop': lambda: handle_stop(ui[0], current_hotkey, put_log),
		'on_manual_scan': lambda: event_queue.put(log_queue.make_trigger_scan_event()),
		'on_favorites': lambda: handle_show_favorites(root, ui[0], favorites, put_log),
	}

	ui[0] = main_window.create_main_window(root, urls, current_hotkey[0], handlers)
	root.protocol('WM_DELETE_WINDOW', lambda: on_closing(root, driver, current_hotkey, ui[0]))
	poll()
	root.mainloop()


def is_driver_alive(driver):
	if driver is None:
		return False
	try:
		_ = driver.window_handles
		return True
	except Exception:
		return False


def handle_show_favorites(root, ui_handle, favorites, put_log):
	window = tk.Toplevel(root)
	window.title('我的最愛 - Live Search')
	window.geometry('420x360')
	window.resizable(False, False)

	name_label = tk.Label(window, text='名稱：')
	name_label.pack(anchor=tk.W, padx=10, pady=(10, 0))
	name_entry = tk.Entry(window, width=40)
	name_entry.pack(fill=tk.X, padx=10)

	url_label = tk.Label(window, text='網址：')
	url_label.pack(anchor=tk.W, padx=10, pady=(10, 0))
	url_entry = tk.Entry(window, width=40)
	url_entry.pack(fill=tk.X, padx=10)

	if ui_handle:
		current_url = ui_handle['get_entry_url']()
		if current_url:
			url_entry.insert(0, current_url)

	list_label = tk.Label(window, text='已儲存的最愛（雙擊名稱以複製網址並填入輸入框）：')
	list_label.pack(anchor=tk.W, padx=10, pady=(15, 0))

	listbox = tk.Listbox(window, height=10)
	listbox.pack(fill=tk.BOTH, expand=True, padx=10, pady=(5, 10))

	def refresh_list():
		listbox.delete(0, tk.END)
		for fav in favorites:
			name = fav.get('name', '')
			url = fav.get('url', '')
			if name:
				listbox.insert(tk.END, name)
			else:
				listbox.insert(tk.END, url)

	def add_favorite():
		name = name_entry.get().strip()
		url = url_entry.get().strip()
		if not url:
			messagebox.showwarning('錯誤', '請輸入網址')
			return
		if not config.is_valid_trade_url(url):
			messagebox.showwarning('錯誤', '請輸入有效的 pathofexile.tw/trade/search 網址')
			return
		if not name:
			name = url
		favorites.append({
			'name': name,
			'url': url,
		})
		config.save_favorites(favorites)
		refresh_list()
		name_entry.delete(0, tk.END)
		url_entry.delete(0, tk.END)
		put_log(f'已新增最愛：{name}')

	def on_select(event):
		selection = listbox.curselection()
		if not selection:
			return
		index = selection[0]
		if index < 0 or index >= len(favorites):
			return
		fav = favorites[index]
		url = fav.get('url', '')
		if not url:
			return
		try:
			root.clipboard_clear()
			root.clipboard_append(url)
		except Exception:
			pass
		name = fav.get('name', url)
		put_log(f'已選取最愛「{name}」，網址已複製到剪貼簿')

	add_btn = tk.Button(window, text='＋ 新增最愛', command=add_favorite)
	add_btn.pack(pady=(0, 5))

	listbox.bind('<Double-Button-1>', on_select)

	refresh_list()


def handle_add_url(ui_handle, urls, put_log):
	url = ui_handle['get_entry_url']()
	if not url:
		messagebox.showwarning('錯誤', '請輸入網址')
		return
	if not config.is_valid_trade_url(url):
		messagebox.showwarning('錯誤', '請輸入有效的 pathofexile.tw/trade/search 網址')
		return
	if url in urls:
		messagebox.showwarning('錯誤', '該網址已在清單中')
		return
	urls.append(url)
	config.save_urls(urls)
	ui_handle['set_urls'](urls)
	ui_handle['clear_entry']()
	put_log('已新增網址')


def handle_remove_url(ui_handle, urls, put_log):
	idx = ui_handle['get_selected_index']()
	if idx is None:
		messagebox.showwarning('錯誤', '請先選取要移除的網址')
		return
	del urls[idx]
	config.save_urls(urls)
	ui_handle['set_urls'](urls)
	put_log('已移除網址')


def handle_refresh_tabs(ui_handle, driver_ref, urls, put_log):
	if not is_driver_alive(driver_ref[0]):
		driver_ref[0] = None
		ui_handle['set_start_enabled'](True)
		ui_handle['set_stop_enabled'](False)
		ui_handle['set_status']('瀏覽器已關閉')
		put_log('偵測到瀏覽器已關閉，請重新啟動監控')
		messagebox.showwarning('尚未啟動', '請先按「啟動」開啟瀏覽器')
		return
	put_log('正在重新載入所有網址...')
	browser.refresh_tabs(driver_ref[0], urls)
	put_log('所有 live search 已重新載入完畢')


def handle_apply_hotkey(ui_handle, current_hotkey_ref, driver_ref, event_queue, put_log):
	new_hotkey = ui_handle['get_hotkey_var']().get().strip()
	if not new_hotkey:
		messagebox.showerror('錯誤', '熱鍵不能空白')
		return
	if new_hotkey == current_hotkey_ref[0]:
		messagebox.showinfo('提示', '已是目前熱鍵')
		return
	if driver_ref[0] is not None:
		try:
			hotkey.add_hotkey(new_hotkey, lambda: event_queue.put(log_queue.make_trigger_scan_event()))
		except Exception as e:
			messagebox.showerror('熱鍵錯誤', f'無法設定熱鍵：{e}')
			return
		hotkey.remove_hotkey(current_hotkey_ref[0])
		put_log(f'熱鍵已更新為：{new_hotkey}')
	current_hotkey_ref[0] = new_hotkey
	cfg = config.load_config()
	cfg['hotkey'] = new_hotkey
	config.save_config(cfg)
	messagebox.showinfo('成功', f'熱鍵已設定為：{new_hotkey}\n看到好貨就按這個鍵！')


def handle_start(ui_handle, driver_ref, urls, current_hotkey_ref, selector, event_queue, put_log):
	if driver_ref[0] is not None:
		if is_driver_alive(driver_ref[0]):
			put_log('瀏覽器已經開啟')
			return
		driver_ref[0] = None
		ui_handle['set_start_enabled'](True)
		ui_handle['set_stop_enabled'](False)
		ui_handle['set_status']('瀏覽器已關閉，重新啟動中...')
		put_log('偵測到先前的瀏覽器已關閉，準備重新啟動')
	try:
		put_log('正在啟動 Chrome 並載入所有網址...')
		driver_ref[0] = browser.create_driver()
		poe_sessid = ''
		if ui_handle and 'get_poe_sessid' in ui_handle:
			poe_sessid = ui_handle['get_poe_sessid']()
		if poe_sessid:
			browser.apply_poe_sessid(driver_ref[0], poe_sessid)
		browser.open_urls(driver_ref[0], urls)
	except Exception as e:
		put_log(f'啟動失敗：{e}')
		messagebox.showerror('啟動失敗', f'無法開啟 Chrome：{str(e)}\n\n請確認已安裝 Chrome 瀏覽器')
		if driver_ref[0]:
			browser.quit_driver(driver_ref[0])
			driver_ref[0] = None
		return

	try:
		hotkey.add_hotkey(
			current_hotkey_ref[0],
			lambda: event_queue.put(log_queue.make_trigger_scan_event()),
		)
	except Exception as e:
		put_log(f'熱鍵啟用失敗：{e}')
		messagebox.showwarning(
			'熱鍵啟用失敗',
			'瀏覽器已啟動，但熱鍵無法啟用。\n請改用「手動掃描一次」按鈕觸發掃描。',
		)

	ui_handle['set_start_enabled'](False)
	ui_handle['set_stop_enabled'](True)
	ui_handle['set_status'](f'監控中 | 熱鍵：{current_hotkey_ref[0]} | {len(urls)} 個分頁')
	put_log('瀏覽器啟動成功！所有 live search 已載入')
	put_log(f'看到想要的道具就按【{current_hotkey_ref[0]}】立即搶！')


def handle_stop(ui_handle, current_hotkey_ref, put_log):
	hotkey.remove_hotkey(current_hotkey_ref[0])
	ui_handle['set_start_enabled'](True)
	ui_handle['set_stop_enabled'](False)
	ui_handle['set_status']('熱鍵已停止 | 瀏覽器仍開啟中')
	put_log('熱鍵已停止（可重新套用或重新啟動）')


def on_closing(root, driver_ref, current_hotkey_ref, ui_handle):
	if driver_ref[0] is not None:
		if not messagebox.askokcancel('關閉程式', '確定要關閉程式並結束 Chrome 嗎？'):
			return
		try:
			hotkey.remove_hotkey(current_hotkey_ref[0])
		except Exception:
			pass
		browser.quit_driver(driver_ref[0])
		driver_ref[0] = None
	root.destroy()

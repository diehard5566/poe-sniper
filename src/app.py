import queue
import time
import tkinter as tk
from tkinter import messagebox
from tkinter import simpledialog

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
	monitor_items = config.load_urls()
	favorites = cfg.get('favorites', [])
	if not isinstance(favorites, list):
		favorites = []
	root.geometry(f"{cfg.get('windowWidth', 900)}x{cfg.get('windowHeight', 700)}")
	root.resizable(True, True)

	event_queue = queue.Queue()
	driver = [None]
	is_monitoring_active = [False]
	current_hotkey = [cfg.get('hotkey', config.DEFAULT_HOTKEY)]
	selector = cfg.get('buttonSelector', config.DEFAULT_SELECTOR)
	detect_interval_ms = int(cfg.get('detectIntervalMs', 1200))
	notify_throttle_ms = int(cfg.get('notifyThrottleMs', 4500))
	ui = [None]
	page_activity_map = {}
	recent_activity = []

	def put_log(message):
		event_queue.put(log_queue.make_log_event(message))

	def do_trigger_scan():
		if driver[0] is None:
			put_log('瀏覽器未啟動')
			return
		enabled_urls = get_enabled_urls(monitor_items)
		if len(enabled_urls) == 0:
			put_log('目前沒有啟用中的監控網址')
			return
		priority_map = build_monitor_priority_map(monitor_items)
		preferred_urls = build_preferred_urls(recent_activity, priority_map, enabled_urls)
		success, message, clicked_url = scanner.scan_and_click_travel_to_hideout(
			driver[0],
			selector,
			preferred_urls,
		)
		put_log(message)
		if success and clicked_url != '':
			mark_recent_activity_hit(recent_activity, clicked_url)

	def on_log(message):
		if ui[0]:
			ui[0]['append_log'](message)

	def on_trigger_scan():
		do_trigger_scan()

	def poll():
		log_queue.process_queue(event_queue, on_log, on_trigger_scan)
		root.after(log_queue.POLL_MS, poll)

	def detect_new_item_tick():
		if not is_monitoring_active[0]:
			root.after(detect_interval_ms, detect_new_item_tick)
			return
		if not is_driver_alive(driver[0]):
			root.after(detect_interval_ms, detect_new_item_tick)
			return
		now = int(time.time() * 1000)
		candidates = scanner.detect_travel_candidates(driver[0], selector)
		priority_map = build_monitor_priority_map(monitor_items)
		for candidate in candidates:
			url = candidate.get('url', '')
			if url == '':
				continue
			signature = candidate.get('signature', '')
			if signature == '':
				continue
			state = page_activity_map.get(url, {})
			last_signature = str(state.get('signature', ''))
			if last_signature == signature:
				continue
			priority = get_candidate_priority(candidate, priority_map)
			update_recent_activity(
				recent_activity=recent_activity,
				url=url,
				changed_at=now,
				priority=priority,
			)
			last_log_ts = int(state.get('last_log_ts', 0))
			if now - last_log_ts >= notify_throttle_ms:
				put_log(candidate.get('message', '偵測到可搶道具'))
				state['last_log_ts'] = now
			state['signature'] = signature
			state['changed_at'] = now
			state['priority'] = priority
			page_activity_map[url] = state
		root.after(detect_interval_ms, detect_new_item_tick)

	handlers = {
		'on_add_url_item': lambda: handle_add_url_item(ui[0], monitor_items, put_log),
		'on_edit_url_item': lambda index: handle_edit_url_item(root, ui[0], monitor_items, index, put_log),
		'on_remove_url_item': lambda index: handle_remove_url_item(ui[0], monitor_items, index, put_log),
		'on_copy_url_item': lambda index: handle_copy_url_item(root, monitor_items, index, put_log),
		'on_toggle_url_item': lambda index: handle_toggle_url_item(ui[0], monitor_items, index, put_log),
		'on_refresh_tabs': lambda: handle_refresh_tabs(ui[0], driver, monitor_items, put_log),
		'on_apply_hotkey': lambda: handle_apply_hotkey(ui[0], current_hotkey, driver, event_queue, put_log),
		'on_start': lambda: handle_start(ui[0], driver, monitor_items, current_hotkey, selector, event_queue, put_log, is_monitoring_active),
		'on_stop': lambda: handle_stop(ui[0], current_hotkey, put_log, is_monitoring_active),
		'on_manual_scan': lambda: event_queue.put(log_queue.make_trigger_scan_event()),
		'on_favorites': lambda: handle_show_favorites(root, ui[0], favorites, put_log),
	}

	ui[0] = main_window.create_main_window(root, monitor_items, current_hotkey[0], handlers)
	root.protocol('WM_DELETE_WINDOW', lambda: on_closing(root, driver, current_hotkey, ui[0]))
	poll()
	detect_new_item_tick()
	root.mainloop()


def is_driver_alive(driver):
	return browser.is_session_alive(driver)


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


def get_enabled_monitor_items(monitor_items):
	return [item for item in monitor_items if bool(item.get('enabled', True))]


def get_enabled_urls(monitor_items):
	enabled_items = get_enabled_monitor_items(monitor_items)
	return [item.get('url', '').strip() for item in enabled_items if item.get('url', '').strip() != '']


def build_monitor_priority_map(monitor_items):
	priority_map = {}
	for index, item in enumerate(monitor_items):
		url = item.get('url', '').strip()
		if url == '':
			continue
		custom_priority = item.get('priority')
		if isinstance(custom_priority, int):
			priority_map[url] = custom_priority
			continue
		priority_map[url] = index
	return priority_map


def get_candidate_priority(candidate, priority_map):
	url = candidate.get('url', '').strip()
	if url in priority_map:
		return int(priority_map[url])
	return 999999


def update_recent_activity(recent_activity, url, changed_at, priority):
	found_item = None
	for item in recent_activity:
		if item.get('url', '') == url:
			found_item = item
			break
	if found_item is None:
		found_item = {
			'url': url,
			'changed_at': changed_at,
			'priority': priority,
			'last_hit_at': 0,
		}
		recent_activity.append(found_item)
	else:
		found_item['changed_at'] = changed_at
		found_item['priority'] = priority
	recent_activity.sort(key=lambda item: (-int(item.get('changed_at', 0)), int(item.get('priority', 999999))))


def mark_recent_activity_hit(recent_activity, clicked_url):
	for item in recent_activity:
		if item.get('url', '') == clicked_url:
			item['last_hit_at'] = int(time.time() * 1000)
			item['changed_at'] = 0
			break


def build_preferred_urls(recent_activity, priority_map, enabled_urls):
	enabled_set = set(enabled_urls)
	ordered_urls = []
	for item in recent_activity:
		url = item.get('url', '')
		if url == '' or url not in enabled_set:
			continue
		if url not in ordered_urls:
			ordered_urls.append(url)

	remaining_urls = sorted(
		[url for url in enabled_urls if url not in ordered_urls],
		key=lambda url: int(priority_map.get(url, 999999)),
	)
	return [*ordered_urls, *remaining_urls]


def get_item_name(item):
	name = str(item.get('name', '')).strip()
	if name != '':
		return name
	return str(item.get('url', '')).strip()


def ensure_hotkey_registered(combo, event_queue):
	if combo.strip() == '':
		return False
	# 先清掉同組合，避免重複註冊造成 callback 疊加。
	hotkey.remove_hotkey(combo)
	return hotkey.add_hotkey(
		combo,
		lambda: event_queue.put(log_queue.make_trigger_scan_event()),
	)


def ensure_hotkey_removed(combo):
	if combo.strip() == '':
		return False
	return hotkey.remove_hotkey(combo)


def handle_add_url_item(ui_handle, monitor_items, put_log):
	url = ui_handle['get_entry_url']()
	name = ui_handle['get_entry_name']()
	if not url:
		messagebox.showwarning('錯誤', '請輸入網址')
		return
	if not config.is_valid_trade_url(url):
		messagebox.showwarning('錯誤', '請輸入有效的 pathofexile.tw/trade/search 網址')
		return
	existing = [item.get('url', '').strip() for item in monitor_items]
	if url in existing:
		messagebox.showwarning('錯誤', '該網址已在清單中')
		return

	if name == '':
		name = config.guess_monitor_name(url)

	monitor_items.append({
		'name': name,
		'url': url,
		'enabled': True,
	})
	config.save_urls(monitor_items)
	ui_handle['set_urls'](monitor_items)
	ui_handle['clear_entry']()
	put_log(f'已新增監控項目：{name}')


def handle_edit_url_item(root, ui_handle, monitor_items, index, put_log):
	if index < 0 or index >= len(monitor_items):
		return
	item = monitor_items[index]
	old_name = get_item_name(item)
	old_url = item.get('url', '').strip()
	new_name = simpledialog.askstring('編輯名稱', '請輸入新的名稱：', initialvalue=old_name, parent=root)
	if new_name is None:
		return
	new_name = new_name.strip()
	if new_name == '':
		new_name = config.guess_monitor_name(old_url)
	new_url = simpledialog.askstring('編輯網址', '請輸入新的網址：', initialvalue=old_url, parent=root)
	if new_url is None:
		return
	new_url = new_url.strip()
	if new_url == '':
		messagebox.showwarning('錯誤', '網址不能空白')
		return
	if not config.is_valid_trade_url(new_url):
		messagebox.showwarning('錯誤', '請輸入有效的 pathofexile.tw/trade/search 網址')
		return
	duplicated = [
		i for i, monitor_item in enumerate(monitor_items)
		if i != index and monitor_item.get('url', '').strip() == new_url
	]
	if len(duplicated) > 0:
		messagebox.showwarning('錯誤', '該網址已在清單中')
		return
	item['name'] = new_name
	item['url'] = new_url
	config.save_urls(monitor_items)
	ui_handle['set_urls'](monitor_items)
	put_log(f'已更新監控項目：{new_name}')


def handle_remove_url_item(ui_handle, monitor_items, index, put_log):
	if index < 0 or index >= len(monitor_items):
		return
	item = monitor_items[index]
	item_name = get_item_name(item)
	del monitor_items[index]
	config.save_urls(monitor_items)
	ui_handle['set_urls'](monitor_items)
	put_log(f'已移除監控項目：{item_name}')


def handle_copy_url_item(root, monitor_items, index, put_log):
	if index < 0 or index >= len(monitor_items):
		return
	item = monitor_items[index]
	item_url = item.get('url', '').strip()
	if item_url == '':
		return
	root.clipboard_clear()
	root.clipboard_append(item_url)
	item_name = get_item_name(item)
	put_log(f'已複製網址：{item_name}')


def handle_toggle_url_item(ui_handle, monitor_items, index, put_log):
	if index < 0 or index >= len(monitor_items):
		return
	item = monitor_items[index]
	enabled = bool(item.get('enabled', True))
	item['enabled'] = not enabled
	config.save_urls(monitor_items)
	ui_handle['set_urls'](monitor_items)
	item_name = get_item_name(item)
	if item['enabled']:
		put_log(f'已啟用監控：{item_name}')
	else:
		put_log(f'已停用監控：{item_name}')


def handle_refresh_tabs(ui_handle, driver_ref, monitor_items, put_log):
	if not is_driver_alive(driver_ref[0]):
		driver_ref[0] = None
		ui_handle['set_start_enabled'](True)
		ui_handle['set_stop_enabled'](False)
		ui_handle['set_status']('瀏覽器已關閉')
		put_log('偵測到瀏覽器已關閉，請重新啟動監控')
		messagebox.showwarning('尚未啟動', '請先按「啟動」開啟瀏覽器')
		return
	enabled_urls = get_enabled_urls(monitor_items)
	if len(enabled_urls) == 0:
		messagebox.showwarning('尚無啟用項目', '請至少啟用一個監控項目')
		return
	put_log('正在重新載入所有網址...')
	browser.refresh_tabs(driver_ref[0], enabled_urls)
	put_log('所有 live search 已重新載入完畢')


def handle_apply_hotkey(ui_handle, current_hotkey_ref, driver_ref, event_queue, put_log):
	new_hotkey = ui_handle['get_hotkey_var']().get().strip()
	if not new_hotkey:
		messagebox.showerror('錯誤', '熱鍵不能空白')
		return
	if new_hotkey == current_hotkey_ref[0]:
		messagebox.showinfo('提示', '已是目前熱鍵')
		return
	if is_driver_alive(driver_ref[0]):
		is_registered = ensure_hotkey_registered(new_hotkey, event_queue)
		if not is_registered:
			messagebox.showerror('熱鍵錯誤', '無法設定熱鍵，請用系統管理員權限啟動或改用其他組合鍵')
			return
		ensure_hotkey_removed(current_hotkey_ref[0])
		put_log(f'熱鍵已更新為：{new_hotkey}')
	current_hotkey_ref[0] = new_hotkey
	cfg = config.load_config()
	cfg['hotkey'] = new_hotkey
	config.save_config(cfg)
	messagebox.showinfo('成功', f'熱鍵已設定為：{new_hotkey}\n看到好貨就按這個鍵！')


def handle_start(
	ui_handle,
	driver_ref,
	monitor_items,
	current_hotkey_ref,
	selector,
	event_queue,
	put_log,
	is_monitoring_active_ref=None,
):
	enabled_urls = get_enabled_urls(monitor_items)
	if len(enabled_urls) == 0:
		messagebox.showwarning('尚無啟用項目', '請至少啟用一個監控項目')
		return
	if driver_ref[0] is not None:
		if is_driver_alive(driver_ref[0]):
			is_registered = ensure_hotkey_registered(current_hotkey_ref[0], event_queue)
			if is_registered:
				put_log(f'監控已恢復，熱鍵已啟用：{current_hotkey_ref[0]}')
			else:
				put_log('監控已恢復，但熱鍵啟用失敗，請改用「手動掃描一次」')
			if is_monitoring_active_ref is not None:
				is_monitoring_active_ref[0] = True
			ui_handle['set_start_enabled'](False)
			ui_handle['set_stop_enabled'](True)
			ui_handle['set_status'](f'監控中（背景） | 熱鍵：{current_hotkey_ref[0]} | 已連線')
			return
		driver_ref[0] = None
		ui_handle['set_start_enabled'](True)
		ui_handle['set_stop_enabled'](False)
		ui_handle['set_status']('瀏覽器已關閉，重新啟動中...')
		put_log('偵測到先前的瀏覽器已關閉，準備重新啟動')
	try:
		put_log('正在啟動 Playwright 背景監控並載入所有網址...')
		driver_ref[0] = browser.create_driver(headless=True)
		poe_sessid = ''
		if ui_handle and 'get_poe_sessid' in ui_handle:
			poe_sessid = ui_handle['get_poe_sessid']()
		if poe_sessid:
			browser.apply_poe_sessid(driver_ref[0], poe_sessid)
		browser.open_urls(driver_ref[0], enabled_urls)
	except Exception as e:
		put_log(f'啟動失敗：{e}')
		messagebox.showerror('啟動失敗', f'無法開啟 Chrome：{str(e)}\n\n請確認已安裝 Chrome 瀏覽器')
		if driver_ref[0]:
			browser.quit_driver(driver_ref[0])
			driver_ref[0] = None
		return

	is_registered = ensure_hotkey_registered(current_hotkey_ref[0], event_queue)
	if not is_registered:
		put_log('熱鍵啟用失敗')
		messagebox.showwarning(
			'熱鍵啟用失敗',
			'瀏覽器已啟動，但熱鍵無法啟用。\n請改用「手動掃描一次」按鈕觸發掃描。',
		)

	ui_handle['set_start_enabled'](False)
	ui_handle['set_stop_enabled'](True)
	ui_handle['set_status'](f'監控中（背景） | 熱鍵：{current_hotkey_ref[0]} | {len(enabled_urls)} 個分頁')
	if is_monitoring_active_ref is not None:
		is_monitoring_active_ref[0] = True
	put_log('背景監控啟動成功！所有 live search 已載入')
	put_log(f'看到想要的道具就按【{current_hotkey_ref[0]}】立即搶！')


def handle_stop(ui_handle, current_hotkey_ref, put_log, is_monitoring_active_ref=None):
	ensure_hotkey_removed(current_hotkey_ref[0])
	if is_monitoring_active_ref is not None:
		is_monitoring_active_ref[0] = False
	ui_handle['set_start_enabled'](True)
	ui_handle['set_stop_enabled'](False)
	ui_handle['set_status']('監控已停止 | 背景瀏覽器仍開啟中')
	put_log('監控與熱鍵已停止（可重新啟動）')


def on_closing(root, driver_ref, current_hotkey_ref, ui_handle):
	if driver_ref[0] is not None:
		if not messagebox.askokcancel('關閉程式', '確定要關閉程式並結束 Chrome 嗎？'):
			return
		ensure_hotkey_removed(current_hotkey_ref[0])
		browser.quit_driver(driver_ref[0])
		driver_ref[0] = None
	root.destroy()

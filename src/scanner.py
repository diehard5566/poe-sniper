from src import browser
from src.config import TRADE_PATH


def scan_and_click_travel_to_hideout(session, selector):
	"""
	遍歷所有分頁，只處理 URL 含 /trade/search/ 的，找第一個可點的按鈕並點擊。
	回傳 (success: bool, message: str)。
	"""
	if session is None:
		return (False, '瀏覽器未啟動')

	found, message, _notify_key = detect_travel_button(session, selector, should_click=True)
	return (found, message)


def detect_travel_button(session, selector, should_click=False):
	if session is None:
		return (False, '瀏覽器未啟動', '')

	for page in browser.get_pages(session):
		url = get_page_url(page)
		if TRADE_PATH not in url:
			continue
		try:
			button = page.locator(selector).first
			if button.count() == 0:
				continue
			if not button.is_visible():
				continue
			if not button.is_enabled():
				continue
			if should_click:
				button.click(timeout=1200)
				url_preview = url[:80] + '...' if len(url) > 80 else url
				message = f'搶到道具！已觸發 Travel to Hideout（分頁：{url_preview}）'
			else:
				url_preview = url[:80] + '...' if len(url) > 80 else url
				message = f'偵測到可搶道具（分頁：{url_preview}）'
			notify_key = url
			return (True, message, notify_key)
		except Exception:
			continue

	if should_click:
		return (False, '目前所有分頁都沒有可點的 Travel to Hideout 按鈕', '')
	return (False, '', '')


def get_page_url(page):
	try:
		return str(page.url or '')
	except Exception:
		return ''

from src import browser
from src.config import TRADE_PATH


def scan_and_click_travel_to_hideout(session, selector, preferred_urls=None):
	"""
	遍歷所有分頁（可依 preferred_urls 排序），
	只處理 URL 含 /trade/search/ 的，找第一個可點的按鈕並點擊。
	回傳 (success: bool, message: str, clicked_url: str)。
	"""
	if session is None:
		return (False, '瀏覽器未啟動', '')

	pages = browser.get_pages(session)
	ordered_pages = order_pages_by_urls(pages, preferred_urls or [])
	for page in ordered_pages:
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
			button.click(timeout=1200)
			url_preview = url[:80] + '...' if len(url) > 80 else url
			message = f'搶到道具！已觸發 Travel to Hideout（分頁：{url_preview}）'
			return (True, message, url)
		except Exception:
			continue

	return (False, '目前所有分頁都沒有可點的 Travel to Hideout 按鈕', '')


def detect_travel_button(session, selector, should_click=False):
	if session is None:
		return (False, '瀏覽器未啟動', '')

	candidates = detect_travel_candidates(session, selector)
	if len(candidates) > 0:
		target = candidates[0]
		if should_click:
			success, message, clicked_url = scan_and_click_travel_to_hideout(session, selector, [target.get('url', '')])
			return (success, message, clicked_url)
		return (True, target['message'], target['notify_key'])

	if should_click:
		return (False, '目前所有分頁都沒有可點的 Travel to Hideout 按鈕', '')
	return (False, '', '')


def detect_travel_candidates(session, selector):
	if session is None:
		return []

	candidates = []
	for page in browser.get_pages(session):
		candidate = detect_candidate_from_page(page, selector)
		if candidate is None:
			continue
		candidates.append(candidate)

	return candidates


def detect_candidate_from_page(page, selector):
	url = get_page_url(page)
	if TRADE_PATH not in url:
		return None
	try:
		button = page.locator(selector).first
		if button.count() == 0:
			return None
		if not button.is_visible():
			return None
		if not button.is_enabled():
			return None

		url_preview = url[:80] + '...' if len(url) > 80 else url
		notify_key = url
		signature = build_candidate_signature(page, button, url)
		return {
			'notify_key': notify_key,
			'url': url,
			'url_preview': url_preview,
			'signature': signature,
			'message': f'偵測到可搶道具（分頁：{url_preview}）',
		}
	except Exception:
		return None


def build_candidate_signature(page, button, url):
	try:
		button_text = (button.inner_text(timeout=500) or '').strip()
	except Exception:
		button_text = ''

	try:
		container_text = page.evaluate(
			"""(selector) => {
				const button = document.querySelector(selector);
				if (!button) return '';
				const row = button.closest('div, article, li, tr');
				if (!row) return '';
				return (row.innerText || '').slice(0, 240);
			}""",
			selector,
		)
	except Exception:
		container_text = ''

	return f'{url}|{button_text}|{container_text}'


def order_pages_by_urls(pages, preferred_urls):
	if len(preferred_urls) == 0:
		return pages

	priority_index_map = {}
	for index, url in enumerate(preferred_urls):
		if url not in priority_index_map:
			priority_index_map[url] = index

	scored = []
	for idx, page in enumerate(pages):
		url = get_page_url(page)
		priority = priority_index_map.get(url, 999999)
		scored.append((priority, idx, page))
	scored.sort(key=lambda item: (item[0], item[1]))
	return [item[2] for item in scored]


def get_page_url(page):
	try:
		return str(page.url or '')
	except Exception:
		return ''

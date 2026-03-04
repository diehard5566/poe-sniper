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

	candidates = detect_travel_candidates(session, selector)
	if len(candidates) > 0:
		target = candidates[0]
		if should_click:
			return click_travel_target(session, selector, target)
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


def click_travel_target(session, selector, target):
	if session is None:
		return (False, '瀏覽器未啟動', '')

	if target is None:
		return (False, '目前沒有可搶的目標', '')

	target_fingerprint = target.get('fingerprint', '')
	target_notify_key = target.get('notify_key', '')
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

			current_fingerprint = build_candidate_fingerprint(page, button, url)
			current_key = url
			is_matched = False
			if target_fingerprint != '' and current_fingerprint == target_fingerprint:
				is_matched = True
			elif target_fingerprint == '' and target_notify_key != '' and current_key == target_notify_key:
				is_matched = True
			if not is_matched:
				continue

			button.click(timeout=1200)
			url_preview = url[:80] + '...' if len(url) > 80 else url
			message = f'搶到道具！已觸發 Travel to Hideout（分頁：{url_preview}）'
			return (True, message, current_key)
		except Exception:
			continue

	return (False, '目標已失效或被其他人搶走，請等待下一筆', target_notify_key)


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
		fingerprint = build_candidate_fingerprint(page, button, url)
		return {
			'notify_key': notify_key,
			'url': url,
			'url_preview': url_preview,
			'fingerprint': fingerprint,
			'message': f'偵測到可搶道具（分頁：{url_preview}）',
		}
	except Exception:
		return None


def build_candidate_fingerprint(page, button, url):
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


def get_page_url(page):
	try:
		return str(page.url or '')
	except Exception:
		return ''

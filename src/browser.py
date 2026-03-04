from dataclasses import dataclass
from playwright.sync_api import sync_playwright
from playwright.sync_api import TimeoutError as PlaywrightTimeoutError


@dataclass
class BrowserSession:
	playwright: object
	browser: object
	context: object


def create_driver(headless=True):
	try:
		playwright = sync_playwright().start()
		browser = playwright.chromium.launch(
			channel='chrome',
			headless=headless,
			args=[
				'--disable-blink-features=AutomationControlled',
				'--no-default-browser-check',
				'--no-first-run',
			],
		)
		context = browser.new_context(
			viewport={
				'width': 1440,
				'height': 900,
			},
			ignore_https_errors=True,
		)
		return BrowserSession(
			playwright=playwright,
			browser=browser,
			context=context,
		)
	except Exception as e:
		raise RuntimeError(f'Playwright 啟動失敗：{e}')


def is_session_alive(session):
	if session is None:
		return False
	try:
		return session.browser.is_connected()
	except Exception:
		return False


def get_pages(session):
	if session is None:
		return []
	try:
		return list(session.context.pages)
	except Exception:
		return []


def open_urls(session, url_list, delay=0.5):
	if not url_list:
		return

	close_all_pages(session)
	for index, url in enumerate(url_list):
		page = session.context.new_page()
		try:
			page.goto(url, wait_until='domcontentloaded', timeout=15000)
		except PlaywrightTimeoutError:
			pass
		except Exception:
			pass
		if index == 0:
			try:
				page.bring_to_front()
			except Exception:
				pass


def refresh_tabs(session, url_list, delay=0.3):
	open_urls(session, url_list, delay=delay)


def close_all_pages(session):
	for page in get_pages(session):
		try:
			page.close()
		except Exception:
			pass


def quit_driver(session):
	if session is None:
		return
	try:
		session.context.close()
	except Exception:
		pass
	try:
		session.browser.close()
	except Exception:
		pass
	try:
		session.playwright.stop()
	except Exception:
		pass


def apply_poe_sessid(session, sessid):
	if session is None or not sessid:
		return
	try:
		session.context.add_cookies([{
			'name': 'POESESSID',
			'value': sessid,
			'domain': 'pathofexile.tw',
			'path': '/',
			'httpOnly': True,
			'secure': True,
		}])
	except Exception:
		# 失敗就當沒登入，不影響後續流程
		pass

import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def create_driver():
	options = Options()
	options.add_argument('--start-maximized')
	options.add_argument('--disable-blink-features=AutomationControlled')
	options.add_argument('--remote-allow-origins=*')
	options.add_experimental_option('excludeSwitches', ['enable-automation'])
	service = Service(ChromeDriverManager().install())
	return webdriver.Chrome(service=service, options=options)


def open_urls(driver, url_list, delay=0.5):
	if not url_list:
		return

	# 直接用現有的第一個分頁載入第一個 URL，避免留下 data:, 的空白分頁
	driver.get(url_list[0])
	time.sleep(delay)

	for url in url_list[1:]:
		driver.execute_script(f"window.open('{url}', '_blank');")
		time.sleep(delay)

	if driver.window_handles:
		driver.switch_to.window(driver.window_handles[0])


def refresh_tabs(driver, url_list, delay=0.3):
	handles = list(driver.window_handles)
	if not handles:
		return
	driver.switch_to.window(handles[0])
	for handle in handles[1:]:
		try:
			driver.switch_to.window(handle)
			driver.close()
		except Exception:
			pass
	if driver.window_handles:
		driver.switch_to.window(driver.window_handles[0])
	for url in url_list:
		driver.execute_script(f"window.open('{url}', '_blank');")
		time.sleep(delay)
	if driver.window_handles:
		driver.switch_to.window(driver.window_handles[0])


def quit_driver(driver):
	if driver is None:
		return
	try:
		driver.quit()
	except Exception:
		pass


def apply_poe_sessid(driver, sessid):
	if driver is None or not sessid:
		return
	try:
		driver.get('https://pathofexile.tw')
		driver.add_cookie({
			'name': 'POESESSID',
			'value': sessid,
			'domain': 'pathofexile.tw',
			'path': '/',
		})
	except Exception:
		# 失敗就當沒登入，不影響後續流程
		pass

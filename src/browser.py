import os
import platform
import tempfile
import time
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from webdriver_manager.chrome import ChromeDriverManager


def create_driver():
	chrome_log_path = os.path.join(
		tempfile.gettempdir(),
		f"poe-sniper-chromedriver-{int(time.time())}.log",
	)
	errors = []

	for profile in ('safe_port', 'minimal'):
		try:
			options = build_chrome_options(profile)
			service = make_service_with_webdriver_manager(chrome_log_path)
			return webdriver.Chrome(service=service, options=options)
		except Exception as e1:
			errors.append(f'profile={profile}, service=webdriver_manager, error={e1}')

		try:
			options = build_chrome_options(profile)
			service = make_service_with_selenium_manager(chrome_log_path)
			return webdriver.Chrome(service=service, options=options)
		except Exception as e2:
			errors.append(f'profile={profile}, service=selenium_manager, error={e2}')

	detail = '\n'.join(errors)
	raise RuntimeError(f'Chrome 啟動失敗。\n{detail}\nChromeDriver log: {chrome_log_path}')


def build_chrome_options(profile='stable_pipe'):
	options = Options()
	options.add_argument('--start-maximized')
	options.add_argument('--no-first-run')
	options.add_argument('--no-default-browser-check')
	options.add_argument('--disable-blink-features=AutomationControlled')

	# 固定用專用 profile，與使用者平常的 Chrome 完全分開，不需關閉既有 Chrome。
	# 重複使用同一目錄可避免每次啟動都跑「首次設定」，較穩定。
	user_data_dir = os.path.join(tempfile.gettempdir(), 'poe-sniper-profile')
	options.add_argument(f'--user-data-dir={user_data_dir}')

	if profile == 'stable_pipe':
		options.add_argument('--remote-debugging-pipe')
		options.add_argument('--disable-gpu')
		options.add_argument('--disable-extensions')
		options.add_argument('--disable-features=RendererCodeIntegrity')
	elif profile == 'safe_port':
		options.add_argument('--remote-allow-origins=*')
		options.add_argument('--remote-debugging-port=0')
		options.add_argument('--no-sandbox')
		options.add_argument('--disable-dev-shm-usage')
		options.add_argument('--disable-gpu')
		options.add_argument('--disable-software-rasterizer')
		options.add_argument('--disable-extensions')
	elif profile == 'minimal':
		options.add_argument('--remote-allow-origins=*')
		options.add_argument('--remote-debugging-port=0')
		options.add_argument('--no-sandbox')
		options.add_argument('--disable-dev-shm-usage')

	options.add_experimental_option('excludeSwitches', ['enable-automation'])

	chrome_binary = resolve_chrome_binary()
	if chrome_binary:
		options.binary_location = chrome_binary

	return options


def resolve_chrome_binary():
	env_binary = os.environ.get('CHROME_BINARY')
	if env_binary and os.path.exists(env_binary):
		return env_binary

	system_name = platform.system().lower()
	candidates = []

	if system_name == 'windows':
		candidates = [
			r'C:\Program Files\Google\Chrome\Application\chrome.exe',
			r'C:\Program Files (x86)\Google\Chrome\Application\chrome.exe',
		]
	elif system_name == 'darwin':
		candidates = [
			'/Applications/Google Chrome.app/Contents/MacOS/Google Chrome',
		]
	else:
		candidates = [
			'/usr/bin/google-chrome',
			'/usr/bin/google-chrome-stable',
		]

	for path in candidates:
		if os.path.exists(path):
			return path

	return None


def make_service_with_webdriver_manager(chrome_log_path):
	driver_path = ChromeDriverManager().install()
	try:
		return Service(executable_path=driver_path, log_output=chrome_log_path)
	except TypeError:
		return Service(executable_path=driver_path)


def make_service_with_selenium_manager(chrome_log_path):
	try:
		return Service(log_output=chrome_log_path)
	except TypeError:
		return Service()


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

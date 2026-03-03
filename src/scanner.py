from selenium.webdriver.common.by import By

from src.config import TRADE_PATH


def scan_and_click_travel_to_hideout(driver, selector):
	"""
	遍歷所有分頁，只處理 URL 含 /trade/search/ 的，找第一個可點的按鈕並點擊。
	回傳 (success: bool, message: str)。
	"""
	if driver is None:
		return (False, '瀏覽器未啟動')

	original_handle = driver.current_window_handle
	found = False
	message = ''

	for handle in driver.window_handles:
		try:
			driver.switch_to.window(handle)
		except Exception as e:
			message = f'切換分頁失敗: {e}'
			continue
		url = driver.current_url
		if TRADE_PATH not in url:
			continue
		try:
			btn = driver.find_element(By.CSS_SELECTOR, selector)
			if btn.is_displayed() and btn.is_enabled():
				driver.execute_script('arguments[0].click();', btn)
				url_preview = url[:80] + '...' if len(url) > 80 else url
				message = f'搶到道具！已觸發 Travel to Hideout（分頁：{url_preview}）'
				found = True
				break
		except Exception as e:
			continue

	try:
		driver.switch_to.window(original_handle)
	except Exception:
		pass

	if not found and not message:
		message = '目前所有分頁都沒有可點的 Travel to Hideout 按鈕'
	return (found, message)

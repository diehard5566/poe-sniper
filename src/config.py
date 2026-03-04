import json
import os
from urllib.parse import unquote, urlparse

DEFAULT_HOTKEY = 'ctrl+alt+t'
DEFAULT_SELECTOR = 'button.direct-btn'
ALLOWED_TRADE_DOMAIN = 'pathofexile.tw'
TRADE_PATH = '/trade/search/'


def get_base_dir():
	"""專案或 exe 所在目錄，打包後可改為使用者目錄。"""
	return os.path.dirname(os.path.dirname(os.path.abspath(__file__)))


def get_urls_path():
	return os.path.join(get_base_dir(), 'poe_urls.json')


def get_config_path():
	return os.path.join(get_base_dir(), 'config.json')


def load_urls():
	path = get_urls_path()
	if not os.path.exists(path):
		return []
	try:
		with open(path, 'r', encoding='utf-8') as f:
			data = json.load(f)
			if not isinstance(data, list):
				return []
			return normalize_monitor_items(data)
	except Exception:
		return []


def save_urls(urls):
	path = get_urls_path()
	monitor_items = normalize_monitor_items(urls if isinstance(urls, list) else [])
	with open(path, 'w', encoding='utf-8') as f:
		json.dump(monitor_items, f, ensure_ascii=False, indent=2)


def load_config():
	path = get_config_path()
	default = {
		'hotkey': DEFAULT_HOTKEY,
		'buttonSelector': DEFAULT_SELECTOR,
		'windowWidth': 900,
		'windowHeight': 700,
		'favorites': [],
		'detectIntervalMs': 1200,
		'notifyThrottleMs': 4500,
	}
	if not os.path.exists(path):
		return default
	try:
		with open(path, 'r', encoding='utf-8') as f:
			data = json.load(f)
			default.update(data)
			if not isinstance(default.get('favorites'), list):
				default['favorites'] = []
			return default
	except Exception:
		return default


def save_config(config):
	path = get_config_path()
	with open(path, 'w', encoding='utf-8') as f:
		json.dump(config, f, ensure_ascii=False, indent=2)


def save_favorites(favorites):
	cfg = load_config()
	cfg['favorites'] = favorites
	save_config(cfg)


def is_valid_trade_url(url):
	if not url or not isinstance(url, str):
		return False
	s = url.strip()
	if not s or TRADE_PATH not in s:
		return False
	try:
		from urllib.parse import urlparse
		parsed = urlparse(s)
		netloc = (parsed.netloc or '').lower()
		return ALLOWED_TRADE_DOMAIN in netloc
	except Exception:
		return False


def normalize_monitor_items(items):
	normalized = []
	for item in items:
		monitor_item = normalize_monitor_item(item)
		if monitor_item is None:
			continue
		normalized.append(monitor_item)
	return normalized


def normalize_monitor_item(item):
	if isinstance(item, str):
		url = item.strip()
		if url == '':
			return None
		return {
			'name': guess_monitor_name(url),
			'url': url,
			'enabled': True,
		}

	if not isinstance(item, dict):
		return None

	url = item.get('url', '')
	if not isinstance(url, str):
		return None
	url = url.strip()
	if url == '':
		return None

	name = item.get('name', '')
	if not isinstance(name, str):
		name = ''
	name = name.strip()
	if name == '':
		name = guess_monitor_name(url)

	enabled = item.get('enabled', True)
	enabled = bool(enabled)

	return {
		'name': name,
		'url': url,
		'enabled': enabled,
	}


def guess_monitor_name(url):
	try:
		parsed = urlparse(url)
		parts = [part for part in (parsed.path or '').split('/') if part != '']
		if len(parts) >= 4:
			keyword = unquote(parts[3])
			if keyword != '':
				return keyword
	except Exception:
		pass

	return url

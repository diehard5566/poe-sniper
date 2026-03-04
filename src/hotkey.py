import sys

USE_KEYBOARD = sys.platform.startswith('win')

if USE_KEYBOARD:
	import keyboard
else:
	keyboard = None


def add_hotkey(combo, callback):
	"""註冊熱鍵，callback 應只做 thread-safe 的事（例如 queue.put）。"""
	if not USE_KEYBOARD or keyboard is None:
		return False
	try:
		keyboard.add_hotkey(combo, callback)
		return True
	except Exception:
		# 在某些環境（權限不足等）可能會失敗，當作無法啟用熱鍵處理
		return False


def remove_hotkey(combo):
	if not USE_KEYBOARD or keyboard is None:
		return False
	try:
		keyboard.remove_hotkey(combo)
		return True
	except Exception:
		return False

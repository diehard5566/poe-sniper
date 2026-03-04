import platform
import threading


IS_WINDOWS = platform.system().lower().startswith('win')

if IS_WINDOWS:
	try:
		from win10toast import ToastNotifier
	except Exception:
		ToastNotifier = None
	try:
		import winsound
	except Exception:
		winsound = None
else:
	ToastNotifier = None
	winsound = None


_toaster_lock = threading.Lock()
_toaster = None


def get_toaster():
	global _toaster
	if not IS_WINDOWS or ToastNotifier is None:
		return None
	with _toaster_lock:
		if _toaster is None:
			_toaster = ToastNotifier()
	return _toaster


def notify_new_item(title, message):
	toaster = get_toaster()
	if toaster is None:
		return False
	try:
		toaster.show_toast(
			title,
			message,
			duration=4,
			threaded=True,
		)
		return True
	except Exception:
		return False


def play_alert_sound():
	if not IS_WINDOWS or winsound is None:
		return False
	try:
		winsound.MessageBeep(winsound.MB_ICONEXCLAMATION)
		return True
	except Exception:
		return False

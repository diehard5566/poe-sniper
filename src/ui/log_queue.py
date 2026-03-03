import queue
import time

EVENT_LOG = 'LOG'
EVENT_TRIGGER_SCAN = 'TRIGGER_SCAN'

POLL_MS = 100


def make_log_event(message):
	return {'type': EVENT_LOG, 'message': message}


def make_trigger_scan_event():
	return {'type': EVENT_TRIGGER_SCAN}


def process_queue(event_queue, on_log, on_trigger_scan):
	"""主線程輪詢：從 queue 取事件，LOG 寫入 on_log，TRIGGER_SCAN 呼叫 on_trigger_scan。"""
	try:
		while True:
			ev = event_queue.get_nowait()
			if ev.get('type') == EVENT_LOG:
				msg = ev.get('message', '')
				if msg and callable(on_log):
					on_log(msg)
			elif ev.get('type') == EVENT_TRIGGER_SCAN:
				if callable(on_trigger_scan):
					on_trigger_scan()
	except queue.Empty:
		pass


def schedule_next_poll(root, event_queue, on_log, on_trigger_scan):
	process_queue(event_queue, on_log, on_trigger_scan)
	root.after(POLL_MS, lambda: schedule_next_poll(root, event_queue, on_log, on_trigger_scan))


def log_with_timestamp(message):
	return f"[{time.strftime('%H:%M:%S')}] {message}"

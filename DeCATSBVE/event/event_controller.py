# event_controller.py
class EventController:
    def __init__(self):
        self._listeners = {}

    def bind(self, event_name, callback):
        self._listeners.setdefault(event_name, []).append(callback)

    def emit(self, event_name, *args, **kwargs):
        for cb in self._listeners.get(event_name, []):
            cb(*args, **kwargs)

    def unbind(self, event_name, callback=None):
        """특정 이벤트에서 콜백을 제거하거나, 콜백이 없으면 전체 제거"""
        if event_name not in self._listeners:
            return
        if callback is None:
            # 전체 콜백 제거
            self._listeners.pop(event_name, None)
        else:
            try:
                self._listeners[event_name].remove(callback)
                # 리스트가 비면 키도 제거
                if not self._listeners[event_name]:
                    self._listeners.pop(event_name, None)
            except ValueError:
                pass

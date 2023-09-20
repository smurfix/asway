from blinker import Signal as _Signal, ANY

class NotGiven:
    pass

class Signal(_Signal):
    def send(self,data=NotGiven):
        """Emit this signal on behalf of *sender*, passing on ``data``.
        """
        if data is NotGiven:
            for receiver in self.receivers_for(None):
                receiver()
        else:
            for receiver in self.receivers_for(None):
                receiver(data)


class PubSub(object):
    def __init__(self, conn):
        self.conn = conn
        self._subscriptions = {}

    def _signal(self, name):
        return Signal(name)

    def subscribe(self, detailed_event, handler):
        event = detailed_event.replace('-', '_')
        detail = ''

        try:
            event, detail = detailed_event.split('::', 1)
        except ValueError:
            pass

        v = (event,detail)
        n = r"{event}::{detail}"
        try:
            sig = self._subscriptions[v]
        except KeyError:
            self._subscriptions[v] = sig = self._signal(n)

        sig.connect(handler)

    def unsubscribe(self, handler):
        for v in self._subscriptions.values():
            v.disconnect(handler)

    def emit(self, event, data=NotGiven):
        if data and hasattr(data, 'change'):
            detail = data.change

        sig = self._subscriptions.get((event,))
        if sig is not None:
            sig.send(data)
        if detail:
            sig = self._subscriptions.get((event,detail))
            if sig is not None:
                sig.send(data)

class PubSub(object):
    def __init__(self, conn):
        self.conn = conn
        self._subscriptions = {}

    def subscribe(self, detailed_event, handler):
        event = detailed_event.replace('-', '_')
        detail = ''

        try:
            event, detail = detailed_event.split('::', 1)
        except ValueError:
            pass

        handlers = self._subscriptions.setdefault(event,{})
        handlers[id(handler)] = {'detail': detail, 'handler': handler}

    def unsubscribe(self, handler):
        for k,v in self._subscriptions.values():
            v.pop(id(handler), None)

    def emit(self, event, data):
        detail = ''

        if data and hasattr(data, 'change'):
            detail = data.change

        handlers = self._subscriptions.get(event)
        if not handlers:
            return
        for v in list(handlers.values()):
            if not s['detail'] or s['detail'] == detail:
                if data:
                    s['handler'](self.conn, data)
                else:
                    s['handler'](self.conn)

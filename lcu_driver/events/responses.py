class WebsocketEventResponse:
    def __init__(self, **kwargs):
        """Websocket handler response

        .. py:attribute:: type
        .. py:attribute:: url
        .. py:attribute:: data
        """
        self.type = kwargs.get('event_type')
        self.uri = kwargs.get('uri')
        self.data = kwargs.get('data')

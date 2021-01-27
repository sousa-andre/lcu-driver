import asyncio
from abc import ABC
from typing import Union, Callable, Awaitable, Iterable

from lcu_driver.events.responses import WebsocketEventResponse


class ConnectorEventManager(ABC):
    """Connector Events Manager Base Class"""

    def __init__(self):
        self._handlers = {}

    @property
    def handlers(self):
        return self._handlers

    def _set_event(self, event_name, func_or_coro: Union[Callable, Awaitable]):
        if event_name in self._handlers:
            self.handlers[event_name].append(func_or_coro)
        else:
            self.handlers[event_name] = [func_or_coro, ]
        return self.handlers[event_name][-1]

    async def run_event(self, event_name, *args, **kwargs):
        for event in self._handlers.get(event_name, []):
            await asyncio.create_task(
                event(*args, **kwargs)
            )

    def open(self, coro_func):
        return self._set_event('open', coro_func)

    def ready(self, coro_func):
        return self._set_event('ready', coro_func)

    def close(self, coro_func):
        return self._set_event('close', coro_func)


class WebsocketEventManager(ABC):
    """Connector Events Manager Base Class"""

    def __init__(self):
        self._registered_uris = []

    @property
    def registered_uris(self) -> list:
        """Websocket registered handlers

        :rtype: list
        """
        return self._registered_uris

    def register(self, uri: str, *, event_types: Iterable = ('CREATE', 'UPDATE', 'DELETE',)):
        """Register an event for the given handler.

        :param string uri: Endpoint to call. If the endpoint last character is a slash it will match all events starting with the endpoint.
        :param event_types: Expects an iterable. The allowed types are CREATE, UPDATE and DELETE (case-sensitive).
        :type event_types: tuple(str, str)
        """
        allowed_events = ('CREATE', 'UPDATE', 'DELETE',)

        if not uri.startswith('/'):
            raise RuntimeError('every endpoint should start with backslash')

        def register_wrapper(coro_func):
            for event in event_types:
                if event not in allowed_events:
                    raise RuntimeError(f'Event {event} not recognized.')

            self._registered_uris.append({
                'uri': uri,
                'event_types': event_types,
                'coroutine_or_callable': coro_func
            })
            return coro_func
        return register_wrapper

    @staticmethod
    def match_event(connector, connection, data):
        """Match registered websocket events and create a task with each handler"""
        for event in connector.ws.registered_uris:
            if event['uri'] == data['uri'] or (
                    event['uri'].endswith('/') and data['uri'].startswith(event['uri'])
            ):
                if data['eventType'].upper() in event['event_types']:
                    ws_dto = WebsocketEventResponse(
                        event_type=data['eventType'],
                        uri=data['uri'],
                        data=data['data'],
                    )
                    asyncio.create_task(event['coroutine_or_callable'](connection, ws_dto))

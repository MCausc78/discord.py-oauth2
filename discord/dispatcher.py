from __future__ import annotations

import asyncio
import logging
from typing import Any, Callable, Dict, Coroutine, List, Tuple, TypeVar

_log = logging.getLogger(__name__)

T = TypeVar('T')
Coro = Coroutine[Any, Any, T]
CoroT = TypeVar('CoroT', bound=Callable[..., Coro[Any]])


class _LoopSentinel:
    __slots__ = ()

    def __getattr__(self, attr: str) -> None:
        msg = (
            'loop attribute cannot be accessed in non-async contexts. '
            'Consider using either an asynchronous main function and passing it to asyncio.run or '
            'using asynchronous initialisation hooks such as Client.setup_hook'
        )
        raise AttributeError(msg)


_loop: Any = _LoopSentinel()


class Dispatcher:
    """Implements discord.py event system.

    .. versionadded:: 3.0
    """

    _listeners: Dict[str, List[Tuple[asyncio.Future, Callable[..., bool]]]] = {}
    _logger: logging.Logger
    loop: asyncio.AbstractEventLoop

    def __init__(self, *, logger: logging.Logger) -> None:
        self._listeners = {}
        self._logger: logging.Logger = logger
        self.loop = _loop

    async def _run_event(
        self,
        coro: Callable[..., Coroutine[Any, Any, Any]],
        event_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> None:
        try:
            await coro(*args, **kwargs)
        except asyncio.CancelledError:
            pass
        except Exception:
            try:
                await self.on_error(event_name, *args, **kwargs)
            except asyncio.CancelledError:
                pass

    def _schedule_event(
        self,
        coro: Callable[..., Coroutine[Any, Any, Any]],
        event_name: str,
        *args: Any,
        **kwargs: Any,
    ) -> asyncio.Task:
        wrapped = self._run_event(coro, event_name, *args, **kwargs)
        # Schedules the task
        return self.loop.create_task(wrapped, name=f'discord.py: {event_name}')

    def dispatch(self, event: str, /, *args: Any, **kwargs: Any) -> None:
        r"""Dispatch an event.

        Examples
        --------

        Dispatch an ``mention`` event when client is mentioned in a message: ::

            @client.event
            async def on_message(message):
                if client.user.mentioned_in(message):
                    client.dispatch('mention', message)

            @client.event
            async def on_mention(message):
                print(f'I was mentioned in message by {message.author.name}!')

        Parameters
        ----------
        event: :class:`str`
            The event to dispatch. Do not prefix this with ``on_`` as library will do it for you.
        \*args: Any
            The event positional arguments.
        \*\*kwargs: Any
            The event keyword arguments.
        """

        self._logger.debug('Dispatching event %s', event)
        method = 'on_' + event

        listeners = self._listeners.get(event)
        if listeners:
            removed = []
            for i, (future, condition) in enumerate(listeners):
                if future.cancelled():
                    removed.append(i)
                    continue

                try:
                    result = condition(*args)
                except Exception as exc:
                    future.set_exception(exc)
                    removed.append(i)
                else:
                    if result:
                        if len(args) == 0:
                            future.set_result(None)
                        elif len(args) == 1:
                            future.set_result(args[0])
                        else:
                            future.set_result(args)
                        removed.append(i)

            if len(removed) == len(listeners):
                self._listeners.pop(event)
            else:
                for idx in reversed(removed):
                    del listeners[idx]

        try:
            coro = getattr(self, method)
        except AttributeError:
            pass
        else:
            self._schedule_event(coro, method, *args, **kwargs)

    async def on_error(self, event_method: str, /, *args: Any, **kwargs: Any) -> None:
        """|coro|

        The default error handler provided by the client.

        By default this logs to the library logger however it could be
        overridden to have a different implementation.
        Check :func:`~discord.on_error` for more details.

        .. versionchanged:: 2.0

            ``event_method`` parameter is now positional-only
            and instead of writing to ``sys.stderr`` it logs instead.
        """
        _log.exception('Ignoring exception in %s', event_method)

    def event(self, coro: CoroT, /) -> CoroT:
        """A decorator that registers an event to listen to.

        You can find more info about the events on the :ref:`documentation below <discord-api-events>`.

        The events must be a :ref:`coroutine <coroutine>`, if not, :exc:`TypeError` is raised.

        Example
        -------

        .. code-block:: python3

            @client.event
            async def on_ready():
                print('Ready!')

        .. versionchanged:: 2.0

            ``coro`` parameter is now positional-only.

        Raises
        ------
        TypeError
            The coroutine passed is not actually a coroutine.
        """

        if not asyncio.iscoroutinefunction(coro):
            raise TypeError('event registered must be a coroutine function')

        setattr(self, coro.__name__, coro)
        _log.debug('%s has successfully been registered as an event', coro.__name__)
        return coro

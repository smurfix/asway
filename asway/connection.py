from ._private import pubsub, MessageType, EventType, Synchronizer
from .replies import (BarConfigReply, CommandReply, ConfigReply, OutputReply, TickReply,
                       VersionReply, WorkspaceReply, SeatReply, InputReply)
from .events import (IpcBaseEvent, BarconfigUpdateEvent, BindingEvent, OutputEvent, ShutdownEvent,
                      WindowEvent, TickEvent, ModeEvent, WorkspaceEvent, InputEvent, Event)
from .con import Con
from inspect import iscoroutine
import os
import json
from typing import Optional, List, Tuple, Callable, Union
from contextlib import asynccontextmanager
import struct
import socket
import logging

import anyio
from subprocess import PIPE
import sys

_MAGIC = b'i3-ipc'  # safety string for i3-ipc
_chunk_size = 1024  # in bytes
_struct_header = f'={len(_MAGIC)}sII'
_struct_header_size = struct.calcsize(_struct_header)
_running_futures = set()

logger = logging.getLogger(__name__)



from blinker import Signal as _Signal, ANY

class NotGiven:
    pass

class Signal(pubsub.Signal):
    async def send(self, tg, data=NotGiven):
        """Emit this signal on behalf of *sender*, passing on ``data``.
        """
        receivers= list(self.receivers_for(None))
        if not receivers:
            return

        async def mas(p,*a):
            r = p(*a)
            if iscoroutine(r):
                await r

        if len(receivers) == 1:
            if data is NotGiven:
                await mas(receivers[0])
            else:
                await mas(receivers[0], data)
            return

        else:
            if data is NotGiven:
                for rec in receivers:
                    tg.start_soon(mas, rec)
            else:
                for rec in receivers:
                    tg.start_soon(mas, rec, data)


class PubSub(pubsub.PubSub):
    def _signal(self, name):
        return Signal(name)

    async def emit(self, event, data=NotGiven):
        detail = ''
        if data and hasattr(data, 'change'):
            detail = data.change

        sigs = []
        sig = self._subscriptions.get((event,''))
        if sig is not None:
            sigs.append(sig)
        if detail:
            sig = self._subscriptions.get((event,detail))
            if sig is not None:
                sigs.append(sig)
        if not sigs:
            return
        if len(sigs) == 1:
            await sigs[0].send(self._tg, data)
        else:
            for sig in sigs:
                self._tg.start_soon(sig.send, self._tg, data)


def _pack(msg_type: MessageType, payload: str) -> bytes:
    pb = payload.encode()
    s = struct.pack('=II', len(pb), msg_type.value)
    return b''.join((_MAGIC, s, pb))


def _unpack_header(data: bytes) -> Tuple[bytes, int, int]:
    return struct.unpack(_struct_header, data[:_struct_header_size])


async def _find_socket_path() -> Optional[str]:
    socket_path = None

    def exists(path):
        if not path:
            return False
        result = os.path.exists(path)
        if not result:
            logger.info('file not found: %s', socket_path)
        return result

    # first try environment variables
    socket_path = os.environ.get('I3SOCK')
    if socket_path:
        logger.info('got socket path from I3SOCK env variable: %s', socket_path)
        if exists(socket_path):
            return socket_path

    socket_path = os.environ.get('SWAYSOCK')
    if socket_path:
        logger.info('got socket path from SWAYSOCK env variable: %s', socket_path)
        if exists(socket_path):
            return socket_path

    # finally try the binaries
    return None
    for binary in ('i3', 'sway'):
        try:
            result = await anyio.run_process([binary, '--get-socketpath'])
            socket_path = result.stdout.decode().strip()
            logger.info('got socket path from %r binary: %s', binary, socket_path)
            if exists(socket_path):
                return socket_path
        except Exception as e:
            logger.info('could not get i3 socket path from %r binary', binary, exc_info=e)
            continue

    logger.info('could not find i3 socket path')
    return None


class Connection:
    """A connection to the i3 ipc used for querying window manager state and
    listening to events.

    The ``Connection`` class is the entry point into all features of the
    library.  :func:`connect() <asway.aio.Connection.connect>` is an async
    context manager. The connection is only useable within the context.

    :Example:

    .. code-block:: python3

        async with Connection().connect() as i3:
            workspaces = await i3.get_workspaces()
            await i3.command('focus left')

    :param socket_path: A path to the i3 ipc socket path to connect to. If not
        given, find the socket path through the default search path.
    :type socket_path: str
    :param auto_reconnect: Whether to attempt to reconnect if the connection to
        the socket is broken when i3 restarts.
    :type auto_reconnect: bool

    :raises Exception: If the connection to i3 cannot be established.
    """
    _cmd_socket = None
    _sub_socket = None

    def __init__(self, socket_path: Optional[str] = None, auto_reconnect: bool = False):
        self._socket_path = socket_path
        self._auto_reconnect = auto_reconnect
        self._pubsub = PubSub(self)
        self._subscriptions = set()
        self._main_future = None
        self._reconnect_event = None
        self._reconnect_error = None
        self._synchronizer = None
        self._wlock = anyio.Lock()

    def _sync(self):
        if self._synchronizer is None:
            self._synchronizer = Synchronizer()

        self._synchronizer.sync()

    @property
    def socket_path(self) -> str:
        """The path of the socket this ``Connection`` is connected to.

        :rtype: str
        """
        return self._socket_path

    @property
    def auto_reconnect(self) -> bool:
        """Whether this ``Connection`` will attempt to reconnect when the
        connection to the socket is broken.

        :rtype: bool
        """
        return self._auto_reconnect

    async def _ipc_recv(self, sock):
        pass

    async def _message_reader(self):
        while True:
            await self._read_message()

    async def _read_message(self):

        error = None
        buf = b''
        while True:
            try:
                buf = await self._sub_socket.receive(_struct_header_size)
            except ConnectionError as e:
                if self._auto_reconnect:
                    logger.info('could not read message, reconnecting', exc_info=error)
                    await self._reconnect()
                else:
                    raise
            else:
                break

        magic, message_length, event_type = _unpack_header(buf)
        assert magic == _MAGIC
        raw_message = await self._sub_socket.receive(message_length)
        message = json.loads(raw_message)

        # events have the highest bit set
        if not event_type & (1 << 31):
            # a reply
            return

        event_type = EventType(1 << (event_type & 0x7f))
        logger.info('got message on subscription socket: type=%s, message=%s', event_type,
                    raw_message)

        if event_type == EventType.WORKSPACE:
            event = WorkspaceEvent(message, self, _Con=Con)
        elif event_type == EventType.OUTPUT:
            event = OutputEvent(message)
        elif event_type == EventType.MODE:
            event = ModeEvent(message)
        elif event_type == EventType.WINDOW:
            event = WindowEvent(message, self, _Con=Con)
        elif event_type == EventType.BARCONFIG_UPDATE:
            event = BarconfigUpdateEvent(message)
        elif event_type == EventType.BINDING:
            event = BindingEvent(message)
        elif event_type == EventType.SHUTDOWN:
            event = ShutdownEvent(message)
        elif event_type == EventType.TICK:
            event = TickEvent(message)
        elif event_type == EventType.INPUT:
            event = InputEvent(message)
        else:
            # we have not implemented this event
            return

        await self._pubsub.emit(event_type.to_string(), event)

    async def _connect(self):
        if self._socket_path:
            logger.info('using user provided socket path: {}', self._socket_path)

        if not self._socket_path:
            self._socket_path = await _find_socket_path()

        if not self.socket_path:
            raise RuntimeError('Failed to retrieve the i3 or sway IPC socket path')

        try:
            self._cmd_socket = await anyio.connect_unix(self.socket_path)
            self._sub_socket = await anyio.connect_unix(self.socket_path)
        except ConnectionRefusedError:
            breakpoint()
            raise
        await self.subscribe(list(self._subscriptions), force=True)

    @asynccontextmanager
    async def connect(self) -> 'Connection':
        """Connects to the i3 ipc socket. This is an async context manager.

        :returns: The ``Connection``.
        :rtype: :class:`~.Connection`
        """
        try:
            async with anyio.create_task_group() as tg:
                self.tg = tg
                self._pubsub._tg = tg
                await self._reconnect()
                tg.start_soon(self._message_reader)
                yield self
                tg.cancel_scope.cancel()
        finally:
            self.tg = None
            if self._cmd_socket is not None:
                await self._cmd_socket.aclose()
            if self._sub_socket is not None:
                await self._sub_socket.aclose()

    async def _reconnect(self):
        if self._reconnect_event is not None:
            await self._reconnect_event.wait()
            if self._reconnect_error is not None:
                raise self._reconnect_error
            return

        self._reconnect_event = anyio.Event()
        error = None
        for tries in range(250):
            try:
                await self._connect()
                error = None
                break
            except Exception as e:
                error = e
                await anyio.sleep(0.01)

        self._reconnect_event.set()
        self._reconnect_event = None
        self._reconnect_error = error
        if error is not None:
            raise error

    async def _message(self, message_type: MessageType, payload: str = '') -> bytearray:
        async with self._wlock:
            return await self._message_l(message_type, payload)

    async def _message_l(self, message_type: MessageType, payload: str = '') -> bytearray:
        if message_type is MessageType.SUBSCRIBE:
            raise Exception('cannot subscribe on the command socket')

        logger.info('sending message: type=%s, payload=%s', message_type, payload)
        err = None
        buf = None

        for tries in range(0, 5):
            try:
                await self._cmd_socket.send(_pack(message_type, payload))
                buf = await self._cmd_socket.receive(_struct_header_size)
                break
            except Exception as e:
                if not self._auto_reconnect:
                    raise e

                logger.info('got connection error, attempting to reconnect', exc_info=e)
                if err is None:
                    err = e
                await self._reconnect()

        if self._cmd_socket is None:
            return
        if buf is None:
            raise e

        magic, message_length, reply_type = _unpack_header(buf)
        assert reply_type == message_type.value
        assert magic == _MAGIC

        try:
            message = bytearray()
            remaining_length = message_length
            while remaining_length:
                buf = await self._cmd_socket.receive(remaining_length)
                if not buf:
                    logger.error('premature ending while reading message (%s bytes remaining)',
                                 remaining_length)
                    break
                message.extend(buf)
                remaining_length -= len(buf)
        except ConnectionError as e:
            if self._auto_reconnect:
                await self._reconnect()
            raise e

        logger.info('got message reply: %s', message)
        return message

    async def subscribe(self, events: Union[List[Event], List[str]], force: bool = False):
        """Send a ``SUBSCRIBE`` command to the ipc subscription connection and
        await the result. To attach event handlers, use :func:`Connection.on()
        <asway.aio.Connection.on()>`. Calling this is only needed if you want
        to be notified when events will start coming in.

        :ivar events: A list of events to subscribe to. Currently you cannot
            subscribe to detailed events.
        :vartype events: list(:class:`Event <asway.Event>`) or list(str)
        :ivar force: If ``False``, the message will not be sent if this
            connection is already subscribed to the event.
        :vartype force: bool
        """
        if not events:
            return

        if type(events) is not list:
            raise TypeError('events must be a list of events')

        subscriptions = set()

        for e in events:
            e = Event(e)
            if e not in Event._subscribable_events:
                correct_event = str.split(e.value, '::')[0].upper()
                raise ValueError(
                    f'only nondetailed events are subscribable (use Event.{correct_event})')
            subscriptions.add(e)

        logger.info('current subscriptions: %s', self._subscriptions)
        if not force:
            subscriptions = subscriptions.difference(self._subscriptions)
            if not subscriptions:
                logger.info('no new subscriptions')
                return
        logger.info('subscribing to events: %s', subscriptions)

        self._subscriptions.update(subscriptions)

        payload = json.dumps([s.value for s in subscriptions])

        logger.info('sending SUBSCRIBE message with payload: %s', payload)

        async with self._wlock:
            await self._sub_socket.send(_pack(MessageType.SUBSCRIBE, payload))

    def on(self,
           event: Union[Event, str],
           handler: Callable[['Connection', IpcBaseEvent], None] = None):
        def on_wrapped(handler):
            self._on(event, handler)
            return handler

        if handler:
            return on_wrapped(handler)
        else:
            return on_wrapped

    def _on(self, event: Union[Event, str], handler: Callable[['Connection', IpcBaseEvent], None]):
        """Subscribe to the event and call the handler when it is emitted by
        the i3 ipc.

        :param event: The event to subscribe to.
        :type event: :class:`Event <asway.Event>` or str
        :param handler: The event handler to call.
        :type handler: :class:`Callable`
        """
        if type(event) is Event:
            event = event.value

        event = event.replace('-', '_')

        if event.count('::') > 0:
            [base_event, __] = event.split('::')
        else:
            base_event = event

        logger.info('adding event handler: event=%s, handler=%s', event, handler)

        self._pubsub.subscribe(event, handler)
        self.tg.start_soon(self.subscribe, [base_event])

    def off(self, handler: Callable[['Connection', IpcBaseEvent], None]):
        """Unsubscribe the handler from being called on ipc events.

        :param handler: The handler that was previously attached with
            :func:`on()`.
        :type handler: :class:`Callable`
        """
        logger.info('removing event handler: handler=%s', handler)
        self._pubsub.unsubscribe(handler)

    async def command(self, cmd: str) -> List[CommandReply]:
        """Sends a command to i3.

        .. seealso:: https://i3wm.org/docs/userguide.html#list_of_commands

        :param cmd: The command to send to i3.
        :type cmd: str
        :returns: A list of replies that contain info for the result of each
            command given.
        :rtype: list(:class:`CommandReply <asway.CommandReply>`)
        """
        data = await self._message(MessageType.COMMAND, cmd)

        if data:
            data = json.loads(data)
            return CommandReply._parse_list(data)
        else:
            return []

    async def get_version(self) -> VersionReply:
        """Gets the i3 version.

        :returns: The i3 version.
        :rtype: :class:`asway.VersionReply`
        """
        data = await self._message(MessageType.GET_VERSION)
        data = json.loads(data)
        return VersionReply(data)

    async def get_bar_config_list(self) -> List[str]:
        """Gets the names of all bar configurations.

        :returns: A list of all bar configurations.
        :rtype: list(str)
        """
        data = await self._message(MessageType.GET_BAR_CONFIG)
        return json.loads(data)

    async def get_bar_config(self, bar_id=None) -> Optional[BarConfigReply]:
        """Gets the bar configuration specified by the id.

        :param bar_id: The bar id to get the configuration for. If not given,
            get the configuration for the first bar id.
        :type bar_id: str

        :returns: The bar configuration for the bar id.
        :rtype: :class:`BarConfigReply <asway.BarConfigReply>` or :class:`None`
            if no bar configuration is found.
        """
        if not bar_id:
            bar_config_list = await self.get_bar_config_list()
            if not bar_config_list:
                return None
            bar_id = bar_config_list[0]

        data = await self._message(MessageType.GET_BAR_CONFIG, bar_id)
        data = json.loads(data)
        return BarConfigReply(data)

    async def get_outputs(self) -> List[OutputReply]:
        """Gets the list of current outputs.

        :returns: A list of current outputs.
        :rtype: list(:class:`asway.OutputReply`)
        """
        data = await self._message(MessageType.GET_OUTPUTS)
        data = json.loads(data)
        return OutputReply._parse_list(data)

    async def get_workspaces(self) -> List[WorkspaceReply]:
        """Gets the list of current workspaces.

        :returns: A list of current workspaces
        :rtype: list(:class:`asway.WorkspaceReply`)
        """
        data = await self._message(MessageType.GET_WORKSPACES)
        data = json.loads(data)
        return WorkspaceReply._parse_list(data)

    async def get_raw_tree(self) -> Con:
        """Gets the i3 layout tree.

        :returns: The i3 layout data.
        :rtype: :class:`dict`
        """
        data = await self._message(MessageType.GET_TREE)
        return json.loads(data)

    async def get_tree(self) -> Con:
        """Gets the root container of the i3 layout tree.

        :returns: The root container of the i3 layout tree.
        :rtype: :class:`asway.Con`
        """
        return Con(await self.get_raw_tree(), None, self)

    async def get_marks(self) -> List[str]:
        """Gets the names of all currently set marks.

        :returns: A list of currently set marks.
        :rtype: list(str)
        """
        data = await self._message(MessageType.GET_MARKS)
        return json.loads(data)

    async def get_binding_modes(self) -> List[str]:
        """Gets the names of all currently configured binding modes

        :returns: A list of binding modes
        :rtype: list(str)
        """
        data = await self._message(MessageType.GET_BINDING_MODES)
        return json.loads(data)

    async def get_config(self) -> ConfigReply:
        """Returns the last loaded i3 config.

        :returns: A class containing the config.
        :rtype: :class:`asway.ConfigReply`
        """
        data = await self._message(MessageType.GET_CONFIG)
        data = json.loads(data)
        return ConfigReply(data)

    async def send_tick(self, payload: str = "") -> TickReply:
        """Sends a tick with the specified payload.

        :returns: The reply to the tick command
        :rtype: :class:`asway.TickReply`
        """
        data = await self._message(MessageType.SEND_TICK, payload)
        data = json.loads(data)
        return TickReply(data)

    async def get_inputs(self) -> List[InputReply]:
        """(sway only) Gets the inputs connected to the compositor.

        :returns: The reply to the inputs command
        :rtype: list(:class:`asway.InputReply`)
        """
        data = await self._message(MessageType.GET_INPUTS)
        data = json.loads(data)
        return InputReply._parse_list(data)

    async def get_seats(self) -> List[SeatReply]:
        """(sway only) Gets the seats configured on the compositor

        :returns: The reply to the seats command
        :rtype: list(:class:`asway.SeatReply`)
        """
        data = await self._message(MessageType.GET_SEATS)
        data = json.loads(data)
        return SeatReply._parse_list(data)

import threading
from enum import IntEnum, auto
from functools import wraps
from queue import Empty, Full, Queue
from typing import Callable, Literal, Optional

from common.types.event import Event

Receiver = Callable[[bool], Optional[Event]]
Transmitter = Callable[[Event, bool], Literal[None, True]]


class UniDirChannel:
    class Status(IntEnum):
        SUCCESS = auto()

    def __init__(self):
        self.__data = Queue()

    def rx(self, block: bool=True) -> Optional[Event]:
        try:
            return self.__data.get(block=block)
        except Empty:
            pass

    def tx(self, evt: Event, block: bool=True) -> Literal[None, True]:
        try:
            self.__data.put(evt, block=block)
            return True
        except Full:
            pass


class BiDirChannel:
    def __init__(self, rx: Optional[UniDirChannel] = None , tx: Optional[UniDirChannel] = None):
        self.__rx_channel = rx or UniDirChannel()
        self.__tx_channel = tx or UniDirChannel()
        self.rx = self.__rx_channel.rx
        self.tx = self.__tx_channel.tx

    def reverse(self) -> 'BiDirChannel':
        return BiDirChannel(rx=self.__tx_channel, tx=self.__rx_channel)


def shedule(task):
    @wraps(task)
    def sheduler(*args, **kwargs):
        threading.Thread(target=task, args=args, kwargs=kwargs, daemon=True).start()
    return sheduler


def shedule_bidir(task):
    @wraps(task)
    def sheduler(*args, **kwargs) -> BiDirChannel:
        chan = BiDirChannel()
        threading.Thread(
            target=task, args=(*args, chan), kwargs=kwargs, daemon=True
        ).start()
        return chan.reverse()

    return sheduler


def shedule_consumer(task):
    @wraps(task)
    def sheduler(*args, **kwargs) -> Transmitter:
        chan = UniDirChannel()
        threading.Thread(
            target=task, args=(*args, chan.rx), kwargs=kwargs, daemon=True
        ).start()
        return chan.tx
    return sheduler


def shedule_producer(task):
    @wraps(task)
    def sheduler(*args, **kwargs) -> Receiver:
        chan = UniDirChannel()
        threading.Thread(
            target=task, args=(*args, chan.tx), kwargs=kwargs, daemon=True
        ).start()
        return chan.rx
    return sheduler


class Router:
    def __init__(self):
        self.__subs: list[tuple[Receiver, tuple[Transmitter, ...]]] = []
        self.__tx = self.rout()

    @shedule_consumer
    def rout(self, rx: Receiver):
        while True:
            (sub := rx(False)) is None or self.__subs.append(sub)
            for subscribtion in self.__subs:
                src, dsts = subscribtion
                (evt := src(False)) is None or [dst(evt, True) for dst in dsts]

    def subscribe(self, src, *dsts):
        self.__tx((src, dsts))
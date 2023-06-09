import httpx

from time import time
from api.verification import AuthReq, AuthRsp, AuthError
from common.types.event import Event
from common.types.vector import Vector
from models import edgenet_face

from ..settings import settings
from . import task as _task
from .constants import EventType
import multiprocessing as mp


class Errors:
    Connection= "Failed to connect to the service"

def f(conn: mp.Pipe):
    model = edgenet_face.load()

    base_url = f"{settings.verification_service_url}/auth/{settings.lock_id}"
    with httpx.Client(
        base_url=base_url
    ) as verification:
        while True:
            face = conn.recv()
            t = time()
            fv = model(face)
            print(f"==> fv: {time()-t}")
            try:
                    t = time()
                    rsp = verification.post(
                        url="/", data=AuthReq(data=Vector.from_tensor(fv)).json()
                    ).json()
                    print(f"lock <== server: {time()-t}")
                    conn.send(Event(
                        type=EventType.VERIFICATION_RSP,
                        data=AuthRsp(**rsp).status
                    ))
            except Exception as err:
                    conn.send(Event(
                        type=EventType.VERIFICATION_RSP,
                        data=AuthError.CONNECTION
                    ))



@_task.shedule_bidir
def task(chan: _task.BiDirChannel):
    parent, child = mp.Pipe()
    mp.Process(target=f, args=(child,)).start()
    for evt in iter(chan.rx, None):
        parent.send(evt.data)
        chan.tx(
            parent.recv()
        )
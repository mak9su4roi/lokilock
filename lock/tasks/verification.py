import httpx

from api.verification import AuthReq, AuthRsp, AuthError
from common.types.event import Event
from common.types.vector import Vector
from models import edgenet_face

from ..settings import settings
from . import task as _task
from .constants import EventType


class Errors:
    Connection= "Failed to connect to the service"

@_task.shedule_bidir
def task(chan: _task.BiDirChannel):
    with httpx.Client(
        base_url=f"{settings.verification_service_url}/auth/{settings.lock_id}"
    ) as verification:
        model = edgenet_face.load()
        for evt in iter(chan.rx, None):
            intermediate_fv = model(evt.data)
            try:
                rsp = verification.post(
                    url="/", data=AuthReq(data=Vector.from_tensor(intermediate_fv)).json()
                ).json()
                chan.tx(Event(
                    type=EventType.VERIFICATION_RSP,
                    data=AuthRsp(**rsp).status
                ))
            except Exception:
                chan.tx(Event(
                    type=EventType.VERIFICATION_RSP,
                    data=AuthError.CONNECTION
                ))

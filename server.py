import asyncio
import json
import uuid
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from aiohttp import web, WSMsgType
from abc import ABC, abstractmethod

# --- Message type constants ---
MESSAGE_TYPE_COMMAND = 0
MESSAGE_TYPE_COMMAND_RESPONSE = 1
MESSAGE_TYPE_NOTIFICATION = 2
MESSAGE_TYPE_SUBSCRIPTION = 3
MESSAGE_TYPE_SUBSCRIPTION_RESPONSE = 4
MESSAGE_TYPE_ERROR = 5


# --- Data types ---
@dataclass
class ElementId:
    level: int
    index: int


@dataclass
class DeviceControl:
    type: str
    href: str
    authorization: bool


@dataclass
class NmosDevice:
    id: str
    label: str
    description: str
    senders: List[str]
    receivers: List[str]
    node_id: str
    type: str
    version: str
    controls: List[DeviceControl]


@dataclass
class IdArgs:
    id: ElementId


@dataclass
class IdArgsValue:
    id: ElementId
    value: Any


@dataclass
class PropertyChangedEventData:
    propertyId: ElementId
    changeType: int
    value: Any
    sequenceItemIndex: Optional[int] = None


@dataclass
class PropertyChangedEvent:
    oid: int
    eventId: ElementId
    eventData: PropertyChangedEventData


# --- Helpers ---


def tai_timestamp() -> str:
    now = time.time()
    secs = int(now) + 37
    nsec = int((now - int(now)) * 1_000_000_000)
    return f"{secs}:{nsec}"


def make_event(
    oid: int,
    prop_id: ElementId,
    change_type: int,
    value: Any,
    seq_idx: Optional[int] = None,
):
    return PropertyChangedEvent(
        oid=oid,
        eventId=ElementId(1, 1),
        eventData=PropertyChangedEventData(prop_id, change_type, value, seq_idx),
    )


def serialize_event(ev: PropertyChangedEvent) -> dict:
    return {
        "oid": ev.oid,
        "eventId": asdict(ev.eventId),
        "eventData": {
            "propertyId": asdict(ev.eventData.propertyId),
            "changeType": ev.eventData.changeType,
            "value": ev.eventData.value,
            "sequenceItemIndex": ev.eventData.sequenceItemIndex,
        },
    }


class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        if hasattr(o, "__dict__") and not isinstance(o, ElementId):
            return asdict(o)
        if isinstance(o, ElementId):
            return {"level": o.level, "index": o.index}
        return super().default(o)


# --- Property change type ---


class NcPropertyChangeType:
    ValueChanged = 0
    SequenceItemAdded = 1
    SequenceItemChanged = 2
    SequenceItemRemoved = 3


# --- NMOS Object/Block ---


class NcMember(ABC):
    @abstractmethod
    def member_type(self) -> str:
        pass

    @abstractmethod
    def get_role(self) -> str:
        pass

    @abstractmethod
    def get_oid(self) -> int:
        pass

    @abstractmethod
    def get_constant_oid(self) -> bool:
        pass

    @abstractmethod
    def get_class_id(self) -> List[int]:
        pass

    @abstractmethod
    def get_user_label(self) -> Optional[str]:
        pass

    @abstractmethod
    def get_property(self, oid: int, id_args: IdArgs) -> tuple[Optional[str], Any]:
        pass

    @abstractmethod
    def set_property(
        self, oid: int, id_args_value: IdArgsValue
    ) -> tuple[Optional[str], bool]:
        pass

    @abstractmethod
    def invoke_method(
        self, oid: int, method_id: ElementId, args: Any
    ) -> tuple[Optional[str], Any]:
        pass


class NcObject(NcMember):
    def __init__(self, class_id, oid, constant_oid, owner, role, user_label, notifier):
        self.class_id, self.oid, self.constant_oid = class_id, oid, constant_oid
        self.owner, self.role, self.user_label = owner, role, user_label
        self.notifier = notifier

    def member_type(self):
        return "NcObject"

    def get_role(self):
        return self.role

    def get_oid(self):
        return self.oid

    def get_constant_oid(self):
        return self.constant_oid

    def get_class_id(self):
        return self.class_id

    def get_user_label(self):
        return self.user_label

    def get_property(self, oid, id_args):
        mapping = {
            (1, 1): self.class_id,
            (1, 2): self.oid,
            (1, 3): self.constant_oid,
            (1, 4): self.owner,
            (1, 5): self.role,
            (1, 6): self.user_label,
        }
        return None, mapping.get((id_args.id.level, id_args.id.index), None)

    async def _notify(self, prop_id, change_type, value, seq_idx=None):
        await self.notifier.put(
            make_event(self.oid, prop_id, change_type, value, seq_idx)
        )

    def set_property(self, oid, id_args_value):
        if (
            id_args_value.id.level == 1
            and id_args_value.id.index == 6
            and isinstance(id_args_value.value, str)
        ):
            self.user_label = id_args_value.value
            asyncio.create_task(
                self._notify(
                    id_args_value.id,
                    NcPropertyChangeType.ValueChanged,
                    id_args_value.value,
                )
            )
            return None, True
        return "Property not found", False

    def invoke_method(self, oid, method_id, args):
        return "Methods not yet implemented", None


class NcBlock(NcMember):
    def __init__(
        self,
        is_root,
        class_id,
        oid,
        constant_oid,
        owner,
        role,
        user_label,
        enabled,
        notifier,
    ):
        self.base = NcObject(
            class_id, oid, constant_oid, owner, role, user_label, notifier
        )
        self.is_root = is_root
        self.enabled = enabled
        self.members: List[NcMember] = []

    def member_type(self):
        return "NcBlock"

    def get_role(self):
        return self.base.get_role()

    def get_oid(self):
        return self.base.get_oid()

    def get_constant_oid(self):
        return self.base.get_constant_oid()

    def get_class_id(self):
        return self.base.get_class_id()

    def get_user_label(self):
        return self.base.get_user_label()

    def get_property(self, oid, id_args):
        if oid == self.base.oid:
            lvl, idx = id_args.id.level, id_args.id.index
            if (lvl, idx) == (2, 1):
                return None, self.enabled
            if (lvl, idx) == (2, 2):
                return None, self.generate_members_descriptors()
            return self.base.get_property(oid, id_args)
        m = self.find_member(oid)
        return m.get_property(oid, id_args) if m else ("Member not found", None)

    def set_property(self, oid, id_args_value):
        if oid == self.base.oid:
            return self.base.set_property(oid, id_args_value)
        m = self.find_member(oid)
        return m.set_property(oid, id_args_value) if m else ("Member not found", False)

    def invoke_method(self, oid, method_id, args):
        if oid == self.base.oid:
            return self.base.invoke_method(oid, method_id, args)
        m = self.find_member(oid)
        return (
            m.invoke_method(oid, method_id, args) if m else ("Member not found", None)
        )

    def add_member(self, member):
        self.members.append(member)
        ev = make_event(
            self.base.oid,
            ElementId(2, 2),
            NcPropertyChangeType.ValueChanged,
            self.generate_members_descriptors(),
        )
        asyncio.create_task(self.base.notifier.put(ev))

    def find_member(self, oid):
        for m in self.members:
            if m.get_oid() == oid:
                return m
            if isinstance(m, NcBlock):
                found = m.find_member(oid)
                if found:
                    return found
        return None

    def generate_members_descriptors(self):
        return [
            {
                "role": m.get_role(),
                "oid": m.get_oid(),
                "constantOid": m.get_constant_oid(),
                "classId": m.get_class_id(),
                "userLabel": m.get_user_label() or "",
                "owner": self.base.get_oid(),
            }
            for m in self.members
        ]


# --- App state ---


class ConnectionState:
    def __init__(self, ws):
        self.websocket, self.subscribed_oids = ws, set()

    async def send_text(self, text):
        if not self.websocket.closed:
            await self.websocket.send_str(text)


class AppState:
    def __init__(self):
        self.connections: Dict[str, ConnectionState] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.root_block: Optional[NcBlock] = None
        self.device = NmosDevice(
            id=str(uuid.uuid4()),
            label="Example Device",
            description="NMOS Example Device",
            senders=[],
            receivers=[],
            node_id=str(uuid.uuid4()),
            type="urn:x-nmos:device:generic",
            version=tai_timestamp(),
            controls=[
                DeviceControl(
                    "urn:x-nmos:control:ncp/v1.0", "ws://127.0.0.1:3000/ws", False
                )
            ],
        )

    async def notify_subscribers(self, ev):
        text = json.dumps(
            {
                "messageType": MESSAGE_TYPE_NOTIFICATION,
                "notifications": [serialize_event(ev)],
            },
            cls=CustomEncoder,
        )
        for conn in list(self.connections.values()):
            if ev.oid in conn.subscribed_oids:
                try:
                    await conn.send_text(text)
                except Exception:
                    pass

    async def event_loop(self):
        while True:
            await self.notify_subscribers(await self.event_queue.get())


app_state = AppState()

# --- REST handlers ---


async def devices_handler(request):
    return web.json_response([asdict(app_state.device)])


async def device_handler(request):
    device_id = request.match_info.get("device_id")
    if device_id == app_state.device.id:
        return web.json_response(asdict(app_state.device))
    return web.json_response({"error": "device not found"}, status=404)


# --- WebSocket ---


async def process_command(msg):
    responses = []
    root = app_state.root_block
    for cmd in msg.get("commands", []):
        handle, oid, args = cmd.get("handle"), cmd.get("oid"), cmd.get("arguments")
        method_id = ElementId(**cmd.get("methodId", {}))
        status, error, value = 200, None, None

        try:
            if (method_id.level, method_id.index) == (1, 1):
                err, val = root.get_property(oid, IdArgs(ElementId(**args["id"])))
                value = val if err is None else None
                if err:
                    status, error = 400, err
            elif (method_id.level, method_id.index) == (1, 2):
                err, ok = root.set_property(
                    oid, IdArgsValue(ElementId(**args["id"]), args.get("value"))
                )
                if not ok:
                    status, error = 400, err
            else:
                err, resp = root.invoke_method(oid, method_id, args)
                if err is None:
                    value = resp
                else:
                    status, error = 400, err
        except Exception as e:
            status, error = 400, str(e)

        responses.append(
            {
                "handle": handle,
                "result": {"status": status, "value": value, "errorMessage": error},
            }
        )
    return {"messageType": MESSAGE_TYPE_COMMAND_RESPONSE, "responses": responses}


async def websocket_handler(request):
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    conn_id, conn = str(uuid.uuid4()), ConnectionState(ws)
    app_state.connections[conn_id] = conn

    try:
        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                continue
            try:
                data = json.loads(msg.data)
            except Exception:
                await conn.send_text(
                    json.dumps(
                        {
                            "messageType": MESSAGE_TYPE_ERROR,
                            "status": 400,
                            "errorMessage": "Invalid JSON",
                        }
                    )
                )
                continue

            mt = data.get("messageType")
            if mt == MESSAGE_TYPE_COMMAND and "commands" in data:
                await conn.send_text(
                    json.dumps(await process_command(data), cls=CustomEncoder)
                )
            elif mt == MESSAGE_TYPE_SUBSCRIPTION and "subscriptions" in data:
                conn.subscribed_oids = set(data["subscriptions"])
                await conn.send_text(
                    json.dumps(
                        {
                            "messageType": MESSAGE_TYPE_SUBSCRIPTION_RESPONSE,
                            "subscriptions": list(conn.subscribed_oids),
                        }
                    )
                )
            else:
                await conn.send_text(
                    json.dumps(
                        {
                            "messageType": MESSAGE_TYPE_ERROR,
                            "status": 400,
                            "errorMessage": "Invalid message",
                        }
                    )
                )
    finally:
        app_state.connections.pop(conn_id, None)
    return ws


# --- Main ---


async def init_app():
    app = web.Application()
    app.add_routes(
        [
            web.get("/x-nmos/node/v1.3/devices/", devices_handler),
            web.get("/x-nmos/node/v1.3/devices/{device_id}", device_handler),
            web.get("/ws", websocket_handler),
        ]
    )

    # Root block
    root = NcBlock(
        True, [1, 1], 1, True, None, "root", None, True, app_state.event_queue
    )
    # Child member
    root.add_member(NcObject([1], 2, True, 1, "test", "test", app_state.event_queue))
    # Child block
    child_block = NcBlock(
        False, [1, 1], 3, True, None, "child_block", None, True, app_state.event_queue
    )
    child_block.add_member(
        NcObject([1], 4, True, 3, "child_block_member", "Child", app_state.event_queue)
    )
    root.add_member(child_block)

    app_state.root_block = root

    asyncio.create_task(app_state.event_loop())
    return app


if __name__ == "__main__":
    web.run_app(init_app(), host="0.0.0.0", port=3000)

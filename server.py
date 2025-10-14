import asyncio
import json
import uuid
import time
from dataclasses import dataclass, asdict
from typing import Any, Dict, List, Optional
from aiohttp import web, WSMsgType
from abc import ABC, abstractmethod
from enum import IntEnum

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

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "index": self.index,
        }


class NcPropertyChangeType(IntEnum):
    ValueChanged = 0
    SequenceItemAdded = 1
    SequenceItemChanged = 2
    SequenceItemRemoved = 3


class NcDeviceGenericState(IntEnum):
    Unknown = 0
    NormalOperation = 1
    Initializing = 2
    Updating = 3
    LicensingError = 4
    InternalError = 5


class NcResetCause(IntEnum):
    Unknown = 0
    PowerOn = 1
    InternalError = 2
    Upgrade = 3
    ControllerRequest = 4
    ManualReset = 5


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
    property_id: ElementId
    change_type: NcPropertyChangeType
    value: Any
    sequence_item_index: Optional[int] = None

    def to_dict(self) -> dict:
        return {
            "propertyId": self.property_id.to_dict(),
            "changeType": int(self.change_type),
            "value": self.value,
            "sequenceItemIndex": self.sequence_item_index,
        }


@dataclass
class PropertyChangedEvent:
    oid: int
    event_id: ElementId
    event_data: PropertyChangedEventData

    def to_dict(self) -> dict:
        return {
            "oid": self.oid,
            "eventId": self.event_id.to_dict(),
            "eventData": self.event_data.to_dict(),
        }


@dataclass
class NcManufacturer:
    name: str
    organization_id: Optional[int] = None
    website: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "organizationId": self.organization_id,
            "website": self.website,
        }


@dataclass
class NcProduct:
    name: str
    key: str
    revision_level: str
    brand_name: Optional[str] = None
    uuid: Optional[str] = None
    description: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "key": self.key,
            "revisionLevel": self.revision_level,
            "brandName": self.brand_name,
            "uuid": self.uuid,
            "description": self.description,
        }


@dataclass
class NcDeviceOperationalState:
    generic: NcDeviceGenericState
    device_specific_details: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "generic": int(self.generic),
            "deviceSpecificDetails": self.device_specific_details,
        }


# ====================================================
# =============== JSON encoders/helpers ==============
# ====================================================


def tai_timestamp() -> str:
    now = time.time()
    secs = int(now) + 37
    nsec = int((now - int(now)) * 1_000_000_000)
    return f"{secs}:{nsec}"


def make_event(
    oid: int,
    prop_id: ElementId,
    change_type: NcPropertyChangeType,
    value: Any,
    seq_idx: Optional[int] = None,
):
    return PropertyChangedEvent(
        oid=oid,
        event_id=ElementId(1, 1),
        event_data=PropertyChangedEventData(prop_id, change_type, value, seq_idx),
    )


class CustomEncoder(json.JSONEncoder):
    """
    Keep your older behavior but also serialize IntEnum as numbers and dataclasses properly.
    """

    def default(self, o):
        # IntEnum -> numeric value
        if isinstance(o, IntEnum):
            return int(o)
        # dataclasses -> asdict
        if hasattr(o, "__dataclass_fields__"):
            return asdict(o)
        # ElementId as dict
        if isinstance(o, ElementId):
            return {"level": o.level, "index": o.index}
        # Generic fallback to asdict for objects with __dict__
        if hasattr(o, "__dict__"):
            return asdict(o)
        return super().default(o)


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
        oid,
        constant_oid,
        owner,
        role,
        user_label,
        enabled,
        notifier,
    ):
        self.base = NcObject(
            class_id=[1, 1],
            oid=oid,
            constant_oid=constant_oid,
            owner=owner,
            role=role,
            user_label=user_label,
            notifier=notifier,
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
            lvl, idx = method_id.level, method_id.index
            if (lvl, idx) == (2, 1):  # 2m1
                return None, self.get_member_descriptors(args)
            if (lvl, idx) == (2, 2):  # 2m2
                return None, self.find_members_by_path(args)
            if (lvl, idx) == (2, 3):  # 2m3
                return None, self.find_members_by_role(args)
            if (lvl, idx) == (2, 4):  # 2m4
                return None, self.find_members_by_class_id(args)
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

    @staticmethod
    def make_member_descriptor(member, owner):
        return {
            "role": member.get_role(),
            "oid": member.get_oid(),
            "constantOid": member.get_constant_oid(),
            "classId": member.get_class_id(),
            "userLabel": member.get_user_label() or "",
            "owner": owner,
        }

    # 2m1
    def get_member_descriptors(self, args):
        recurse = args.get("recurse", False)
        results = [
            self.make_member_descriptor(m, self.base.get_oid()) for m in self.members
        ]
        if recurse:
            for m in self.members:
                if isinstance(m, NcBlock):
                    results.extend(m.get_member_descriptors(args))
        return results

    # 2m2
    def find_members_by_path(self, args):
        path = args.get("path")
        if not isinstance(path, list) or not path:
            return []

        segments = [s.strip() for s in path if isinstance(s, str) and s.strip()]
        if not segments:
            return []

        return self._find_members_by_path_recursive(segments)

    def _find_members_by_path_recursive(self, segments):
        if not segments:
            return []

        first, rest = segments[0], segments[1:]
        results = []

        for m in self.members:
            if m.get_role() == first:
                if not rest:
                    results.append(self.make_member_descriptor(m, self.base.get_oid()))
                elif isinstance(m, NcBlock):
                    results.extend(m._find_members_by_path_recursive(rest))
        return results

    # 2m3
    def find_members_by_role(self, args):
        role = str(args.get("role", "")).strip()
        if not role:
            return []

        case_sensitive = args.get("caseSensitive", False)
        match_whole = args.get("matchWholeString", False)
        recurse = args.get("recurse", False)

        # Normalize search string
        search_role = role if case_sensitive else role.lower()

        def matches(r: str) -> bool:
            if not r:
                return False
            target = r if case_sensitive else r.lower()
            return target == search_role if match_whole else search_role in target

        results = [
            self.make_member_descriptor(m, self.base.get_oid())
            for m in self.members
            if matches(m.get_role())
        ]

        if recurse:
            for m in self.members:
                if isinstance(m, NcBlock):
                    results.extend(m.find_members_by_role(args))

        return results

    # 2m4
    def find_members_by_class_id(self, args):
        class_id = args.get("classId")
        if not class_id:
            return []

        recurse = args.get("recurse", False)
        include_derived = args.get("includeDerived", False)

        class_id_str = ".".join(str(x) for x in class_id)

        def matches_class_id(cid):
            cid_str = ".".join(str(x) for x in cid)
            return (
                cid_str.startswith(class_id_str)
                if include_derived
                else cid_str == class_id_str
            )

        results = [
            self.make_member_descriptor(m, self.base.get_oid())
            for m in self.members
            if matches_class_id(m.get_class_id())
        ]

        if recurse:
            for m in self.members:
                if isinstance(m, NcBlock):
                    results.extend(m.find_members_by_class_id(args))

        if self.is_root and matches_class_id(self.base.get_class_id()):
            results.append(
                {
                    "role": self.base.get_role(),
                    "oid": self.base.get_oid(),
                    "constantOid": self.base.get_constant_oid(),
                    "classId": self.base.get_class_id(),
                    "userLabel": self.base.get_user_label() or "",
                    "owner": self.base.get_oid(),
                }
            )
        return results


class NcDeviceManager(NcMember):
    def __init__(
        self,
        oid: int,
        constant_oid: bool,
        owner: Optional[int],
        role: str,
        user_label: Optional[str],
        nc_version: str,
        manufacturer: NcManufacturer,
        product: NcProduct,
        serial_number: str,
        notifier: asyncio.Queue,
    ):
        self.base = NcObject(
            class_id=[1, 3, 1],
            oid=oid,
            constant_oid=constant_oid,
            owner=owner,
            role=role,
            user_label=user_label,
            notifier=notifier,
        )
        self.nc_version = nc_version
        self.manufacturer = manufacturer
        self.product = product
        self.serial_number = serial_number
        self.user_inventory_code: Optional[str] = None
        self.device_name: Optional[str] = None
        self.device_role: Optional[str] = None
        self.operational_state = NcDeviceOperationalState(
            generic=NcDeviceGenericState.NormalOperation, device_specific_details=None
        )
        self.reset_cause = NcResetCause.PowerOn
        self.message: Optional[str] = None

    def member_type(self) -> str:
        return "NcDeviceManager"

    def get_role(self) -> str:
        return self.base.get_role()

    def get_oid(self) -> int:
        return self.base.get_oid()

    def get_constant_oid(self) -> bool:
        return self.base.get_constant_oid()

    def get_class_id(self) -> List[int]:
        return self.base.get_class_id()

    def get_user_label(self) -> Optional[str]:
        return self.base.get_user_label()

    def get_property(self, _oid: int, id_args: IdArgs) -> tuple[Optional[str], Any]:
        # properties at level 3 -> map indexes to fields
        lvl, idx = id_args.id.level, id_args.id.index
        if lvl == 3:
            if idx == 1:
                return None, self.nc_version
            if idx == 2:
                return None, self.manufacturer.to_dict()
            if idx == 3:
                return None, self.product.to_dict()
            if idx == 4:
                return None, self.serial_number
            if idx == 5:
                return None, self.user_inventory_code
            if idx == 6:
                return None, self.device_name
            if idx == 7:
                return None, self.device_role
            if idx == 8:
                return None, self.operational_state.to_dict()
            if idx == 9:
                return None, int(self.reset_cause)
            if idx == 10:
                return None, self.message
            return None, None
        # fall back to base object
        return self.base.get_property(_oid, id_args)

    def set_property(
        self, _oid: int, id_args_value: IdArgsValue
    ) -> tuple[Optional[str], bool]:
        if id_args_value.id.level == 3:
            idx = id_args_value.id.index
            # 5: userInventoryCode
            if idx == 5:
                if id_args_value.value is None:
                    self.user_inventory_code = None
                elif isinstance(id_args_value.value, str):
                    self.user_inventory_code = id_args_value.value
                else:
                    return ("Property value was invalid", False)
                asyncio.create_task(
                    self.base._notify(
                        id_args_value.id,
                        NcPropertyChangeType.ValueChanged,
                        self.user_inventory_code,
                    )
                )
                return None, True
            # 6: deviceName
            if idx == 6:
                if id_args_value.value is None:
                    self.device_name = None
                elif isinstance(id_args_value.value, str):
                    self.device_name = id_args_value.value
                else:
                    return ("Property value was invalid", False)
                asyncio.create_task(
                    self.base._notify(
                        id_args_value.id,
                        NcPropertyChangeType.ValueChanged,
                        self.device_name,
                    )
                )
                return None, True
            # 7: deviceRole
            if idx == 7:
                if id_args_value.value is None:
                    self.device_role = None
                elif isinstance(id_args_value.value, str):
                    self.device_role = id_args_value.value
                else:
                    return ("Property value was invalid", False)
                asyncio.create_task(
                    self.base._notify(
                        id_args_value.id,
                        NcPropertyChangeType.ValueChanged,
                        self.device_role,
                    )
                )
                return None, True
            # Other level-3 properties are read-only
            return ("Could not find the property or it is read-only", False)
        # not level 3 => delegate to base
        return self.base.set_property(_oid, id_args_value)

    def invoke_method(
        self, _oid: int, method_id: ElementId, args: Any
    ) -> tuple[Optional[str], Any]:
        # No methods on NcDeviceManager itself in this implementation - delegate to base
        return self.base.invoke_method(_oid, method_id, args)


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
            id="67c25159-ce25-4000-a66c-f31fff890265",  # id=str(uuid.uuid4()),
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
                "notifications": [ev.to_dict()],
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
    root = NcBlock(True, 1, True, None, "root", None, True, app_state.event_queue)

    # Add NcDeviceManager (mirrors your Rust usage)
    manufacturer = NcManufacturer(
        name="Your Company", organization_id=None, website="https://example.com"
    )
    product = NcProduct(
        name="Your Product",
        key="MODEL-XYZ-2000",
        revision_level="1.0",
        brand_name="Your Brand",
        uuid="550e8400-e29b-41d4-a716-446655440000",
        description="Professional device",
    )

    device_manager = NcDeviceManager(
        oid=2,
        constant_oid=True,
        owner=1,
        role="DeviceManager",
        user_label="Device Manager",
        nc_version="v1.0.0",
        manufacturer=manufacturer,
        product=product,
        serial_number="SN-123456789",
        notifier=app_state.event_queue,
    )
    root.add_member(device_manager)

    # Child member (keep existing objects)
    root.add_member(
        NcObject([1], 3, True, 1, "my-obj-01", "My object 01", app_state.event_queue)
    )

    # Child block
    child_block = NcBlock(
        False, 4, True, None, "my-block-01", None, True, app_state.event_queue
    )
    child_block.add_member(
        NcObject([1], 5, True, 3, "my-nested-block-obj", None, app_state.event_queue)
    )
    root.add_member(child_block)

    app_state.root_block = root

    asyncio.create_task(app_state.event_loop())
    return app


if __name__ == "__main__":
    web.run_app(init_app(), host="0.0.0.0", port=3000)

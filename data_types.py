from dataclasses import dataclass, field
import time
from typing import Any, List, Optional, Dict
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
class NmosResource:
    id: str
    label: str
    description: str
    version: str
    tags: Dict[str, List[str]] = field(default_factory=dict)


@dataclass
class DeviceControl:
    type: str
    href: str
    authorization: bool

    def to_dict(self) -> dict:
        return {
            "type": self.type,
            "href": self.href,
            "authorization": self.authorization,
        }


@dataclass
class NmosDevice:
    id: str
    label: str
    description: str
    version: str
    senders: List[str]
    receivers: List[str]
    node_id: str
    type: str
    controls: List[DeviceControl]
    tags: Dict[str, List[str]] = field(default_factory=dict)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "description": self.description,
            "version": self.version,
            "tags": self.tags,
            "senders": self.senders,
            "receivers": self.receivers,
            "node_id": self.node_id,
            "type": self.type,
            "controls": [c.to_dict() for c in self.controls],
        }


@dataclass
class NmosClock:
    name: str
    ref_type: str

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "ref_type": self.ref_type,
        }


@dataclass
class NmosInterface:
    chassis_id: str
    name: str
    port_id: str

    def to_dict(self) -> dict:
        return {
            "chassis_id": self.chassis_id,
            "name": self.name,
            "port_id": self.port_id,
        }


@dataclass
class NmosEndpoint:
    host: str
    port: int
    protocol: str

    def to_dict(self) -> dict:
        return {
            "host": self.host,
            "port": self.port,
            "protocol": self.protocol,
        }


@dataclass
class NmosApi:
    endpoints: List[NmosEndpoint]
    versions: List[str]

    def to_dict(self) -> dict:
        return {
            "endpoints": [e.to_dict() for e in self.endpoints],
            "versions": self.versions,
        }


@dataclass
class NmosNode:
    id: str
    label: str
    description: str
    version: str
    href: str
    hostname: str
    clocks: List[NmosClock]
    interfaces: List[NmosInterface]
    api: NmosApi
    tags: Dict[str, List[str]] = field(default_factory=dict)
    caps: Dict[str, Any] = field(default_factory=dict)
    services: List[Dict[str, Any]] = field(default_factory=list)

    def to_dict(self) -> dict:
        return {
            "id": self.id,
            "label": self.label,
            "description": self.description,
            "version": self.version,
            "tags": self.tags,
            "href": self.href,
            "hostname": self.hostname,
            "caps": self.caps,
            "services": self.services,
            "clocks": [c.to_dict() for c in self.clocks],
            "interfaces": [i.to_dict() for i in self.interfaces],
            "api": self.api.to_dict(),
        }


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

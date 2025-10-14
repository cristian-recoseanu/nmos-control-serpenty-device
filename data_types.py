from dataclasses import dataclass
import time
from typing import Any, List, Optional
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

from dataclasses import dataclass, field
import time
from typing import Any, List, Optional, Dict
from enum import IntEnum

MESSAGE_TYPE_COMMAND = 0
MESSAGE_TYPE_COMMAND_RESPONSE = 1
MESSAGE_TYPE_NOTIFICATION = 2
MESSAGE_TYPE_SUBSCRIPTION = 3
MESSAGE_TYPE_SUBSCRIPTION_RESPONSE = 4
MESSAGE_TYPE_ERROR = 5


@dataclass
class NcPropertyConstraintsNumber:
    base: "NcPropertyConstraints"
    maximum: Optional[float] = None
    minimum: Optional[float] = None
    step: Optional[float] = None

    def to_dict(self) -> dict:
        d = self.base.to_dict()
        d.update({"maximum": self.maximum, "minimum": self.minimum, "step": self.step})
        return d

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Numeric property constraints"),
                name="NcPropertyConstraintsNumber",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(NcDescriptor(None), "maximum", None, True, False),
                NcFieldDescriptor(NcDescriptor(None), "minimum", None, True, False),
                NcFieldDescriptor(NcDescriptor(None), "step", None, True, False),
            ],
            parentType="NcPropertyConstraints",
        )
        if include_inherited:
            base = NcPropertyConstraints.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current


@dataclass
class NcPropertyConstraintsString:
    base: "NcPropertyConstraints"
    max_characters: Optional[int] = None
    pattern: Optional[str] = None

    def to_dict(self) -> dict:
        d = self.base.to_dict()
        d.update({"maxCharacters": self.max_characters, "pattern": self.pattern})
        return d

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("String property constraints"),
                name="NcPropertyConstraintsString",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None), "maxCharacters", "NcUint32", True, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "pattern", "NcRegex", True, False
                ),
            ],
            parentType="NcPropertyConstraints",
        )
        if include_inherited:
            base = NcPropertyConstraints.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current


class NcMethodStatus(IntEnum):
    Ok = 200
    PropertyDeprecated = 298
    MethodDeprecated = 299
    BadCommandFormat = 400
    Unauthorized = 401
    BadOid = 404
    Readonly = 405
    InvalidRequest = 406
    Conflict = 409
    BufferOverflow = 413
    IndexOutOfBounds = 414
    ParameterError = 417
    Locked = 423
    DeviceError = 500
    MethodNotImplemented = 501
    PropertyNotImplemented = 502
    NotReady = 503
    Timeout = 504


@dataclass
class NcMethodResult:
    handle: Optional[int]
    status: NcMethodStatus

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        return NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Method result base"),
                name="NcMethodResult",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None), "status", "NcMethodStatus", False, False
                )
            ],
            parentType=None,
        )


@dataclass
class NcMethodResultError(NcMethodResult):
    errorMessage: str

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Error result"),
                name="NcMethodResultError",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None), "errorMessage", "NcString", False, False
                )
            ],
            parentType="NcMethodResult",
        )
        if include_inherited:
            base = NcMethodResult.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current

    def to_dict(self) -> dict:
        result = {
            "handle": self.handle,
            "status": int(self.status),
            "errorMessage": getattr(self, "errorMessage", ""),
        }
        if hasattr(self, "value"):
            value = getattr(self, "value")
            result["value"] = value.to_dict() if hasattr(value, "to_dict") else value
        return result


@dataclass
class NcMethodResultPropertyValue(NcMethodResult):
    value: Any

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Get/sequence result"),
                name="NcMethodResultPropertyValue",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[NcFieldDescriptor(NcDescriptor(None), "value", None, True, False)],
            parentType="NcMethodResult",
        )
        if include_inherited:
            base = NcMethodResult.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current


@dataclass
class ElementId:
    level: int
    index: int

    def to_dict(self) -> dict:
        return {
            "level": self.level,
            "index": self.index,
        }


@dataclass
class IdArgs:
    id: ElementId


@dataclass
class IdArgsValue:
    id: ElementId
    value: Any


@dataclass
class NcElementId:
    level: int
    index: int

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        base = NcDatatypeDescriptor(
            base=NcDescriptor("Descriptor of an element id"),
            name="NcElementId",
            type=NcDatatypeType.Struct,
            constraints=None,
        )
        current = NcDatatypeDescriptorStruct(
            base=base,
            fields=[
                NcFieldDescriptor(
                    base=NcDescriptor(None),
                    name="level",
                    typeName="NcUint16",
                    isNullable=False,
                    isSequence=False,
                ),
                NcFieldDescriptor(
                    base=NcDescriptor(None),
                    name="index",
                    typeName="NcUint16",
                    isNullable=False,
                    isSequence=False,
                ),
            ],
            parentType=None,
        )
        return current

    def to_dict(self) -> dict:
        return {"level": self.level, "index": self.index}


@dataclass
class NcPropertyId:
    base: NcElementId

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Property id descriptor"),
                name="NcPropertyId",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[],
            parentType="NcElementId",
        )
        if include_inherited:
            base = NcDescriptor.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current

    def to_dict(self) -> dict:
        return {"level": self.base.level, "index": self.base.index}


@dataclass
class NcMethodId:
    base: NcElementId

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Method id descriptor"),
                name="NcMethodId",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[],
            parentType="NcElementId",
        )
        if include_inherited:
            base = NcDescriptor.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current

    def to_dict(self) -> dict:
        return {"level": self.base.level, "index": self.base.index}


@dataclass
class NcEventId:
    base: NcElementId

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Event id descriptor"),
                name="NcEventId",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[],
            parentType="NcElementId",
        )
        if include_inherited:
            base = NcDescriptor.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current

    def to_dict(self) -> dict:
        return {"level": self.base.level, "index": self.base.index}


class NcDatatypeType(IntEnum):
    Primitive = 0
    Typedef = 1
    Struct = 2
    Enum = 3


@dataclass
class NcDescriptor:
    description: Optional[str]

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        base = NcDatatypeDescriptor(
            base=NcDescriptor("Descriptor of a struct"),
            name="NcDescriptor",
            type=NcDatatypeType.Struct,
            constraints=None,
        )
        current = NcDatatypeDescriptorStruct(
            base=base,
            fields=[
                NcFieldDescriptor(
                    base=NcDescriptor(None),
                    name="description",
                    typeName="NcString",
                    isNullable=True,
                    isSequence=False,
                )
            ],
            parentType=None,
        )
        return current

    def to_dict(self) -> dict:
        return {"description": self.description}


@dataclass
class NcDatatypeDescriptor:
    base: NcDescriptor
    name: str
    type: NcDatatypeType
    constraints: Optional[Any] = None

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Datatype descriptor base"),
                name="NcDatatypeDescriptor",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(NcDescriptor(None), "name", "NcName", False, False),
                NcFieldDescriptor(
                    NcDescriptor(None), "type", "NcDatatypeType", False, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None),
                    "constraints",
                    "NcParameterConstraints",
                    True,
                    False,
                ),
            ],
            parentType="NcDescriptor",
        )
        if include_inherited:
            base = NcDescriptor.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current

    def to_dict(self) -> dict:
        return {
            "description": self.base.description,
            "name": self.name,
            "type": int(self.type) if isinstance(self.type, IntEnum) else self.type,
            "constraints": self.constraints.to_dict() if self.constraints else None,
        }


@dataclass
class NcFieldDescriptor:
    base: NcDescriptor
    name: str
    typeName: Optional[str]
    isNullable: bool
    isSequence: bool
    constraints: Optional[Any] = None

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Descriptor of a struct field"),
                name="NcFieldDescriptor",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(NcDescriptor(None), "name", "NcName", False, False),
                NcFieldDescriptor(
                    NcDescriptor(None), "typeName", "NcName", True, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "isNullable", "NcBoolean", False, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "isSequence", "NcBoolean", False, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None),
                    "constraints",
                    "NcParameterConstraints",
                    True,
                    False,
                ),
            ],
            parentType="NcDescriptor",
        )
        if include_inherited:
            base = NcDescriptor.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current

    def to_dict(self) -> dict:
        return {
            **self.base.to_dict(),
            "name": self.name,
            "typeName": self.typeName,
            "isNullable": self.isNullable,
            "isSequence": self.isSequence,
            "constraints": self.constraints.to_dict() if self.constraints else None,
        }


@dataclass
class NcDatatypeDescriptorStruct:
    base: NcDatatypeDescriptor
    fields: List[NcFieldDescriptor]
    parentType: Optional[str] = None

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Struct datatype descriptor"),
                name="NcDatatypeDescriptorStruct",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None), "fields", "NcFieldDescriptor", False, True
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "parentType", "NcName", True, False
                ),
            ],
            parentType="NcDatatypeDescriptor",
        )
        if include_inherited:
            base = NcDatatypeDescriptor.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current

    def to_dict(self) -> dict:
        return {
            **self.base.to_dict(),
            "fields": [f.to_dict() for f in self.fields],
            "parentType": self.parentType,
        }


@dataclass
class NcDatatypeDescriptorPrimitive:
    base: NcDatatypeDescriptor

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Primitive datatype descriptor"),
                name="NcDatatypeDescriptorPrimitive",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[],
            parentType="NcDatatypeDescriptor",
        )
        if include_inherited:
            base = NcDatatypeDescriptor.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current

    def to_dict(self) -> dict:
        return {**self.base.to_dict()}


@dataclass
class NcMethodResultDatatypeDescriptor(NcMethodResult):
    value: NcDatatypeDescriptor

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Datatype descriptor result"),
                name="NcMethodResultDatatypeDescriptor",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None), "value", "NcDatatypeDescriptor", False, False
                )
            ],
            parentType="NcMethodResult",
        )
        if include_inherited:
            base = NcMethodResult.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current


@dataclass
class NcParameterDescriptor:
    base: NcDescriptor
    name: str
    typeName: Optional[str]
    isNullable: bool
    isSequence: bool
    constraints: Optional["NcParameterConstraints"] = None

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Descriptor of a method parameter"),
                name="NcParameterDescriptor",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(NcDescriptor(None), "name", "NcName", False, False),
                NcFieldDescriptor(
                    NcDescriptor(None), "typeName", "NcName", True, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "isNullable", "NcBoolean", False, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "isSequence", "NcBoolean", False, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None),
                    "constraints",
                    "NcParameterConstraints",
                    True,
                    False,
                ),
            ],
            parentType="NcDescriptor",
        )
        if include_inherited:
            base = NcDescriptor.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current

    def to_dict(self) -> dict:
        return {
            "description": self.base.description,
            "name": self.name,
            "typeName": self.typeName,
            "isNullable": self.isNullable,
            "isSequence": self.isSequence,
            "constraints": self.constraints.to_dict() if self.constraints else None,
        }


@dataclass
class NcMethodDescriptor:
    base: NcDescriptor
    id: ElementId
    name: str
    resultDatatype: str
    parameters: List[NcParameterDescriptor]
    isDeprecated: bool

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Descriptor of a method"),
                name="NcMethodDescriptor",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(NcDescriptor(None), "id", "NcMethodId", False, False),
                NcFieldDescriptor(NcDescriptor(None), "name", "NcName", False, False),
                NcFieldDescriptor(
                    NcDescriptor(None), "resultDatatype", "NcName", False, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None),
                    "parameters",
                    "NcParameterDescriptor",
                    False,
                    True,
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "isDeprecated", "NcBoolean", False, False
                ),
            ],
            parentType="NcDescriptor",
        )
        if include_inherited:
            base = NcDescriptor.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current

    def to_dict(self) -> dict:
        return {
            "description": self.base.description,
            "id": self.id.to_dict(),
            "name": self.name,
            "resultDatatype": self.resultDatatype,
            "parameters": [p.to_dict() for p in self.parameters],
            "isDeprecated": self.isDeprecated,
        }


@dataclass
class NcPropertyDescriptor:
    base: NcDescriptor
    id: ElementId
    name: str
    typeName: Optional[str]
    isReadOnly: bool
    isNullable: bool
    isSequence: bool
    isDeprecated: bool
    constraints: Optional["NcParameterConstraints"] = None

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Descriptor of a property"),
                name="NcPropertyDescriptor",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None), "id", "NcPropertyId", False, False
                ),
                NcFieldDescriptor(NcDescriptor(None), "name", "NcName", False, False),
                NcFieldDescriptor(
                    NcDescriptor(None), "typeName", "NcName", True, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "isReadOnly", "NcBoolean", False, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "isNullable", "NcBoolean", False, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "isSequence", "NcBoolean", False, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "isDeprecated", "NcBoolean", False, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None),
                    "constraints",
                    "NcParameterConstraints",
                    True,
                    False,
                ),
            ],
            parentType="NcDescriptor",
        )
        if include_inherited:
            base = NcDescriptor.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current

    def to_dict(self) -> dict:
        return {
            "description": self.base.description,
            "id": self.id.to_dict(),
            "name": self.name,
            "typeName": self.typeName,
            "isReadOnly": self.isReadOnly,
            "isNullable": self.isNullable,
            "isSequence": self.isSequence,
            "isDeprecated": self.isDeprecated,
            "constraints": self.constraints.to_dict() if self.constraints else None,
        }


@dataclass
class NcEventDescriptor:
    base: NcDescriptor
    id: ElementId
    name: str
    eventDatatype: str
    isDeprecated: bool

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Descriptor of an event"),
                name="NcEventDescriptor",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(NcDescriptor(None), "id", "NcEventId", False, False),
                NcFieldDescriptor(NcDescriptor(None), "name", "NcName", False, False),
                NcFieldDescriptor(
                    NcDescriptor(None), "eventDatatype", "NcName", False, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "isDeprecated", "NcBoolean", False, False
                ),
            ],
            parentType="NcDescriptor",
        )
        if include_inherited:
            base = NcDescriptor.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current

    def to_dict(self) -> dict:
        return {
            "description": self.base.description,
            "id": self.id.to_dict(),
            "name": self.name,
            "eventDatatype": self.eventDatatype,
            "isDeprecated": self.isDeprecated,
        }


@dataclass
class NcClassDescriptor:
    base: NcDescriptor
    classId: List[int]
    name: str
    fixedRole: Optional[str]
    properties: List[NcPropertyDescriptor]
    methods: List[NcMethodDescriptor]
    events: List[NcEventDescriptor]

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Descriptor of a class"),
                name="NcClassDescriptor",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None), "classId", "NcClassId", False, False
                ),
                NcFieldDescriptor(NcDescriptor(None), "name", "NcName", False, False),
                NcFieldDescriptor(
                    NcDescriptor(None), "fixedRole", "NcString", True, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None),
                    "properties",
                    "NcPropertyDescriptor",
                    False,
                    True,
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "methods", "NcMethodDescriptor", False, True
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "events", "NcEventDescriptor", False, True
                ),
            ],
            parentType="NcDescriptor",
        )
        if include_inherited:
            base = NcDescriptor.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current

    def to_dict(self) -> dict:
        return {
            "description": self.base.description,
            "classId": self.classId,
            "name": self.name,
            "fixedRole": self.fixedRole,
            "properties": [
                p.to_dict() if hasattr(p, "to_dict") else str(p)
                for p in self.properties
            ],
            "methods": [
                m.to_dict() if hasattr(m, "to_dict") else str(m) for m in self.methods
            ],
            "events": [
                e.to_dict() if hasattr(e, "to_dict") else str(e) for e in self.events
            ],
        }


@dataclass
class NcMethodResultClassDescriptor(NcMethodResult):
    value: NcClassDescriptor

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Class descriptor result"),
                name="NcMethodResultClassDescriptor",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None), "value", "NcClassDescriptor", False, False
                )
            ],
            parentType="NcMethodResult",
        )
        if include_inherited:
            base = NcMethodResult.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current


@dataclass
class NcBlockMemberDescriptor:
    base: NcDescriptor
    role: str
    oid: int
    constant_oid: bool
    class_id: List[int]
    user_label: Optional[str]
    owner: int

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Block member descriptor"),
                name="NcBlockMemberDescriptor",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(NcDescriptor(None), "role", "NcString", False, False),
                NcFieldDescriptor(NcDescriptor(None), "oid", "NcOid", False, False),
                NcFieldDescriptor(
                    NcDescriptor(None), "constantOid", "NcBoolean", False, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "classId", "NcClassId", False, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "userLabel", "NcString", True, False
                ),
                NcFieldDescriptor(NcDescriptor(None), "owner", "NcOid", False, False),
            ],
            parentType="NcDescriptor",
        )
        if include_inherited:
            base = NcDescriptor.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current

    def to_dict(self) -> dict:
        return {
            "description": self.base.description,
            "role": self.role,
            "oid": self.oid,
            "constantOid": self.constant_oid,
            "classId": self.class_id,
            "userLabel": self.user_label,
            "owner": self.owner,
        }


@dataclass
class NcMethodResultBlockMemberDescriptors(NcMethodResult):
    value: List[NcBlockMemberDescriptor]

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Block member descriptors result"),
                name="NcMethodResultBlockMemberDescriptors",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None), "value", "NcBlockMemberDescriptor", False, True
                )
            ],
            parentType="NcMethodResult",
        )
        if include_inherited:
            base = NcMethodResult.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current


@dataclass
class NcMethodResultId(NcMethodResult):
    value: int

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Id result"),
                name="NcMethodResultId",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(NcDescriptor(None), "value", "NcId", False, False)
            ],
            parentType="NcMethodResult",
        )
        if include_inherited:
            base = NcMethodResult.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current


@dataclass
class NcMethodResultLength(NcMethodResult):
    value: int

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Length result"),
                name="NcMethodResultLength",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(NcDescriptor(None), "value", "NcUint32", True, False)
            ],
            parentType="NcMethodResult",
        )
        if include_inherited:
            base = NcMethodResult.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current


@dataclass
class NcDatatypeDescriptorTypeDef:
    base: NcDatatypeDescriptor
    parentType: str
    isSequence: bool

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Typedef datatype descriptor"),
                name="NcDatatypeDescriptorTypeDef",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None), "parentType", "NcName", False, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "isSequence", "NcBoolean", False, False
                ),
            ],
            parentType="NcDatatypeDescriptor",
        )
        if include_inherited:
            base = NcDatatypeDescriptor.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current

    def to_dict(self) -> dict:
        base_dict = self.base.to_dict()
        return {
            **base_dict,
            "parentType": self.parentType,
            "isSequence": self.isSequence,
        }


@dataclass
class NcEnumItemDescriptor:
    base: NcDescriptor
    name: str
    value: int

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Descriptor of an enum item"),
                name="NcEnumItemDescriptor",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(NcDescriptor(None), "name", "NcName", False, False),
                NcFieldDescriptor(
                    NcDescriptor(None), "value", "NcUint16", False, False
                ),
            ],
            parentType="NcDescriptor",
        )
        if include_inherited:
            base = NcDescriptor.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current

    def to_dict(self) -> dict:
        base_dict = self.base.to_dict()
        return {**base_dict, "name": self.name, "value": self.value}


@dataclass
class NcDatatypeDescriptorEnum:
    base: NcDatatypeDescriptor
    items: List[NcEnumItemDescriptor]

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Enum datatype descriptor"),
                name="NcDatatypeDescriptorEnum",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None), "items", "NcEnumItemDescriptor", False, True
                ),
            ],
            parentType="NcDatatypeDescriptor",
        )
        if include_inherited:
            base = NcDatatypeDescriptor.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current

    def to_dict(self) -> dict:
        base_dict = self.base.to_dict()
        items_list = [item.to_dict() for item in self.items] if self.items else []
        return {**base_dict, "items": items_list}


@dataclass
class NcPropertyConstraints:
    property_id: ElementId
    default_value: Optional[Any] = None

    def to_dict(self) -> dict:
        return {
            "propertyId": self.property_id.to_dict(),
            "defaultValue": self.default_value,
        }

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        return NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Base property constraints"),
                name="NcPropertyConstraints",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None), "propertyId", "NcPropertyId", False, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "defaultValue", None, True, False
                ),
            ],
            parentType=None,
        )


@dataclass
class NcParameterConstraints:
    defaultValue: Optional[Any] = None

    def to_dict(self) -> dict:
        return {
            "defaultValue": self.defaultValue,
        }

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        return NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Base parameter constraints"),
                name="NcParameterConstraints",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None), "defaultValue", None, True, False
                ),
            ],
            parentType=None,
        )


@dataclass
class NcParameterConstraintsNumber(NcParameterConstraints):
    maximum: Optional[float] = None
    minimum: Optional[float] = None
    step: Optional[float] = None

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Numeric parameter constraints"),
                name="NcParameterConstraintsNumber",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(NcDescriptor(None), "maximum", None, True, False),
                NcFieldDescriptor(NcDescriptor(None), "minimum", None, True, False),
                NcFieldDescriptor(NcDescriptor(None), "step", None, True, False),
            ],
            parentType="NcParameterConstraints",
        )
        if include_inherited:
            base = NcParameterConstraints.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current


@dataclass
class NcParameterConstraintsString(NcParameterConstraints):
    maxCharacters: Optional[int] = None
    pattern: Optional[str] = None

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("String parameter constraints"),
                name="NcParameterConstraintsString",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None), "maxCharacters", "NcUint32", True, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "pattern", "NcRegex", True, False
                ),
            ],
            parentType="NcParameterConstraints",
        )
        if include_inherited:
            base = NcParameterConstraints.get_type_descriptor(True)
            current.fields = list(current.fields) + list(base.fields)
        return current


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
    clocks: List["NmosClock"]
    interfaces: List["NmosInterface"]
    api: "NmosApi"
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

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        return NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Manufacturer descriptor"),
                name="NcManufacturer",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(NcDescriptor(None), "name", "NcString", False, False),
                NcFieldDescriptor(
                    NcDescriptor(None),
                    "organizationId",
                    "NcOrganizationId",
                    True,
                    False,
                ),
                NcFieldDescriptor(NcDescriptor(None), "website", "NcUri", True, False),
            ],
            parentType=None,
        )


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

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        return NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Product descriptor"),
                name="NcProduct",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(NcDescriptor(None), "name", "NcString", False, False),
                NcFieldDescriptor(NcDescriptor(None), "key", "NcString", False, False),
                NcFieldDescriptor(
                    NcDescriptor(None), "revisionLevel", "NcString", False, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "brandName", "NcString", True, False
                ),
                NcFieldDescriptor(NcDescriptor(None), "uuid", "NcUuid", True, False),
                NcFieldDescriptor(
                    NcDescriptor(None), "description", "NcString", True, False
                ),
            ],
            parentType=None,
        )


@dataclass
class NcDeviceOperationalState:
    generic: NcDeviceGenericState
    device_specific_details: Optional[str] = None

    def to_dict(self) -> dict:
        return {
            "generic": int(self.generic),
            "deviceSpecificDetails": self.device_specific_details,
        }

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        return NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Device operational state"),
                name="NcDeviceOperationalState",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None), "generic", "NcDeviceGenericState", False, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None), "deviceSpecificDetails", "NcString", True, False
                ),
            ],
            parentType=None,
        )


@dataclass
class NcTouchpoint:
    context_namespace: str

    def to_dict(self) -> dict:
        return {
            "contextNamespace": self.context_namespace,
        }

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        return NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Touchpoint"),
                name="NcTouchpoint",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None), "contextNamespace", "NcString", False, False
                )
            ],
            parentType=None,
        )


@dataclass
class NcTouchpointResource:
    resource_type: str

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        return NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Touchpoint resource"),
                name="NcTouchpointResource",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None), "resourceType", "NcString", False, False
                )
            ],
            parentType=None,
        )


@dataclass
class NcTouchpointResourceNmos:
    resource_type: str
    id: Any

    def to_dict(self) -> dict:
        return {
            "resourceType": self.resource_type,
            "id": self.id,
        }

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        base = NcTouchpointResource.get_type_descriptor(True)
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Touchpoint NMOS resource"),
                name="NcTouchpointResourceNmos",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(NcDescriptor(None), "id", "NcUuid", False, False)
            ],
            parentType="NcTouchpointResource",
        )
        if include_inherited:
            current.fields = list(current.fields) + list(base.fields)
        return current


@dataclass
class NcTouchpointNmos:
    base: NcTouchpoint
    resource: NcTouchpointResourceNmos

    def to_dict(self) -> dict:
        d = self.base.to_dict()
        d.update({"resource": self.resource.to_dict()})
        return d

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        tp = NcTouchpoint.get_type_descriptor(include_inherited)
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Touchpoint NMOS"),
                name="NcTouchpointNmos",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None),
                    "resource",
                    "NcTouchpointResourceNmos",
                    False,
                    False,
                )
            ],
            parentType="NcTouchpoint",
        )
        if include_inherited:
            current.fields = list(current.fields) + list(tp.fields)
        return current


@dataclass
class NcTouchpointResourceNmosChannelMapping:
    resource_type: str
    id: Any
    io_id: Any

    def to_dict(self) -> dict:
        return {
            "resourceType": self.resource_type,
            "id": self.id,
            "ioId": self.io_id,
        }

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        base = NcTouchpointResourceNmos.get_type_descriptor(True)
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Touchpoint NMOS channel mapping resource"),
                name="NcTouchpointResourceNmosChannelMapping",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(NcDescriptor(None), "ioId", "NcString", False, False)
            ],
            parentType="NcTouchpointResourceNmos",
        )
        if include_inherited:
            current.fields = list(current.fields) + list(base.fields)
        return current


@dataclass
class NcTouchpointNmosChannelMapping:
    base: NcTouchpoint
    resource: NcTouchpointResourceNmosChannelMapping

    def to_dict(self) -> dict:
        d = self.base.to_dict()
        d.update({"resource": self.resource.to_dict()})
        return d

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        tp = NcTouchpoint.get_type_descriptor(include_inherited)
        current = NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Touchpoint NMOS channel mapping"),
                name="NcTouchpointNmosChannelMapping",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None),
                    "resource",
                    "NcTouchpointResourceNmosChannelMapping",
                    False,
                    False,
                )
            ],
            parentType="NcTouchpoint",
        )
        if include_inherited:
            current.fields = list(current.fields) + list(tp.fields)
        return current


@dataclass
class NcPropertyChangedEventData:
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

    @staticmethod
    def get_type_descriptor(include_inherited: bool) -> "NcDatatypeDescriptorStruct":
        return NcDatatypeDescriptorStruct(
            base=NcDatatypeDescriptor(
                base=NcDescriptor("Property changed event data"),
                name="NcPropertyChangedEventData",
                type=NcDatatypeType.Struct,
                constraints=None,
            ),
            fields=[
                NcFieldDescriptor(
                    NcDescriptor(None), "propertyId", "NcPropertyId", False, False
                ),
                NcFieldDescriptor(
                    NcDescriptor(None),
                    "changeType",
                    "NcPropertyChangeType",
                    False,
                    False,
                ),
                NcFieldDescriptor(NcDescriptor(None), "value", None, True, False),
                NcFieldDescriptor(
                    NcDescriptor(None), "sequenceItemIndex", "NcId", True, False
                ),
            ],
            parentType=None,
        )


@dataclass
class PropertyChangedEvent:
    oid: int
    event_id: ElementId
    event_data: NcPropertyChangedEventData

    def to_dict(self) -> dict:
        return {
            "oid": self.oid,
            "eventId": self.event_id.to_dict(),
            "eventData": self.event_data.to_dict(),
        }


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
        event_data=NcPropertyChangedEventData(prop_id, change_type, value, seq_idx),
    )

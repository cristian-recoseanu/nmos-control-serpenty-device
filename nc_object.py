from __future__ import annotations
import asyncio
from abc import ABC, abstractmethod
from typing import Any, List, Optional, TYPE_CHECKING

from data_types import (
    ElementId,
    NcMethodStatus,
    IdArgs,
    IdArgsValue,
    NcPropertyChangeType,
    NcClassDescriptor,
    NcDescriptor,
    NcPropertyDescriptor,
    NcMethodDescriptor,
    NcParameterDescriptor,
    NcEventDescriptor,
    make_event,
)

if TYPE_CHECKING:
    from data_types import (
        NcClassDescriptor,
        NcDescriptor,
        NcPropertyDescriptor,
        NcMethodDescriptor,
        NcParameterDescriptor,
        NcEventDescriptor,
    )
    from data_types import make_event


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
    def get_property(
        self, oid: int, id_args: IdArgs
    ) -> tuple[NcMethodStatus, Optional[str], Any]:
        pass

    @abstractmethod
    def set_property(
        self, oid: int, id_args_value: IdArgsValue
    ) -> tuple[NcMethodStatus, Optional[str], Any]:
        pass

    @abstractmethod
    def invoke_method(
        self, oid: int, method_id: ElementId, args: Any
    ) -> tuple[NcMethodStatus, Optional[str], Any]:
        pass


class NcObject(NcMember):
    def __init__(
        self,
        notifier,
        class_id,
        oid,
        constant_oid,
        owner,
        role,
        user_label,
        touchpoints: Optional[List[Any]],
        runtime_property_constraints: Optional[List[Any]],
    ):
        self.class_id, self.oid, self.constant_oid = class_id, oid, constant_oid
        self.owner, self.role, self.user_label = owner, role, user_label
        self.touchpoints = touchpoints
        self.runtime_property_constraints = runtime_property_constraints
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
            (1, 7): None
            if self.touchpoints is None
            else [tp.to_dict() for tp in self.touchpoints],
            (1, 8): None
            if self.runtime_property_constraints is None
            else [c.to_dict() for c in self.runtime_property_constraints],
        }
        key = (id_args.id.level, id_args.id.index)
        if key in mapping:
            return NcMethodStatus.Ok, None, mapping[key]
        return (
            NcMethodStatus.PropertyNotImplemented,
            "Could not find the property",
            None,
        )

    async def _notify(self, prop_id, change_type, value, seq_idx=None):
        await self.notifier.put(
            make_event(self.oid, prop_id, change_type, value, seq_idx)
        )

    def set_property(self, oid, id_args_value):
        if id_args_value.id.level == 1 and id_args_value.id.index == 6:
            if isinstance(id_args_value.value, str):
                self.user_label = id_args_value.value
            elif id_args_value.value is None:
                self.user_label = None
            else:
                return (
                    NcMethodStatus.ParameterError,
                    "Property value was invalid",
                    False,
                )
            asyncio.create_task(
                self._notify(
                    id_args_value.id,
                    NcPropertyChangeType.ValueChanged,
                    self.user_label,
                )
            )
            return NcMethodStatus.Ok, None, True
        elif id_args_value.id.level == 1 and (
            id_args_value.id.index == 1
            or id_args_value.id.index == 2
            or id_args_value.id.index == 3
            or id_args_value.id.index == 4
            or id_args_value.id.index == 5
            or id_args_value.id.index == 7
            or id_args_value.id.index == 8
        ):
            return (
                NcMethodStatus.Readonly,
                "Property is readonly",
                False,
            )
        return (
            NcMethodStatus.PropertyNotImplemented,
            "Could not find the property",
            False,
        )

    def invoke_method(self, oid, method_id, args):
        if method_id.level == 1 and method_id.index == 3:  # GetSequenceItem (1m3)
            if not isinstance(args, dict):
                return NcMethodStatus.ParameterError, "Invalid arguments", None

            if "id" not in args or "index" not in args:
                return NcMethodStatus.ParameterError, "Invalid arguments", None

            if not isinstance(args.get("index"), int) or args["index"] < 0:
                return NcMethodStatus.ParameterError, "Invalid index parameter", None

            prop_id = args.get("id", {})
            if not isinstance(prop_id, dict):
                return NcMethodStatus.ParameterError, "Invalid id parameter", None

            level = prop_id.get("level")
            index = prop_id.get("index")

            # Handle touchpoints (1p7)
            if level == 1 and index == 7:
                touchpoints = self.touchpoints or []
                if args["index"] >= len(touchpoints):
                    return (
                        NcMethodStatus.IndexOutOfBounds,
                        f"Index {args['index']} out of bounds",
                        None,
                    )
                return (
                    NcMethodStatus.Ok,
                    None,
                    touchpoints[args["index"]].to_dict()
                    if touchpoints[args["index"]]
                    else None,
                )

            # Handle runtimePropertyConstraints (1p8)
            elif level == 1 and index == 8:
                constraints = self.runtime_property_constraints or []
                if args["index"] >= len(constraints):
                    return (
                        NcMethodStatus.IndexOutOfBounds,
                        f"Index {args['index']} out of bounds",
                        None,
                    )
                return (
                    NcMethodStatus.Ok,
                    None,
                    constraints[args["index"]].to_dict()
                    if constraints[args["index"]]
                    else None,
                )

            return NcMethodStatus.ParameterError, "Invalid property", None

        elif method_id.level == 1 and method_id.index == 7:  # GetSequenceLength (1m7)
            if not isinstance(args, dict) or "id" not in args:
                return NcMethodStatus.ParameterError, "Invalid arguments", None

            prop_id = args.get("id", {})
            if not isinstance(prop_id, dict):
                return NcMethodStatus.ParameterError, "Invalid id parameter", None

            level = prop_id.get("level")
            index = prop_id.get("index")

            # Handle touchpoints (1p7)
            if level == 1 and index == 7:
                return NcMethodStatus.Ok, None, len(self.touchpoints or [])

            # Handle runtimePropertyConstraints (1p8)
            elif level == 1 and index == 8:
                return (
                    NcMethodStatus.Ok,
                    None,
                    len(self.runtime_property_constraints or []),
                )

            return NcMethodStatus.ParameterError, "Invalid property", None

        return NcMethodStatus.MethodNotImplemented, "Method not implemented", None

    @staticmethod
    def get_class_descriptor(include_inherited: bool = True) -> NcClassDescriptor:
        properties = [
            NcPropertyDescriptor(
                base=NcDescriptor(
                    "Static value. All instances of the same class will have the same identity value"
                ),
                id=ElementId(1, 1),
                name="classId",
                typeName="NcClassId",
                isReadOnly=True,
                isNullable=False,
                isSequence=False,
                isDeprecated=False,
                constraints=None,
            ),
            NcPropertyDescriptor(
                base=NcDescriptor("Object identifier"),
                id=ElementId(1, 2),
                name="oid",
                typeName="NcOid",
                isReadOnly=True,
                isNullable=False,
                isSequence=False,
                isDeprecated=False,
                constraints=None,
            ),
            NcPropertyDescriptor(
                base=NcDescriptor("TRUE iff OID is hardwired into device"),
                id=ElementId(1, 3),
                name="constantOid",
                typeName="NcBoolean",
                isReadOnly=True,
                isNullable=False,
                isSequence=False,
                isDeprecated=False,
                constraints=None,
            ),
            NcPropertyDescriptor(
                base=NcDescriptor(
                    "OID of containing block. Can only ever be null for the root block"
                ),
                id=ElementId(1, 4),
                name="owner",
                typeName="NcOid",
                isReadOnly=True,
                isNullable=True,
                isSequence=False,
                isDeprecated=False,
                constraints=None,
            ),
            NcPropertyDescriptor(
                base=NcDescriptor("role of obj in containing block"),
                id=ElementId(1, 5),
                name="role",
                typeName="NcString",
                isReadOnly=True,
                isNullable=False,
                isSequence=False,
                isDeprecated=False,
                constraints=None,
            ),
            NcPropertyDescriptor(
                base=NcDescriptor("Scribble strip"),
                id=ElementId(1, 6),
                name="userLabel",
                typeName="NcString",
                isReadOnly=False,
                isNullable=True,
                isSequence=False,
                isDeprecated=False,
                constraints=None,
            ),
            NcPropertyDescriptor(
                base=NcDescriptor("Touchpoints to other contexts"),
                id=ElementId(1, 7),
                name="touchpoints",
                typeName="NcTouchpoint",
                isReadOnly=True,
                isNullable=True,
                isSequence=True,
                isDeprecated=False,
                constraints=None,
            ),
            NcPropertyDescriptor(
                base=NcDescriptor("Runtime property constraints"),
                id=ElementId(1, 8),
                name="runtimePropertyConstraints",
                typeName="NcPropertyConstraints",
                isReadOnly=True,
                isNullable=True,
                isSequence=True,
                isDeprecated=False,
                constraints=None,
            ),
        ]

        methods = [
            NcMethodDescriptor(
                base=NcDescriptor("Get property value"),
                id=ElementId(1, 1),
                name="Get",
                resultDatatype="NcMethodResultPropertyValue",
                parameters=[
                    NcParameterDescriptor(
                        base=NcDescriptor("Property id"),
                        name="id",
                        typeName="NcPropertyId",
                        isNullable=False,
                        isSequence=False,
                        constraints=None,
                    )
                ],
                isDeprecated=False,
            ),
            NcMethodDescriptor(
                base=NcDescriptor("Set property value"),
                id=ElementId(1, 2),
                name="Set",
                resultDatatype="NcMethodResult",
                parameters=[
                    NcParameterDescriptor(
                        base=NcDescriptor("Property id"),
                        name="id",
                        typeName="NcPropertyId",
                        isNullable=False,
                        isSequence=False,
                        constraints=None,
                    ),
                    NcParameterDescriptor(
                        base=NcDescriptor("Property value"),
                        name="value",
                        typeName=None,
                        isNullable=True,
                        isSequence=False,
                        constraints=None,
                    ),
                ],
                isDeprecated=False,
            ),
            NcMethodDescriptor(
                base=NcDescriptor("Get sequence item"),
                id=ElementId(1, 3),
                name="GetSequenceItem",
                resultDatatype="NcMethodResultPropertyValue",
                parameters=[
                    NcParameterDescriptor(
                        base=NcDescriptor("Property id"),
                        name="id",
                        typeName="NcPropertyId",
                        isNullable=False,
                        isSequence=False,
                        constraints=None,
                    ),
                    NcParameterDescriptor(
                        base=NcDescriptor("Index of item in the sequence"),
                        name="index",
                        typeName="NcId",
                        isNullable=False,
                        isSequence=False,
                        constraints=None,
                    ),
                ],
                isDeprecated=False,
            ),
            NcMethodDescriptor(
                base=NcDescriptor("Set sequence item value"),
                id=ElementId(1, 4),
                name="SetSequenceItem",
                resultDatatype="NcMethodResult",
                parameters=[
                    NcParameterDescriptor(
                        base=NcDescriptor("Property id"),
                        name="id",
                        typeName="NcPropertyId",
                        isNullable=False,
                        isSequence=False,
                        constraints=None,
                    ),
                    NcParameterDescriptor(
                        base=NcDescriptor("Index of item in the sequence"),
                        name="index",
                        typeName="NcId",
                        isNullable=False,
                        isSequence=False,
                        constraints=None,
                    ),
                    NcParameterDescriptor(
                        base=NcDescriptor("Value"),
                        name="value",
                        typeName=None,
                        isNullable=True,
                        isSequence=False,
                        constraints=None,
                    ),
                ],
                isDeprecated=False,
            ),
            NcMethodDescriptor(
                base=NcDescriptor("Add item to sequence"),
                id=ElementId(1, 5),
                name="AddSequenceItem",
                resultDatatype="NcMethodResultId",
                parameters=[
                    NcParameterDescriptor(
                        base=NcDescriptor("Property id"),
                        name="id",
                        typeName="NcPropertyId",
                        isNullable=False,
                        isSequence=False,
                        constraints=None,
                    ),
                    NcParameterDescriptor(
                        base=NcDescriptor("Value"),
                        name="value",
                        typeName=None,
                        isNullable=True,
                        isSequence=False,
                        constraints=None,
                    ),
                ],
                isDeprecated=False,
            ),
            NcMethodDescriptor(
                base=NcDescriptor("Delete sequence item"),
                id=ElementId(1, 6),
                name="RemoveSequenceItem",
                resultDatatype="NcMethodResult",
                parameters=[
                    NcParameterDescriptor(
                        base=NcDescriptor("Property id"),
                        name="id",
                        typeName="NcPropertyId",
                        isNullable=False,
                        isSequence=False,
                        constraints=None,
                    ),
                    NcParameterDescriptor(
                        base=NcDescriptor("Index of item in the sequence"),
                        name="index",
                        typeName="NcId",
                        isNullable=False,
                        isSequence=False,
                        constraints=None,
                    ),
                ],
                isDeprecated=False,
            ),
            NcMethodDescriptor(
                base=NcDescriptor("Get sequence length"),
                id=ElementId(1, 7),
                name="GetSequenceLength",
                resultDatatype="NcMethodResultLength",
                parameters=[
                    NcParameterDescriptor(
                        base=NcDescriptor("Property id"),
                        name="id",
                        typeName="NcPropertyId",
                        isNullable=False,
                        isSequence=False,
                        constraints=None,
                    )
                ],
                isDeprecated=False,
            ),
        ]

        events = [
            NcEventDescriptor(
                base=NcDescriptor("Property changed event"),
                id=ElementId(1, 1),
                name="PropertyChanged",
                eventDatatype="NcPropertyChangedEventData",
                isDeprecated=False,
            )
        ]

        desc = NcClassDescriptor(
            base=NcDescriptor("NcObject class descriptor"),
            classId=[1],
            name="NcObject",
            fixedRole=None,
            properties=properties,
            methods=methods,
            events=events,
        )
        return desc

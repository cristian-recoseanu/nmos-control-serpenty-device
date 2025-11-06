from __future__ import annotations
from typing import Any, List, Optional, TYPE_CHECKING

from data_types import (
    ElementId,
    NcMethodStatus,
    NcPropertyChangeType,
    IdArgs,
    IdArgsValue,
    make_event,
)

from nc_object import NcMember, NcObject

if TYPE_CHECKING:
    from data_types import NcClassDescriptor


class NcWorker(NcMember):
    def __init__(
        self,
        class_id: List[int],
        oid: int,
        constant_oid: bool,
        owner: Optional[Any],
        role: str,
        user_label: Optional[str] = None,
        enabled: bool = True,
        touchpoints: Optional[List[Any]] = None,
        runtime_property_constraints: Optional[List[Any]] = None,
        notifier=None,
    ):
        self.base = NcObject(
            notifier=notifier,
            class_id=class_id,
            oid=oid,
            constant_oid=constant_oid,
            owner=owner,
            role=role,
            user_label=user_label,
            touchpoints=touchpoints,
            runtime_property_constraints=runtime_property_constraints,
        )
        self.enabled = enabled

    def member_type(self) -> str:
        return "NcWorker"

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

    def get_property(
        self, oid: int, id_args: IdArgs
    ) -> tuple[NcMethodStatus, Optional[str], Any]:
        if oid == self.base.oid:
            # Handle NcWorker specific properties
            if (
                id_args.id.level == 2 and id_args.id.index == 1
            ):  # 2.1 for enabled property
                return NcMethodStatus.Ok, None, self.enabled

            # Delegate to base class for other properties
            return self.base.get_property(oid, id_args)

        return NcMethodStatus.BadOid, "Object not found", None

    def set_property(
        self, oid: int, id_args_value: IdArgsValue
    ) -> tuple[NcMethodStatus, Optional[str], Any]:
        if oid == self.base.oid:
            # Handle NcWorker specific properties
            if (
                id_args_value.id.level == 2 and id_args_value.id.index == 1
            ):  # 2.1 for enabled property
                if isinstance(id_args_value.value, bool):
                    old_value = self.enabled
                    self.enabled = id_args_value.value

                    # Notify about the property change if value actually changed
                    if old_value != self.enabled and self.base.notifier:
                        event = make_event(
                            oid=oid,
                            prop_id=id_args_value.id,
                            change_type=NcPropertyChangeType.ValueChanged,
                            value=self.enabled,
                        )
                        self.base.notifier(event)

                    return NcMethodStatus.Ok, None, old_value
                else:
                    return (
                        NcMethodStatus.ParameterError,
                        "Invalid value type for enabled property",
                        None,
                    )

            # Delegate to base class for other properties
            return self.base.set_property(oid, id_args_value)

        return NcMethodStatus.BadOid, "Object not found", None

    def invoke_method(
        self, oid: int, method_id: ElementId, args: Any
    ) -> tuple[NcMethodStatus, Optional[str], Any]:
        if oid == self.base.oid:
            # No methods specific to NcWorker, delegate to base class
            return self.base.invoke_method(oid, method_id, args)

        return NcMethodStatus.BadOid, "Object not found", None

    @staticmethod
    def get_class_descriptor(include_inherited: bool = True) -> "NcClassDescriptor":
        from data_types import NcClassDescriptor, NcDescriptor
        from data_types import (
            NcPropertyDescriptor,
            NcMethodDescriptor,
            NcEventDescriptor,
        )

        properties: list[NcPropertyDescriptor] = []
        methods: list[NcMethodDescriptor] = []
        events: list[NcEventDescriptor] = []

        # Add NcWorker specific properties
        properties.append(
            NcPropertyDescriptor(
                base=NcDescriptor("enabled"),
                id=ElementId(level=2, index=1),
                name="enabled",
                typeName="NcBoolean",
                isReadOnly=False,
                isNullable=False,
                isSequence=False,
                isDeprecated=False,
                constraints=None,
            )
        )

        if include_inherited:
            base = NcObject.get_class_descriptor(True)
            properties = [*properties, *base.properties]
            methods = [*methods, *base.methods]
            events = [*events, *base.events]

        return NcClassDescriptor(
            base=NcDescriptor("NcWorker class descriptor"),
            classId=[1, 2],
            name="NcWorker",
            fixedRole=None,
            properties=properties,
            methods=methods,
            events=events,
        )

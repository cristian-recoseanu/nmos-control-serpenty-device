from __future__ import annotations
from typing import Any, Optional, List, TYPE_CHECKING

from data_types import IdArgs, IdArgsValue, NcMethodStatus
from nc_object import NcMember, NcObject

if TYPE_CHECKING:
    from data_types import NcClassDescriptor


class NcManager(NcMember):
    def __init__(
        self,
        notifier,
        class_id: List[int],
        oid: int,
        constant_oid: bool,
        owner: Optional[int],
        role: str,
        user_label: Optional[str],
        touchpoints: Optional[List[Any]] = None,
        runtime_property_constraints: Optional[List[Any]] = None,
    ):
        self.base = NcObject(
            notifier,
            class_id=class_id,
            oid=oid,
            constant_oid=constant_oid,
            owner=owner,
            role=role,
            user_label=user_label,
            touchpoints=touchpoints,
            runtime_property_constraints=runtime_property_constraints,
        )

    def member_type(self) -> str:
        return "NcManager"

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
        return self.base.get_property(oid, id_args)

    def set_property(
        self, oid: int, id_args_value: IdArgsValue
    ) -> tuple[NcMethodStatus, Optional[str], Any]:
        return self.base.set_property(oid, id_args_value)

    def invoke_method(
        self, oid: int, method_id, args: Any
    ) -> tuple[NcMethodStatus, Optional[str], Any]:
        return self.base.invoke_method(oid, method_id, args)

    async def _notify(self, prop_id, change_type, value, seq_idx=None):
        await self.base._notify(prop_id, change_type, value, seq_idx)

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

        if include_inherited:
            base = NcObject.get_class_descriptor(True)
            properties = [*properties, *base.properties]
            methods = [*methods, *base.methods]
            events = [*events, *base.events]

        return NcClassDescriptor(
            base=NcDescriptor("NcManager class descriptor"),
            classId=[1, 3],
            name="NcManager",
            fixedRole=None,
            properties=properties,
            methods=methods,
            events=events,
        )

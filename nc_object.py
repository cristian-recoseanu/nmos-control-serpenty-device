import asyncio
from abc import ABC, abstractmethod
from typing import Any, List, Optional

from data_types import (
    ElementId,
    IdArgs,
    IdArgsValue,
    NcPropertyChangeType,
    make_event,
)


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

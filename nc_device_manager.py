import asyncio
from typing import Any, List, Optional

from data_types import (
    ElementId,
    IdArgs,
    IdArgsValue,
    NcMethodStatus,
    NcDeviceGenericState,
    NcDeviceOperationalState,
    NcManufacturer,
    NcProduct,
    NcPropertyChangeType,
    NcResetCause,
)
from nc_object import NcMember, NcObject


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

    def get_property(
        self, _oid: int, id_args: IdArgs
    ) -> tuple[NcMethodStatus, Optional[str], Any]:
        # properties at level 3 -> map indexes to fields
        lvl, idx = id_args.id.level, id_args.id.index
        if lvl == 3:
            if idx == 1:
                return NcMethodStatus.Ok, None, self.nc_version
            if idx == 2:
                return NcMethodStatus.Ok, None, self.manufacturer.to_dict()
            if idx == 3:
                return NcMethodStatus.Ok, None, self.product.to_dict()
            if idx == 4:
                return NcMethodStatus.Ok, None, self.serial_number
            if idx == 5:
                return NcMethodStatus.Ok, None, self.user_inventory_code
            if idx == 6:
                return NcMethodStatus.Ok, None, self.device_name
            if idx == 7:
                return NcMethodStatus.Ok, None, self.device_role
            if idx == 8:
                return NcMethodStatus.Ok, None, self.operational_state.to_dict()
            if idx == 9:
                return NcMethodStatus.Ok, None, int(self.reset_cause)
            if idx == 10:
                return NcMethodStatus.Ok, None, self.message
            return NcMethodStatus.BadOid, "Property not found", None
        # fall back to base object
        return self.base.get_property(_oid, id_args)

    def set_property(
        self, _oid: int, id_args_value: IdArgsValue
    ) -> tuple[NcMethodStatus, Optional[str], Any]:
        if id_args_value.id.level == 3:
            idx = id_args_value.id.index
            # 5: userInventoryCode
            if idx == 5:
                if id_args_value.value is None:
                    self.user_inventory_code = None
                elif isinstance(id_args_value.value, str):
                    self.user_inventory_code = id_args_value.value
                else:
                    return (
                        NcMethodStatus.ParameterError,
                        "Property value was invalid",
                        False,
                    )
                asyncio.create_task(
                    self.base._notify(
                        id_args_value.id,
                        NcPropertyChangeType.ValueChanged,
                        self.user_inventory_code,
                    )
                )
                return NcMethodStatus.Ok, None, True
            # 6: deviceName
            if idx == 6:
                if id_args_value.value is None:
                    self.device_name = None
                elif isinstance(id_args_value.value, str):
                    self.device_name = id_args_value.value
                else:
                    return (
                        NcMethodStatus.ParameterError,
                        "Property value was invalid",
                        False,
                    )
                asyncio.create_task(
                    self.base._notify(
                        id_args_value.id,
                        NcPropertyChangeType.ValueChanged,
                        self.device_name,
                    )
                )
                return NcMethodStatus.Ok, None, True
            # 7: deviceRole
            if idx == 7:
                if id_args_value.value is None:
                    self.device_role = None
                elif isinstance(id_args_value.value, str):
                    self.device_role = id_args_value.value
                else:
                    return (
                        NcMethodStatus.ParameterError,
                        "Property value was invalid",
                        False,
                    )
                asyncio.create_task(
                    self.base._notify(
                        id_args_value.id,
                        NcPropertyChangeType.ValueChanged,
                        self.device_role,
                    )
                )
                return NcMethodStatus.Ok, None, True
            # Other level-3 properties are read-only
            return (
                NcMethodStatus.Readonly,
                "Could not find the property or it is read-only",
                False,
            )
        # not level 3 => delegate to base
        return self.base.set_property(_oid, id_args_value)

    def invoke_method(
        self, _oid: int, method_id: ElementId, args: Any
    ) -> tuple[NcMethodStatus, Optional[str], Any]:
        # No methods on NcDeviceManager itself in this implementation - delegate to base
        return self.base.invoke_method(_oid, method_id, args)

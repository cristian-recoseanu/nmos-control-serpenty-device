from __future__ import annotations
import asyncio
from typing import Any, List, Optional, TYPE_CHECKING

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
    NcClassDescriptor,
    NcDescriptor,
    NcPropertyDescriptor,
    NcMethodDescriptor,
    NcEventDescriptor,
)

if TYPE_CHECKING:
    from data_types import (
        NcClassDescriptor,
        NcDescriptor,
        NcPropertyDescriptor,
        NcMethodDescriptor,
        NcEventDescriptor,
    )
from nc_object import NcMember
from nc_manager import NcManager


class NcDeviceManager(NcMember):
    def __init__(
        self,
        notifier: asyncio.Queue,
        oid: int,
        constant_oid: bool,
        owner: Optional[int],
        role: str,
        user_label: Optional[str],
        nc_version: str,
        manufacturer: NcManufacturer,
        product: NcProduct,
        serial_number: str,
        touchpoints: Optional[List[Any]] = None,
        runtime_property_constraints: Optional[List[Any]] = None,
    ):
        self.base = NcManager(
            notifier,
            class_id=[1, 3, 1],
            oid=oid,
            constant_oid=constant_oid,
            owner=owner,
            role=role,
            user_label=user_label,
            touchpoints=touchpoints,
            runtime_property_constraints=runtime_property_constraints,
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
            return (
                NcMethodStatus.PropertyNotImplemented,
                "Could not find the property",
                None,
            )
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
        # No methods on NcDeviceManager - delegate to base
        return self.base.invoke_method(_oid, method_id, args)

    @staticmethod
    def get_class_descriptor(include_inherited: bool = True) -> "NcClassDescriptor":
        properties = [
            NcPropertyDescriptor(
                NcDescriptor(None),
                ElementId(3, 1),
                "ncVersion",
                "NcVersionCode",
                True,
                False,
                False,
                False,
                None,
            ),
            NcPropertyDescriptor(
                NcDescriptor(None),
                ElementId(3, 2),
                "manufacturer",
                "NcManufacturer",
                True,
                False,
                False,
                False,
                None,
            ),
            NcPropertyDescriptor(
                NcDescriptor(None),
                ElementId(3, 3),
                "product",
                "NcProduct",
                True,
                False,
                False,
                False,
                None,
            ),
            NcPropertyDescriptor(
                NcDescriptor(None),
                ElementId(3, 4),
                "serialNumber",
                "NcString",
                True,
                False,
                False,
                False,
                None,
            ),
            NcPropertyDescriptor(
                NcDescriptor(None),
                ElementId(3, 5),
                "userInventoryCode",
                "NcString",
                False,
                True,
                False,
                False,
                None,
            ),
            NcPropertyDescriptor(
                NcDescriptor(None),
                ElementId(3, 6),
                "deviceName",
                "NcString",
                False,
                True,
                False,
                False,
                None,
            ),
            NcPropertyDescriptor(
                NcDescriptor(None),
                ElementId(3, 7),
                "deviceRole",
                "NcString",
                False,
                True,
                False,
                False,
                None,
            ),
            NcPropertyDescriptor(
                NcDescriptor(None),
                ElementId(3, 8),
                "operationalState",
                "NcDeviceOperationalState",
                True,
                False,
                False,
                False,
                None,
            ),
            NcPropertyDescriptor(
                NcDescriptor(None),
                ElementId(3, 9),
                "resetCause",
                "NcResetCause",
                True,
                False,
                False,
                False,
                None,
            ),
            NcPropertyDescriptor(
                NcDescriptor(None),
                ElementId(3, 10),
                "message",
                "NcString",
                True,
                True,
                False,
                False,
                None,
            ),
        ]

        methods: list[NcMethodDescriptor] = []
        events: list[NcEventDescriptor] = []

        if include_inherited:
            base = NcManager.get_class_descriptor(True)
            properties = [*properties, *base.properties]
            methods = [*methods, *base.methods]
            events = [*events, *base.events]

        return NcClassDescriptor(
            base=NcDescriptor("NcDeviceManager class descriptor"),
            classId=[1, 3, 1],
            name="NcDeviceManager",
            fixedRole="DeviceManager",
            properties=properties,
            methods=methods,
            events=events,
        )

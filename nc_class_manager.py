from __future__ import annotations
from typing import Any, Dict, List, Optional, TYPE_CHECKING

from data_types import (
    IdArgs,
    IdArgsValue,
    NcMethodStatus,
    NcDescriptor,
    NcDatatypeType,
    NcDatatypeDescriptor,
    NcDatatypeDescriptorTypeDef,
    NcDatatypeDescriptorStruct,
    NcDatatypeDescriptorEnum,
    NcEnumItemDescriptor,
    NcDeviceGenericState,
    NcParameterDescriptor,
    NcPropertyChangeType,
    NcResetCause,
)

if TYPE_CHECKING:
    from data_types import (
        NcClassDescriptor,
        NcEventDescriptor,
    )

from nc_manager import NcManager
from nc_object import NcMember, NcObject
from nc_device_manager import NcDeviceManager
from nc_block import NcBlock
from nc_worker import NcWorker


class NcClassManager(NcMember):
    def __init__(
        self,
        notifier,
        oid: int,
        constant_oid: bool,
        owner: Optional[int],
        role: str = "ClassManager",
        user_label: Optional[str] = None,
        touchpoints: Optional[List[Any]] = None,
        runtime_property_constraints: Optional[List[Any]] = None,
    ) -> None:
        self.base = NcManager(
            notifier,
            class_id=[1, 3, 2],
            oid=oid,
            constant_oid=constant_oid,
            owner=owner,
            role=role,
            user_label=user_label,
            touchpoints=touchpoints,
            runtime_property_constraints=runtime_property_constraints,
        )
        self._control_classes = self._generate_class_descriptors()
        self._datatypes = self._generate_type_descriptors()

    def member_type(self) -> str:
        return "NcClassManager"

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

    @staticmethod
    def _class_id_key(class_id: List[int]) -> str:
        return ".".join(str(x) for x in class_id)

    def _generate_class_descriptors(self) -> Dict[str, dict]:
        reg: Dict[str, dict] = {}

        def add(cls_id: List[int], desc_any):
            reg[self._class_id_key(cls_id)] = desc_any

        add([1], NcObject.get_class_descriptor(False).to_dict())
        add([1, 1], NcBlock.get_class_descriptor(False).to_dict())
        add([1, 2], NcWorker.get_class_descriptor(False).to_dict())
        add([1, 3], NcManager.get_class_descriptor(False).to_dict())
        add([1, 3, 1], NcDeviceManager.get_class_descriptor(False).to_dict())
        add([1, 3, 2], NcClassManager.get_class_descriptor(False).to_dict())

        return reg

    def _generate_type_descriptors(self) -> Dict[str, Any]:
        reg: Dict[str, Any] = {}

        def add_primitive(name: str, description: str = ""):
            reg[name] = NcDatatypeDescriptor(
                base=NcDescriptor(description or None),
                name=name,
                type=NcDatatypeType.Primitive,
                constraints=None,
            )

        def add_typedef(
            name: str, parent: str, is_sequence: bool, description: str = ""
        ):
            reg[name] = NcDatatypeDescriptorTypeDef(
                base=NcDatatypeDescriptor(
                    base=NcDescriptor(description or None),
                    name=name,
                    type=NcDatatypeType.Typedef,
                    constraints=None,
                ),
                parentType=parent,
                isSequence=is_sequence,
            )

        def add_enum_from_intenum(name: str, enum_cls, description: str = ""):
            items = [
                NcEnumItemDescriptor(
                    base=NcDescriptor(None), name=member.name, value=int(member.value)
                )
                for member in enum_cls
            ]
            reg[name] = NcDatatypeDescriptorEnum(
                base=NcDatatypeDescriptor(
                    base=NcDescriptor(description or None),
                    name=name,
                    type=NcDatatypeType.Enum,
                    constraints=None,
                ),
                items=items,
            )

        add_primitive("NcBoolean", "Boolean value")
        add_primitive("NcInt16", "16-bit signed integer")
        add_primitive("NcInt32", "32-bit signed integer")
        add_primitive("NcInt64", "64-bit signed integer")
        add_primitive("NcUint16", "16-bit unsigned integer")
        add_primitive("NcUint32", "32-bit unsigned integer")
        add_primitive("NcUint64", "64-bit unsigned integer")
        add_primitive("NcFloat32", "32-bit floating point")
        add_primitive("NcFloat64", "64-bit floating point")
        add_primitive("NcString", "String value")

        add_typedef("NcName", "NcString", False, "Programmatically significant name")
        add_typedef("NcRolePath", "NcString", True, "Role path")
        add_typedef("NcRegex", "NcString", False, "Regex pattern")
        add_typedef("NcRole", "NcString", False, "Role string")
        add_typedef("NcClassId", "NcInt32", True, "Sequence of class ID fields")
        add_typedef("NcId", "NcUint32", False, "Identifier handler")
        add_typedef("NcOid", "NcUint32", False, "Object id")
        add_typedef(
            "NcOrganizationId", "NcInt32", False, "Unique 24-bit organization id"
        )
        add_typedef("NcUri", "NcString", False, "Uniform resource identifier")
        add_typedef("NcVersionCode", "NcString", False, "Semantic version code")
        add_typedef("NcUuid", "NcString", False, "UUID")
        add_typedef("NcTimeInterval", "NcInt64", False, "Nanoseconds interval")

        add_enum_from_intenum(
            "NcMethodStatus", NcMethodStatus, "Method invokation status"
        )
        add_enum_from_intenum("NcDatatypeType", NcDatatypeType, "Datatype type kind")
        add_enum_from_intenum(
            "NcDeviceGenericState", NcDeviceGenericState, "Device generic state"
        )
        add_enum_from_intenum(
            "NcResetCause", NcResetCause, "Reason for most recent reset"
        )
        add_enum_from_intenum(
            "NcPropertyChangeType", NcPropertyChangeType, "Type of property change"
        )

        from data_types import (
            NcElementId as _NcElementIdType,
            NcPropertyId as _NcPropertyIdType,
            NcMethodId as _NcMethodIdType,
            NcEventId as _NcEventIdType,
            NcDescriptor as _NcDescriptorType,
            NcDatatypeDescriptor as _NcDatatypeDescriptorType,
            NcDatatypeDescriptorStruct as _NcDatatypeDescriptorStructType,
            NcDatatypeDescriptorTypeDef as _NcDatatypeDescriptorTypeDefType,
            NcDatatypeDescriptorEnum as _NcDatatypeDescriptorEnumType,
            NcDatatypeDescriptorPrimitive as _NcDatatypeDescriptorPrimitiveType,
            NcFieldDescriptor as _NcFieldDescriptorType,
            NcEnumItemDescriptor as _NcEnumItemDescriptorType,
            NcParameterDescriptor as _NcParameterDescriptorType,
            NcMethodDescriptor as _NcMethodDescriptorType,
            NcPropertyDescriptor as _NcPropertyDescriptorType,
            NcEventDescriptor as _NcEventDescriptorType,
            NcClassDescriptor as _NcClassDescriptorType,
            NcBlockMemberDescriptor as _NcBlockMemberDescriptorType,
            NcMethodResult as _NcMethodResultType,
            NcMethodResultPropertyValue as _NcMethodResultPropertyValueType,
            NcMethodResultDatatypeDescriptor as _NcMethodResultDatatypeDescriptorType,
            NcMethodResultClassDescriptor as _NcMethodResultClassDescriptorType,
            NcMethodResultId as _NcMethodResultIdType,
            NcMethodResultLength as _NcMethodResultLengthType,
            NcMethodResultError as _NcMethodResultErrorType,
            NcMethodResultBlockMemberDescriptors as _NcMethodResultBlockMemberDescriptorsType,
            NcPropertyConstraints as _NcPropertyConstraintsType,
            NcPropertyConstraintsNumber as _NcPropertyConstraintsNumberType,
            NcPropertyConstraintsString as _NcPropertyConstraintsStringType,
            NcParameterConstraints as _NcParameterConstraintsType,
            NcParameterConstraintsNumber as _NcParameterConstraintsNumberType,
            NcParameterConstraintsString as _NcParameterConstraintsStringType,
            NcManufacturer as _NcManufacturerType,
            NcProduct as _NcProductType,
            NcDeviceOperationalState as _NcDeviceOperationalStateType,
            NcTouchpoint as _NcTouchpointType,
            NcTouchpointResource as _NcTouchpointResourceType,
            NcTouchpointResourceNmos as _NcTouchpointResourceNmosType,
            NcTouchpointResourceNmosChannelMapping as _NcTouchpointResourceNmosChannelMappingType,
            NcTouchpointNmos as _NcTouchpointNmosType,
            NcTouchpointNmosChannelMapping as _NcTouchpointNmosChannelMappingType,
            NcPropertyChangedEventData as _NcPropertyChangedEventDataType,
        )

        struct_types: List[Any] = [
            _NcElementIdType,
            _NcPropertyIdType,
            _NcMethodIdType,
            _NcEventIdType,
            _NcDescriptorType,
            _NcDatatypeDescriptorType,
            _NcDatatypeDescriptorStructType,
            _NcDatatypeDescriptorTypeDefType,
            _NcDatatypeDescriptorEnumType,
            _NcDatatypeDescriptorPrimitiveType,
            _NcFieldDescriptorType,
            _NcEnumItemDescriptorType,
            _NcParameterDescriptorType,
            _NcMethodDescriptorType,
            _NcPropertyDescriptorType,
            _NcEventDescriptorType,
            _NcClassDescriptorType,
            _NcBlockMemberDescriptorType,
            _NcMethodResultType,
            _NcMethodResultPropertyValueType,
            _NcMethodResultDatatypeDescriptorType,
            _NcMethodResultClassDescriptorType,
            _NcMethodResultIdType,
            _NcMethodResultLengthType,
            _NcMethodResultErrorType,
            _NcMethodResultBlockMemberDescriptorsType,
            _NcPropertyConstraintsType,
            _NcPropertyConstraintsNumberType,
            _NcPropertyConstraintsStringType,
            _NcParameterConstraintsType,
            _NcParameterConstraintsNumberType,
            _NcParameterConstraintsStringType,
            _NcManufacturerType,
            _NcProductType,
            _NcDeviceOperationalStateType,
            _NcBlockMemberDescriptorType,
            _NcTouchpointType,
            _NcTouchpointResourceType,
            _NcTouchpointResourceNmosType,
            _NcTouchpointResourceNmosChannelMappingType,
            _NcTouchpointNmosType,
            _NcTouchpointNmosChannelMappingType,
            _NcPropertyChangedEventDataType,
        ]

        for t in struct_types:
            desc = t.get_type_descriptor(False)
            reg[desc.base.name] = desc

        return reg

    def get_property(
        self, _oid: int, id_args: IdArgs
    ) -> tuple[NcMethodStatus, Optional[str], Any]:
        lvl, idx = id_args.id.level, id_args.id.index
        if lvl == 3:
            if idx == 1:
                return (
                    NcMethodStatus.Ok,
                    None,
                    list(self._control_classes.values()),
                )
            if idx == 2:
                return (
                    NcMethodStatus.Ok,
                    None,
                    list(dtype.to_dict() for dtype in self._datatypes.values()),
                )
            return (
                NcMethodStatus.PropertyNotImplemented,
                "Could not find the property",
                None,
            )
        return self.base.get_property(_oid, id_args)

    def set_property(
        self, _oid: int, id_args_value: IdArgsValue
    ) -> tuple[NcMethodStatus, Optional[str], Any]:
        if id_args_value.id.level == 3:
            return (
                NcMethodStatus.Readonly,
                "Could not find the property or it is read-only",
                False,
            )
        return self.base.set_property(_oid, id_args_value)

    def invoke_method(
        self, _oid: int, method_id, args: Any
    ) -> tuple[NcMethodStatus, Optional[str], Any]:
        # Handle GetSequenceItem (1m3)
        if method_id.level == 1 and method_id.index == 3:
            if not isinstance(args, dict):
                return NcMethodStatus.ParameterError, "Invalid arguments", None

            if "id" not in args or "index" not in args:
                return NcMethodStatus.ParameterError, "Invalid arguments", None

            if not isinstance(args.get("index"), int) or args["index"] < 0:
                return NcMethodStatus.ParameterError, "Invalid index parameter", None

            # Check if the id is for controlClasses (3p1) or datatypes (3p2)
            id_obj = args.get("id", {})
            if not isinstance(id_obj, dict):
                return NcMethodStatus.ParameterError, "Invalid id parameter", None

            level = id_obj.get("level")
            index = id_obj.get("index")

            # Handle controlClasses (3p1)
            if level == 3 and index == 1:
                control_classes = list(self._control_classes.values())
                if args["index"] >= len(control_classes):
                    return (
                        NcMethodStatus.IndexOutOfBounds,
                        f"Index {args['index']} out of bounds",
                        None,
                    )
                return NcMethodStatus.Ok, None, control_classes[args["index"]]

            # Handle datatypes (3p2)
            elif level == 3 and index == 2:
                datatypes = [dtype.to_dict() for dtype in self._datatypes.values()]
                if args["index"] >= len(datatypes):
                    return (
                        NcMethodStatus.IndexOutOfBounds,
                        f"Index {args['index']} out of bounds",
                        None,
                    )
                return NcMethodStatus.Ok, None, datatypes[args["index"]]

            return NcMethodStatus.ParameterError, "Invalid property", None

        # Handle GetSequenceLength (1m7)
        elif method_id.level == 1 and method_id.index == 7:
            if not isinstance(args, dict) or "id" not in args:
                return NcMethodStatus.ParameterError, "Invalid arguments", None

            id_obj = args.get("id", {})
            if not isinstance(id_obj, dict):
                return NcMethodStatus.ParameterError, "Invalid id parameter", None

            level = id_obj.get("level")
            index = id_obj.get("index")

            # Handle controlClasses (3p1)
            if level == 3 and index == 1:
                return NcMethodStatus.Ok, None, len(self._control_classes)

            # Handle datatypes (3p2)
            elif level == 3 and index == 2:
                return NcMethodStatus.Ok, None, len(self._datatypes)

            return NcMethodStatus.ParameterError, "Invalid property", None

        # Existing methods
        if method_id.level == 3 and method_id.index == 1:
            class_id = args.get("classId") or []
            include_inherited = bool(args.get("includeInherited", False))

            if not include_inherited:
                key = self._class_id_key(class_id)
                desc = self._control_classes.get(key)
                if not desc:
                    return (
                        NcMethodStatus.PropertyNotImplemented,
                        "Class not found",
                        None,
                    )
                return NcMethodStatus.Ok, None, desc

            if class_id == [1]:
                return (
                    NcMethodStatus.Ok,
                    None,
                    NcObject.get_class_descriptor(True).to_dict(),
                )
            elif class_id == [1, 1]:
                return (
                    NcMethodStatus.Ok,
                    None,
                    NcBlock.get_class_descriptor(True).to_dict(),
                )
            elif class_id == [1, 2]:
                return (
                    NcMethodStatus.Ok,
                    None,
                    NcWorker.get_class_descriptor(True).to_dict(),
                )
            elif class_id == [1, 3]:
                return (
                    NcMethodStatus.Ok,
                    None,
                    NcManager.get_class_descriptor(True).to_dict(),
                )
            elif class_id == [1, 3, 1]:
                return (
                    NcMethodStatus.Ok,
                    None,
                    NcDeviceManager.get_class_descriptor(True).to_dict(),
                )
            elif class_id == [1, 3, 2]:
                return (
                    NcMethodStatus.Ok,
                    None,
                    NcClassManager.get_class_descriptor(True).to_dict(),
                )
            else:
                return NcMethodStatus.PropertyNotImplemented, "Class not found", None

        elif method_id.level == 3 and method_id.index == 2:
            name = args.get("name")
            if not isinstance(name, str):
                return NcMethodStatus.ParameterError, "Invalid name", None
            dtype = self._datatypes.get(name)
            if not dtype:
                return NcMethodStatus.PropertyNotImplemented, "Datatype not found", None
            include_inherited = bool(args.get("includeInherited", False))
            if include_inherited and isinstance(dtype, NcDatatypeDescriptorStruct):
                result_desc = self._expand_struct_including_inherited(name)
            else:
                result_desc = dtype
            return NcMethodStatus.Ok, None, result_desc.to_dict()

        return self.base.invoke_method(_oid, method_id, args)

    @staticmethod
    def get_class_descriptor(include_inherited: bool = True) -> "NcClassDescriptor":
        from data_types import (
            NcClassDescriptor,
            NcDescriptor,
            NcPropertyDescriptor,
            NcMethodDescriptor,
            ElementId,
        )

        properties = [
            NcPropertyDescriptor(
                base=NcDescriptor(None),
                id=ElementId(3, 1),
                name="controlClasses",
                typeName="NcClassDescriptor",
                isReadOnly=True,
                isNullable=False,
                isSequence=True,
                isDeprecated=False,
                constraints=None,
            ),
            NcPropertyDescriptor(
                base=NcDescriptor(None),
                id=ElementId(3, 2),
                name="datatypes",
                typeName="NcDatatypeDescriptor",
                isReadOnly=True,
                isNullable=False,
                isSequence=True,
                isDeprecated=False,
                constraints=None,
            ),
        ]

        methods = [
            NcMethodDescriptor(
                base=NcDescriptor(None),
                id=ElementId(3, 1),
                name="GetControlClass",
                resultDatatype="NcMethodResultClassDescriptor",
                parameters=[
                    NcParameterDescriptor(
                        base=NcDescriptor(None),
                        name="classId",
                        typeName="NcClassId",
                        isNullable=False,
                        isSequence=False,
                        constraints=None,
                    ),
                    NcParameterDescriptor(
                        base=NcDescriptor(None),
                        name="includeInherited",
                        typeName="NcBoolean",
                        isNullable=False,
                        isSequence=False,
                        constraints=None,
                    ),
                ],
                isDeprecated=False,
            ),
            NcMethodDescriptor(
                base=NcDescriptor(None),
                id=ElementId(3, 2),
                name="GetDatatype",
                resultDatatype="NcMethodResultDatatypeDescriptor",
                parameters=[
                    NcParameterDescriptor(
                        base=NcDescriptor(None),
                        name="name",
                        typeName="NcName",
                        isNullable=False,
                        isSequence=False,
                        constraints=None,
                    ),
                    NcParameterDescriptor(
                        base=NcDescriptor(None),
                        name="includeInherited",
                        typeName="NcBoolean",
                        isNullable=False,
                        isSequence=False,
                        constraints=None,
                    ),
                ],
                isDeprecated=False,
            ),
        ]

        events: list[NcEventDescriptor] = []

        if include_inherited:
            base = NcManager.get_class_descriptor(True)
            properties = [*properties, *base.properties]
            methods = [*methods, *base.methods]
            events = [*events, *base.events]

        return NcClassDescriptor(
            base=NcDescriptor("NcClassManager class descriptor"),
            classId=[1, 3, 2],
            name="NcClassManager",
            fixedRole="ClassManager",
            properties=properties,
            methods=methods,
            events=events,
        )

    def _expand_struct_including_inherited(
        self, name: str
    ) -> NcDatatypeDescriptorStruct:
        base_desc = self._datatypes.get(name)
        if not isinstance(base_desc, NcDatatypeDescriptorStruct):
            from data_types import NcDatatypeDescriptor, NcDescriptor, NcDatatypeType

            minimal_base = NcDatatypeDescriptor(
                base=NcDescriptor(description=None),
                name=name,
                type=NcDatatypeType.Struct,
                constraints=None,
            )
            return NcDatatypeDescriptorStruct(
                base=minimal_base, fields=[], parentType=None
            )
        fields: List = list(base_desc.fields)
        parent_name = base_desc.parentType
        while parent_name:
            parent = self._datatypes.get(parent_name)
            if isinstance(parent, NcDatatypeDescriptorStruct):
                fields = fields + list(parent.fields)
                parent_name = parent.parentType
            else:
                break
        return NcDatatypeDescriptorStruct(
            base=base_desc.base, fields=fields, parentType=base_desc.parentType
        )

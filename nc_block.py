import asyncio
from typing import List, Optional, Any

from data_types import ElementId, NcMethodStatus, NcPropertyChangeType, make_event
from nc_object import NcMember, NcObject


class NcBlock(NcMember):
    def __init__(
        self,
        notifier,
        is_root,
        oid,
        constant_oid,
        owner,
        role,
        user_label,
        enabled,
        touchpoints: Optional[List[Any]] = None,
        runtime_property_constraints: Optional[List[Any]] = None,
    ):
        self.base = NcObject(
            notifier,
            class_id=[1, 1],
            oid=oid,
            constant_oid=constant_oid,
            owner=owner,
            role=role,
            user_label=user_label,
            touchpoints=touchpoints,
            runtime_property_constraints=runtime_property_constraints,
        )

        self.is_root = is_root
        self.enabled = enabled
        self.members: List[NcMember] = []

    def member_type(self):
        return "NcBlock"

    def get_role(self):
        return self.base.get_role()

    def get_oid(self):
        return self.base.get_oid()

    def get_constant_oid(self):
        return self.base.get_constant_oid()

    def get_class_id(self):
        return self.base.get_class_id()

    def get_user_label(self):
        return self.base.get_user_label()

    def get_property(self, oid, id_args):
        if oid == self.base.oid:
            lvl, idx = id_args.id.level, id_args.id.index
            if (lvl, idx) == (2, 1):
                return NcMethodStatus.Ok, None, self.enabled
            if (lvl, idx) == (2, 2):
                return NcMethodStatus.Ok, None, self.generate_members_descriptors()
            return self.base.get_property(oid, id_args)
        m = self.find_member(oid)
        return (
            m.get_property(oid, id_args)
            if m
            else (NcMethodStatus.BadOid, "Member not found", None)
        )

    def set_property(self, oid, id_args_value):
        if oid == self.base.oid:
            return self.base.set_property(oid, id_args_value)
        m = self.find_member(oid)
        return (
            m.set_property(oid, id_args_value)
            if m
            else (NcMethodStatus.BadOid, "Member not found", False)
        )

    def invoke_method(self, oid, method_id, args):
        if oid == self.base.oid:
            lvl, idx = method_id.level, method_id.index
            if (lvl, idx) == (2, 1):  # 2m1
                return NcMethodStatus.Ok, None, self.get_member_descriptors(args)
            if (lvl, idx) == (2, 2):  # 2m2
                return NcMethodStatus.Ok, None, self.find_members_by_path(args)
            if (lvl, idx) == (2, 3):  # 2m3
                return NcMethodStatus.Ok, None, self.find_members_by_role(args)
            if (lvl, idx) == (2, 4):  # 2m4
                return NcMethodStatus.Ok, None, self.find_members_by_class_id(args)
            return self.base.invoke_method(oid, method_id, args)
        m = self.find_member(oid)
        return (
            m.invoke_method(oid, method_id, args)
            if m
            else (NcMethodStatus.BadOid, "Member not found", None)
        )

    def add_member(self, member):
        self.members.append(member)
        ev = make_event(
            self.base.oid,
            ElementId(2, 2),
            NcPropertyChangeType.ValueChanged,
            self.generate_members_descriptors(),
        )
        asyncio.create_task(self.base.notifier.put(ev))

    def find_member(self, oid):
        for m in self.members:
            if m.get_oid() == oid:
                return m
            if isinstance(m, NcBlock):
                found = m.find_member(oid)
                if found:
                    return found
        return None

    def generate_members_descriptors(self):
        return [
            {
                "role": m.get_role(),
                "oid": m.get_oid(),
                "constantOid": m.get_constant_oid(),
                "classId": m.get_class_id(),
                "userLabel": m.get_user_label() or "",
                "owner": self.base.get_oid(),
            }
            for m in self.members
        ]

    @staticmethod
    def make_member_descriptor(member, owner):
        return {
            "role": member.get_role(),
            "oid": member.get_oid(),
            "constantOid": member.get_constant_oid(),
            "classId": member.get_class_id(),
            "userLabel": member.get_user_label() or "",
            "owner": owner,
        }

    # 2m1
    def get_member_descriptors(self, args):
        recurse = args.get("recurse", False)
        results = [
            self.make_member_descriptor(m, self.base.get_oid()) for m in self.members
        ]
        if recurse:
            for m in self.members:
                if isinstance(m, NcBlock):
                    results.extend(m.get_member_descriptors(args))
        return results

    # 2m2
    def find_members_by_path(self, args):
        path = args.get("path")
        if not isinstance(path, list) or not path:
            return []

        segments = [s.strip() for s in path if isinstance(s, str) and s.strip()]
        if not segments:
            return []

        return self._find_members_by_path_recursive(segments)

    def _find_members_by_path_recursive(self, segments):
        if not segments:
            return []

        first, rest = segments[0], segments[1:]
        results = []

        for m in self.members:
            if m.get_role() == first:
                if not rest:
                    results.append(self.make_member_descriptor(m, self.base.get_oid()))
                elif isinstance(m, NcBlock):
                    results.extend(m._find_members_by_path_recursive(rest))
        return results

    # 2m3
    def find_members_by_role(self, args):
        role = str(args.get("role", "")).strip()
        if not role:
            return []

        case_sensitive = args.get("caseSensitive", False)
        match_whole = args.get("matchWholeString", False)
        recurse = args.get("recurse", False)

        # Normalize search string
        search_role = role if case_sensitive else role.lower()

        def matches(r: str) -> bool:
            if not r:
                return False
            target = r if case_sensitive else r.lower()
            return target == search_role if match_whole else search_role in target

        results = [
            self.make_member_descriptor(m, self.base.get_oid())
            for m in self.members
            if matches(m.get_role())
        ]

        if recurse:
            for m in self.members:
                if isinstance(m, NcBlock):
                    results.extend(m.find_members_by_role(args))

        return results

    # 2m4
    def find_members_by_class_id(self, args):
        class_id = args.get("classId")
        if not class_id:
            return []

        recurse = args.get("recurse", False)
        include_derived = args.get("includeDerived", False)

        class_id_str = ".".join(str(x) for x in class_id)

        def matches_class_id(cid):
            cid_str = ".".join(str(x) for x in cid)
            return (
                cid_str.startswith(class_id_str)
                if include_derived
                else cid_str == class_id_str
            )

        results = [
            self.make_member_descriptor(m, self.base.get_oid())
            for m in self.members
            if matches_class_id(m.get_class_id())
        ]

        if recurse:
            for m in self.members:
                if isinstance(m, NcBlock):
                    results.extend(m.find_members_by_class_id(args))

        if self.is_root and matches_class_id(self.base.get_class_id()):
            results.append(
                {
                    "role": self.base.get_role(),
                    "oid": self.base.get_oid(),
                    "constantOid": self.base.get_constant_oid(),
                    "classId": self.base.get_class_id(),
                    "userLabel": self.base.get_user_label() or "",
                    "owner": self.base.get_oid(),
                }
            )
        return results

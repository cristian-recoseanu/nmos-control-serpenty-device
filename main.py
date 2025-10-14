import asyncio
import json
import uuid
from dataclasses import asdict
from typing import Dict, Optional

from aiohttp import web

from data_types import (
    DeviceControl,
    MESSAGE_TYPE_NOTIFICATION,
    NcManufacturer,
    NcProduct,
    NmosDevice,
    tai_timestamp,
)
from nc_block import NcBlock
from nc_device_manager import NcDeviceManager
from nc_object import NcObject
from websocket import CustomEncoder, websocket_handler


class AppState:
    def __init__(self):
        self.connections: Dict[str, any] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.root_block: Optional[NcBlock] = None
        self.device = NmosDevice(
            id="67c25159-ce25-4000-a66c-f31fff890265",
            label="Example Device",
            description="NMOS Example Device",
            senders=[],
            receivers=[],
            node_id=str(uuid.uuid4()),
            type="urn:x-nmos:device:generic",
            version=tai_timestamp(),
            controls=[
                DeviceControl(
                    "urn:x-nmos:control:ncp/v1.0", "ws://127.0.0.1:3000/ws", False
                )
            ],
        )

    async def notify_subscribers(self, ev):
        text = json.dumps(
            {
                "messageType": MESSAGE_TYPE_NOTIFICATION,
                "notifications": [ev.to_dict()],
            },
            cls=CustomEncoder,
        )
        for conn in list(self.connections.values()):
            if ev.oid in conn.subscribed_oids:
                try:
                    await conn.send_text(text)
                except Exception:
                    pass

    async def event_loop(self):
        while True:
            await self.notify_subscribers(await self.event_queue.get())


app_state = AppState()


# --- REST handlers ---


async def devices_handler(request):
    return web.json_response([asdict(app_state.device)])


async def device_handler(request):
    device_id = request.match_info.get("device_id")
    if device_id == app_state.device.id:
        return web.json_response(asdict(app_state.device))
    return web.json_response({"error": "device not found"}, status=404)


# --- Main ---


async def init_app():
    app = web.Application()

    # Store app_state in the app for access by handlers
    app["app_state"] = app_state

    app.add_routes(
        [
            web.get("/x-nmos/node/v1.3/devices/", devices_handler),
            web.get("/x-nmos/node/v1.3/devices/{device_id}", device_handler),
            web.get("/ws", websocket_handler),
        ]
    )

    # Root block
    root = NcBlock(True, 1, True, None, "root", None, True, app_state.event_queue)

    # Add NcDeviceManager
    manufacturer = NcManufacturer(
        name="Your Company", organization_id=None, website="https://example.com"
    )
    product = NcProduct(
        name="Your Product",
        key="MODEL-XYZ-2000",
        revision_level="1.0",
        brand_name="Your Brand",
        uuid="550e8400-e29b-41d4-a716-446655440000",
        description="Professional device",
    )

    device_manager = NcDeviceManager(
        oid=2,
        constant_oid=True,
        owner=1,
        role="DeviceManager",
        user_label="Device Manager",
        nc_version="v1.0.0",
        manufacturer=manufacturer,
        product=product,
        serial_number="SN-123456789",
        notifier=app_state.event_queue,
    )
    root.add_member(device_manager)

    # Child member
    root.add_member(
        NcObject([1], 3, True, 1, "my-obj-01", "My object 01", app_state.event_queue)
    )

    # Child block
    child_block = NcBlock(
        False, 4, True, None, "my-block-01", None, True, app_state.event_queue
    )
    child_block.add_member(
        NcObject([1], 5, True, 3, "my-nested-block-obj", None, app_state.event_queue)
    )
    root.add_member(child_block)

    app_state.root_block = root

    asyncio.create_task(app_state.event_loop())
    return app


if __name__ == "__main__":
    web.run_app(init_app(), host="0.0.0.0", port=3000)

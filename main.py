import asyncio
import json
import uuid
import socket
from typing import Dict, Optional

from aiohttp import web

from data_types import (
    DeviceControl,
    MESSAGE_TYPE_NOTIFICATION,
    NcManufacturer,
    NcProduct,
    NmosNode,
    NmosClock,
    NmosInterface,
    NmosApi,
    NmosEndpoint,
    NmosDevice,
    tai_timestamp,
    NcTouchpointNmos,
    NcTouchpoint,
    NcTouchpointResourceNmos,
)

from nc_block import NcBlock
from nc_device_manager import NcDeviceManager
from nc_class_manager import NcClassManager
from nc_object import NcObject
from nc_worker import NcWorker
from websocket import CustomEncoder, websocket_handler


class AppState:
    def __init__(self):
        self.connections: Dict[str, any] = {}
        self.event_queue: asyncio.Queue = asyncio.Queue()
        self.root_block: Optional[NcBlock] = None

        # Get hostname
        hostname = socket.gethostname()

        # Create node
        self.node = NmosNode(
            id=str(uuid.uuid4()),
            label="Example Node",
            description="An example NMOS node",
            version=tai_timestamp(),
            href="http://127.0.0.1:3000",
            hostname=hostname,
            clocks=[NmosClock(name="clk0", ref_type="internal")],
            interfaces=[
                NmosInterface(
                    chassis_id="00-15-5d-67-c3-4e",
                    name="eth0",
                    port_id="00-15-5d-67-c3-4e",
                ),
                NmosInterface(
                    chassis_id="96-1c-70-61-b1-54",
                    name="eth1",
                    port_id="96-1c-70-61-b1-54",
                ),
            ],
            api=NmosApi(
                endpoints=[NmosEndpoint(host="127.0.0.1", port=3000, protocol="http")],
                versions=["v1.3"],
            ),
            tags={},
        )

        # Create device
        self.device = NmosDevice(
            id="67c25159-ce25-4000-a66c-f31fff890265",
            label="Example Device",
            description="NMOS Example Device",
            senders=[],
            receivers=[],
            node_id=self.node.id,
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


async def base_is_04_rest_api_handler(request):
    return web.json_response(
        ["self/", "sources/", "flows/", "devices/", "senders/", "receivers/"]
    )


async def node_self_rest_api_handler(request):
    app_state = request.app["app_state"]
    return web.json_response(app_state.node.to_dict())


async def sources_rest_api_handler(request):
    return web.json_response([])


async def source_rest_api_handler(request):
    return web.json_response({"error": "source not found"}, status=404)


async def flows_rest_api_handler(request):
    return web.json_response([])


async def flow_rest_api_handler(request):
    return web.json_response({"error": "flow not found"}, status=404)


async def senders_rest_api_handler(request):
    return web.json_response([])


async def sender_rest_api_handler(request):
    return web.json_response({"error": "sender not found"}, status=404)


async def receivers_rest_api_handler(request):
    return web.json_response([])


async def receiver_rest_api_handler(request):
    return web.json_response({"error": "receiver not found"}, status=404)


async def devices_rest_api_handler(request):
    app_state = request.app["app_state"]
    return web.json_response([app_state.device.to_dict()])


async def device_rest_api_handler(request):
    app_state = request.app["app_state"]
    device_id = request.match_info.get("device_id")

    if device_id == app_state.device.id:
        return web.json_response(app_state.device.to_dict())

    return web.json_response({"error": "device not found"}, status=404)


# --- Main ---


async def init_app():
    app = web.Application()

    # Store app_state in the app for access by handlers
    app["app_state"] = app_state

    app.add_routes(
        [
            # Base API endpoint
            web.get("/x-nmos/node/v1.3", base_is_04_rest_api_handler),
            web.get("/x-nmos/node/v1.3/", base_is_04_rest_api_handler),
            # Self endpoint
            web.get("/x-nmos/node/v1.3/self", node_self_rest_api_handler),
            # Sources endpoints
            web.get("/x-nmos/node/v1.3/sources", sources_rest_api_handler),
            web.get("/x-nmos/node/v1.3/sources/", sources_rest_api_handler),
            web.get("/x-nmos/node/v1.3/sources/{source_id}", source_rest_api_handler),
            # Flows endpoints
            web.get("/x-nmos/node/v1.3/flows", flows_rest_api_handler),
            web.get("/x-nmos/node/v1.3/flows/", flows_rest_api_handler),
            web.get("/x-nmos/node/v1.3/flows/{flow_id}", flow_rest_api_handler),
            # Senders endpoints
            web.get("/x-nmos/node/v1.3/senders", senders_rest_api_handler),
            web.get("/x-nmos/node/v1.3/senders/", senders_rest_api_handler),
            web.get("/x-nmos/node/v1.3/senders/{sender_id}", sender_rest_api_handler),
            # Receivers endpoints
            web.get("/x-nmos/node/v1.3/receivers", receivers_rest_api_handler),
            web.get("/x-nmos/node/v1.3/receivers/", receivers_rest_api_handler),
            web.get(
                "/x-nmos/node/v1.3/receivers/{receiver_id}", receiver_rest_api_handler
            ),
            # Devices endpoints
            web.get("/x-nmos/node/v1.3/devices", devices_rest_api_handler),
            web.get("/x-nmos/node/v1.3/devices/", devices_rest_api_handler),
            web.get("/x-nmos/node/v1.3/devices/{device_id}", device_rest_api_handler),
            # WebSocket endpoint
            web.get("/ws", websocket_handler),
        ]
    )

    # Root block
    root = NcBlock(
        app_state.event_queue,
        True,
        1,
        True,
        None,
        "root",
        None,
        True,
    )

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
        touchpoints=[
            NcTouchpointNmos(
                base=NcTouchpoint(context_namespace="x-nmos"),
                resource=NcTouchpointResourceNmos(
                    resource_type="device",
                    id=app_state.device.id,
                ),
            )
        ],
        runtime_property_constraints=None,
    )
    root.add_member(device_manager)

    # Add NcClassManager
    class_manager = NcClassManager(
        notifier=app_state.event_queue,
        oid=3,
        constant_oid=True,
        owner=1,
        role="ClassManager",
        user_label="Class Manager",
        touchpoints=None,
        runtime_property_constraints=None,
    )
    root.add_member(class_manager)

    # Child member
    obj1 = NcObject(
        app_state.event_queue,
        [1],
        4,
        True,
        1,
        "my-obj-01",
        "My object 01",
        None,
        None,
    )
    root.add_member(obj1)

    # Add NcWorker
    worker1 = NcWorker(
        class_id=[1, 2],
        oid=5,
        constant_oid=True,
        owner=1,
        role="my-worker-01",
        user_label="My worker 01",
        enabled=True,
        touchpoints=None,
        runtime_property_constraints=None,
        notifier=app_state.event_queue,
    )
    root.add_member(worker1)

    # Child block
    child_block = NcBlock(
        app_state.event_queue,
        False,
        6,
        True,
        1,
        "my-block-01",
        None,
        True,
    )
    obj2 = NcObject(
        app_state.event_queue,
        [1],
        7,
        True,
        6,
        "my-nested-block-obj",
        "My nested block obj",
        None,
        None,
    )
    child_block.add_member(obj2)

    # Add NcWorker to child block
    worker2 = NcWorker(
        class_id=[1, 2],
        oid=8,
        constant_oid=True,
        owner=6,
        role="my-worker-02",
        user_label="My worker 02",
        enabled=True,
        touchpoints=None,
        runtime_property_constraints=None,
        notifier=app_state.event_queue,
    )
    child_block.add_member(worker2)

    root.add_member(child_block)

    app_state.root_block = root

    asyncio.create_task(app_state.event_loop())
    return app


if __name__ == "__main__":
    web.run_app(init_app(), host="0.0.0.0", port=3000)

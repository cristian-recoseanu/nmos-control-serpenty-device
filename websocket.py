import json
import uuid
from aiohttp import web, WSMsgType

from data_types import (
    ElementId,
    IdArgs,
    IdArgsValue,
    MESSAGE_TYPE_COMMAND,
    MESSAGE_TYPE_COMMAND_RESPONSE,
    MESSAGE_TYPE_ERROR,
    MESSAGE_TYPE_SUBSCRIPTION,
    MESSAGE_TYPE_SUBSCRIPTION_RESPONSE,
)


class CustomEncoder(json.JSONEncoder):
    def default(self, o):
        # IntEnum -> numeric value
        from enum import IntEnum
        from dataclasses import asdict

        if isinstance(o, IntEnum):
            return int(o)
        # dataclasses -> asdict
        if hasattr(o, "__dataclass_fields__"):
            return asdict(o)
        # ElementId as dict
        if isinstance(o, ElementId):
            return {"level": o.level, "index": o.index}
        # Generic fallback to asdict for objects with __dict__
        if hasattr(o, "__dict__"):
            return asdict(o)
        return super().default(o)


class ConnectionState:
    def __init__(self, ws):
        self.websocket, self.subscribed_oids = ws, set()

    async def send_text(self, text):
        if not self.websocket.closed:
            await self.websocket.send_str(text)


async def process_command(msg, root_block):
    responses = []
    for cmd in msg.get("commands", []):
        handle, oid, args = cmd.get("handle"), cmd.get("oid"), cmd.get("arguments")
        method_id = ElementId(**cmd.get("methodId", {}))
        status, error, value = 200, None, None

        try:
            if (method_id.level, method_id.index) == (1, 1):
                err, val = root_block.get_property(oid, IdArgs(ElementId(**args["id"])))
                value = val if err is None else None
                if err:
                    status, error = 400, err
            elif (method_id.level, method_id.index) == (1, 2):
                err, ok = root_block.set_property(
                    oid, IdArgsValue(ElementId(**args["id"]), args.get("value"))
                )
                if not ok:
                    status, error = 400, err
            else:
                err, resp = root_block.invoke_method(oid, method_id, args)
                if err is None:
                    value = resp
                else:
                    status, error = 400, err
        except Exception as e:
            status, error = 400, str(e)

        responses.append(
            {
                "handle": handle,
                "result": {"status": status, "value": value, "errorMessage": error},
            }
        )
    return {"messageType": MESSAGE_TYPE_COMMAND_RESPONSE, "responses": responses}


async def websocket_handler(request):
    app_state = request.app["app_state"]
    ws = web.WebSocketResponse()
    await ws.prepare(request)
    conn_id, conn = str(uuid.uuid4()), ConnectionState(ws)
    app_state.connections[conn_id] = conn

    try:
        async for msg in ws:
            if msg.type != WSMsgType.TEXT:
                continue
            try:
                data = json.loads(msg.data)
            except Exception:
                await conn.send_text(
                    json.dumps(
                        {
                            "messageType": MESSAGE_TYPE_ERROR,
                            "status": 400,
                            "errorMessage": "Invalid JSON",
                        }
                    )
                )
                continue

            mt = data.get("messageType")
            if mt == MESSAGE_TYPE_COMMAND and "commands" in data:
                await conn.send_text(
                    json.dumps(
                        await process_command(data, app_state.root_block),
                        cls=CustomEncoder,
                    )
                )
            elif mt == MESSAGE_TYPE_SUBSCRIPTION and "subscriptions" in data:
                conn.subscribed_oids = set(data["subscriptions"])
                await conn.send_text(
                    json.dumps(
                        {
                            "messageType": MESSAGE_TYPE_SUBSCRIPTION_RESPONSE,
                            "subscriptions": list(conn.subscribed_oids),
                        }
                    )
                )
            else:
                await conn.send_text(
                    json.dumps(
                        {
                            "messageType": MESSAGE_TYPE_ERROR,
                            "status": 400,
                            "errorMessage": "Invalid message",
                        }
                    )
                )
    finally:
        app_state.connections.pop(conn_id, None)
    return ws

from typing import List
from fastapi import WebSocket
import json
import logging
import asyncio

class SocketManager:
    def __init__(self):
        # We separate connections so we know who to broadcast to
        self.ui_connections: List[WebSocket] = []
        self.spy_connections: List[WebSocket] = []
        self.logger = logging.getLogger("Antigravity.SocketManager")
        
        # ELE-ST FIX 4: Batching & Debouncing
        self.message_queue = []
        self._batch_task = None

    def _start_batch_task(self):
        if self._batch_task is None:
            self._batch_task = asyncio.create_task(self._process_batch_queue())

    async def _process_batch_queue(self):
        while True:
            await asyncio.sleep(0.25) # 250ms UI updates
            if self.message_queue:
                batch = self.message_queue.copy()
                self.message_queue.clear()
                
                # Format as a grouped BATCH
                batch_data = {
                    "type": "BATCH",
                    "payload": batch
                }
                
                # ELE-ST FIX 6: Forensic Corruption (Bytes Serialization)
                def sanitize_bytes(obj):
                    if isinstance(obj, bytes):
                        return obj.hex()
                    return str(obj)

                message = json.dumps(batch_data, default=sanitize_bytes)
                
                async def send_with_timeout(connection):
                    try:
                        await asyncio.wait_for(connection.send_text(message), timeout=2.0)
                        return None
                    except Exception as e:
                        return connection

                if self.ui_connections:
                    results = await asyncio.gather(*(send_with_timeout(conn) for conn in self.ui_connections), return_exceptions=True)
                    for dead in results:
                        if isinstance(dead, WebSocket) and dead in self.ui_connections:
                            self.ui_connections.remove(dead)

    async def connect(self, websocket: WebSocket, client_type: str = "ui"):
        self._start_batch_task()
        await websocket.accept()
        if client_type == "spy":
            self.spy_connections.append(websocket)
            self.logger.info("Spy Extension Connected.")
            # Notify UIs that Spy is Online
            await self.broadcast_to_ui({
                "type": "SPY_STATUS",
                "payload": {"connected": True}
            })
        else:
            self.ui_connections.append(websocket)
            self.logger.info("UI Client Connected.")
            # Tell the new UI client if Spy is currently connected
            spy_is_online = len(self.spy_connections) > 0
            await websocket.send_text(json.dumps({
                "type": "SPY_STATUS",
                "payload": {"connected": spy_is_online}
            }))

    def disconnect(self, websocket: WebSocket):
        if websocket in self.spy_connections:
            self.spy_connections.remove(websocket)
            self.logger.info("Spy Extension Disconnected.")
        elif websocket in self.ui_connections:
            self.ui_connections.remove(websocket)
            self.logger.info("UI Client Disconnected.")

    async def broadcast(self, data: dict):
        """Broadcasts to UI clients via batch queue."""
        await self.broadcast_to_ui(data)

    async def broadcast_to_ui(self, data: dict):
        # Queue the message instead of sending immediately
        self.message_queue.append(data)

manager = SocketManager()

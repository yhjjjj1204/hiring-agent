from typing import Dict, List, Set, Any
from fastapi import WebSocket, WebSocketDisconnect
import json
import logging

logger = logging.getLogger(__name__)

class ConnectionManager:
    def __init__(self):
        # Maps user_id (username) to a set of active WebSockets
        self.user_sessions: Dict[str, Set[WebSocket]] = {}
        # Maps topic strings (e.g., "job:{id}", "system:alerts") to a set of WebSockets
        self.topics: Dict[str, Set[WebSocket]] = {}
        # Reverse mapping: websocket -> set of topics (for easy cleanup)
        self.socket_topics: Dict[WebSocket, Set[str]] = {}

    async def connect(self, websocket: WebSocket, user_id: str):
        await websocket.accept()
        if user_id not in self.user_sessions:
            self.user_sessions[user_id] = set()
        self.user_sessions[user_id].add(websocket)
        self.socket_topics[websocket] = set()
        logger.info(f"User {user_id} connected. Total sessions for user: {len(self.user_sessions[user_id])}")

    def disconnect(self, websocket: WebSocket, user_id: str):
        # 1. Remove from user sessions
        if user_id in self.user_sessions:
            self.user_sessions[user_id].discard(websocket)
            if not self.user_sessions[user_id]:
                del self.user_sessions[user_id]
        
        # 2. Unsubscribe from all topics
        if websocket in self.socket_topics:
            for topic in self.socket_topics[websocket]:
                if topic in self.topics:
                    self.topics[topic].discard(websocket)
                    if not self.topics[topic]:
                        del self.topics[topic]
            del self.socket_topics[websocket]
        
        logger.info(f"User {user_id} disconnected.")

    async def subscribe(self, websocket: WebSocket, topic: str):
        """Internalized subscription logic."""
        if topic not in self.topics:
            self.topics[topic] = set()
        self.topics[topic].add(websocket)
        
        if websocket not in self.socket_topics:
            self.socket_topics[websocket] = set()
        self.socket_topics[websocket].add(topic)
        
        logger.info(f"WebSocket subscribed to topic: {topic}")

    async def send_to_user(self, user_id: str, message: Any):
        """Send a message to all active sessions of a specific user."""
        if user_id in self.user_sessions:
            data = json.dumps(message)
            for connection in self.user_sessions[user_id]:
                try:
                    await connection.send_text(data)
                except Exception as e:
                    logger.error(f"Error sending message to user {user_id}: {e}")

    async def broadcast_to_topic(self, topic: str, message: Any):
        """Send a message to all WebSockets subscribed to a specific topic."""
        if topic in self.topics:
            data = json.dumps(message)
            for connection in self.topics[topic]:
                try:
                    await connection.send_text(data)
                except Exception as e:
                    logger.error(f"Error broadcasting to topic {topic}: {e}")

manager = ConnectionManager()

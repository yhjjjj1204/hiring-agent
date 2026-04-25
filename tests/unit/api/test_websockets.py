import pytest
import json
from unittest.mock import AsyncMock, MagicMock
from fastapi import WebSocket
from api.websockets import ConnectionManager

@pytest.mark.asyncio
async def test_websocket_connect_disconnect():
    manager = ConnectionManager()
    mock_ws = AsyncMock(spec=WebSocket)
    user_id = "user1"
    
    # Test Connect
    await manager.connect(mock_ws, user_id)
    assert user_id in manager.user_sessions
    assert mock_ws in manager.user_sessions[user_id]
    assert mock_ws.accept.called
    
    # Test Disconnect
    manager.disconnect(mock_ws, user_id)
    assert user_id not in manager.user_sessions
    assert mock_ws not in manager.socket_topics

@pytest.mark.asyncio
async def test_websocket_subscribe_broadcast():
    manager = ConnectionManager()
    mock_ws = AsyncMock(spec=WebSocket)
    topic = "job:123"
    
    await manager.connect(mock_ws, "alice")
    await manager.subscribe(mock_ws, topic)
    
    assert topic in manager.topics
    assert mock_ws in manager.topics[topic]
    assert topic in manager.socket_topics[mock_ws]
    
    # Test Broadcast
    msg = {"status": "update"}
    await manager.broadcast_to_topic(topic, msg)
    mock_ws.send_text.assert_called_once_with(json.dumps(msg))
    
    # Disconnect should clean up topics
    manager.disconnect(mock_ws, "alice")
    assert topic not in manager.topics

@pytest.mark.asyncio
async def test_websocket_send_to_user():
    manager = ConnectionManager()
    mock_ws1 = AsyncMock(spec=WebSocket)
    mock_ws2 = AsyncMock(spec=WebSocket)
    user_id = "bob"
    
    await manager.connect(mock_ws1, user_id)
    await manager.connect(mock_ws2, user_id)
    
    msg = {"hello": "world"}
    await manager.send_to_user(user_id, msg)
    
    mock_ws1.send_text.assert_called_once_with(json.dumps(msg))
    mock_ws2.send_text.assert_called_once_with(json.dumps(msg))

@pytest.mark.asyncio
async def test_websocket_send_error_handling():
    manager = ConnectionManager()
    mock_ws = AsyncMock(spec=WebSocket)
    mock_ws.send_text.side_effect = Exception("Send failed")
    
    await manager.connect(mock_ws, "alice")
    # This should not raise
    await manager.send_to_user("alice", {"test": 1})
    assert mock_ws.send_text.called

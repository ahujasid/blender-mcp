import pytest
import socket
import json
from unittest.mock import patch, MagicMock
from blender_mcp.server import BlenderConnection, get_blender_connection, server_lifespan, mcp


@pytest.fixture
def blender_connection():
    return BlenderConnection(host='127.0.0.1', port=1234)


def test_connection_lifecycle(blender_connection):
    """Test connection establishment and disconnection"""
    with patch('socket.socket') as mock_socket:
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        
        # Test connection
        assert blender_connection.connect()
        mock_socket.assert_called_once_with(socket.AF_INET, socket.SOCK_STREAM)
        mock_socket_instance.connect.assert_called_once_with(('127.0.0.1', 1234))
        
        # Test repeated connection
        assert blender_connection.connect()
        # Ensure no new socket is created
        mock_socket.assert_called_once()
        
        # Test disconnection
        blender_connection.disconnect()
        mock_socket_instance.close.assert_called_once()
        assert blender_connection.sock is None


def test_connection_failure(blender_connection):
    """Test connection failure scenario"""
    with patch('socket.socket') as mock_socket:
        mock_socket_instance = MagicMock()
        mock_socket_instance.connect.side_effect = socket.error("Connection refused")
        mock_socket.return_value = mock_socket_instance
        
        assert not blender_connection.connect()
        assert blender_connection.sock is None


def test_receive_full_response(blender_connection):
    """Test receiving complete response"""
    mock_socket = MagicMock()
    response_data = {"status": "success", "result": {"value": 42}}
    encoded_response = json.dumps(response_data).encode('utf-8')
    
    # Simulate chunked data reception
    mock_socket.recv.side_effect = [
        encoded_response[:10],
        encoded_response[10:],
        b''  # Indicates end of connection
    ]
    
    received_data = blender_connection.receive_full_response(mock_socket)
    assert json.loads(received_data.decode('utf-8')) == response_data


def test_receive_full_response_timeout(blender_connection):
    """Test response timeout scenario"""
    mock_socket = MagicMock()
    mock_socket.recv.side_effect = socket.timeout()
    
    with pytest.raises(Exception, match="No data received"):
        blender_connection.receive_full_response(mock_socket)


def test_receive_full_response_incomplete_json(blender_connection):
    """Test receiving incomplete JSON response"""
    mock_socket = MagicMock()
    mock_socket.recv.side_effect = [
        b'{"incomplete": "json',
        socket.timeout()
    ]
    
    with pytest.raises(Exception, match="Incomplete JSON response received"):
        blender_connection.receive_full_response(mock_socket)


def test_send_command_success(blender_connection):
    """Test successful command sending and response receiving"""
    with patch('socket.socket') as mock_socket:
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        
        # Mock successful response
        response_data = {
            "status": "success",
            "result": {"value": "test_result"}
        }
        mock_socket_instance.recv.return_value = json.dumps(response_data).encode('utf-8')
        
        # Connect and send command
        blender_connection.connect()
        result = blender_connection.send_command("test_command", {"param": "value"})
        
        # Verify sent command
        expected_command = {
            "type": "test_command",
            "params": {"param": "value"}
        }
        mock_socket_instance.sendall.assert_called_once_with(
            json.dumps(expected_command).encode('utf-8')
        )
        
        # Verify returned result
        assert result == {"value": "test_result"}


def test_send_command_error_response(blender_connection):
    """Test receiving error response when sending command"""
    with patch('socket.socket') as mock_socket:
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        
        # Mock error response
        error_response = {
            "status": "error",
            "message": "Test error message"
        }
        mock_socket_instance.recv.return_value = json.dumps(error_response).encode('utf-8')
        
        # Connect and test command sending
        blender_connection.connect()
        with pytest.raises(Exception, match="Test error message"):
            blender_connection.send_command("test_command")


def test_send_command_connection_error(blender_connection):
    """Test sending command without connection"""
    # Try to send command without establishing connection
    with pytest.raises(ConnectionError, match="Not connected to Blender"):
        blender_connection.send_command("test_command")


def test_send_command_socket_timeout(blender_connection):
    """Test socket timeout when sending command"""
    with patch('socket.socket') as mock_socket:
        mock_socket_instance = MagicMock()
        mock_socket.return_value = mock_socket_instance
        mock_socket_instance.recv.side_effect = socket.timeout()
        
        blender_connection.connect()
        with pytest.raises(Exception, match="Communication error with Blender: No data received"):
            blender_connection.send_command("test_command")
        
        # Verify socket is cleaned up after timeout
        assert blender_connection.sock is None


def test_get_blender_connection():
    """Test the get_blender_connection function's connection management"""
    with patch('blender_mcp.server.BlenderConnection') as mock_connection:
        # Mock successful connection
        mock_instance = MagicMock()
        mock_instance.connect.return_value = True
        mock_instance.send_command.return_value = {"enabled": True}
        mock_connection.return_value = mock_instance
        
        # First call should create new connection
        connection1 = get_blender_connection()
        mock_connection.assert_called_once_with(host="localhost", port=9876)
        
        # Second call should reuse existing connection
        connection2 = get_blender_connection()
        assert connection1 == connection2
        mock_connection.assert_called_once()
        
        # Test connection failure handling
        mock_instance.connect.return_value = False
        mock_instance.send_command.side_effect = Exception("Connection lost")
        with pytest.raises(Exception, match="Could not connect to Blender"):
            get_blender_connection()


@pytest.mark.asyncio
async def test_server_lifespan():
    """Test the server lifespan context manager"""
    mock_server = MagicMock()
    
    with patch('blender_mcp.server.get_blender_connection') as mock_get_connection:
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        
        # Mock the global connection
        with patch('blender_mcp.server._blender_connection', mock_connection):
            async with server_lifespan(mock_server) as context:
                assert isinstance(context, dict)
                assert len(context) == 0
                mock_get_connection.assert_called_once()
                mock_connection.disconnect.assert_not_called()
            
            # Verify disconnect was called after context exit
            mock_connection.disconnect.assert_called_once()


def test_get_scene_info():
    """Test the get_scene_info tool function"""
    with patch('blender_mcp.server.get_blender_connection') as mock_get_connection:
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        
        # Mock successful response
        mock_scene_info = {
            "objects": ["Cube", "Camera", "Light"],
            "active_object": "Cube"
        }
        mock_connection.send_command.return_value = mock_scene_info
        
        # Test successful case
        ctx = MagicMock()
        from blender_mcp.server import get_scene_info
        result = get_scene_info(ctx)
        assert json.loads(result) == mock_scene_info
        mock_connection.send_command.assert_called_once_with("get_scene_info")
        
        # Test error case
        mock_connection.send_command.side_effect = Exception("Blender error")
        result = get_scene_info(ctx)
        assert "Error getting scene info" in result


def test_get_object_info():
    """Test the get_object_info tool function"""
    with patch('blender_mcp.server.get_blender_connection') as mock_get_connection:
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        
        # Mock successful response
        mock_object_info = {
            "name": "Cube",
            "type": "MESH",
            "location": [0, 0, 0]
        }
        mock_connection.send_command.return_value = mock_object_info
        
        # Test successful case
        ctx = MagicMock()
        from blender_mcp.server import get_object_info
        result = get_object_info(ctx, object_name="Cube")
        assert json.loads(result) == mock_object_info
        mock_connection.send_command.assert_called_once_with(
            "get_object_info",
            {"name": "Cube"}
        )


def test_create_object():
    """Test the create_object tool function"""
    with patch('blender_mcp.server.get_blender_connection') as mock_get_connection:
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        
        # Mock successful response
        mock_response = {"name": "Cube.001"}
        mock_connection.send_command.return_value = mock_response
        
        # Test basic cube creation
        ctx = MagicMock()
        from blender_mcp.server import create_object
        result = create_object(ctx, type="CUBE")
        assert "Created CUBE object" in result
        mock_connection.send_command.assert_called_once_with(
            "create_object",
            {
                "type": "CUBE",
                "location": [0, 0, 0],
                "rotation": [0, 0, 0],
                "scale": [1, 1, 1]
            }
        )


def test_modify_object():
    """Test the modify_object tool function"""
    with patch('blender_mcp.server.get_blender_connection') as mock_get_connection:
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        
        # Mock successful response
        mock_response = {"name": "Cube"}
        mock_connection.send_command.return_value = mock_response
        
        # Test object modification
        ctx = MagicMock()
        from blender_mcp.server import modify_object
        result = modify_object(
            ctx,
            name="Cube",
            location=[1, 1, 1],
            rotation=[0, 0, 0],
            scale=[2, 2, 2],
            visible=True
        )
        assert "Modified object" in result
        mock_connection.send_command.assert_called_once_with(
            "modify_object",
            {
                "name": "Cube",
                "location": [1, 1, 1],
                "rotation": [0, 0, 0],
                "scale": [2, 2, 2],
                "visible": True
            }
        )


def test_delete_object():
    """Test the delete_object tool function"""
    with patch('blender_mcp.server.get_blender_connection') as mock_get_connection:
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        
        # Mock successful response
        mock_response = {"success": True}
        mock_connection.send_command.return_value = mock_response
        
        # Test object deletion
        ctx = MagicMock()
        from blender_mcp.server import delete_object
        result = delete_object(ctx, name="Cube")
        assert "Deleted object" in result
        mock_connection.send_command.assert_called_once_with(
            "delete_object",
            {"name": "Cube"}
        )


def test_set_material():
    """Test the set_material tool function"""
    with patch('blender_mcp.server.get_blender_connection') as mock_get_connection:
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        
        # Mock successful response
        mock_response = {"material_name": "Material.001"}
        mock_connection.send_command.return_value = mock_response
        
        # Test material setting
        ctx = MagicMock()
        from blender_mcp.server import set_material
        result = set_material(
            ctx,
            object_name="Cube",
            material_name="Red",
            color=[1, 0, 0]
        )
        assert "Applied material" in result
        mock_connection.send_command.assert_called_once_with(
            "set_material",
            {
                "object_name": "Cube",
                "material_name": "Red",
                "color": [1, 0, 0]
            }
        )


def test_execute_blender_code():
    """Test the execute_blender_code tool function"""
    with patch('blender_mcp.server.get_blender_connection') as mock_get_connection:
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        
        # Mock successful response
        mock_response = {"result": "Code executed successfully"}
        mock_connection.send_command.return_value = mock_response
        
        # Test code execution
        ctx = MagicMock()
        test_code = "bpy.ops.mesh.primitive_cube_add()"
        from blender_mcp.server import execute_blender_code
        result = execute_blender_code(ctx, code=test_code)
        assert "Code executed successfully" in result
        mock_connection.send_command.assert_called_once_with(
            "execute_code",
            {"code": test_code}
        )


def test_polyhaven_integration():
    """Test PolyHaven integration functions"""
    with patch('blender_mcp.server.get_blender_connection') as mock_get_connection:
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        ctx = MagicMock()
        
        # Test get_polyhaven_status
        mock_connection.send_command.return_value = {"enabled": True}
        mock_tool = MagicMock()
        mock_tool.return_value = json.dumps({"enabled": True})
        with patch.object(mcp, "tool", return_value=mock_tool):
            result = mcp.tool("get_polyhaven_status")(ctx)
            assert json.loads(result)["enabled"]
        
        # Test get_polyhaven_categories
        mock_categories = {"hdris": ["indoor", "outdoor"]}
        mock_connection.send_command.return_value = mock_categories
        mock_tool = MagicMock()
        mock_tool.return_value = json.dumps(mock_categories)
        with patch.object(mcp, "tool", return_value=mock_tool):
            result = mcp.tool("get_polyhaven_categories")(ctx)
            assert json.loads(result) == mock_categories
        
        # Test search_polyhaven_assets
        mock_assets = {"assets": ["asset1", "asset2"]}
        mock_connection.send_command.return_value = mock_assets
        mock_tool = MagicMock()
        mock_tool.return_value = json.dumps(mock_assets)
        with patch.object(mcp, "tool", return_value=mock_tool):
            result = mcp.tool("search_polyhaven_assets")(ctx)
            assert json.loads(result) == mock_assets
            # Verify the command and parameters sent
            mock_connection.send_command.assert_called_once_with(
                "search_polyhaven_assets", {}
            )
        
        # Test download_polyhaven_asset
        mock_download = {"status": "success"}
        mock_connection.send_command.return_value = mock_download
        mock_tool = MagicMock()
        mock_tool.return_value = json.dumps(mock_download)
        with patch.object(mcp, "tool", return_value=mock_tool):
            result = mcp.tool("download_polyhaven_asset")(
                ctx,
                asset_id="test_asset",
                asset_type="hdris"
            )
            assert json.loads(result) == mock_download
            # Verify the command and parameters sent
            mock_connection.send_command.assert_called_once_with(
                "download_polyhaven_asset",
                {"asset_id": "test_asset", "asset_type": "hdris"}
            )


def test_hyper3d_integration():
    """Test Hyper3D integration functions"""
    with patch('blender_mcp.server.get_blender_connection') as mock_get_connection:
        mock_connection = MagicMock()
        mock_get_connection.return_value = mock_connection
        ctx = MagicMock()
        
        # Test get_hyper3d_status
        mock_connection.send_command.return_value = {"enabled": True}
        mock_tool = MagicMock()
        mock_tool.return_value = json.dumps({"enabled": True})
        with patch.object(mcp, "tool", return_value=mock_tool):
            result = mcp.tool("get_hyper3d_status")(ctx)
            assert json.loads(result)["enabled"]
        
        # Test generate_hyper3d_model_via_text
        mock_generation = {
            "status": "success",
            "subscription_key": "test_key"
        }
        mock_connection.send_command.return_value = mock_generation
        mock_tool = MagicMock()
        mock_tool.return_value = json.dumps(mock_generation)
        with patch.object(mcp, "tool", return_value=mock_tool):
            result = mcp.tool("generate_hyper3d_model_via_text")(
                ctx,
                text_prompt="a red cube"
            )
            assert json.loads(result) == mock_generation
        
        # Test poll_rodin_job_status
        mock_status = {"status": "COMPLETED"}
        mock_connection.send_command.return_value = mock_status
        mock_tool = MagicMock()
        mock_tool.return_value = json.dumps(mock_status)
        with patch.object(mcp, "tool", return_value=mock_tool):
            result = mcp.tool("poll_rodin_job_status")(
                ctx,
                subscription_key="test_key"
            )
            assert json.loads(result) == mock_status
        
        # Test import_generated_asset
        mock_import = {"status": "success"}
        mock_connection.send_command.return_value = mock_import
        mock_tool = MagicMock()
        mock_tool.return_value = json.dumps(mock_import)
        with patch.object(mcp, "tool", return_value=mock_tool):
            result = mcp.tool("import_generated_asset")(
                ctx,
                name="generated_model",
                task_uuid="test_uuid"
            )
            assert json.loads(result) == mock_import
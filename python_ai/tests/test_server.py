import json
import socket
import threading
import unittest

from src.serwer import GameServer


class GameServerTests(unittest.TestCase):
    def test_update_is_received_and_policy_action_is_returned(self) -> None:
        def policy(message: dict) -> dict:
            return {
                "action": "build_tower",
                "tower_type": "BASIC",
                "x": message["step"],
                "y": 3,
            }

        server = GameServer(policy=policy)
        server_socket, client_socket = socket.socketpair()
        try:
            message = {
                "type": "update",
                "episode_id": "test-episode",
                "step": 4,
                "resources": {"ai_money": 150, "base_health": 1000},
            }
            server._handle_line(
                server_socket,
                json.dumps(message).encode("utf-8"),
            )
            response = json.loads(client_socket.recv(4096).decode("utf-8"))
            self.assertEqual(server.latest_observation, message)
            self.assertEqual(
                response,
                {"action": "build_tower", "tower_type": "BASIC", "x": 4, "y": 3},
            )
        finally:
            server_socket.close()
            client_socket.close()

    def test_malformed_json_is_ignored(self) -> None:
        server = GameServer()
        server_socket, client_socket = socket.socketpair()
        try:
            server._handle_line(server_socket, b"{not json")
            self.assertIsNone(server.latest_observation)
        finally:
            server_socket.close()
            client_socket.close()

    def test_server_handles_fragmented_and_coalesced_messages(self) -> None:
        server = GameServer(
            policy=lambda message: (
                {"action": "build_tower", "tower_type": "BASIC", "x": 1, "y": 2}
                if message.get("type") == "update"
                else None
            )
        )
        server_socket, client_socket = socket.socketpair()
        thread = threading.Thread(target=server._serve_client, args=(server_socket,))
        thread.start()
        try:
            client_socket.sendall(b'{"type":"init","episode_id":"test"}\n{"type":"upd')
            client_socket.sendall(
                b'ate","episode_id":"test","step":2}\n'
            )
            response = json.loads(client_socket.recv(4096).decode("utf-8"))
            self.assertEqual(response["action"], "build_tower")
            self.assertEqual(server.latest_init["episode_id"], "test")
            self.assertEqual(server.latest_observation["step"], 2)
            client_socket.shutdown(socket.SHUT_WR)
            thread.join(timeout=2)
            self.assertFalse(thread.is_alive())
        finally:
            client_socket.close()
            server_socket.close()


if __name__ == "__main__":
    unittest.main()

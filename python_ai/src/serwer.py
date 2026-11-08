from __future__ import annotations

import argparse
import json
import logging
import socket
from collections.abc import Callable
from typing import Any


LOGGER = logging.getLogger("kittycatch.server")
MAX_MESSAGE_BYTES = 8 * 1024 * 1024
Policy = Callable[[dict[str, Any]], dict[str, Any] | None]


class GameServer:
    """TCP endpoint that receives Godot observations and optionally returns AI actions."""

    def __init__(
        self,
        host: str = "127.0.0.1",
        port: int = 8080,
        policy: Policy | None = None,
    ) -> None:
        self.host = host
        self.port = port
        self.policy = policy
        self.latest_init: dict[str, Any] | None = None
        self.latest_observation: dict[str, Any] | None = None
        self._stop_requested = False
        self._listener: socket.socket | None = None

    def serve_forever(self) -> None:
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as server:
            self._listener = server
            server.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
            server.bind((self.host, self.port))
            server.listen()
            LOGGER.info("Listening for Godot on %s:%d", self.host, self.port)
            while not self._stop_requested:
                try:
                    connection, address = server.accept()
                except OSError:
                    if self._stop_requested:
                        break
                    raise
                LOGGER.info("Godot connected from %s:%d", *address)
                try:
                    self._serve_client(connection)
                except OSError as error:
                    LOGGER.warning("Godot connection ended: %s", error)
                except ValueError as error:
                    LOGGER.warning("Closing invalid Godot connection: %s", error)
                finally:
                    connection.close()
            self._listener = None

    def stop(self) -> None:
        self._stop_requested = True
        if self._listener is not None:
            self._listener.close()

    def _serve_client(self, connection: socket.socket) -> None:
        buffer = bytearray()
        while not self._stop_requested:
            chunk = connection.recv(65536)
            if not chunk:
                LOGGER.info("Godot disconnected")
                return
            buffer.extend(chunk)
            if len(buffer) > MAX_MESSAGE_BYTES and b"\n" not in buffer:
                raise ValueError(
                    f"JSON message exceeded {MAX_MESSAGE_BYTES} bytes without a newline"
                )

            while b"\n" in buffer:
                line, _, remainder = buffer.partition(b"\n")
                buffer = bytearray(remainder)
                if not line.strip():
                    continue
                if len(line) > MAX_MESSAGE_BYTES:
                    LOGGER.error("Ignoring oversized message (%d bytes)", len(line))
                    continue
                self._handle_line(connection, line)

    def _handle_line(self, connection: socket.socket, line: bytes) -> None:
        try:
            message = json.loads(line.decode("utf-8"))
        except UnicodeDecodeError as error:
            LOGGER.error("Ignoring non-UTF-8 message: %s", error)
            return
        except json.JSONDecodeError as error:
            LOGGER.error("Ignoring invalid JSON from Godot: %s", error)
            return
        if not isinstance(message, dict):
            LOGGER.error("Ignoring JSON message that is not an object")
            return

        message_type = message.get("type")
        if message_type == "init":
            self.latest_init = message
            self.latest_observation = None
            LOGGER.info(
                "Episode %s started (protocol %s, AI funds %s)",
                message.get("episode_id", "unknown"),
                message.get("protocol_version", "legacy"),
                message.get("ai_money", message.get("money", "?")),
            )
        elif message_type == "update":
            self.latest_observation = message
            resources = message.get("resources", {})
            counts = message.get("counts", {})
            enemies = counts.get("enemies_by_type", {})
            LOGGER.info(
                "Episode %s step %s | AI $%s | base %s | enemies %s | towers %s",
                message.get("episode_id", "unknown"),
                message.get("step", "?"),
                resources.get("ai_money", message.get("ai_money", "?")),
                resources.get("base_health", message.get("base", {}).get("health", "?")),
                sum(enemies.values()) if enemies else len(message.get("units", [])),
                len(message.get("towers", [])),
            )
        else:
            LOGGER.warning("Ignoring unknown Godot message type: %r", message_type)
            return

        if self.policy is None:
            return
        action = self.policy(message)
        if action is None:
            return
        if not isinstance(action, dict) or not isinstance(action.get("action"), str):
            raise TypeError("Policy must return an action dictionary or None")
        payload = json.dumps(action, separators=(",", ":"), ensure_ascii=False)
        connection.sendall(payload.encode("utf-8") + b"\n")
        LOGGER.info("Sent AI action %s", action.get("action"))


def _build_once_policy(
    tower_type: str,
    x: int,
    y: int,
) -> Policy:
    sent = False

    def policy(message: dict[str, Any]) -> dict[str, Any] | None:
        nonlocal sent
        if sent or message.get("type") != "update":
            return None
        sent = True
        return {
            "action": "build_tower",
            "command_id": f"manual-{message.get('episode_id', 'episode')}-{message.get('step', 0)}",
            "tower_type": tower_type,
            "x": x,
            "y": y,
        }

    return policy


def main() -> None:
    parser = argparse.ArgumentParser(description="Receive KittyCatch observations from Godot")
    parser.add_argument("--host", default="127.0.0.1")
    parser.add_argument("--port", type=int, default=8080)
    parser.add_argument("--build-once", action="store_true", help="Send one test tower action")
    parser.add_argument("--tower-type", choices=("BASIC", "SNIPER"), default="BASIC")
    parser.add_argument("--x", type=int, default=3)
    parser.add_argument("--y", type=int, default=3)
    args = parser.parse_args()

    logging.basicConfig(level=logging.INFO, format="%(asctime)s %(levelname)s %(message)s")
    policy = (
        _build_once_policy(args.tower_type, args.x, args.y) if args.build_once else None
    )
    GameServer(args.host, args.port, policy).serve_forever()


if __name__ == "__main__":
    main()

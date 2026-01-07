import socket
import threading
import time

from shared_lib.networking.robot_server import (
    AXIS_SCALE,
    FRAME_STRUCT,
    TYPE_AXIS,
    TYPE_BUTTON,
    TYPE_HAT,
    RobotSocketServer,
)


def test_robot_socket_server_decodes_frames() -> None:
    events: dict[str, list[tuple[int, object]]] = {"axis": [], "button": [], "hat": []}

    def on_axis(index: int, value: float) -> None:
        events["axis"].append((index, value))

    def on_button(index: int, pressed: bool) -> None:
        events["button"].append((index, pressed))

    def on_hat(index: int, value: tuple[int, int]) -> None:
        events["hat"].append((index, value))

    server = RobotSocketServer(
        "127.0.0.1", 0, on_axis=on_axis, on_button=on_button, on_hat=on_hat
    )
    server.start()
    assert server._socket is not None
    port = server._socket.getsockname()[1]

    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    client = socket.create_connection(("127.0.0.1", port), timeout=2)
    try:
        axis_value = 0.25
        axis_scaled = int(round(axis_value * AXIS_SCALE))
        client.sendall(FRAME_STRUCT.pack(TYPE_AXIS, 2, axis_scaled))
        client.sendall(FRAME_STRUCT.pack(TYPE_BUTTON, 3, 1))
        hat_value = (1, 0)
        hat_packed = (hat_value[0] + 1) * 3 + (hat_value[1] + 1)
        client.sendall(FRAME_STRUCT.pack(TYPE_HAT, 4, hat_packed))
    finally:
        client.close()

    deadline = time.time() + 1.0
    while time.time() < deadline:
        if (
            len(events["axis"]) == 1
            and len(events["button"]) == 1
            and len(events["hat"]) == 1
        ):
            break
        time.sleep(0.01)

    server.stop()
    thread.join(timeout=1.0)

    assert events["axis"] == [(2, axis_value)]
    assert events["button"] == [(3, True)]
    assert events["hat"] == [(4, hat_value)]

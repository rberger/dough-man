import asyncio
from textual.app import App, ComposeResult
from textual.widgets import Footer, Header, Static
from textual.scroll_view import ScrollView
from textual.reactive import reactive
from serial_asyncio import open_serial_connection
from vl53_400_lib import AsyncSerialAccess


class RiseDisplay(Static):
    line_output = reactive("")

    def __init__(self, serial_port, baud_rate, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.rangefinder = AsyncSerialAccess(serial_port=self.serial_port, baud_rate=self.baud_rate)

    async def on_mount(self):
        print("on_mount")
        await self.rangefinder.open_connection()
        asyncio.create_task(self.update_line_output())

    async def update_line_output(self):
        self.update("Waiting for data...")
        while True:
            result = await self.rangefinder.get_distance()
            self.line_output = f"Distance: {result['distance']} {result['units']}"

    def watch_line_output(self, line_output: str) -> None:
        self.update(line_output)


class SerialDisplay(Static):
    line_output = reactive("")

    def __init__(self, serial_port, baud_rate, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.serial_conn = None

    async def on_mount(self):
        print("on_mount")
        self.serial_conn = await open_serial_connection(url=self.serial_port, baudrate=self.baud_rate)
        print("serial_conn", self.serial_conn)
        asyncio.create_task(self.update_line_output())

    async def update_line_output(self):
        reader, _ = self.serial_conn
        self.update("Waiting for data...")
        while True:
            line = await reader.readline()
            self.line_output = line.decode("utf-8").rstrip()

    def watch_line_output(self, line_output: str) -> None:
        self.update(line_output)


class DoughMonApp(App):
    TITLE = "DoughMan TUI"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, serial_port, baud_rate, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serial_port = serial_port
        self.baud_rate = baud_rate

    def compose(self) -> "ComposeResult":
        yield Header()
        yield RiseDisplay(serial_port=self.serial_port, baud_rate=self.baud_rate)
        yield Footer()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


def tui_run() -> None:
    app = DoughMonApp(serial_port="/dev/tty.usbserial-910", baud_rate=115200)
    app.run()


if __name__ == "__main__":
    app = DoughMonApp(serial_port="/dev/tty.usbserial-910", baud_rate=115200)
    app.run()

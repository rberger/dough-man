import asyncio
from textual import on
from textual.app import App, ComposeResult
from textual.screen import ModalScreen
from textual.widgets import Footer, Header, Static, OptionList, TabbedContent, TabPane, Select, Label
from textual.scroll_view import ScrollView
from textual.reactive import reactive
from serial_asyncio import open_serial_connection
from serial.tools.list_ports import comports
from vl53_400_lib import AsyncSerialAccess


class RiseDisplay(Static):
    line_output = reactive("")

    def __init__(self, serial_port, baud_rate, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        print(f"RiseDisplay: serial_port={self.serial_port}, baud_rate={self.baud_rate}")
        self.rangefinder = AsyncSerialAccess(serial_port=self.serial_port, baud_rate=self.baud_rate)

    async def on_mount(self):
        print("RiseDisplay: on_mount")
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


class SerialConfigScreen(Static):
    """
    A modal screen that allows user to pick the serial port
    """

    def __init__(self, serial_ports, baud_rate, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serial_ports = serial_ports
        self.baud_rate = baud_rate
        self.serial_port = None

    def compose(self) -> ComposeResult:
        yield Label("Serial Port")
        yield Select(
            ((port, port) for port in self.serial_ports),
            id="serial_port",
            prompt="Select serial port",
            name="Serial Port",
        )

    @on(Select.Changed)
    def select_changed(self, event: Select.Changed) -> None:
        self.serial_port = str(event.value)


class DoughMonApp(App):
    TITLE = "DoughMan TUI"
    BINDINGS = [
        ("d", "toggle_dark", "Toggle dark mode"),
        ("q", "quit", "Quit"),
    ]

    def __init__(self, serial_port=None, baud_rate=115200, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.serial_ports = None
        self.serial_port = serial_port
        self.baud_rate = baud_rate
        self.set_serial_ports()

    def get_serial_ports(self):
        ports = comports()
        for p in ports:
            print(p.device)
        serial_ports = [port.device for port in comports() if port.device.startswith("/dev/cu.usbserial")]
        return serial_ports

    def compose(self) -> "ComposeResult":
        print("APp compose: serial_ports", self.serial_ports)
        yield Header()
        with TabbedContent(initial="config"):
            with TabPane("Config", id="config"):
                yield SerialConfigScreen(serial_ports=self.serial_ports, baud_rate=self.baud_rate)
            with TabPane("Data", id="data"):
                yield RiseDisplay(serial_port=self.serial_port, baud_rate=self.baud_rate)
        yield Footer()

    def set_serial_ports(self):
        serial_ports = self.get_serial_ports()
        print("serial_ports", serial_ports)
        if not serial_ports or len(serial_ports) == 0:
            raise "No serial ports found"
        if len(serial_ports) == 1:
            self.serial_ports = serial_ports
            self.serial_port = serial_ports[0]
        else:
            self.serial_ports = serial_ports
            self.query_one(TabbedContent).active = "config"

    def on_mount(self):
        self.set_serial_ports()

    def action_toggle_dark(self) -> None:
        """An action to toggle dark mode."""
        self.dark = not self.dark


def tui_run() -> None:
    app = DoughMonApp(serial_port=None, baud_rate=115200)
    app.run()


if __name__ == "__main__":
    app = DoughMonApp(serial_port=None, baud_rate=115200)
    app.run()

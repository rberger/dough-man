#!/usr/bin/env python3
import sys
import click
from vl53_400_lib import RangeFinder
from loguru import logger


@click.command()
@click.option(
    "--serial-port",
    default="/dev/tty.usbserial-A10",
    help="The serial port to connect to.",
)
@click.option("--baud-rate", default=115200, help="The baud rate to use.")
@click.option("--timeout", default=1, help="The timeout to use.")
@click.option(
    "--return-rate",
    type=click.Choice(["0.1", "0.2", "0.5", "1", "2", "5", "10", "20", "50", "100"]),
    help="Set Return Rate in Hz",
)
@click.option(
    "--mode",
    type=click.Choice(["serial", "modbus", "iic"]),
    help="Comm mode (modbus stops serial spew)",
)
@click.option(
    "--op",
    type=click.Choice(["stream", "get_return_rate", "lstream", "reset"]),
    help="The operation to perform.",
)
@click.option("--debug", is_flag=True, help="Enable debug logging.")
def cli(
    serial_port: str,
    baud_rate: int,
    timeout: int,
    return_rate: float,
    mode: str,
    op: str,
    debug: bool,
) -> None:
    # Configure logging
    logger.remove(0)
    if debug:
        logger.add(sys.stderr, level="DEBUG")
    else:
        logger.add(sys.stderr, level="INFO")

    # Setup loguru logging to enable debug logging in the vl53_400_lib modules
    logger.enable("vl53_400_lib.device_access")
    logger.enable("vl53_400_lib.main")

    logger.debug(
        f"cli: {serial_port}, baud_rate: {baud_rate} timeout: {timeout} return_rate: {return_rate} debug: {debug}"
    )
    try:
        range_finder = RangeFinder(serial_port, baud_rate, timeout, return_rate, debug)
    except Exception as e:
        exit_with_msg(f"Error initializing RangeFinder: {e}")

    op = "set_return_rate" if return_rate else op
    op = "mode" if mode else op
    match op:
        case "reset":
            range_finder.reset()
        case "mode":
            range_finder.set_sensor_mode("mode")
        case "get_return_rate":
            result = range_finder.get_return_rate()
        case "stream":
            range_finder.stream_data()
        case "lstream":
            range_finder.lstream_data()
        case "set_return_rate":
            range_finder.set_return_rate(return_rate)
        case _:
            exit_with_msg("No operation specified. Exiting.")


def exit_with_msg(msg: str) -> None:
    logger.error(msg)
    sys.exit(1)


if __name__ == "__main__":
    try:
        cli()
    except KeyboardInterrupt:
        logger.warning("Closing the serial port.")
        self.ser.close()

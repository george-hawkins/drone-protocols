# From https://learn.adafruit.com/circuitpython-essentials/circuitpython-uart-serial
import board
import busio
from microcontroller import Pin
 
 
def is_hardware_uart(tx, rx):
    try:
        p = busio.UART(tx, rx)
        p.deinit()
        return True
    except ValueError:
        return False
 
 
def get_unique_pins():
    exclude = ['NEOPIXEL', 'APA102_MOSI', 'APA102_SCK']
    pins = [pin for pin in [getattr(board, p) for p in dir(board) if p not in exclude] if isinstance(pin, Pin)]
    unique = []
    for p in pins:
        if p not in unique:
            unique.append(p)
    return unique
 
 
for tx_pin in get_unique_pins():
    if is_hardware_uart(tx_pin, tx_pin):
        print("TX/RX pin:", tx_pin)
    else:
        print("Failed:", tx_pin)

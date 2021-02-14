import board
import digitalio
import storage

# By default CircuitPython boots such that you can write to it as a USB drive but Python code sees the drive as read-only.
# To toggle this behavior, i.e. Python can write to the drive but you can't, you need to remount the drive here.
# Remounting must be done in `boot.py` (and requires a hard reboot) - once USB is active, it's too late to change.
# For more details see https://learn.adafruit.com/cpu-temperature-logging-with-circuit-python/writing-to-the-filesystem

# If you get stuck, you can erase the drive, even if it's read-only, from the Python prompt like so:
# >>> import storage
# >>> storage.erase_filesystem()
# And remember to press Reset afterwards.

switch = digitalio.DigitalInOut(board.D12)
switch.direction = digitalio.Direction.INPUT
switch.pull = digitalio.Pull.UP

# If D12 is connected to ground you can write to the drive but Python cannot.
storage.remount("/", not switch.value)

print("/ is {} for Python".format("writable" if switch.value else "read-only"))

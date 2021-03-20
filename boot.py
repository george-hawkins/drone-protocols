import board
import digitalio
import storage

# When connected via USB, a CircuitPython dev-board appears as a USB drive. By default you can write to the drive
# but CircuitPython code running on the board cannot. To toggle this behavior, such that CircuitPython code can
# write to the drive but you cannot, the filesystem needs to be remounted as required here in `boot.py`.
# Remounting requires a hard reboot and must be done here as once USB is active, it's too late to change.
# For more details see https://learn.adafruit.com/cpu-temperature-logging-with-circuit-python/writing-to-the-filesystem

# If you get stuck, you can erase the drive, even if it's read-only, from the Python prompt like so:
# >>> import storage
# >>> storage.erase_filesystem()
# And remember to press Reset afterwards.

switch = digitalio.DigitalInOut(board.D12)
switch.direction = digitalio.Direction.INPUT
switch.pull = digitalio.Pull.UP

# If D12 is left floating, CircuitPython can write to the drive.
# If D12 is connected to ground then you can write to the drive but CircuitPython cannot.
storage.remount("/", not switch.value)

# This output will appear in `boot_out.txt` on the dev-board USB drive.
print("/ is {} for Python".format("writable" if switch.value else "read-only"))

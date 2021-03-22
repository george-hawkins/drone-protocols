S.BUS notes
===========

S.BUS is a very simple protocol. Each packet consists of 25 bytes with the first byte always being 0x0F and the last byte always being 0x00 (for most S.BUS RXs). The payload between these start and bytes consists of 22 bytes of channel data followed by one byte of flags.

22 bytes is _22 * 8 = 176 bits_, each channel is 11 bits, so there are _176 / 11 = 16 channels_ packed into those 22 bytes. The last byte then consists of four flags, two are for an additional two channels that are either fully on or fully off and the other two are a lost frame flag and a failsafe flag.

Adjustment function
-------------------

11 bits allows you to cover the range 0 to 2048 for each channel. Other RX protocols will have different ranges so in Betaflight there are protocol specific adjustment functions such that the rest of the Betaflight code can work with channel values without worrying about the underlying protocol.

The S.BUS adjustment function is `sbusChannelsReadRawRC` in [`sbus_channels.c`](https://github.com/betaflight/betaflight/blob/master/src/main/rx/sbus_channels.c). This function is assigned to `rxRuntimeState->rcReadRawFn` and is then used by `readRxChannelsApplyRanges` in [`rx.c`](https://github.com/betaflight/betaflight/blob/master/src/main/rx/rx.c).

Bit fields
----------

In Betaflight [`sbus_channels.h`](https://github.com/betaflight/betaflight/blob/master/src/main/rx/sbus_channels.h) you can see that they use a feature of C called bit fields:

```
unsigned int chan0 : 11;
unsigned int chan1 : 11;
unsigned int chan2 : 11;
```

I.e. in C you can tell it that the channels are 11 bits each within a larger structure of bytes (for more on bit fields, see this SO [answer](https://stackoverflow.com/a/8564597/245602)). So you don't need any clever unpacking logic. CPython also supports bit fields as part of the `ctypes` module - see [here](https://docs.python.org/3/library/ctypes.html#bit-fields-in-structures-and-unions). And MicroPython provides cut down version documented [here](https://docs.micropython.org/en/latest/library/uctypes.html). CircuitPython, however, does not support `ctypes` for SAMD.

Betaflight S.BUS source
-----------------------

The Betaflight code for S.BUS is easy to read and can be found in:

* [`src/main/rx/sbus.c`](https://github.com/betaflight/betaflight/blob/master/src/main/rx/sbus.c)
* [`src/main/rx/sbus_channels.c`](https://github.com/betaflight/betaflight/blob/master/src/main/rx/sbus_channels.c)
* [`src/main/rx/sbus_channels.h`](https://github.com/betaflight/betaflight/blob/master/src/main/rx/sbus_channels.h)

`sbus_channels.h` is just worth looking at for the `sbusChannels_s` structure of bit fields mentioned above.

Issues
------

The S.BUS protocol is a bit too simple - 0x0F indicates the start of a packet but it can also validly appear within the packet. Once you're in-sync and reading packet after packet, this isn't an issue. But when searching initially, it is guaranteed that 0x0F is definitely the start of a packet.

There's no checksum either - so if you detect 0x0F and then read 24 bytes, there's no way to tell that you haven't just hit a 0x0F _within_ a packet. For most RXs, you can at least check that the end byte is 0x00 - however, Futuba have produced an S.BUS2 protocol where the end byte is used for telemetry (for more see the comment, with links, for `sbusFrame_s` in [`sbus.c`](https://github.com/betaflight/betaflight/blob/master/src/main/rx/sbus.c)).

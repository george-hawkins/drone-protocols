Debug snippets
==============

```
print("MSP frame: ", "".join("\\x{:02X}".format(ch) for ch in frame.payload).join(['"', '"']))
```

```
if frame_id == FrameId.MSP_SERVER:
    for b in frame_data:
        print("{:02X}".format(b))
    print("----")
```

#include <stdint.h>
#include <stdio.h>
#include <string.h>

typedef struct {
    uint8_t *ptr;          // data pointer must be first (sbuf_t* is equivalent to uint8_t **)
    uint8_t *end;
} sbuf_t;

sbuf_t *sbufInit(sbuf_t *sbuf, uint8_t *ptr, uint8_t *end)
{
    sbuf->ptr = ptr;
    sbuf->end = end;
    return sbuf;
}

int sbufBytesRemaining(sbuf_t *buf)
{
    return buf->end - buf->ptr;
}

void sbufReadData(sbuf_t *src, void *data, int len)
{
    memcpy(data, src->ptr, len);
}

void sbufAdvance(sbuf_t *buf, int size)
{
    buf->ptr += size;
}

int main(void)
{
    uint8_t contents[] = { 0x01, 0x02, 0x03, 0x04, 0x05, 0x06, 0x77 };
    sbuf_t sbuf;

    sbuf_t *frameBuf = sbufInit(&sbuf, contents, contents + 6);
    const uint8_t frameBytesRemaining = sbufBytesRemaining(frameBuf);
    printf("%d\n", frameBytesRemaining);
    uint8_t payload[frameBytesRemaining];

    sbufReadData(frameBuf, payload, bufferBytesRemaining);
    sbufAdvance(frameBuf, bufferBytesRemaining);

    printf("%x\n", *frameBuf->ptr);

    return 0;
}

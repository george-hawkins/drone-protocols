// Generate a complete frame with checksum and print the bytes that would then be written to a UART.
#include <stdint.h>
#include <stdio.h>

typedef struct {
    uint8_t  frameId;
    uint16_t valueId;
    uint32_t data;
} __attribute__((packed)) smartPortPayload_t;

enum
{
    FSSP_START_STOP = 0x7E,

    FSSP_DLE        = 0x7D,
    FSSP_DLE_XOR    = 0x20,

    FSSP_DATA_FRAME = 0x10,
};

enum {
    FSSP_DATAID_T1         = 0x0400
};

static void frskyCheckSumStep(uint16_t *checksum, uint8_t byte)
{
    *checksum += byte;
}

static void frskyCheckSumFini(uint16_t *checksum)
{
    while (*checksum > 0xFF) {
        *checksum = (*checksum & 0xFF) + (*checksum >> 8);
    }

    *checksum = 0xFF - *checksum;
}

static void serialWrite(uint8_t c)
{
    printf("%02x\n", c);
}

static void smartPortSendByte(uint8_t c, uint16_t *checksum)
{
    // smart port escape sequence
    if (c == FSSP_DLE || c == FSSP_START_STOP) {
        serialWrite(FSSP_DLE);
        serialWrite(c ^ FSSP_DLE_XOR);
    } else {
        serialWrite(c);
    }

    if (checksum != NULL) {
        frskyCheckSumStep(checksum, c);
    }
}

static void smartPortWriteFrame(const smartPortPayload_t *payload)
{
    uint16_t checksum = 0;
    uint8_t *data = (uint8_t *)payload;
    for (unsigned i = 0; i < sizeof(smartPortPayload_t); i++) {
        smartPortSendByte(*data++, &checksum);
    }
    frskyCheckSumFini(&checksum);
    smartPortSendByte(checksum, NULL);
}

static void smartPortSendPackage(uint16_t id, uint32_t val)
{
    smartPortPayload_t payload;
    payload.frameId = FSSP_DATA_FRAME;
    payload.valueId = id;
    payload.data = val;

    smartPortWriteFrame(&payload);
}

int main(void)
{
    uint16_t id = FSSP_DATAID_T1;
    uint32_t value = 54321;
    smartPortSendPackage(id, value);

    return 0;
}

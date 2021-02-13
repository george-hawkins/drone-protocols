#include <stdbool.h>
#include <stdint.h>
#include <string.h>

// ---

// src/main/common/streambuf.h

typedef struct {
    uint8_t *ptr;          // data pointer must be first (sbuf_t* is equivalent to uint8_t **)
    uint8_t *end;
} sbuf_t;

sbuf_t *sbufInit(sbuf_t *sbuf, uint8_t *ptr, uint8_t *end);

void sbufWriteU8(sbuf_t *dst, uint8_t val);
void sbufWriteData(sbuf_t *dst, const void *data, int len);

uint8_t sbufReadU8(sbuf_t *src);
void sbufReadData(sbuf_t *dst, void *data, int len);

int sbufBytesRemaining(sbuf_t *buf);
void sbufAdvance(sbuf_t *buf, int size);

void sbufSwitchToReader(sbuf_t *buf, uint8_t * base);

// ---

// src/main/msp/msp.h

// return positive for ACK, negative on error, zero for no reply
typedef enum {
    MSP_RESULT_ACK = 1,
    MSP_RESULT_ERROR = -1,
    MSP_RESULT_NO_REPLY = 0,
    MSP_RESULT_CMD_UNKNOWN = -2,   // don't know how to process command, try next handler
} mspResult_e;

typedef struct {
    sbuf_t buf;
    int16_t cmd;
    uint8_t flags;
    int16_t result;
    uint8_t direction;
} mspPacket_t;

typedef int mspDescriptor_t;

struct serialPort_s;
typedef void (*mspPostProcessFnPtr)(struct serialPort_s *port); // msp post process function, used for gracefully handling reboots, etc.

extern mspResult_e mspFcProcessCommand(mspDescriptor_t srcDesc, mspPacket_t *cmd, mspPacket_t *reply, mspPostProcessFnPtr *mspPostProcessFn);

static int mspDescriptor = 0;

mspDescriptor_t mspDescriptorAlloc(void)
{
    return (mspDescriptor_t)mspDescriptor++;
}

// ---

// src/main/telemetry/smartport.h
#define SMARTPORT_MSP_TX_BUF_SIZE 256
#define SMARTPORT_MSP_RX_BUF_SIZE 64

// ---

// src/main/telemetry/msp_shared.h

typedef void (*mspResponseFnPtr)(uint8_t *payload);

typedef struct {
    sbuf_t requestFrame;
    uint8_t *requestBuffer;
    uint8_t *responseBuffer;
    mspPacket_t *requestPacket;
    mspPacket_t *responsePacket;
} mspPackage_t;

// ---

// src/main/msp/msp_protocol.h
#define MSP_EEPROM_WRITE 250

// ---

#define TELEMETRY_MSP_VERSION    1
#define TELEMETRY_MSP_VER_SHIFT  5
#define TELEMETRY_MSP_VER_MASK   (0x7 << TELEMETRY_MSP_VER_SHIFT)
#define TELEMETRY_MSP_ERROR_FLAG (1 << 5)
#define TELEMETRY_MSP_START_FLAG (1 << 4)
#define TELEMETRY_MSP_SEQ_MASK   0x0F
#define TELEMETRY_MSP_RES_ERROR (-10)

#define TELEMETRY_REQUEST_SKIPS_AFTER_EEPROMWRITE 5

enum {
    TELEMETRY_MSP_VER_MISMATCH=0,
    TELEMETRY_MSP_CRC_ERROR=1,
    TELEMETRY_MSP_ERROR=2
};

static uint8_t checksum = 0;
static mspPackage_t mspPackage;
static uint8_t mspRxBuffer[SMARTPORT_MSP_RX_BUF_SIZE];
static uint8_t mspTxBuffer[SMARTPORT_MSP_TX_BUF_SIZE];
static mspPacket_t mspRxPacket;
static mspPacket_t mspTxPacket;
static mspDescriptor_t mspSharedDescriptor;

void initSharedMsp(void)
{
    // GCH - IMPORTANT: setting `end` is `set_length` in Pythong.
    // Setting `ptr` is alway just setting `offset` back to 0 in Python.
    mspPackage.requestBuffer = (uint8_t *)&mspRxBuffer;
    mspPackage.requestPacket = &mspRxPacket;
    mspPackage.requestPacket->buf.ptr = mspPackage.requestBuffer;
    mspPackage.requestPacket->buf.end = mspPackage.requestBuffer;

    mspPackage.responseBuffer = (uint8_t *)&mspTxBuffer;
    mspPackage.responsePacket = &mspTxPacket;
    mspPackage.responsePacket->buf.ptr = mspPackage.responseBuffer;
    mspPackage.responsePacket->buf.end = mspPackage.responseBuffer;

    // GCH - the individual sources of MSP commands each get a unique numeric ID (starting at 0).
    // So this here is the ID for telemetry (it's only called "initSharedMsp" because it's shared between CSRF and SmartPort telemetry).
    // Any UARTs on your FC that are configured for MSP (e.g. the one you use to talk to the Configurator) will get their own ID.
    // **Update:** actually `mspSharedDescriptor` gets updated everytime `handleMspFrame` is called and `mspStarted` is 0.
    mspSharedDescriptor = mspDescriptorAlloc();
}

static void processMspPacket(void)
{
    mspPackage.responsePacket->cmd = 0;
    mspPackage.responsePacket->result = 0;
    mspPackage.responsePacket->buf.end = mspPackage.responseBuffer;

    mspPostProcessFnPtr mspPostProcessFn = NULL;
    // GCH - `&mspPostProcessFn` is only used for command `MSP_SET_PASSTHROUGH` - which I don't see Configurator using (check Lua scripts for 245 - but seems unlikely).
    if (mspFcProcessCommand(mspSharedDescriptor, mspPackage.requestPacket, mspPackage.responsePacket, &mspPostProcessFn) == MSP_RESULT_ERROR) {
        sbufWriteU8(&mspPackage.responsePacket->buf, TELEMETRY_MSP_ERROR);
    }
    if (mspPostProcessFn) {
        mspPostProcessFn(NULL);
    }

    sbufSwitchToReader(&mspPackage.responsePacket->buf, mspPackage.responseBuffer);
}

void sendMspErrorResponse(uint8_t error, int16_t cmd)
{
    mspPackage.responsePacket->cmd = cmd;
    mspPackage.responsePacket->result = TELEMETRY_MSP_RES_ERROR;
    mspPackage.responsePacket->buf.end = mspPackage.responseBuffer;

    sbufWriteU8(&mspPackage.responsePacket->buf, error);
    sbufSwitchToReader(&mspPackage.responsePacket->buf, mspPackage.responseBuffer);
}

bool handleMspFrame(uint8_t *frameStart, int frameLength, uint8_t *skipsBeforeResponse)
{
    static uint8_t mspStarted = 0;
    static uint8_t lastSeq = 0;

    if (sbufBytesRemaining(&mspPackage.responsePacket->buf) > 0) {
        mspStarted = 0;
    }

    if (mspStarted == 0) {
        initSharedMsp();
    }

    mspPacket_t *packet = mspPackage.requestPacket;
    sbuf_t *frameBuf = sbufInit(&mspPackage.requestFrame, frameStart, frameStart + (uint8_t)frameLength);
    sbuf_t *rxBuf = &mspPackage.requestPacket->buf;
    const uint8_t header = sbufReadU8(frameBuf);
    const uint8_t seqNumber = header & TELEMETRY_MSP_SEQ_MASK;
    const uint8_t version = (header & TELEMETRY_MSP_VER_MASK) >> TELEMETRY_MSP_VER_SHIFT;

    if (version != TELEMETRY_MSP_VERSION) {
        sendMspErrorResponse(TELEMETRY_MSP_VER_MISMATCH, 0);
        return true;
    }

    if (header & TELEMETRY_MSP_START_FLAG) {
        // first packet in sequence
        uint8_t mspPayloadSize = sbufReadU8(frameBuf);

        packet->cmd = sbufReadU8(frameBuf);
        packet->result = 0;
        packet->buf.ptr = mspPackage.requestBuffer;
        packet->buf.end = mspPackage.requestBuffer + mspPayloadSize;

        checksum = mspPayloadSize ^ packet->cmd;
        mspStarted = 1;
    } else if (!mspStarted) {
        // no start packet yet, throw this one away
        return false;
    } else if (((lastSeq + 1) & TELEMETRY_MSP_SEQ_MASK) != seqNumber) {
        // packet loss detected!
        mspStarted = 0;
        return false;
    }

    const uint8_t bufferBytesRemaining = sbufBytesRemaining(rxBuf);
    const uint8_t frameBytesRemaining = sbufBytesRemaining(frameBuf);
    uint8_t payload[frameBytesRemaining];

    if (bufferBytesRemaining >= frameBytesRemaining) {
        sbufReadData(frameBuf, payload, frameBytesRemaining);
        sbufAdvance(frameBuf, frameBytesRemaining);
        sbufWriteData(rxBuf, payload, frameBytesRemaining);
        lastSeq = seqNumber;

        return false;
    } else {
        sbufReadData(frameBuf, payload, bufferBytesRemaining);
        sbufAdvance(frameBuf, bufferBytesRemaining);
        sbufWriteData(rxBuf, payload, bufferBytesRemaining);
        sbufSwitchToReader(rxBuf, mspPackage.requestBuffer);
        while (sbufBytesRemaining(rxBuf)) {
            checksum ^= sbufReadU8(rxBuf);
        }

        if (checksum != *frameBuf->ptr) {
            mspStarted = 0;
            sendMspErrorResponse(TELEMETRY_MSP_CRC_ERROR, packet->cmd);
            return true;
        }
    }

    // Skip a few telemetry requests if command is MSP_EEPROM_WRITE
    if (packet->cmd == MSP_EEPROM_WRITE && skipsBeforeResponse) {
        *skipsBeforeResponse = TELEMETRY_REQUEST_SKIPS_AFTER_EEPROMWRITE;
    }

    mspStarted = 0;
    sbufSwitchToReader(rxBuf, mspPackage.requestBuffer);
    processMspPacket();
    return true;
}

bool sendMspReply(uint8_t payloadSize, mspResponseFnPtr responseFn)
{
    static uint8_t checksum = 0;
    static uint8_t seq = 0;

    // GCH - the caller could just pass in a 6 byte buffer (a `memoryview` slice perhaps) and not pass 
    // in the `responseFn` - the caller should just call that fn (irrespective of `true` or `false` return) on the buffer itself.
    uint8_t payloadOut[payloadSize];
    sbuf_t payload;
    sbuf_t *payloadBuf = sbufInit(&payload, payloadOut, payloadOut + payloadSize);
    sbuf_t *txBuf = &mspPackage.responsePacket->buf;

    // detect first reply packet
    // GCH, i.e. is `offset` currently 0?
    if (txBuf->ptr == mspPackage.responseBuffer) {

        // header
        uint8_t head = TELEMETRY_MSP_START_FLAG | (seq++ & TELEMETRY_MSP_SEQ_MASK);
        if (mspPackage.responsePacket->result < 0) {
            head |= TELEMETRY_MSP_ERROR_FLAG;
        }
        sbufWriteU8(payloadBuf, head);

        uint8_t size = sbufBytesRemaining(txBuf);
        sbufWriteU8(payloadBuf, size);
    } else {
        // header
        sbufWriteU8(payloadBuf, (seq++ & TELEMETRY_MSP_SEQ_MASK));
    }

    const uint8_t bufferBytesRemaining = sbufBytesRemaining(txBuf);
    const uint8_t payloadBytesRemaining = sbufBytesRemaining(payloadBuf);
    uint8_t frame[payloadBytesRemaining];

    if (bufferBytesRemaining >= payloadBytesRemaining) {

        sbufReadData(txBuf, frame, payloadBytesRemaining);
        sbufAdvance(txBuf, payloadBytesRemaining);
        sbufWriteData(payloadBuf, frame, payloadBytesRemaining);
        responseFn(payloadOut);

        return true;

    } else {

        sbufReadData(txBuf, frame, bufferBytesRemaining);
        sbufAdvance(txBuf, bufferBytesRemaining);
        sbufWriteData(payloadBuf, frame, bufferBytesRemaining);
        sbufSwitchToReader(txBuf, mspPackage.responseBuffer);

        checksum = sbufBytesRemaining(txBuf) ^ mspPackage.responsePacket->cmd;

        while (sbufBytesRemaining(txBuf)) {
            checksum ^= sbufReadU8(txBuf);
        }
        sbufWriteU8(payloadBuf, checksum);

        while (sbufBytesRemaining(payloadBuf)>1) {
            sbufWriteU8(payloadBuf, 0);
        }

    }

    responseFn(payloadOut);
    return false;
}

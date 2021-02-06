#include <stdint.h>
#include <stdbool.h>
#include <string.h> // Just for `memcpy`.

// ----

// src/main/drivers/serial.h

typedef enum {
    MODE_RX = 1 << 0,
    MODE_TX = 1 << 1,
    MODE_RXTX = MODE_RX | MODE_TX
} portMode_e;

typedef enum {
    SERIAL_NOT_INVERTED  = 0 << 0,
    SERIAL_INVERTED      = 1 << 0,
    SERIAL_UNIDIR        = 0 << 3,
    SERIAL_BIDIR         = 1 << 3,
} portOptions_e;

// Forward declaration of opaque structure.
typedef struct serialPort_s serialPort_t;

// This can be thrown away with the first four arguments of `openSerialPort` below.
typedef void (*serialReceiveCallbackPtr)(uint16_t data, void *rxCallbackData);   // used by serial drivers to return frames to app

void serialWrite(serialPort_t *instance, uint8_t ch);
uint32_t serialRxBytesWaiting(const serialPort_t *instance);
uint8_t serialRead(serialPort_t *instance);

// ----

// src/main/io/serial.h

typedef enum {
    SERIAL_PORT_NONE = -1,
    SERIAL_PORT_USART1 = 0,
    SERIAL_PORT_USART2,
    SERIAL_PORT_USART3,
    SERIAL_PORT_UART4,
} serialPortIdentifier_e;

// I think `FUNCTION_TELEMETRY_SMARTPORT` is only important if you're searching for the config with that function.
// In our context it's simply important that it's not `FUNCTION_NONE`.
typedef enum {
    FUNCTION_NONE                = 0,
    FUNCTION_TELEMETRY_SMARTPORT = (1 << 5),  // 32
} serialPortFunction_e;

// The first four parameters are irrelevant for us - only `baudrate`, `mode` and `options` are actually important.
serialPort_t *openSerialPort(
    serialPortIdentifier_e identifier,
    serialPortFunction_e function,
    serialReceiveCallbackPtr rxCallback,
    void *rxCallbackData,
    uint32_t baudrate,
    portMode_e mode,
    portOptions_e options
);

// ----

// src/main/common/time.h:

// time difference, 32 bits always sufficient
typedef int32_t timeDelta_t;
// microsecond time
typedef uint32_t timeUs_t;

static inline timeDelta_t cmpTimeUs(timeUs_t a, timeUs_t b) { return (timeDelta_t)(a - b); }

// ----

// src/main/drivers/system.c
// Return system uptime in microseconds - rolls-over every 70 minutes -
extern uint32_t micros(void);

// ----

// src/main/telemetry/msp_shared.h
typedef void (*mspResponseFnPtr)(uint8_t *payload);

bool handleMspFrame(uint8_t *frameStart, int frameLength, uint8_t *skipsBeforeResponse);
bool sendMspReply(uint8_t payloadSize, mspResponseFnPtr responseFn);

// ----

// src/main/telemetry/smartport.h:

enum
{
    FSSP_START_STOP = 0x7E,

    FSSP_DLE        = 0x7D,
    FSSP_DLE_XOR    = 0x20,

    FSSP_DATA_FRAME = 0x10,
    FSSP_MSPC_FRAME_SMARTPORT = 0x30, // MSP client frame
    FSSP_MSPS_FRAME = 0x32, // MSP server frame

    // ID of sensor. Must be something that is polled by FrSky RX
    FSSP_SENSOR_ID1 = 0x1B,
    FSSP_SENSOR_ID2 = 0x0D
};

typedef struct {
    uint8_t  frameId;
    uint16_t valueId;
    uint32_t data;
} __attribute__((packed)) smartPortPayload_t;

// ----

// Standins for telemetryConfig()->halfDuplex and telemetryConfig()->telemetry_inverted from src/main/telemetry/telemetry.h
extern bool configHalfDuplex;
extern bool configTelemetryInverted;

// ----

// src/main/rx/frsky_crc.c
static void frskyCheckSumStep(uint16_t *checksum, uint8_t byte)
{
    *checksum += byte;
}

// src/main/rx/frsky_crc.c
static void frskyCheckSumFini(uint16_t *checksum)
{
    while (*checksum > 0xFF) {
        *checksum = (*checksum & 0xFF) + (*checksum >> 8);
    }

    *checksum = 0xFF - *checksum;
}

// ----

// these data identifiers are obtained from https://github.com/opentx/opentx/blob/master/radio/src/telemetry/frsky_hub.h
enum
{
    FSSP_DATAID_SPEED      = 0x0830 ,
    FSSP_DATAID_VFAS       = 0x0210 ,
    FSSP_DATAID_VFAS1      = 0x0211 ,
    FSSP_DATAID_VFAS2      = 0x0212 ,
    FSSP_DATAID_VFAS3      = 0x0213 ,
    FSSP_DATAID_VFAS4      = 0x0214 ,
    FSSP_DATAID_VFAS5      = 0x0215 ,
    FSSP_DATAID_VFAS6      = 0x0216 ,
    FSSP_DATAID_VFAS7      = 0x0217 ,
    FSSP_DATAID_VFAS8      = 0x0218 ,
    FSSP_DATAID_CURRENT    = 0x0200 ,
    FSSP_DATAID_CURRENT1   = 0x0201 ,
    FSSP_DATAID_CURRENT2   = 0x0202 ,
    FSSP_DATAID_CURRENT3   = 0x0203 ,
    FSSP_DATAID_CURRENT4   = 0x0204 ,
    FSSP_DATAID_CURRENT5   = 0x0205 ,
    FSSP_DATAID_CURRENT6   = 0x0206 ,
    FSSP_DATAID_CURRENT7   = 0x0207 ,
    FSSP_DATAID_CURRENT8   = 0x0208 ,
    FSSP_DATAID_RPM        = 0x0500 ,
    FSSP_DATAID_RPM1       = 0x0501 ,
    FSSP_DATAID_RPM2       = 0x0502 ,
    FSSP_DATAID_RPM3       = 0x0503 ,
    FSSP_DATAID_RPM4       = 0x0504 ,
    FSSP_DATAID_RPM5       = 0x0505 ,
    FSSP_DATAID_RPM6       = 0x0506 ,
    FSSP_DATAID_RPM7       = 0x0507 ,
    FSSP_DATAID_RPM8       = 0x0508 ,
    FSSP_DATAID_ALTITUDE   = 0x0100 ,
    FSSP_DATAID_FUEL       = 0x0600 ,
    FSSP_DATAID_ADC1       = 0xF102 ,
    FSSP_DATAID_ADC2       = 0xF103 ,
    FSSP_DATAID_LATLONG    = 0x0800 ,
    FSSP_DATAID_CAP_USED   = 0x0600 ,
    FSSP_DATAID_VARIO      = 0x0110 ,
    FSSP_DATAID_CELLS      = 0x0300 ,
    FSSP_DATAID_CELLS_LAST = 0x030F ,
    FSSP_DATAID_HEADING    = 0x0840 ,
    FSSP_DATAID_T1         = 0x0400 ,
    FSSP_DATAID_T11        = 0x0401 ,
    FSSP_DATAID_T2         = 0x0410 ,
    FSSP_DATAID_HOME_DIST  = 0x0420 ,
    FSSP_DATAID_GPS_ALT    = 0x0820 ,
    FSSP_DATAID_ASPD       = 0x0A00 ,
    FSSP_DATAID_TEMP       = 0x0B70 ,
    FSSP_DATAID_TEMP1      = 0x0B71 ,
    FSSP_DATAID_TEMP2      = 0x0B72 ,
    FSSP_DATAID_TEMP3      = 0x0B73 ,
    FSSP_DATAID_TEMP4      = 0x0B74 ,
    FSSP_DATAID_TEMP5      = 0x0B75 ,
    FSSP_DATAID_TEMP6      = 0x0B76 ,
    FSSP_DATAID_TEMP7      = 0x0B77 ,
    FSSP_DATAID_TEMP8      = 0x0B78 ,
    FSSP_DATAID_A3         = 0x0900 ,
    FSSP_DATAID_A4         = 0x0910
};

// if adding more sensors then increase this value (should be equal to the maximum number of ADD_SENSOR calls)
#define MAX_DATAIDS 20

static uint16_t frSkyDataIdTable[MAX_DATAIDS];

typedef struct {
    uint16_t * table;
    uint8_t size;
    uint8_t index;
} frSkyTableInfo_t;

static frSkyTableInfo_t frSkyDataIdTableInfo = { frSkyDataIdTable, 0, 0 };

#define SMARTPORT_BAUD 57600
#define SMARTPORT_UART_MODE MODE_RXTX
#define SMARTPORT_SERVICE_TIMEOUT_US 1000 // max allowed time to find a value to send

static serialPort_t *smartPortSerialPort = NULL; // The 'SmartPort'(tm) Port.

typedef struct smartPortFrame_s {
    uint8_t  sensorId;
    smartPortPayload_t payload;
    uint8_t  crc;
} __attribute__((packed)) smartPortFrame_t;

#define SMARTPORT_MSP_PAYLOAD_SIZE (sizeof(smartPortPayload_t) - sizeof(uint8_t))

static bool smartPortMspReplyPending = false;

static bool readyToSend(void)
{
    return (serialRxBytesWaiting(smartPortSerialPort) == 0);
}

static smartPortPayload_t *smartPortDataReceive(uint16_t c, bool *clearToSend)
{
    static uint8_t rxBuffer[sizeof(smartPortPayload_t)];
    static uint8_t smartPortRxBytes = 0;
    static bool skipUntilStart = true;
    static bool awaitingSensorId = false;
    static bool byteStuffing = false;
    static uint16_t checksum = 0;

    if (c == FSSP_START_STOP) {
        *clearToSend = false;
        smartPortRxBytes = 0;
        awaitingSensorId = true;
        skipUntilStart = false;

        return NULL;
    } else if (skipUntilStart) {
        return NULL;
    }

    if (awaitingSensorId) {
        awaitingSensorId = false;
        if ((c == FSSP_SENSOR_ID1) && readyToSend()) {
            // our slot is starting, start sending
            *clearToSend = true;
            // no need to decode more
            skipUntilStart = true;
        } else if (c == FSSP_SENSOR_ID2) {
            checksum = 0;
        } else {
            skipUntilStart = true;
        }
    } else {
        if (c == FSSP_DLE) {
            byteStuffing = true;

            return NULL;
        } else if (byteStuffing) {
            c ^= FSSP_DLE_XOR;
            byteStuffing = false;
        }

        if (smartPortRxBytes < sizeof(smartPortPayload_t)) {
            rxBuffer[smartPortRxBytes++] = (uint8_t)c;
            checksum += c;
        } else {
            skipUntilStart = true;

            checksum += c;
            checksum = (checksum & 0xFF) + (checksum >> 8);
            if (checksum == 0xFF) {
                return (smartPortPayload_t *)&rxBuffer;
            }
        }
    }

    return NULL;
}

static void smartPortSendByte(uint8_t c, uint16_t *checksum)
{
    // smart port escape sequence
    if (c == FSSP_DLE || c == FSSP_START_STOP) {
        serialWrite(smartPortSerialPort, FSSP_DLE);
        serialWrite(smartPortSerialPort, c ^ FSSP_DLE_XOR);
    } else {
        serialWrite(smartPortSerialPort, c);
    }

    if (checksum != NULL) {
        frskyCheckSumStep(checksum, c);
    }
}

static bool smartPortPayloadContainsMSP(const smartPortPayload_t *payload)
{
    return payload->frameId == FSSP_MSPC_FRAME_SMARTPORT;
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

#define ADD_SENSOR(dataId) frSkyDataIdTableInfo.table[frSkyDataIdTableInfo.index++] = dataId

static void initSmartPortSensors(void)
{
    frSkyDataIdTableInfo.index = 0;

    ADD_SENSOR(FSSP_DATAID_T1);
    ADD_SENSOR(FSSP_DATAID_T2);

    frSkyDataIdTableInfo.size = frSkyDataIdTableInfo.index;
    frSkyDataIdTableInfo.index = 0;
}

void initSmartPortTelemetry(void)
{
    initSmartPortSensors();

    portOptions_e portOptions = (configHalfDuplex ? SERIAL_BIDIR : SERIAL_UNIDIR) | (configTelemetryInverted ? SERIAL_NOT_INVERTED : SERIAL_INVERTED);

    serialPortIdentifier_e identifier = SERIAL_PORT_USART3; // GCH: enum defined in serial.h, simple numerical value, e.g. SERIAL_PORT_USART3 is 2.

    smartPortSerialPort = openSerialPort(identifier, FUNCTION_TELEMETRY_SMARTPORT, NULL, NULL, SMARTPORT_BAUD, SMARTPORT_UART_MODE, portOptions);
}

static void smartPortSendPackage(uint16_t id, uint32_t val)
{
    smartPortPayload_t payload;
    payload.frameId = FSSP_DATA_FRAME;
    payload.valueId = id;
    payload.data = val;

    smartPortWriteFrame(&payload);
}

static void smartPortSendMspResponse(uint8_t *data) {
    smartPortPayload_t payload;
    payload.frameId = FSSP_MSPS_FRAME;
    memcpy(&payload.valueId, data, SMARTPORT_MSP_PAYLOAD_SIZE);

    smartPortWriteFrame(&payload);
}

static void processSmartPortTelemetry(smartPortPayload_t *payload, volatile bool *clearToSend, const timeUs_t *requestTimeout)
{
    static uint8_t smartPortIdCycleCnt = 0;
    static uint8_t t1Cnt = 0;
    static uint8_t t2Cnt = 0;
    static uint8_t skipRequests = 0;

    // GCH: `payload` is only relevant for MSP frames.

    if (skipRequests) {
        skipRequests--;
    } else if (payload && smartPortPayloadContainsMSP(payload)) {
        // Do not check the physical ID here again
        // unless we start receiving other sensors' packets
        // Pass only the payload: skip frameId
        uint8_t *frameStart = (uint8_t *)&payload->valueId;
        smartPortMspReplyPending = handleMspFrame(frameStart, SMARTPORT_MSP_PAYLOAD_SIZE, &skipRequests);

        // Don't send MSP response after write to eeprom
        // CPU just got out of suspended state after writeEEPROM()
        // We don't know if the receiver is listening again
        // Skip a few telemetry requests before sending response
        if (skipRequests) {
            *clearToSend = false;
        }
    }

    bool doRun = true;
    while (doRun && *clearToSend && !skipRequests) {
        // Ensure we won't get stuck in the loop if there happens to be nothing available to send in a timely manner - dump the slot if we loop in there for too long.
        if (requestTimeout) {
            if (cmpTimeUs(micros(), *requestTimeout) >= 0) {
                *clearToSend = false;

                return;
            }
        } else {
            doRun = false;
        }

        if (smartPortMspReplyPending) {
            smartPortMspReplyPending = sendMspReply(SMARTPORT_MSP_PAYLOAD_SIZE, &smartPortSendMspResponse);
            *clearToSend = false;

            return;
        }

        // we can send back any data we want, our tables keep track of the order and frequency of each data type we send
        frSkyTableInfo_t * tableInfo = &frSkyDataIdTableInfo;

        if (tableInfo->index == tableInfo->size) { // end of table reached, loop back
            tableInfo->index = 0;
        }

        uint16_t id = tableInfo->table[tableInfo->index];
        smartPortIdCycleCnt++;
        tableInfo->index++;

        int32_t tmpi;
        uint32_t tmp2 = 0;

        switch (id) {
            case FSSP_DATAID_T1         :
                tmpi = 1234; // Dummy value of at most 4 digits that we want to encode in Tmp1.

                // the t1Cnt simply allows the telemetry view to show at least some changes
                t1Cnt++;
                if (t1Cnt == 4) {
                    t1Cnt = 1;
                }
                tmpi += t1Cnt * 10000; // start off with at least one digit so the most significant 0 won't be cut off
                // the Taranis seems to be able to fit 5 digits on the screen
                // the Taranis seems to consider this number a signed 16 bit integer

                smartPortSendPackage(id, (uint32_t)tmpi);
                *clearToSend = false;
                break;
            case FSSP_DATAID_T2         :
                tmp2 = 5678;
                t2Cnt++;
                if (t2Cnt == 4) {
                    t2Cnt = 0;
                }
                tmp2 += t2Cnt * 10000;
                smartPortSendPackage(id, tmp2);
                *clearToSend = false;
                break;
            default:
                break;
                // if nothing is sent, hasRequest isn't cleared, we already incremented the counter, just loop back to the start
        }
    }
}

void handleSmartPortTelemetry(void)
{
    const timeUs_t requestTimeout = micros() + SMARTPORT_SERVICE_TIMEOUT_US;

    smartPortPayload_t *payload = NULL;
    bool clearToSend = false;
    while (serialRxBytesWaiting(smartPortSerialPort) > 0 && !payload) {
        uint8_t c = serialRead(smartPortSerialPort);
        payload = smartPortDataReceive(c, &clearToSend);
    }

    processSmartPortTelemetry(payload, &clearToSend, &requestTimeout);
}

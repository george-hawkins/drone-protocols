#include <stdlib.h>
#include <stdio.h>
#include <stdint.h>
#include <time.h>

#define SBUS_STARTBYTE 0x0f
#define SBUS_ENDBYTE   0x00
#define SBUS_FAILSAFE_INACTIVE 0
#define SBUS_FAILSAFE_ACTIVE   1

// This code generates a valid random SBUS frame and then parses it.
// The output is used to validate my Python implementation of SBUS frame parsing.
//
// The parsing logic here is from the Dennis Marinus's SBUS library, see:
// https://github.com/zendes/SBUS/blob/5cf196c/SBUS.cpp#L33
//
int main(void) {
    uint8_t buffer[25];

    buffer[0] = SBUS_STARTBYTE;
    buffer[24] = SBUS_ENDBYTE;

    srand(time(NULL));

    for (int i = 1; i <= 23; i++) {
        buffer[i] = rand();
    }

    for (int i = 0; i <= 24; i++) {
        if (i > 0) printf(":");
        printf("%02X", buffer[i]);
    }
    printf("\n");

    int _channels[18];
    int _failsafe;
    long _lostFrames = 0;

    _channels[0]  = ((buffer[1]    |buffer[2]<<8)                 & 0x07FF);
    _channels[1]  = ((buffer[2]>>3 |buffer[3]<<5)                 & 0x07FF);
    _channels[2]  = ((buffer[3]>>6 |buffer[4]<<2 |buffer[5]<<10)  & 0x07FF);
    _channels[3]  = ((buffer[5]>>1 |buffer[6]<<7)                 & 0x07FF);
    _channels[4]  = ((buffer[6]>>4 |buffer[7]<<4)                 & 0x07FF);
    _channels[5]  = ((buffer[7]>>7 |buffer[8]<<1 |buffer[9]<<9)   & 0x07FF);
    _channels[6]  = ((buffer[9]>>2 |buffer[10]<<6)                & 0x07FF);
    _channels[7]  = ((buffer[10]>>5|buffer[11]<<3)                & 0x07FF);
    _channels[8]  = ((buffer[12]   |buffer[13]<<8)                & 0x07FF);
    _channels[9]  = ((buffer[13]>>3|buffer[14]<<5)                & 0x07FF);
    _channels[10] = ((buffer[14]>>6|buffer[15]<<2|buffer[16]<<10) & 0x07FF);
    _channels[11] = ((buffer[16]>>1|buffer[17]<<7)                & 0x07FF);
    _channels[12] = ((buffer[17]>>4|buffer[18]<<4)                & 0x07FF);
    _channels[13] = ((buffer[18]>>7|buffer[19]<<1|buffer[20]<<9)  & 0x07FF);
    _channels[14] = ((buffer[20]>>2|buffer[21]<<6)                & 0x07FF);
    _channels[15] = ((buffer[21]>>5|buffer[22]<<3)                & 0x07FF);

    _channels[16] = ((buffer[23])      & 0x0001) ? 2047 : 0;
    _channels[17] = ((buffer[23] >> 1) & 0x0001) ? 2047 : 0;

    if ((buffer[23] >> 2) & 0x0001) {
        _lostFrames++;
    }

    _failsafe = ((buffer[23] >> 3) & 0x0001) ? SBUS_FAILSAFE_ACTIVE : SBUS_FAILSAFE_INACTIVE;

    for (int i = 0; i <= 17; i++) {
        if (i > 0) printf(":");
        printf("%03X", _channels[i]);
    }
    printf("\n");
    printf("_lostFrames: %ld\n", _lostFrames);
    printf("_failsafe: %d\n", _failsafe);

    return EXIT_SUCCESS;
}

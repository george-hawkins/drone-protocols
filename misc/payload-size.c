#include <stdint.h>
#include <stdio.h>

typedef struct {
    uint8_t  frameId;
    uint16_t valueId;
    uint32_t data;
} __attribute__((packed)) smartPortPayload_t;

int main(void) {
    printf("%lu\n", sizeof(smartPortPayload_t));
    printf("%lu\n", sizeof(smartPortPayload_t) - sizeof(uint8_t));

    return 0;
}

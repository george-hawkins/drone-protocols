#!/bin/bash -e

ROOT=/home/ghawkins/git/betaflight-ghawkins

FILE=msp_shared

arm-none-eabi-gcc \
    -c \
    -o $FILE.o \
    -mthumb \
    -mcpu=cortex-m7 \
    -mfloat-abi=hard \
    -mfpu=fpv5-sp-d16 \
    -fsingle-precision-constant \
    -Wdouble-promotion \
    -I. \
    -I$ROOT/src/main \
    -I$ROOT/src/main/target \
    -I$ROOT/src/main/startup \
    -I$ROOT/lib/main/STM32F7/Drivers/STM32F7xx_HAL_Driver/Inc \
    -I$ROOT/lib/main/STM32F7/Middlewares/ST/STM32_USB_Device_Library/Core/Inc \
    -I$ROOT/lib/main/STM32F7/Middlewares/ST/STM32_USB_Device_Library/Class/CDC/Inc \
    -I$ROOT/lib/main/STM32F7/Middlewares/ST/STM32_USB_Device_Library/Class/HID/Inc \
    -I$ROOT/lib/main/STM32F7/Middlewares/ST/STM32_USB_Device_Library/Class/MSC/Inc \
    -I$ROOT/lib/main/CMSIS/Core/Include \
    -I$ROOT/lib/main/STM32F7/Drivers/CMSIS/Device/ST/STM32F7xx/Include \
    -I$ROOT/src/main/vcp_hal \
    -I$ROOT/lib/main/MAVLink \
    -I$ROOT/src/main/target/NUCLEOF722_MIN \
    -I$ROOT/lib/main/CMSIS/DSP/Include \
    -std=gnu11 \
    -Wall \
    -Wextra \
    -Wunsafe-loop-optimizations \
    -Wdouble-promotion \
    -ffunction-sections \
    -fdata-sections \
    -fno-common \
    -pedantic \
    -DUSE_HAL_DRIVER \
    -DUSE_FULL_LL_DRIVER \
    -DSTM32F722xx \
    -DHSE_VALUE=8000000 \
    -DARM_MATH_MATRIX_CHECK \
    -DARM_MATH_ROUNDING \
    -D__FPU_PRESENT=1 \
    -DUNALIGNED_SUPPORT_DISABLE \
    -DARM_MATH_CM7 \
    -DTARGET_FLASH_SIZE=512 \
    -DHSE_VALUE=8000000 \
    -D_GNU_SOURCE \
    -DUSE_STDPERIPH_DRIVER \
    -DNUCLEOF722_MIN \
    -DNUCLEOF722_MIN \
    -D'__FORKNAME__="betaflight"' \
    -D'__TARGET__="NUCLEOF722_MIN"' \
    -D'__REVISION__="norevision"' \
    -save-temps=obj \
    -MMD \
    -MP \
    -flto \
    -fuse-linker-plugin \
    -ffast-math \
    -O2 \
    $FILE.c

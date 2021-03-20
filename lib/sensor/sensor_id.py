# Taken from https://github.com/opentx/opentx/blob/2.3/radio/src/telemetry/frsky.h
class SensorId:
    ALT_FIRST = 0x0100
    ALT_LAST = 0x010F
    VARIO_FIRST = 0x0110
    VARIO_LAST = 0x011F
    CURR_FIRST = 0x0200
    CURR_LAST = 0x020F
    VFAS_FIRST = 0x0210
    VFAS_LAST = 0x021F
    CELLS_FIRST = 0x0300
    CELLS_LAST = 0x030F
    T1_FIRST = 0x0400
    T1_LAST = 0x040F
    T2_FIRST = 0x0410
    T2_LAST = 0x041F
    RPM_FIRST = 0x0500
    RPM_LAST = 0x050F
    FUEL_FIRST = 0x0600
    FUEL_LAST = 0x060F
    ACCX_FIRST = 0x0700
    ACCX_LAST = 0x070F
    ACCY_FIRST = 0x0710
    ACCY_LAST = 0x071F
    ACCZ_FIRST = 0x0720
    ACCZ_LAST = 0x072F
    GPS_LONG_LATI_FIRST = 0x0800
    GPS_LONG_LATI_LAST = 0x080F
    GPS_ALT_FIRST = 0x0820
    GPS_ALT_LAST = 0x082F
    GPS_SPEED_FIRST = 0x0830
    GPS_SPEED_LAST = 0x083F
    GPS_COURS_FIRST = 0x0840
    GPS_COURS_LAST = 0x084F
    GPS_TIME_DATE_FIRST = 0x0850
    GPS_TIME_DATE_LAST = 0x085F
    A3_FIRST = 0x0900
    A3_LAST = 0x090F
    A4_FIRST = 0x0910
    A4_LAST = 0x091F
    AIR_SPEED_FIRST = 0x0A00
    AIR_SPEED_LAST = 0x0A0F
    FUEL_QTY_FIRST = 0x0A10
    FUEL_QTY_LAST = 0x0A1F
    RBOX_BATT1_FIRST = 0x0B00
    RBOX_BATT1_LAST = 0x0B0F
    RBOX_BATT2_FIRST = 0x0B10
    RBOX_BATT2_LAST = 0x0B1F
    RBOX_STATE_FIRST = 0x0B20
    RBOX_STATE_LAST = 0x0B2F
    RBOX_CNSP_FIRST = 0x0B30
    RBOX_CNSP_LAST = 0x0B3F
    SD1_FIRST = 0x0B40
    SD1_LAST = 0x0B4F
    ESC_POWER_FIRST = 0x0B50
    ESC_POWER_LAST = 0x0B5F
    ESC_RPM_CONS_FIRST = 0x0B60
    ESC_RPM_CONS_LAST = 0x0B6F
    ESC_TEMPERATURE_FIRST = 0x0B70
    ESC_TEMPERATURE_LAST = 0x0B7F
    RB3040_OUTPUT_FIRST = 0x0B80
    RB3040_OUTPUT_LAST = 0x0B8F
    RB3040_CH1_2_FIRST = 0x0B90
    RB3040_CH1_2_LAST = 0x0B9F
    RB3040_CH3_4_FIRST = 0x0BA0
    RB3040_CH3_4_LAST = 0x0BAF
    RB3040_CH5_6_FIRST = 0x0BB0
    RB3040_CH5_6_LAST = 0x0BBF
    RB3040_CH7_8_FIRST = 0x0BC0
    RB3040_CH7_8_LAST = 0x0BCF
    X8R_FIRST = 0x0C20
    X8R_LAST = 0x0C2F
    S6R_FIRST = 0x0C30
    S6R_LAST = 0x0C3F
    GASSUIT_TEMP1_FIRST = 0x0D00
    GASSUIT_TEMP1_LAST = 0x0D0F
    GASSUIT_TEMP2_FIRST = 0x0D10
    GASSUIT_TEMP2_LAST = 0x0D1F
    GASSUIT_SPEED_FIRST = 0x0D20
    GASSUIT_SPEED_LAST = 0x0D2F
    GASSUIT_RES_VOL_FIRST = 0x0D30
    GASSUIT_RES_VOL_LAST = 0x0D3F
    GASSUIT_RES_PERC_FIRST = 0x0D40
    GASSUIT_RES_PERC_LAST = 0x0D4F
    GASSUIT_FLOW_FIRST = 0x0D50
    GASSUIT_FLOW_LAST = 0x0D5F
    GASSUIT_MAX_FLOW_FIRST = 0x0D60
    GASSUIT_MAX_FLOW_LAST = 0x0D6F
    GASSUIT_AVG_FLOW_FIRST = 0x0D70
    GASSUIT_AVG_FLOW_LAST = 0x0D7F
    SBEC_POWER_FIRST = 0x0E50
    SBEC_POWER_LAST = 0x0E5F
    DIY_FIRST = 0x5100
    DIY_LAST = 0x52FF
    DIY_STREAM_FIRST = 0x5000
    DIY_STREAM_LAST = 0x50FF
    SERVO_FIRST = 0x6800
    SERVO_LAST = 0x680F
    FACT_TEST = 0xF000
    VALID_FRAME_RATE = 0xF010
    RSSI = 0xF101
    ADC1 = 0xF102
    ADC2 = 0xF103
    BATT = 0xF104
    RAS = 0xF105
    XJT_VERSION = 0xF106
    R9_PWR = 0xF107
    SP2UART_A = 0xFD00
    SP2UART_B = 0xFD01

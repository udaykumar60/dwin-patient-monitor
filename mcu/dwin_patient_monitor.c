/*
 * Example frames for a real patient-monitor MCU talking to a DWIN T5L panel.
 * UART: 115200 8N1.  MCU TX -> DWIN RX, MCU RX -> DWIN TX, common GND.
 *
 * Replace the demo numbers with ADC / probe values from ECG, RESP, SpO2.
 * This is the same protocol Python uses in this project.
 */
#include <stdint.h>

/* Vital VPs sit at 0x5000+ so they do not overlap DGUS curve RAM 0x1000-0x4FFF. */
#define VP_HR     0x5000
#define VP_SPO2   0x5001
#define VP_TEMP   0x5002  /* value * 10, e.g. 365 = 36.5 C */
#define VP_NIBP   0x5003
#define VP_ALARM  0x5004
#define VP_RESP   0x5005

extern void uart_write(const uint8_t *data, unsigned len);

static void put_u16(uint8_t *p, uint16_t v)
{
    p[0] = (uint8_t)(v >> 8);
    p[1] = (uint8_t)v;
}

static void write_vp_u16(uint16_t addr, uint16_t value)
{
    uint8_t f[8] = {0x5A, 0xA5, 0x05, 0x82};
    put_u16(f + 4, addr);
    put_u16(f + 6, value);
    uart_write(f, 8);
}

/* Real-time curve command 0x84. channel 0=ECG, 1=RESP, 2=SpO2. Y = 0..255. */
static void write_curve(uint8_t channel, const uint16_t *samples, unsigned n)
{
    uint8_t buf[3 + 1 + 1 + 240];
    unsigned i;
    if (n > 120) n = 120;
    buf[0] = 0x5A;
    buf[1] = 0xA5;
    buf[2] = (uint8_t)(2 + n * 2);
    buf[3] = 0x84;
    buf[4] = (uint8_t)(1u << (channel & 7));
    for (i = 0; i < n; i++)
        put_u16(buf + 5 + i * 2, samples[i]);
    uart_write(buf, 5 + n * 2);
}

void dwin_send_vitals(uint16_t hr, uint16_t spo2, uint16_t temp_x10,
                      uint16_t nibp, uint16_t resp, uint16_t alarm)
{
    write_vp_u16(VP_HR, hr);
    write_vp_u16(VP_SPO2, spo2);
    write_vp_u16(VP_TEMP, temp_x10);
    write_vp_u16(VP_NIBP, nibp);
    write_vp_u16(VP_RESP, resp);
    write_vp_u16(VP_ALARM, alarm);
}

void dwin_send_waves(const uint16_t *ecg, const uint16_t *resp,
                     const uint16_t *spo2, unsigned n)
{
    write_curve(0, ecg, n);
    write_curve(1, resp, n);
    write_curve(2, spo2, n);
}

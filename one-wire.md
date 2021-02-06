Bi-directional communication using a single wire
================================================

Steps:

* Just wire up RX and TX (with a resistor for the RX pin) and get things work. Does one see the TX traffic on the RX? I presume so.
* Try specifying the same physical pin for RX and TX. Does this even work? If it does, is there any automatic half-duplex support (see down below)?
* Try configuring ISO 7816 without a clock - can this be used for generic, i.e. non-smartcard, communication?

TODO: find out what determines the resistor size used on the RX pin - various posts mention it but I'm not sure what determins its size.

**Update:**

The resistor is on the TX pin, **not** the RX. From this [thread](https://www.avrfreaks.net/forum/atmega-uart-full-duplex-device-half-duplex), on AVR Freaks, it looks like the resistor is there to limit the current of one side's TX (let's call that the slave side) so that when it's not transmitting it holds the line high (as Wikipedia puts on the [UART page](https://en.wikipedia.org/wiki/Universal_asynchronous_receiver-transmitter), "the idle, no data state is high-voltage, or powered") but doesn't prevent the other side from pulling it low (and high), i.e. transmitting. However, I may be misunderstanding. Other pages refer to the resistor protecting the TX pin, referring to it protecting against a short, i.e. the RX is expecting to sink current but the TX in a typical situation is not expecting to see a signal on its wire but in a single wire setup will see the other side's TX signal.

Posts #7 mentions 470&ohm; - 1K&ohm; while #16 talks about 4.7k&ohm; or 1k&ohm; - so it's not clear what size resistors we should be considering.

It's clear from posts like ??? that the resistor should be based on factors such as whether the other side is using a pullup resistor. However, most pages covering this kind of thing use a 4.7k&ohm; resistor. For the yyy project that specifically involves working with S.PORT (and not just some random one-wire use-case), they used a 4.7k&ohm; resistor initially but then switched to a zzz&ohm; one - it'd be iteresting to know why. Note that the yyy project uses a 5V [Arduino Pro Mini](https://www.sparkfun.com/products/11113) whereas most other projects are using 3.3V boards. I would have naively assumed that a higher voltage might have required a larger resistor, so it would be interesting to know why they shifted to a smaller one. I would have also thought there was an issue with the S.BUS signal being 3.3V - surely some level shifting (like [this](https://www.adafruit.com/product/757))?

TODO: fill in question marks etc. above and link to pages on work Mac.


One-wire USART communication on Atmel processors
------------------------------------------------

It looks like Atmel 8-bit processors like the tinyAVRs and megaAVRs directly support one-wire USART communication in hardware:

> The USART peripheral supported by the tinyAVR 0- and 1-series and megaAVR 0-series has features
> that simplifies one-wire communication. TXD and RXD can be connected internally, eliminating the need
> for two pins. The TXD pin is used as both input and output. The pin supports open-drain mode and a
> configurable internal pull-up, eliminating the need for external hardware. Moreover, compared to the
> 1-Wire bit banging example, there is minimal need for CPU cycles, and interrupts can be enabled the
> whole time.

The above is from section 4 of the _USART in One-Wire Mode_ [application note](https://www.microchip.com/wwwappnotes/appnotes.aspx?appnote=en605794).

Note: this application note distinguishes between the term "one-wire", meaning just meaning communication using a single wire in a general sense, and the term "[1-Wire](https://en.wikipedia.org/wiki/1-Wire)" meaning a specific protocol (from Dallas Semiconductor).

I can't find anything directly equivalent for the SAM family of processors. The _SAM D5x/E5x Family_ datasheet (that's linked to [here](https://microchipdeveloper.com/32bit:samd5) covers RS485 where there's a single RX/TX line and a TE (transmission enable) line. Presumably there's no need to actually do anything with the TE line, so this would _seem_ to correspond to one-wire.

From the diagrams in the RS485 section it looks like this would achieve what's required - the RX is disabled while the TX is active (and one can specify a guard time to keep it disabled for a specified short interval after transmission has stopped).

---

**Update:**

After coming across the RS485 example (covered) below - I think RS485 actually still requires you to wire up external logic to disable the RX (i.e. prevent it from seeing the TX signal) and all that you're getting, with RS485, is the TE signal to drive this logic.

The logic you need is called an RS485 transceiver, like this [SP3485](https://www.sparkfun.com/products/10124) from Sparkfun - if you look at the block diagram in the datasheet for the SP3485, you'll see it's provides identical functionality to the figure shown in the _SAM D5x/E5x Family_ datasheet.

So perhaps ISO 7816 (described next) is still an option. Or the ASF quote later that when "TX and RX are connected to the same pin, the USART will operate in half-duplex mode" means it's as simple as just specifying the same pin for RX and TX. Note: looking at the ASF `usart.c`, it doesn't look like it's checking for TX and RX being the same pin and taking some action, i.e. if this half-duplex mode exists then it would seem to handled at a lower level than ASF.

---

The datasheet also describes ISO 7816 support:

> ISO 7816 is a half duplex communication on a single bidirectional line. The USART connects to a smart card as
> shown below. The output is only driven when the USART is transmitting. The USART is considered as the master of
> the communication as it generates the clock.

However, this protocol requires a clock signal in addition to the RX/TX wire - but perhaps one can do without the clock.

The opening _Features_ section of the datasheet, clearly states (under _System Peripherals_) that:

> Up to eight Serial Communication Interfaces (SERCOM), each configurable to operate as either:
>
> * USART with full-duplex and single-wire half-duplex configuration
> * ISO7816
> * I2C up to 3.4 MHz
> * ...

So they clearly state that the USART can be configured for half-duplex (and they list ISO 7816 separately to USART so maybe one shouldn't view it as simply a USART mode of operation).

The SAM D2x datasheet states the same thing - however, user _Juraj_ states in this Arduino StackExchange [answer](https://arduino.stackexchange.com/a/72028) that he thinks this is a mistake as application note [AT11626](https://www.microchip.com/wwwAppNotes/AppNotes.aspx?appnote=en590861) only talks about USART being "full-duplex in operation".

I'm not so sure - the RS485 support described in the datasheet seems clearly half-duplex.

In this MicroChip [forum post](https://www.microchip.com/forums/FindPost/96267), achieving half-duplex by turning RX on and off is described (for an 8-bit PIC MCU but the process sounds generally applicable). However, post #5 in this [thread](https://www.avrfreaks.net/comment/1445621#comment-1445621) on AVR Freaks suggest this won't really work out. And post #7 suggests that you shouldn't even worry about disabling RX and simply take into account that you'll see your own TX traffic (and can actually use this to track when a "TX char has completed shifting out of its register").

In the [ASF Manual](https://www.microchip.com/wwwAppNotes/AppNotes.aspx?appnote=en590959), in the _SERCOM USART MUX Settings_ section, they note:

> When TX and RX are connected to the same pin, the USART will operate in half-duplex mode if both the transmitter and receivers are enabled.

TODO: is ASF the same as ASF4? It doesn't look like it.

Note that [`asf4/.../sercom0.h`](https://github.com/adafruit/asf4/blob/master/samd51/include/instance/sercom0.h) (and the other `sercomX` header files) includes:

```
#define SERCOM0_USART_ISO7816       1        // USART ISO7816 mode implemented?
...
#define SERCOM0_USART_RS485         1        // USART RS485 mode implemented?
```

But I can't find any code snippets that use either.

Atmel have a small example application - [`qs_rs485.c`](https://github.com/osmocom/atmel-asf-projects/blob/master/sam0/drivers/sercom/usart/quick_start_rs485/qs_rs485.c) - that demonstrates working with RS485 (using ASF, not ASF4). Note that the code is from Atmel but checked in here by the Osmocom organization (as Atmel don't seem to make things available via GitHub or something similar). You can find the implemenation of `uart_init` in [`usart.c`](https://github.com/osmocom/atmel-asf-projects/blob/master/sam0/drivers/sercom/usart/usart.c), there'll you see:

```
#ifdef FEATURE_USART_RS485
    if ((usart_hw->CTRLA.reg & SERCOM_USART_CTRLA_FORM_Msk) != \
        SERCOM_USART_CTRLA_FORM(0x07)) {
        usart_hw->CTRLC.reg &= ~(SERCOM_USART_CTRLC_GTIME(0x7));
        usart_hw->CTRLC.reg |= SERCOM_USART_CTRLC_GTIME(config->rs485_guard_time);
    }
#endif
```

This is just setting guard time - you can find similar code in the ASF4 code base. The `0x07` check seems to be specifically checking that one isn't in ISO 7816 mode (see SAM D5x/E5x Family_ datasheet, where CTRLA.FORM is mentioned for both RS485 and ISO 7816). 

And you can find an example of what `EXT1_RS485_MODULE` etc. map to for a particular MCU here, in [`samc21_xplained_pro.h`](https://github.com/osmocom/atmel-asf-projects/blob/master/sam0/boards/samc21_xplained_pro/samc21_xplained_pro.h):

```
/** \name Extension header #1 USART RS485 definitions
 *  @{
 */
#define EXT1_RS485_MODULE              SERCOM3
#define EXT1_RS485_SERCOM_MUX_SETTING  USART_RX_1_TX_0_XCK_1_TE_2
#define EXT1_RS485_SERCOM_PINMUX_PAD0  PINMUX_PA22C_SERCOM3_PAD0
#define EXT1_RS485_SERCOM_PINMUX_PAD1  PINMUX_PA23C_SERCOM3_PAD1
#define EXT1_RS485_SERCOM_PINMUX_PAD2  PINMUX_PA20D_SERCOM3_PAD2
#define EXT1_RS485_SERCOM_PINMUX_PAD3  PINMUX_UNUSED
#define EXT1_RS485_SERCOM_DMAC_ID_TX   SERCOM1_DMAC_ID_TX
#define EXT1_RS485_SERCOM_DMAC_ID_RX   SERCOM1_DMAC_ID_RX
```

Note: you can find what `RX_1_TX_0_XCK_1` etc. means in the ASF manual linked to above.

This seems odd - here RX and TX are distinct pins - are they connected internally or does one have to connect both and how does this relate to the quote mentioned earlier, that when "TX and RX are connected to the same pin, the USART will operate in half-duplex mode if both the transmitter and receivers are enabled"?

---

As well as the RS485, one can find a corresponding ISO 7816 example in [`qs_smart_card.c`](https://github.com/osmocom/atmel-asf-projects/blob/master/sam0/components/smart_card/quick_start/qs_smart_card.c).

Note: unlike RS485, it seems clear that not all devices support ISO 7816 - in the Osmocom repository, only the SAM L22 Xplained Pro has the necessary `CONF_ISO7816_MUX_SETTING` define in its header files. Is it the case that all SAM D21/51 MCUs support ISO 7816 or only some of them?

---

It's a pity, I can't find any corresponding ASF4 quick start examples. Maybe, something similar is bundled in with e.g. Atmel Studio and it's simply that MicroChip/Atmel don't go out of their way to make them easily available on the web.

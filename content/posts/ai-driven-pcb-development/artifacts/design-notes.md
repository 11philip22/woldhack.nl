# Blue Pill USB VBUS switch, revision 2

Open `bluepill-vbus-switch.kicad_pro` in KiCad 10. The PCB is **53 x 46 mm**, nominally 1.6 mm thick, with four copper layers. All fitted components are on top. Two 1x20 female sockets accept the classic STM32F103 Blue Pill. Its micro-USB connector faces left and remains accessible. The USB-A plug faces left on the lower half; the receptacle faces right. The male plug projects about 15.5 mm beyond the PCB.

## Power and control

- Power the Blue Pill through **its own micro-USB port**. J1/J2's 5 V, 3.3 V and VBAT pads are isolated on the carrier; there is no connection between the two USB supplies. Ground is shared, so this is not galvanic isolation.
- The upstream USB-A male connector supplies downstream VBUS through U1, TPS2552DBVR. It does not power the controller.
- **PA0 HIGH turns VBUS on; LOW or an unpowered/absent Blue Pill turns it off.** Q1 is an open-drain level interface; R2 pulls its gate low. R1 pulls the active-low switch enable up to upstream VBUS. Initialize PA0 low before enabling it as an output.
- D+ and D- pass directly between J3 and J4. They do not connect to PA11/PA12 or to the Blue Pill USB port. Ground and connector shields stay connected when VBUS is off.
- Nominal load target: **500 mA at 5 V**. R4 = 43 kohm, 1%, gives approximately 0.61 A nominal limiting (roughly 0.55-0.68 A across IC/resistor tolerances). This is overload protection, not USB current negotiation. The downstream device must respect the upstream port's negotiated current allowance.
- C3 is a 150 uF, 35 V reservoir after the switch. R5 = 1 kohm discharges it when off; with no external capacitance, its nominal time constant is 150 ms. Connected equipment can change discharge time or remain powered by another supply. U1's fault output is unused.

## Parts

Parts were selected through the connected PCB Parts MCP's LCSC/JLCPCB search. `bom.csv` contains each reference, exact part number, footprint and LCSC code. No ESP socket, ESP power supply or Wi-Fi circuitry is fitted.

| Reference | Part | LCSC |
| --- | --- | --- |
| J1, J2 | Kinghelm KH-2.54FH-1X20P-H8.5, 1x20 female, 2.54 mm pitch, 8.5 mm body | [C2905423](https://www.lcsc.com/product-detail/C2905423.html) |
| J3 | XUNPU USB-212-BCW, USB-A male | [C720521](https://www.lcsc.com/product-detail/C720521.html) |
| J4 | SHOU HAN AF180QT1.0, USB-A female | [C404963](https://www.lcsc.com/product-detail/C404963.html) |
| U1 | Texas Instruments TPS2552DBVR, active-low VBUS switch | [C46506](https://www.lcsc.com/product-detail/C46506.html) |
| Q1 | onsemi 2N7002, SOT-23 | [C124475](https://www.lcsc.com/product-detail/C124475.html) |
| C3 | Lelon VZT151M1VTR-0607, 150 uF, 35 V, 6.3 x 7.7 mm | [C249984](https://www.lcsc.com/product-detail/C249984.html) |

The Blue Pill module is supplied separately. Its socket rows are 15.24 mm apart; both pin 1 pads are at the right/SWD end. The original socket-only design is preserved in `archive/bluepill-socket/`.

## USB routing and fabrication

The data pair runs entirely on F.Cu, with no vias or branches and equal routed lengths of approximately 35.148 mm. Nominal trace width is 0.28 mm, pair edge gap 0.18 mm. In1.Cu and In2.Cu are ground planes. C3 and the switching/control components form a compact group below the data pair. Q1 and U1 share a centerline; C1, C2 and R5 share an upper row, and R3, R1 and R4 share a lower row. Switched VBUS, including the C3 reservoir connection, stays entirely on F.Cu below D+/D−. Only the controller enable and a short upstream-VBUS feed to R1 use B.Cu, separated from USB data by the ground planes.

Use **four layers** with the [JLC04161H-7628 stackup](https://jlcpcb.com/impedance): outer copper 35 um, inner copper 15.2 um, F.Cu-to-In1.Cu dielectric 0.2104 mm / Er 4.4, core 1.065 mm / Er 4.6, lower dielectric 0.2104 mm / Er 4.4. The stackup is included in the PCB file. The declared finished thickness is nominal 1.6 mm; the published constituent thicknesses and solder-mask estimate have normal manufacturing tolerance.

**Specify 90 ohm differential impedance and have the fabricator confirm/adjust the pair geometry for its actual stackup and solder mask.** Width/gap are an engineering starting point, not a measured impedance result. ERC/DRC cannot verify the USB 480 Mbit/s eye diagram. This is a prototype design; verify High-Speed operation, power switching and connector fit on the first assembly before ordering a production run.

The USB connector libraries are project-local. J3's imported footprint has corrected non-plated mounting holes and a drawing-layer edge marker. J4 was redrawn from the manufacturer's land pattern: 7 mm signal span, 2 mm middle pitch, 14.8 mm shell-pad spacing, 4.8 mm peg spacing and 1.3 mm peg holes. The shared 3D models are illustrative; the manufacturing footprints follow the drawings. Datasheets are in `docs/datasheets/`.

## Build and verification

`./build.ps1` runs KiCad CLI ERC, DRC with schematic parity, and exports SVG, PNG, Gerbers and drills. `./build.ps1 -Generate` first regenerates the design from `build_board.py`, overwriting manual schematic/PCB edits. The generator checks socket pin mapping, separation of controller power and matched USB routing. KiCad CLI was run outside the Codex sandbox as requested.

Final reports: `output/erc.rpt`, `output/drc.rpt`. Fabrication package: `output/bluepill-vbus-switch-gerbers.zip`. Do not use the old socket-only Gerbers.

## References

- [TI TPS2552/2553 datasheet](https://www.ti.com/lit/gpn/tps2553), pinout, enable behavior and current-limit equations/table.
- [XUNPU USB-212-BCW drawing](https://atta.szlcsc.com/upload/public/pdf/source/20200810/C720521_9B8BCB15430B8E438AE60E4D526760F3.pdf).
- [SHOU HAN AF180QT1.0 drawing and specification](https://atta.szlcsc.com/upload/public/pdf/source/20241125/4DA01BD26DBE7C4DBBA913DB9F1A3543.pdf).
- [Classic Blue Pill dimensions and pinout](https://stm32-base.org/boards/STM32F103C8T6-Blue-Pill.html).

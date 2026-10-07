---
date: "2026-10-07T00:00:00+02:00"
draft: true
title: "AI driven pcb development"
---

Working with Codex on a ULPI project kept ending in the same place: it asked me to plug or unplug a USB device. I got tired of doing that by hand, so I decided to have Codex design a board that would let it turn the device's VBUS power on and off itself.

<!--more-->

That meant giving Codex a way to work with KiCad. On Windows, KiCad's writes to the registry and files in Documents kept running into Codex CLI's sandbox, so I put both in [Docker](https://github.com/11philip22/codex-kikad-docker).

I started with only the requirements: a USB-A male plug and female socket, USB 2.0 high-speed support, a VBUS switch controlled by an STM32 Blue Pill, and a socket for the Blue Pill. Codex could then look for parts at JLCPCB through the [`pcbparts` MCP server](https://github.com/Averyy/pcbparts-mcp) and download their footprints with [easyeda2kicad.py](https://github.com/uPesy/easyeda2kicad.py).

## First result

This is the first board design Codex produced.

<div class="screenshot-row">
{{< figure src="bluepill-tilted.png" link="bluepill-tilted.png" alt="3D render of the USB VBUS switch board with a USB-A plug, USB-A socket and STM32 Blue Pill" caption="First 3D render of the board." >}}

{{< figure src="pcb-layout.svg" link="pcb-layout.svg" alt="PCB layout showing the Blue Pill socket, USB-A input and output, VBUS switch components and routed traces" caption="First PCB layout." >}}

{{< figure src="schematic.svg" link="schematic.svg" alt="Schematic showing the Blue Pill socket, USB-A input and output, and VBUS switching circuit" caption="First schematic." >}}
</div>

### Switch control

Codex decided the board needed Q1, a 2N7002 MOSFET, and placed it in the control circuit for the [TPS2552's active-low enable pin](https://www.ti.com/lit/ds/symlink/tps2552.pdf). When the Blue Pill drives PA0 high, Q1 pulls `SW_EN_N` to ground and the switch powers the USB device. When PA0 is low or floating, Q1 turns off and R1 pulls `SW_EN_N` up to `VBUS_IN`, turning the power off. R2 keeps Q1's gate low if the Blue Pill is absent. Q1 also keeps the 5 V pull-up away from PA0.

## Placement

I wasn't happy with the first layout. C3 sat above the USB data pair, and the other components were scattered across the board. I gave Codex this prompt:

```
› c3 should be under the d+ and d- so we domt have to route vbus out under the differential pair.
  all other componenents are scattered over the board. group them toghether, align them and make it look nice
```

Codex moved C3 below the data pair and grouped the switch components along the lower edge of the board. The schematic stayed the same; this was a placement and routing change.

<div class="screenshot-row">
{{< figure src="bluepill-placement.png" link="bluepill-placement.png" alt="3D render after Codex grouped the VBUS switch components along the bottom of the board" caption="Board after Codex rearranged the components." >}}

{{< figure src="pcb-layout-placement.svg" link="pcb-layout-placement.svg" alt="PCB layout with C3 below the USB data pair and the switch components grouped along the bottom edge" caption="PCB layout after the placement change." >}}
</div>

## Manual fixes

Codex got the layout much closer, but I still made a pass by hand. I put R2 and R3 together beside Q1, tightened the placement around U1 and C3, and cleaned up the traces and silkscreen. I also redrew the schematic with explicit wires and ground symbols so the connections were easier to follow.

<div class="screenshot-row">
{{< figure src="bluepill-manual.png" link="bluepill-manual.png" alt="3D render of the board after manual component placement and silkscreen cleanup" caption="Board after my manual changes." >}}

{{< figure src="pcb-layout-manual.svg" link="pcb-layout-manual.svg" alt="PCB layout after manual cleanup of the VBUS switch components, traces, and labels" caption="PCB layout after the manual pass." >}}

{{< figure src="schematic-manual.svg" link="schematic-manual.svg" alt="USB VBUS switch schematic with wiring and ground connections drawn between the components" caption="Schematic after the manual pass." >}}
</div>

Codex took the board from a short set of requirements to a schematic and routed PCB. I still had to review the result and make a few manual changes to the placement, traces and schematic.

The real test is the physical board. If it works, Codex can finally turn USB power off and on without asking me to pull the plug.

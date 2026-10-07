---
date: "2026-09-20T00:00:00+02:00"
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

- extra switch explanation
- ai placement

```
› c3 should be under the d+ and d- so we domt have to route vbus out under the differential pair.

  all other componenents are scattered over the board. group them toghether, align them and make it look nice
```

- manual fixes
- result
- closing

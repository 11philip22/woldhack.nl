---
date: "2026-09-17T00:00:00+02:00"
draft: true
title: "Developing for Spartan-6 with ISE in Docker"
---

I'm trying to get a Spartan-6 FPGA talking to a USB3300 USB PHY. I'm using a s602 board with a 6SLX9TQG144 FPGA from AliExpress and a USB3300 ULPI board from Waveshare.

I'm on Windows, where running ISE in a VM requires me to disable WSL. So I run ISE 14.7 in Docker and build from PowerShell, keeping the old tools contained and WSL available.

<!--more-->

{{< figure src="spartan6-board.webp" alt="Spartan-6 board connected to a USB3300 ULPI module and JTAG programmer" caption="S602 board on the right, USB3300 module on the left, and JTAG programmer at the top." width="480" >}}

## Setup

First install Docker with Linux container support. I use [Docked-ISE-147](https://github.com/I-A-S/Docked-ISE-147), which packages ISE for command-line use.

```powershell
git clone https://github.com/I-A-S/Docked-ISE-147.git
cd Docked-ISE-147
```

Download the ISE 14.7 full Linux installer and put `Xilinx_ISE_DS_Lin_14.7_1015_1.tar` in the repository's `Resources` directory. Now build the image:

```powershell
docker build -t docked-ise-147 .
```

## Build

The `ulpi_identity_test` design reads four registers over ULPI and checks for vendor ID `0x0424` and product ID `0x0004`. A matching identity leaves the green LED on; a mismatch or handshake timeout makes it blink quickly.

Back in the FPGA project, I keep `Xilinx.lic` in the project root and the Verilog and matching UCF file in `src`. The UCF contains the pin assignments and timing constraints.

My [build.ps1](https://github.com/11philip22/fpga-skills/blob/master/spartan6-build-flash/assets/build.ps1) template uses the filename `ulpi_clock_test.v`. It copies the sources into `build`, then runs ISE there. This is the Docker command from that script; `$buildDir` and `$license` are absolute paths:

```powershell
& docker run --rm `
    --mount "type=bind,source=$buildDir,target=/workspace" `
    --workdir /workspace `
    --mount "type=bind,source=$license,target=/opt/Xilinx/Xilinx.lic,readonly" `
    --env XILINXD_LICENSE_FILE=/opt/Xilinx/Xilinx.lic `
    docked-ise-147 `
    xflow -p xc6slx9-tqg144-2 `
    -synth xst_verilog.opt `
    -implement balanced.opt `
    -config bitgen.opt `
    ulpi_clock_test.v
```

`xflow` runs synthesis, implementation and bitstream generation. The result is `build/ulpi_clock_test.bit`. Since `build` is mounted from the host, the reports and bitstream remain after Docker removes the container.

Please adjust the part, source filename and UCF for your board. The script checks the exit code and that the bitstream exists. I also check the timing report before programming.

## Programming and debugging

OpenFPGALoader runs on the host. The script is configured for a Digilent HS3; adjust the cable option for your programmer. For a temporary test, load the bitstream into SRAM:

```powershell
openFPGALoader -c digilent_hs3 .\build\ulpi_clock_test.bit
```

This is lost when power is removed. For a design that survives a power cycle, my [flash.ps1](https://github.com/11philip22/fpga-skills/blob/master/spartan6-build-flash/assets/flash.ps1) uses `-f` and downloads the package-specific SPI-over-JTAG bridge. On Windows, the script adds Git for Windows' `usr/bin` directory to `PATH` so OpenFPGALoader can find its runtime DLLs. OpenFPGALoader documents both loading modes [here](https://trabucayre.github.io/openFPGALoader/guide/first-steps.html).

For hardware debugging I use LiteX/LiteScope over JTAGBone to capture internal signals as VCD or CSV. I keep those debug builds separate and load them into SRAM.

The build, flash and debugging workflows are collected in my [FPGA skills](https://github.com/11philip22/fpga-skills).

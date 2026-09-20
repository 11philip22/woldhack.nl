---
date: "2026-09-17T00:00:00+02:00"
draft: true
title: "Developing for Spartan-6 with ISE in Docker"
---

I'm trying to get a Spartan-6 FPGA talking to a USB3300 USB PHY. The hardware is a s602 board with a 6SLX9TQG144 FPGA from AliExpress and a USB3300 ULPI board from Waveshare.

On my Windows setup, running ISE in a VM means disabling WSL. So I run ISE 14.7 in Docker and build from PowerShell, keeping the old crap contained.

<!--more-->

{{< figure src="spartan6-board.webp" alt="Spartan-6 board connected to a USB3300 ULPI module and JTAG programmer" caption="S602 board on the right, USB3300 module on the left, and JTAG programmer at the top." width="480" >}}

## FPGAs

An FPGA (Field-Programmable Gate Array) is a chip with configurable logic, memory and connections. Verilog describes a digital circuit built from those resources. Different parts of the circuit can operate in parallel. This is one of the cool advantages over a CPU: each task can have its own dedicated hardware.

A register stores bits of data using flip-flops, which each hold one bit. Together they can hold a counter value or the current state of the circuit. The logic calculates new values from the inputs and stored values. A clock provides a repeating signal, and the registers accept their new values on a clock edge. In this design that is the rising edge, when the clock changes from 0 to 1.

The build tools produce a bitstream containing the configuration for the logic and its connections. Loading that file makes the FPGA implement the circuit.

### Hardware connections

The FPGA contains the test logic, while the [USB3300](https://ww1.microchip.com/downloads/en/DeviceDoc/00001783C.pdf) handles the electrical side of USB. This is the PHY, or physical layer. It provides the USB transmitter and receiver that the FPGA's general-purpose pins do not. ULPI is the digital connection between them, carrying bytes and control signals. The PHY also supplies its 60 MHz clock to the FPGA.

Programming uses a separate connection. The [Digilent HS3](https://digilent.com/shop/jtag-hs3-programming-cable/) is a USB-to-JTAG programmer. JTAG provides access to the FPGA for loading a bitstream and, with the debug hardware described below, reading internal signals.

{{< figure src="fpga-connections.svg" link="fpga-connections.svg" alt="The PC connects through USB to the Digilent HS3, then through JTAG to the FPGA. The USB host connects to the USB3300 PHY, which connects to the FPGA over ULPI and supplies its 60 MHz clock." caption="The USB test and JTAG programming connections. The USB host can be the same PC used for programming." >}}

## Setup

ISE is Xilinx's software for building FPGA designs. Spartan-6 uses this older toolchain because [Vivado supports devices from the 7 series onward](https://www.amd.com/en/products/software/adaptive-socs-and-fpgas/licensing-faq.html).

[Docked-ISE-147](https://github.com/I-A-S/Docked-ISE-147) packages ISE for command-line use in a Linux container.

```powershell
git clone https://github.com/I-A-S/Docked-ISE-147.git
cd Docked-ISE-147
```

The image build needs the full Linux installer, `Xilinx_ISE_DS_Lin_14.7_1015_1.tar`, in the repository's `Resources` directory:

```powershell
docker build -t docked-ise-147 .
```

## Build

The test design checks that the FPGA can talk to the USB3300 by reading its vendor and product IDs from four ULPI registers. These are storage locations inside the PHY, accessed by address over ULPI. If the IDs match `0x0424` and `0x0004`, the green LED stays on. If either value is wrong or the handshake times out, the LED blinks quickly.

`Xilinx.lic` and the build script are in the project root. The Verilog and matching UCF file are in `src`. The UCF maps signals in the design to physical FPGA pins and sets timing constraints, including the clock periods and the time allowed for signals going to and from the PHY.

[build.ps1](https://github.com/11philip22/fpga-skills/blob/master/spartan6-build-flash/assets/build.ps1) copies the source files to `build` and runs ISE inside Docker:

```powershell
$ErrorActionPreference = 'Stop'

$resolvedRoot = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$buildDir = Join-Path $resolvedRoot 'build'
New-Item -ItemType Directory -Path $buildDir -Force | Out-Null
$resolvedBuild = (Resolve-Path -LiteralPath $buildDir).Path
if ((Split-Path -Parent $resolvedBuild) -ne $resolvedRoot -or (Split-Path -Leaf $resolvedBuild) -ne 'build') {
    throw "Refusing to clean unexpected build path: $resolvedBuild"
}
Get-ChildItem -LiteralPath $resolvedBuild -Force | Where-Object Name -notin @('litescope', 'passive') | Remove-Item -Recurse -Force
Copy-Item -LiteralPath (Join-Path $resolvedRoot 'src\ulpi_clock_test.v'), (Join-Path $resolvedRoot 'src\ulpi_clock_test.ucf') -Destination $buildDir -Force

$license = (Resolve-Path -LiteralPath (Join-Path $resolvedRoot 'Xilinx.lic') -ErrorAction Stop).Path
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
if ($LASTEXITCODE -ne 0) {
    throw "ISE build failed with exit code $LASTEXITCODE"
}

$bitstream = Join-Path $buildDir 'ulpi_clock_test.bit'
if (-not (Test-Path -LiteralPath $bitstream -PathType Leaf)) {
    throw 'ISE finished without creating ulpi_clock_test.bit'
}

Write-Host "Built $bitstream"
```

```powershell
.\build.ps1
```

`xflow` runs synthesis, which turns the Verilog into logic and storage resources, followed by implementation, which places those resources on the FPGA and routes the connections between them. Bitstream generation writes the resulting configuration to `build/ulpi_clock_test.bit`. Since `build` is mounted from the host, the reports and bitstream remain after Docker removes the container.

Signals take time to travel through the logic and connections. A value must reach its destination before the clock edge that stores it and remain stable briefly afterwards. The timing report checks these requirements against the constraints. The clock constraints specify about 16.667 ns between rising edges for the 60 MHz ULPI clock, and 20 ns for the 50 MHz board clock used in the debug build.

Before programming, I check for timing violations and paths missing constraints. A successful build can still produce a bitstream with timing problems.

## Programming

OpenFPGALoader runs on the PC and sends the bitstream through the HS3 to the FPGA's JTAG port. For a temporary test, it loads the configuration into the FPGA's SRAM:

```powershell
openFPGALoader -c digilent_hs3 .\build\ulpi_clock_test.bit
```

The SRAM configuration is lost when power is removed. [flash.ps1](https://github.com/11philip22/fpga-skills/blob/master/spartan6-build-flash/assets/flash.ps1) writes the bitstream to the board's SPI flash instead. The FPGA loads that configuration when it powers on.

The flash is connected to the FPGA, so OpenFPGALoader first loads a small [SPI-over-JTAG bridge](https://github.com/trabucayre/openFPGALoader/blob/master/src/xilinx.cpp) into the FPGA. This temporary design passes commands from JTAG to the flash chip. The script downloads the bridge for this FPGA and sits in the project root alongside `build.ps1`:

```powershell
$ErrorActionPreference = 'Stop'

$root = (Resolve-Path -LiteralPath $PSScriptRoot).Path
$bitstream = (Resolve-Path -LiteralPath (Join-Path $root 'build\ulpi_clock_test.bit') -ErrorAction Stop).Path
$bridgeDir = Join-Path $root '.tools\openFPGALoader'
$bridge = Join-Path $bridgeDir 'spiOverJtag_xc6slx9tqg144.bit.gz'
if (-not (Test-Path -LiteralPath $bridge -PathType Leaf)) {
    New-Item -ItemType Directory -Path $bridgeDir -Force | Out-Null
    $download = "$bridge.download"
    Write-Host 'Downloading Spartan-6 SPI-over-JTAG bridge...'
    Invoke-WebRequest -UseBasicParsing -Uri 'https://raw.githubusercontent.com/trabucayre/openFPGALoader/v1.1.1/spiOverJtag/spiOverJtag_xc6slx9tqg144.bit.gz' -OutFile $download
    Move-Item -LiteralPath $download -Destination $bridge -Force
}

$bridge = (Resolve-Path -LiteralPath $bridge -ErrorAction Stop).Path
$cygpath = (Resolve-Path -LiteralPath 'C:\Program Files\Git\usr\bin\cygpath.exe' -ErrorAction Stop).Path
$loader = (Get-Command openFPGALoader.exe -ErrorAction Stop).Source

$env:Path = "$(Split-Path -Parent $cygpath);$env:Path"
$env:OPENFPGALOADER_SOJ_DIR = & $cygpath -u (Split-Path -Parent $bridge)

& $loader -c digilent_hs3 --fpga-part xc6slx9tqg144 -f $bitstream
if ($LASTEXITCODE -ne 0) {
    throw "Flash failed with exit code $LASTEXITCODE"
}

Write-Host "Flashed $bitstream"
```

```powershell
.\flash.ps1
```

On Windows, the script adds Git for Windows' `usr/bin` directory to `PATH` so OpenFPGALoader can find its runtime DLLs. OpenFPGALoader documents both loading modes [here](https://trabucayre.github.io/openFPGALoader/guide/first-steps.html).

## Debugging

A blinking LED can give you a pass or fail result, but when you want to see what's happening inside the FPGA, [LiteScope](https://github.com/enjoy-digital/litescope) gives you a logic analyzer built into the design. It records selected signals into block RAM, the FPGA's internal memory, for later download as VCD or CSV. A waveform displays how those values changed over time.

The examples below use a separate USB attach/reset test. The Python generator leaves `HOST_ATTACH` at its default of 0, so this design attaches to a USB host and watches for a reset from it.

### Migen and LiteX

The debug hardware is put together with [Migen](https://m-labs.hk/migen/manual/fhdl.html) and [LiteX](https://github.com/enjoy-digital/litex). Migen is a Python library for describing hardware and generating Verilog. LiteX builds on that with buses, control registers and reusable hardware blocks. The Python code runs on the PC to generate the design that ISE builds, including connections to the existing Verilog.

[SoCMini](https://github.com/enjoy-digital/litex/blob/2024.12/litex/soc/integration/soc_core.py) provides a minimal LiteX system around the debug hardware. Here it supplies the bus and register access without a CPU or firmware. [JTAGBone](https://github.com/enjoy-digital/litex/blob/2024.12/litex/soc/integration/soc.py) bridges JTAG to Wishbone, the internal bus used in this setup. That gives the PC access to the analyzer through the same JTAG programmer.

### Clock domains

The design uses two clocks. The parts of the circuit that update from the same clock form a clock domain:

| Domain | Clock | What uses it |
| --- | --- | --- |
| `sys` | 50 MHz from the board | LiteX control registers and bus access |
| `ulpi` | 60 MHz from the USB3300 | Verilog test core and LiteScope sampling |

The PC writes to a control register on the `sys` side, but the test reads its start input on the `ulpi` side. These clocks run independently. A value changing on one clock can arrive just as a flip-flop on the other clock is sampling it. That flip-flop may take too long to settle to a valid 0 or 1. This is called metastability and can cause the receiving logic to behave unpredictably.

The generator marks connections between these clocks as [false paths](https://docs.amd.com/r/en-US/ug949-vivado-design-methodology/Clock-Domain-Crossing). This tells ISE to skip the usual timing checks between them, since their edges have no fixed relationship. The hardware still has to handle the crossing. The start bit is an example of this.

### Starting the test

The debug build waits for the PC to set a start bit. This gives the PC time to prepare the analyzer before the test begins.

`CSRStorage(1, reset=0)` creates a one-bit control register, initially 0, which the PC can write through JTAGBone. `Signal` represents a value in the generated hardware, one bit wide by default. The connection between the two clock domains is made with `MultiReg`:

```python
capture_start = Signal(name="attach_reset_capture_start")

self.attach_reset_start = CSRStorage(1, reset=0)
self.add_csr("attach_reset_start")
self.specials += MultiReg(self.attach_reset_start.storage, capture_start, "ulpi")
```

[MultiReg](https://github.com/m-labs/migen/blob/master/migen/genlib/cdc.py) puts two flip-flops between the control register and `capture_start`. Both use the `ulpi` clock. The first samples the incoming bit, and the second takes the first one's value on the next clock edge. This gives the first flip-flop time to settle and reduces the chance of metastability reaching the test logic.

The control register keeps its value until the PC writes it again. That gives the receiving clock time to pick it up. This works for a start bit that stays at 1; a short pulse could be missed between clock edges.

The synchronized value, `capture_start`, connects to the Verilog core's `test_start` input. The standalone test has this input fixed at 1. In the debug build it starts at 0 and waits for the PC.

Inside the core, `state` records what the test is doing. It begins in `ST_STARTUP`. The startup part of the Verilog looks like this, with the other states and bus assignments omitted:

```verilog
always @(posedge ulpi_clk) begin
    case (state)
        ST_STARTUP: begin
            if (~&startup_count) begin
                startup_count <= startup_count + 1'b1;
            end else if (test_start && !ulpi_dir) begin
                state <= ST_IDLE;
            end
        end
    endcase
end
```

`posedge ulpi_clk` means this logic updates on each rising clock edge. The `<=` assignments schedule the new register values. Other logic using the same edge still reads the old values.

`~&startup_count` is true until all bits in the counter are 1. Each clock adds `1'b1`, a one-bit binary value of 1, until the counter is full. This provides the startup delay. After that, `test_start` must be 1 and `ulpi_dir` must be 0, meaning the bus is free, before the core moves to `ST_IDLE`.

### Debug signals

The LED shows whether the test passed or failed. To see where it got stuck, the analyzer needs the actual state and error code. The Verilog core makes these available through two output ports:

```verilog
reg [3:0] state = ST_STARTUP;
reg [3:0] error_code = 4'd0;

assign debug_state = state;
assign debug_error_code = error_code;
```

`[3:0]` declares four bits, numbered 3 down to 0. `4'd0` is a four-bit decimal value of 0. The `assign` statements connect these stored values to the output ports, so the analyzer can see them.

On the Python side, `Instance` adds the Verilog core to the generated design and connects its ports. `Signal(4)` represents a four-bit value. The `i_` prefixes are inputs to the core and the `o_` prefixes are outputs. Only the clock, start input and two debug outputs are shown here:

```python
debug_state = Signal(4, name="debug_state")
debug_error_code = Signal(4, name="debug_error_code")

self.specials += Instance(
    "ulpi_attach_reset_test_core",
    i_ulpi_clk=self.crg.ulpi_clk,
    i_test_start=capture_start,
    o_debug_state=debug_state,
    o_debug_error_code=debug_error_code,
)
```

### Capturing signals

LiteScope records `capture_start`, `debug_state` and `debug_error_code` together. Each sample is a snapshot of all three values at one clock edge. This makes it possible to see when the start bit reached the core, which state followed and whether an error occurred:

```python
self.submodules.analyzer = LiteScopeAnalyzer(
    [capture_start, debug_state, debug_error_code],
    depth=1024,
    samplerate=60_000_000,
    clock_domain="ulpi",
    register=True,
    csr_csv=str(BUILD_DIR / "analyzer.csv"),
)
self.add_csr("analyzer")
```

`clock_domain="ulpi"` makes the analyzer sample on the test core's 60 MHz clock. With `depth=1024`, it can hold 1024 samples, covering about 17 microseconds. `samplerate` supplies the frequency used to label time in the exported waveform.

`register=True` adds an input register to each recorded signal. This delays all three signals by one clock, keeping their timing relative to each other intact.

Arming the analyzer makes it wait for a trigger, a condition that identifies the event to capture. For this example, a useful trigger is `capture_start` becoming 1. The capture can include samples from before and after that event.

The waveform below illustrates what happens when the startup delay has finished and the bus is free. At the edge where `capture_start` changes to 1, the core still reads its old value of 0. On the next edge it reads 1 and moves from `ST_STARTUP` to `ST_IDLE`.

{{< figure src="capture-example.svg" link="capture-example.svg" alt="Illustrative waveform: capture_start changes from 0 to 1 after a ULPI clock edge. On the next edge, debug_state changes from ST_STARTUP, value 0, to ST_IDLE, value 1. On the following edge it changes to ST_COMMAND, value 2." caption="Illustrative waveform of the core signals, before the analyzer's input registers. Each column is one 60 MHz clock cycle." >}}

The captured data also has to cross between clocks on its way back to the PC. LiteScope uses an [asynchronous FIFO](https://github.com/enjoy-digital/litescope/blob/2024.12/litescope/core.py) for this, a queue that can be written and read using different clocks. Samples enter it from `ulpi` and leave through `sys`. JTAG carries the stored capture to the PC, so its speed affects download time while the sampling runs at 60 MHz.

On Windows, OpenOCD talks to the Digilent HS3. A software bridge connects OpenOCD to the LiteX server, giving the PC capture tools access to the analyzer. The generated files go under `build/attach-reset-litescope`, and the debug bitstream goes into SRAM.

### Finding where the test stops

The analyzer example above only shows three signals. The full generator also records the ULPI data and control signals, the current test phase and several status flags. These help explain why the test has stopped making progress.

#### The test stays in startup

If `debug_state` stays at `ST_STARTUP` (0), the useful signals are `capture_start` and `ulpi_dir`. The startup counter also has to finish first. It is 19 bits wide, so that takes about 8.7 ms at 60 MHz, much longer than one capture.

After that delay, a capture with `capture_start=1` and `ulpi_dir=1` shows that the start bit reached the test, but the PHY still owns the bus. The core is waiting for `ulpi_dir` to become 0. Once both conditions are met, the next clock should move it to `ST_IDLE` (1).

If `capture_start` stays at 0, the start command is the part to check. Reading back the `attach_reset_start` control register shows whether the PC's write reached LiteX. A value of 1 there confirms the write on the `sys` side; the captured `capture_start` shows what reached the `ulpi` side.

A trigger waiting for the start bit will also keep waiting if that bit never arrives. An immediate capture is useful in that case. If no samples arrive at all, the 60 MHz clock is one of the things to check: JTAG access can still work through `sys` while the test and analyzer have no clock.

#### A register command times out

For a fast-blinking LED, `debug_error_code` gives a more useful starting point. An error code of 1 comes from the timeout branch in `ST_WAIT_COMMAND` (3):

```verilog
else if (&timeout_count) begin
    data_oe <= 1'b0;
    error_code <= 4'd1;
    state <= ST_FAIL;
end
```

In this state, the core has put a command on `ulpi_data` and is waiting for the PHY to acknowledge it by raising `ulpi_nxt`. `&timeout_count` becomes true when every bit in the timeout counter is 1.

That counter is 24 bits wide, giving a wait of roughly 280 ms. A capture triggered at the start of the test would finish long before the timeout. A useful trigger here is `debug_error_code == 1`, with part of the buffer reserved for samples before the trigger.

The signals to compare are `debug_state`, `debug_error_code`, `ulpi_data`, `ulpi_nxt` and `ulpi_dir`. A capture showing `ST_WAIT_COMMAND`, with `ulpi_dir=0` and `ulpi_nxt=0`, followed by `ST_FAIL` (11) and error 1 means the FPGA timed out waiting for the acknowledgement. The ULPI pin assignments and timing would be the next things to check.

If `ulpi_dir` becomes 1 instead, this branch moves to `ST_ABORT` (12) and retries once the PHY releases the bus. The state trace makes that different path visible.

#### A status change arrives earlier than expected

There is another useful example in the core. The PHY can report the USB idle state while the FPGA is still configuring its registers. If the test only looks for that report after configuration, it can end up waiting for an event that already happened.

The useful signals here are `debug_state`, `debug_phase`, `debug_line_state` and `debug_session_valid`. `state` tracks the register transactions, while `phase` tracks the overall test. For example, `ST_MONITOR` (9) means the core is watching the PHY, and `PH_WAIT_J` (4) means it is waiting for the bus's idle state after attachment, called J. In this test J is reported as `debug_line_state=1`.

A trigger on `debug_line_state == 1`, with samples before the trigger, shows which state the core was in when J arrived. If it was still configuring registers, the report came before the test was ready to wait for it.

The core keeps the latest reported line state in a register, so that information is still available afterwards. It checks this when configuration finishes and again in `ST_MONITOR`:

```verilog
if (phase == PH_WAIT_J && session_valid && line_state == 2'b01) begin
    saw_j <= 1'b1;
    phase <= PH_WAIT_SE0;
end
```

This lets the test continue even if there is no second report. `debug_saw_j=1` and `debug_phase=PH_WAIT_SE0` (5) then show that it has seen the idle state and is waiting for the host's reset. For that part of the test, a trigger on `debug_phase == 6` captures the start of reset confirmation. The existing `debug_reset_count` signal shows progress towards the core's 150-count threshold. That takes about 2.5 microseconds when no new status reports pause the counting.

The core only checks `test_start` during startup. Writing 0 and then 1 does not restart a completed or failed test, so another run of this design needs the bitstream loaded again.

The build, flash and debugging workflows are collected in my [FPGA skills](https://github.com/11philip22/fpga-skills).

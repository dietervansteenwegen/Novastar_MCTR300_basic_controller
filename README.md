# Novastar MCTRL300 basic controller

Simple, basic control of brightness and test patterns/mode for the [Novastar MCTRL300](https://www.novastar.tech/products/controller/mctrl300/).

Builds/installers are not available but if anyone has use for them, I’d happily create one for you (Windows or Linux only). If so, create an [issue](https://github.com/dietervansteenwegen/Novastar_MCTRL300_basic_controller/issues/new)…

## Why?

I repair several types of LED panels, among which are Desay 6mm and UPAD 2.6mm.

The Novastar software is written for Windows and overkill for simple control of patterns and brightness (which is all I need during testing and repair). This PyQt based solution works faster and runs on my Linux machines as well as Windows.

## Novastar hardware: the MCTRL300 LED controller

The [Novastar MCTRL300](https://www.novastar.tech/products/controller/mctrl300/) controller that can be used to drive these panels has a Windows software that allows you configure your whole led screen as well as display test patterns (full r/g/b, moving lines, white, ...). During repair and testing this last function is something I use all the time. Thus, the software with all its functions is overkill and rather cumbersome. I decided to write my own (simple) interface to call up test patterns quickly. I've also added shortcuts to limit the amount of actions to call up patterns.

The controller has a [Silicon Labs CP2102](https://www.silabs.com/interface/usb-bridges/classic/device.cp2102) USB to UART bridge. Opening the housing reveals a rather pretty board that seems to be made so that it can be used as a PCI extention card in a computer instead of a standalone controller as well. Soldering a couple of wires to the QFN28 package and connecting a logic analyzer allows to log the commands that are sent to the controller. After getting these commands, only a bit of Python remains to be written.

## Example

![Screenshot of beta version](/assets/images/screenshot.png)

## Usage

1. Select the Serial port where the controller is connected
1. Open the port
1. Select to which output the screen is connected (Output 1 or 2)
1. Use the following shortcuts to call up patterns

## Shortcuts

|Shortcut|Function|
|---------|-----------|
|Left|Previous pattern|
|Right|Next pattern|
|Up|Next brightness in list (brighter)|
|Down|Previous brightness in list (dimmer)|
|R|Red|
|G|Green|
|B|Blue|
|C|Cycle through colors|
|S|"Slash" pattern with moving diagonal lines|
|L|"Live" (from video input)|

## Thanks / Acknowledgements

I found a couple of useful documents about the protocol Novastar uses for a couple of other of their controllers on the __Bitfocus Companion__ module Novastar controller [repository](https://github.com/bitfocus/companion-module-novastar-controller), mostly while reading through the issues.

## Links

See [this project page](<https://boxfish.be/posts/20230213-novastar-mctrl300-basic-control-software/.org>) for information on this project.

Version numbers according to [Semantic Versioning 2.0.0](https://semver.org/).

![GitHub last commit (master)](https://img.shields.io/github/last-commit/dietervansteenwegen/Novastar_MCTRL300_basic_controller/master?style=plastic)
![GitHub commit activity (master)](https://img.shields.io/github/commit-activity/w/dietervansteenwegen/Novastar_MCTRL300_basic_controller/develop?style=plastic)
![GitHub](https://img.shields.io/github/license/dietervansteenwegen/Novastar_MCTRL300_basic_controller?style=plastic)

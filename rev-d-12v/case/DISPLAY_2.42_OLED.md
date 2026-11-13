# Display record: 2.42" OLED, SSD1309, 128 x 64, I2C

Chosen by the owner on 13 Nov 2026: AliExpress item 1005007345209025 (TENSTAR ROBOT store), option "I2C interface Blue".
https://www.aliexpress.com/item/1005007345209025.html

**"Blue" is the colour of the lit pixels. The I2C version is the black circuit board marked "2.42OLED-IIC VER:1.0".**
The listing's blue circuit board is the 7-pin SPI version, which is a different size.

All figures below are read from the seller's dimension drawing in the listing (750 px wide image, saved locally in
`lada-panas/brineomatic/research/display-2.42-oled/`, not in this repository because it is the seller's image).
**Nothing has been measured on a real module. Measure the module when it arrives before printing the cover.**

## I2C board (black), the one ordered

| Dimension | mm | How obtained |
|---|---|---|
| Circuit board width x height | 70.08 x 48.04 | printed in the drawing (last digits hard to read) |
| Glass width x height | 62.64 x 39.18 | printed in the drawing |
| Visible area width x height | 57.80 x 29.76 | printed in the drawing |
| Active (pixel) area width x height | 55.40 x 27.78 | printed in the drawing |
| Total thickness, glass face to board back | 5.29 | printed in the drawing |
| Circuit board thickness | 1.00 | printed in the drawing |
| Flex cable fold at the bottom edge, width | 12.64 | printed in the drawing |
| Dimension "3.22" at the lower right mounting hole | 3.22 | printed; what it refers to is not clear (hole diameter or edge distance) |
| **Mounting hole spacing** | **about 65.5 x 43.3** | **not printed.** Scaled from the drawing (16.3 px per mm), tolerance about +-0.4 mm |
| **Mounting hole diameter** | **about 3.2** | **not printed.** Scaled from the drawing, same tolerance |
| Hole centre to board edge | about 2.3 (sides), 2.4 (top/bottom) | scaled |
| Glass position on the board | centred left-right; about 4.3 mm from the top edge, 4.5 mm from the bottom edge | scaled |
| Active area position in the glass | centred left-right; about 2.6 mm from the glass top, 8.9 mm from the glass bottom | scaled |
| Header | 4 pins, 2.54 mm pitch, top centre of the board: GND, VDD, SCL, SDA (left to right seen from the front) | drawing and photo |

Supply: the seller's schematic shows a 3.3 V regulator and a 12 V boost converter on the module and says 3.3 V to 5 V input. I2C address 0x78 / 0x7A as printed on the board (0x3C / 0x3D in 7-bit form).

## SPI board (blue), for comparison only

Circuit board 71.00 x 43.50, mounting holes 67.00 x 39.50 with diameter 2.50, active area 55.01 x 27.49, thickness 3.80 (6.0 max). All printed in the drawing.

## Consequence for the case

Because the I2C board's hole spacing is not printed, the cover does not use the display's mounting holes.
The glass sits in a pocket in the cover and a printed clamp frame, screwed to four bosses outside the display board, holds it.

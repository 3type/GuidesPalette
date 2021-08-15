# Guides Palette

Guides Palette is a plugin for the [Glyphs font editor](http://glyphsapp.com/).

## Usage

Guides Palette can list all the *global* guides with names. You can toggle the display and change the name of them.

Guides with same names will make the plugin unhappy (the behavior will be unpredictable), so please keep the names unique.

### Custom parameters

Guides Palette uses the font custom parameter `Guides Palette Config` to control the appearance of the palette. It can be set with the following format:

    { sortBy = <s>; showAngle = <a>; showCoordinates = <c>; }

where

- `<s>` can be
  - `None`: do not sort (default)
  - `name`: sort by name
  - `x`, `y`: sort by x or y coordinate
  - `-x` or `-y`: sort by x or y coordinate (inverse)
- `<a>` and `<c>` can be
  - `1`: show (default)
  - `0`: not show

Note:

- Each entry can be omitted
- Each entry should end with a semicolon `;` (even for the last one)
- Glyphs will add quotation marks for the values (e.g. `"-x"`), but it's not mandatary

Example:

    { sortBy = -y; showAngle = 0; }

### Remarks

Internally, Guides Palette will add tags like `guide_NAME` for each glyph with guide `NAME`. It's not recommended to edit these tags manually or with plugins like [GutenTag](https://github.com/florianpircher/GutenTag).

## License

Copyright &copy; 2021 3type

Made possible with the [GlyphsSDK](https://github.com/schriftgestalt/GlyphsSDK) by Georg Seifert ([@schriftgestalt](https://github.com/schriftgestalt)) and Rainer Erich Scheichelbauer ([@mekkablue](https://github.com/mekkablue)).

Licensed under the Apache License, Version 2.0 (the "License");
you may not use this file except in compliance with the License.
You may obtain a copy of the License at

<http://www.apache.org/licenses/LICENSE-2.0>

Unless required by applicable law or agreed to in writing, software
distributed under the License is distributed on an "AS IS" BASIS,
WITHOUT WARRANTIES OR CONDITIONS OF ANY KIND, either express or implied.
See the License for the specific language governing permissions and
limitations under the License.

# Text Pastry #

_Text Pastry_ is a free plugin for [Sublime Text](http://www.sublimetext.com/), dedicated to reduce repetetive work by extending the power of [multiple selections](https://www.sublimetext.com/docs/selection).

## How can I get started?
If you're familiar with [multiple selections](https://www.sublimetext.com/docs/selection), it's pretty straight forward. Place multiple cursors by using CMD+Click or Ctrl+Click, open the [Command Palette](http://docs.sublimetext.info/en/latest/reference/command_palette.html) and select _Text Pastry From 1 to X_. That's it! We've just pasted incrementing numbers.

Check out the [wiki](https://github.com/duydao/Text-Pastry/wiki/Examples) for examples!

## Features include: ##

- Incremental numbers/sequences _(1, 2, 3 or 100, 80, 60)_
- Repeatable number ranges _(1, 2, 3, 4, 1, 2, 3, 4 or 2, 1, 2, 1, 2, 1)_
- Generate UUIDS _(ba18f7fc-c387-46da-9544-ed32e49ce6f8 or D306E86C-918F-4551-95A9-CB9865A4DD2F)_
- Extendable list of presets _(Monday, Tuesday, Wednesday or alpha, beta, gamma)_
- Extendable list of commands
- Create and modify selections
- Improved paste _(paste the first three lines of the clipboard data to the three selected locations)_
- Generate date and number ranges
- Convert to upper/lower case
- Duplicate values for pasting _(1, 1, 2, 2, 3, 3, 4, 4)_ or _(a, a, a, b, b, b, c, c, c)_

## What's new ##
- 1.6.1: Fix "Pipe into selection" bug (#78)
- 1.6.0: [New features!](https://github.com/duydao/Text-Pastry/blob/master/RELEASENOTES.md) Support for decimal and hexadecimal ranges - Thanks to [@SmartManoj](https://github.com/SmartManoj), [@miusuncle](https://github.com/miusuncle), [@sagunkho](https://github.com/sagunkho), [@slhck](https://github.com/slhck) and [@charleskawczynski](https://github.com/charleskawczynski)
- 1.5.1: Bugfix release for Find by regex [#56](https://github.com/duydao/Text-Pastry/issues/56) - Thanks [@timLinscott](https://github.com/timLinscott)
- 1.5.0: [New features!](https://github.com/duydao/Text-Pastry/blob/master/RELEASENOTES.md)
- 1.4.10: Scroll into view on search / after find [#33](https://github.com/duydao/Text-Pastry/issues/33) - Thanks again [@miusuncle](https://github.com/miusuncle)
- 1.4.9: Bugfix release for uuid x10 [#31](https://github.com/duydao/Text-Pastry/issues/31) - Thanks [@miusuncle](https://github.com/miusuncle)
- 1.4.8: Added support for repeating increments [#29](https://github.com/duydao/Text-Pastry/issues/29) - Thanks [@mkruselj](https://github.com/mkruselj)
- 1.4.7: Fixed range command (stop condition was ignored)
- 1.4.6: Bugfix release for paste by row - Thanks [@Nieralyte](https://github.com/Nieralyte)
- 1.4.5: Added the paste by row command (use ```pr``` or ```pbr``` in the command line) [#28](https://github.com/duydao/Text-Pastry/issues/28)
- 1.4.4: Bugfix for command ```\i``` [#27](https://github.com/duydao/Text-Pastry/issues/27) - Thanks [@kcko](https://github.com/Kcko)
- 1.4.3: New commands! Generate date ranges command, repeat argument (x-arg), and the [Auto Step](https://github.com/duydao/Text-Pastry/issues/20) command
- 1.4.2: Fix range / negative steps [#24](https://github.com/duydao/Text-Pastry/issues/24) - Thanks [@TheClams](https://github.com/TheClams)
- 1.4.1: Hotfix for [#23](https://github.com/duydao/Text-Pastry/issues/23) - Thanks [@dufferzafar](https://github.com/dufferzafar)
- 1.4.0: [New Features!](https://github.com/duydao/Text-Pastry/blob/master/RELEASENOTES.md#release-notes-140)

## Further information

If you would like to know more about how _Text Pastry_ can help you out, check out our [wiki](https://github.com/duydao/Text-Pastry/wiki).

## Todo ##
- formatters
- wrappers [#20](https://github.com/duydao/Text-Pastry/issues/20)
- smart case: determine case-sensitivity by search term

## Wishlist ##
- Webservice "Shell": use a custom (web-)service to process our selections
- yankring
- Templates: apply formatting right before items are pasted

## Done ##
- ~~Paste by progressing a list (Piping Bag)~~ (1.5.0)
- ~~increment in multiple files~~ (1.5.0)
- ~~loops~~ (1.5.0)
- ~~date ranges~~ (1.4.10)
- ~~incremental search: add search terms to selection by shortcut (work-in-progress)~~ (1.4.0, use ``add``)
- ~~Alphabetical sequence (upper/lower case)~~ (1.4.0)
- ~~Random numbers, strings and sequences~~ (use [Random Everything](https://sublime.wbond.net/packages/Random%20Everything) in combination with commands)
- ~~Command List Overlay~~
- ~~Command History~~
- ~~UUID generation~~
- ~~Settings for word manipulation~~
- ~~Paste as Block~~

## Great plugins that I love to use with Text Pastry ##

__in alphabetical order__

- autoselect - https://github.com/SublimeText/AutoSelect
- Case Conversion - https://github.com/jdc0589/CaseConversion
- Hasher - https://github.com/dangelov/hasher/
- Insert Date - https://github.com/FichteFoll/sublimetext-insertdate

## License ##

The MIT License (MIT)

Copyright (c) 2019 Duy Dao, https://github.com/duydao/Text-Pastry

Permission is hereby granted, free of charge, to any person obtaining a copy
of this software and associated documentation files (the "Software"), to deal
in the Software without restriction, including without limitation the rights
to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
copies of the Software, and to permit persons to whom the Software is
furnished to do so, subject to the following conditions:

The above copyright notice and this permission notice shall be included in
all copies or substantial portions of the Software.

THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
THE SOFTWARE.


## See Also ##

For further information, please take the time to look at following links:

* Sublime Text: http://www.sublimetext.com/
* Sublime Package Control: https://sublime.wbond.net/installation

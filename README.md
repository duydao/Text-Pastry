# Text Pastry #

_Text Pastry_ is a plugin for [Sublime Text](http://www.sublimetext.com/) that will give you the necessary tools to insert or paste a bunch of text, a range of numbers or generated UUIDs into your selected locations.

Ever wanted to paste incrementing numbers or five lines from your clipboard into five different locations at once? _Text Pastry_ can help you out!

## What's new ##
- 1.3.7: Bugfix release [#17](https://github.com/duydao/Text-Pastry/issues/17)
- 1.3.6: Bugfix release [#14](https://github.com/duydao/Text-Pastry/issues/14)
- 1.3.5: History navigation, command shortcuts - Thanks [@JAStanton](https://github.com/JAStanton)
- 1.3.4: Fixed for Sublime Text 3 - Thanks [@forcey](https://github.com/forcey)
- 1.3.3: New commands: \r(regexp) and \r regex
- 1.3.2: Bugfix release


## Release Notes 1.3.5 ##

- history can be accessed by up/down arrows in the _Text Pastry_ command line. [#13](https://github.com/duydao/Text-Pastry/issues/13)
- text insert will only be executed if we have a list of three or more words in it. we can use the ``words`` command to lift this restriction
- commands don't require a leading backslash anymore (but it will still work for backwards compatibility)
- commands are now defined in TextPastry.sublime-settings. Don't like our syntax? Setup your own!


## Changes in 1.3.5 ##

I always found it quiet annoying to use the backslash. with the change on text inserts, it's easier to differentiate between those cases. Examples:

<table>
<tr>
    <th>Old Syntax (still works)</th>
    <th>New Syntax (will do the same)</th>
</tr>
<tr>
    <td>\p</td>
    <td>p</td>
</tr>
<tr>
    <td>\p\n</td>
    <td>pn</td>
</tr>
<tr>
    <td>\i(100,50)</td>
    <td>100 50</td>
</tr>
<tr>
    <td>\uuid</td>
    <td>uuid</td>
</tr>
</table>


## Installation ##

Thanks for using the excelent [Package Control](http://wbond.net/sublime_packages/package_control) to install _Text Pastry_.

We can do a manuall installation by cloning this repository into our Packages folder. Sublime Text -> Preferences -> Browse Packages...

```git clone git@github.com:duydao/Text-Pastry.git```

## Usage ##

To use _Text Pastry_, we need to open a Document in [Sublime Text](http://www.sublimetext.com/) and use [Multiple Selection](http://www.sublimetext.com/docs/2/multiple_selection_with_the_keyboard.html) to mark the 
insert locations _(in this document also referred to as selections)_.

Please keep in mind that the selected text could be replaced when we run the _Text Pastry_ command. To avoid that, we can alway place the cursor between letters by using **CMD + Click** or even select a whole column by using **ALT + Click**

All we need to do now is to press **CMD + ALT + N** to open the _Text Pastry_ command line. The input panel will show up at the bottom of [Sublime Text](http://www.sublimetext.com/).

Now its time to run our first command. Let's enter `first second third` and hit enter to run the command. _Text Pastry_ will add `first` to our first selection, `second` to the next selection and so on.

_Text Pastry_ will only replace as many words as we type into the command line. So if we have more selections then words, the rest of our selection will remain intact.

## Key Bindings ##
The default key bindings are stored at _<packages>/Text Pastry/Default.sublime-keymap_. As always, you can use your [user keymap file](http://docs.sublimetext.info/en/latest/customization/key_bindings.html) to setup your own key bindings.

<table>
<tr>
    <th>Mac</th>
    <th>Linux / Windows</th>
    <th>Action</th>
</tr>
<tr>
    <td><kbd>CMD</kbd> + <kbd>ALT</kbd> + <kbd>T</kbd></td>
	<td><kbd>CTRL</kbd> + <kbd>ALT</kbd> + <kbd>T</kbd></td>
	<td>Show _Text Pastry_ Menu</td>
</tr>
<tr>
    <td><kbd>CMD</kbd> + <kbd>ALT</kbd> + <kbd>N</kbd></td>
    <td><kbd>CTRL</kbd> + <kbd>ALT</kbd> + <kbd>N</kbd></td>
	<td>Open _Text Pastry_ Command Line</td>
</tr>
<tr>
    <td><kbd>CMD</kbd> + <kbd>ALT</kbd> + <kbd>F</kbd></td>
    <td><kbd>CTRL</kbd> + <kbd>ALT</kbd> + <kbd>F</kbd></td>
    <td>Open _Text Pastry_ Command Line</td>
</tr>
</table>

**Note:** The commands from the _Text Pastry_ menu are also available through the Command Palette (<kbd>CTRL</kbd>/<kbd>CMD</kbd> + <kbd>SHIFT</kbd> + <kbd>P</kbd>)

## Command Reference ##

### Regular Text ###

Replaces the first selection with **Lorem**, the second selection with **Ipsum**, etc.:
	
	Lorem Ipsum Dolor

**Note:** Since version 1.3.5, there must be at least three words before this command will be executed. This change will make it possible to define commands without escape character.

We can still use a list of any size by prepeinding the words command:

    words Lorem Ipsum


### Number Sequence ###


Inserts a sequence, starting at 1:

	\i


Inserts a sequence, starting at 0:
	
	\i0


Inserts a sequence by defining start index and step size:
	
	\i(N,M)

* `N` the start index
* `M` the step size

Start index and step size may be negative.

**Note:** The Number Sequence command uses the syntax from [TextPad](http://www.textpad.com/).

Additionally, we can leave the brackets away if we want to:

	\i1000,100

even this will work:

    1000 100


### Clipboard ###

Inserts the content of the clipboard into our selections by [splitting the words](http://docs.python.org/library/stdtypes.html#str.split):

	\p
	
Same as above with a specified [string separator](http://docs.python.org/library/stdtypes.html#str.split):

	\p(sep)
* `sep` the string separator used to split the clipboad data.



**Note:** The Clipboard command uses syntax from [TextPad](http://www.textpad.com/).

### UUID ###

_Text Pastry_ will generate a [UUID](http://en.wikipedia.org/wiki/Universally_unique_identifier) for each selection we have made:

	\uuid

This command will generate a _random UUID_ by using pythons [uuid.uuid4() method](http://docs.python.org/2/library/uuid.html#uuid.uuid4):
	
	dbf8326e-5243-406e-abd9-bd0425d3e842

We can use the following command to generate a _random UUID_ in UPPERCASE:

	\UUID

### Regular Expression as separators ###

We're able to define regex separators for the data that we are pasting, which should give us some new possibilities.

We can [split the clipboard data by regex](http://docs.python.org/2/library/re.html#re.split), and paste the resulting items into the selected locations:

	\r(regex)

or
	
	\r regex

* `regex` the [regular expression](http://docs.python.org/3/library/re.html#regular-expression-syntax) used to split the clipboard data.

**Note:** If you managed to get [python-pcre](https://github.com/awahlig/python-pcre) up and running, the library will be preferred over the default python [re](http://docs.python.org/3/library/re.html) library.

### Insert Nums ###

_Text Pastry_ has a build in support for the [Insert Nums](https://github.com/jbrooksuk/InsertNums/) syntax by providing three numbers separated by one space:

	N M P

* `N`: the start index.
* `M` represents the step size which will be added to the index for each selection.
* `P` must be > 0 and will be used to pad the index with leading zeroes.

Note: 

## Examples ##

Check out the [wiki](https://github.com/duydao/Text-Pastry/wiki/Examples) for examples!

## Todo ##

- Alphabetical sequence (upper/lower case)
- Random numbers, strings and sequences
- ~~Command List Overlay~~
- ~~Command History~~
- ~~UUID generation~~
- ~~Settings for word manipulation~~
- ~~Paste as Block~~

## License ##

The MIT License (MIT)

Copyright (c) 2014 Duy Dao, https://github.com/duydao/Text-Pastry

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

* Sublime Text 3: http://www.sublimetext.com/3/
* Sublime Package Control: https://sublime.wbond.net/installation
* Insert Nums: https://github.com/jbrooksuk/InsertNums
* TextPad: http://www.textpad.com

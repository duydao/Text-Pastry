# Release Notes 1.6.2
- Fix #84 by changing the default keybindings for windows (#84)
- Fix toggle_sidebar keybindings bug (#93)

The legacy keybindings for windows can be added to the default keybindings (Preferences -> Key Bindings) file if requried:

```
[
    { "keys": ["ctrl+alt+n"], "command": "text_pastry_show_command_line", "args": { "text": "" } },
    { "keys": ["ctrl+alt+t"], "command": "text_pastry_show_menu" },
    { "keys": ["ctrl+alt+v"], "command": "text_pastry_insert_text", "args": { "clipboard": true, "separator": "\\n" } },
    { "keys": ["ctrl+alt+b"], "command": "text_pastry_redo" },
    ...
]
```

# Release Notes 1.6.1

- Fix "Pipe into selection" bug (#71)

# Release Notes 1.6.0

We've added a couple of new features and fixed some bugs. All changes are listed at the [1.6.1 Milestone page](https://github.com/duydao/Text-Pastry/milestone/14?closed=1)

## Sublime Text Command Palette:
There are two new options in the command palette:
`From X To 0` and `From X To 1` will generate a decrementing list, ending, according to our selection, at `0` or `1`.

## Text Pastry Command Line
We've added two new commands to the Text Pastry command line. All supported commands and aliases are listed in the [Text Pastry Commands](https://github.com/duydao/Text-Pastry/blob/master/config/TextPastryCommands.json) config file

### Decimal ranges

Use the following command to generate decimal list
`dec <start> <stop> [step] [padding] [precision] [fillchar]`

for example:
`dec 1.25 3 0.25` will generate the following list:

```
1.25
1.50
1.75
2.00
2.25
2.50
2.75
3.00
```

Text Pastry will reverse the list when start is lower than stop.

### Hex ranges

Use the following command to generate hexadecimal list
`hex <start> <stop> [step] [width]`

for example:
`hex 1.25 3 0.25` will generate the following list:

```
1.25
1.50
1.75
2.00
2.25
2.50
2.75
3.00
```

Text Pastry will reverse the list when start is lower than stop.

# Release Notes 1.5.1

Fixed the ```Find by regex``` command (#56)

# Release Notes 1.5.0

I'm excited to release Text Pastry 1.5.0! We've got some new features in this release:

- The Text Pastry Piping Bag
- The Clipboard Viewer
- Loops
- Duplicate values


## Text Pastry Piping Bag

With the Piping Bag feature, we can paste incremental values across multiple files. All we need to do, is to fill the values we want to paste into the piping bag.


## How to use the Piping Bag

Open the command palette and look for "Text Pastry: Show Piping Bag" or open ```Tools -> Text Pastry -> Show Piping Bag```.

Now we need to fill the piping bag with values that we want to paste. *Each line will be used as paste item.*

We can generate a number range to use in the piping bag by using command palette:

```CMD + Shift + P``` -> Text Pastry: Generate a list of numbers from 1 to 100

Now we're ready to go!
- Open a file
- Make as mani selections as we like
- Open the command palette and select ```Text Pastry: Pipe into selections```
- Rinse and repeat

Text pastry will progress the lines in the piping bag and starts from the beginning when the end was reached. A marker will be placed in the _Piping Bag_ which indicates the next value that will be pasted.

*Notice*: Please beware that this command will only be visible in the command palette when we have a single selection in our current view.

Generating a list of numbers will call the range command to generate the list of numbers.  For details on the range command, please check out 3. [Number](https://github.com/duydao/Text-Pastry/wiki/Number-Range)


## Clipboard Viewer

The Clipboard Viewer shows the text representation of the value that is currently in our Clipboard/Pasteboard.

Open the command palette and look for "Text Pastry: Show Clipboard Viewer" or open open ```Tools -> Text Pastry -> Show Clipboard Viewer```.

The Clipboard/Pasteboard will be updated with any modifications that we make in the view, as soon as we open/activate another file.

We can allow Text Pastry to update the clipboard without switching files by activating ```Tools -> Text Pastry -> Settings -> Update clipboard on-the-fly```. This can be helpfull when we want to modify the clipboard for other apps (e.g. Excel or Word).

*Notice*: Before we can use the option ```Update clipboard on-the-fly```, we have to make sure that the Clipboard Viewer is available. This can be done by the command palette or ```Tools -> Text Pastry -> Show Clipboard Viewer```


## Clipboard Tracker

The Clipboard Viewer uses a Clipboard Tracker to check the Clipboard/Pasteboard for changes every few 0.5 seconds. Tracking is disabled by default and can be enabled and configured in our Text Pastry user settings file. The default values are:

```
{
    "tracker_enabled": false,
    "tracker_autostart": false,
    "tracker_log_enabled": false,
    "tracker_interval": 0.5,
}
```

We can enable the tracker by open the Text Pastry Settings (Preferences -> Package Settings -> Text Pastry -> Settings - User) and add the following line:

```
    "tracker_enabled": true
```

## Loops

By default, Text Pastry will count the selections and will increment the value for each selection. We can change this behaviour by setting an end value and adding a loop count:

```0 3 2 end=12 loop=2``` will produce this paste list: ```00 03 06 09 12 00 03 06 09 12```

The list will be repeated as soon as the end is reached. We can do the same with the range command:

```range 0 12 2 padding=2 loop=2``` will give us the same result: ```00 03 06 09 12 00 03 06 09 12```

For details on the range command, please check out 3. [Number](https://github.com/duydao/Text-Pastry/wiki/Number-Range)

## Duplicate values

we can duplicate values by using the each-arg:

```letters a-c upper x3``` will produce this paste list: ```A A A B B B C C C```

this works for numeric values as well

```0 2 2 end=10 x2``` will produce this paste list: ```00 00 02 02 04 04 06 06 08 08 10 10```

We can use an alias for the x-arg:

```0 2 2 end=10 each=2``` will give us the same result: ```00 00 02 02 04 04 06 06 08 08 10 10```

***

# Release Notes 1.4.3

Three new commands were added in 1.4.3!

### Generate date ranges ###

New settings:

```
"parse_date_formats": [
    "%d.%m.%Y"
],
```

parse_date_formats is used to parse the date from the _Text Pastry_ command line. For supported date formats, please check out http://strftime.org/

```
"date_format": "%d.%m.%Y",
```

used to generate the date range. For supported date formats, please check out http://strftime.org/. For our convenience, we can set the date format-setting by calling the date-format command:

```
date-format %Y-%m-%d
```

**date range commands**

Command:

```
days x5
```

Result:

```
14.12.2014
15.12.2014
16.12.2014
17.12.2014
18.12.2014
```

Command:

```
weeks
```

Result:

```
14.12.2014
21.12.2014
28.12.2014
04.01.2015
11.01.2015
```

Command:

```
months
```

Result:

```
14.12.2014
14.01.2015
14.02.2015
14.03.2015
14.04.2015
```

Command:

```
end-of-month
```

Result:

```
31.12.2014
31.01.2015
28.02.2015
31.03.2015
30.04.2015
```

Command:

```
years
```

Result:

```
14.12.2014
14.12.2015
14.12.2016
14.12.2017
14.12.2018
```

We can add a start date to date range commands:

```
weeks 14.03.2015
```

Result:

```
14.03.2015
21.03.2015
28.03.2015
04.04.2015
11.04.2015
```

The date range command supports the newly introduced x-arg! Lets create 30 dates:

```
days x30
```

```
14.12.2014
15.12.2014
16.12.2014
...
10.01.2015
11.01.2015
12.01.2015
```

### Repeat argument (x-arg) ###
Before this release, we had to create empty lines and do a multiselect to create a number sequence. With 1.4.3, we can use this command to create new lines on the fly:


```
    1 x5
```

We will give us this result:

```
    1|
    2|
    3|
    4|
    5|
```

_Text Pastry_ will duplicate the line and add the number sequence to it, so the line doesn't have to be empty:

```
    <div id="row-|"></div>
```

Using ``1 x3`` will give us this:

```
    <div id="row-1"></div>
    <div id="row-2"></div>
    <div id="row-3"></div>
```

The x-arg is supported by the [**UUID/uuid** command](https://github.com/duydao/Text-Pastry/wiki/Command-Line-Reference), the [N M P command](https://github.com/duydao/Text-Pastry/wiki/Examples#insert-nums-syntax), the [range command](https://github.com/duydao/Text-Pastry/wiki/Command-Line-Reference) and the [date range command](https://github.com/duydao/Text-Pastry/wiki/Date-Range).

**Note:**: Please note that the x-argument will be ignored if we have multiple selections. If we have 5 selections, _Text Pastry_ will behave the same way as before and will fill all selections with a sequence number.


### Auto step (aka. Text with sequence [#20](https://github.com/duydao/Text-Pastry/issues/20)) ###

Inspired by @passalini's request, I've added the auto step feature. Use this command:

Command: ```as <text> [step] [x-arg]```

```
    as row-1
```

For each selection we've made, _Text Pastry_ will insert the text and increment the number by ``[step]`` (default is ``1``). As example, if we had 4 selections, we will get this:

Source:

```
    <div id="|"></div>
    <div id="|"></div>
    <div id="|"></div>
    <div id="|"></div>
```

Result:

```
    <div id="row-1"></div>
    <div id="row-2"></div>
    <div id="row-3"></div>
    <div id="row-4"></div>
```

Auto step supports a step size argument:

```
    as row-0 2
```

Result:

```
    <div id="row-0"></div>
    <div id="row-2"></div>
    <div id="row-4"></div>
    <div id="row-6"></div>
```

Auto Step supports the x-arg:

Source:

```
    <div id="|"></div>
```

Command:

```
    as row-10 10 x10
```

will expand to this:

```
    <div id="row-10"></div>
    <div id="row-20"></div>
    <div id="row-30"></div>
    <div id="row-40"></div>
    <div id="row-50"></div>
    <div id="row-60"></div>
    <div id="row-70"></div>
    <div id="row-80"></div>
    <div id="row-90"></div>
    <div id="row-100"></div>
```

### Generate a bunch of UUIDs ###

The UUID/uuid command supports the newly introduced x-arg. Use this command to create 100 UUIDs:

```
    UUID x100
```


## Release Notes 1.4.0 ##

I'm very excited to announce v1.4.0! The Code was actually released a few months ago, but I need the extra time to check the new features and update the [wiki](https://github.com/duydao/Text-Pastry/wiki).

As alwys, please feel free to report any bugs and/or feature request [here](https://github.com/duydao/Text-Pastry/issues).

## New Features ##

### Command-line ###

The _Text Pastry_ text field ( <kbd>CTRL/CMD</kbd> + <kbd>ALT</kbd> + <kbd>N</kbd> ) supports an extendable list of [commands](https://github.com/duydao/Text-Pastry/wiki/Command-Line-Reference).

Text Pastry Commands work like keybindings; you can map a keyword to any command available to [Sublime Text](http://www.sublimetext.com/). We can add new commands by modifying the _Text Pastry_ User-Settings file _(Preferences -> Package Settings -> Text Pastry -> Settings - Default)_.

For more information, please visit the [wiki](https://github.com/duydao/Text-Pastry/wiki/Adding-Commands)

### Presets ###

Presets are a [list of pre-defined values](https://github.com/duydao/Text-Pastry/wiki/Command-Line-Reference#default-presets):

A start/range operator is supported, as well as reverse and case modifiers.

We can extend this list as we like by modifying the text pastry user settings file _(Preferences -> Package Settings -> Text Pastry -> Settings - Default)_

### Selection Modifiers ###

I've added four commands to create, add and modify the current selection:

<table>
<tr><th>Command</th><th>Alias</th><th>Action</th></tr>
<tr><td>find</td><td>search</td><td>Create new selections</td></tr>
<tr><td>add</td><td>&nbsp;</td><td>Add to the current selection</td></tr>
<tr><td>remove</td><td>reduce, subtract</td><td>Remove from the current selections</td></tr>
<tr><td>filter</td><td>&nbsp;</td><td>search in selection</td></tr>
</table>

#### find ####

Clears the current selection, looks for the search term and marks them as new selections. The special thing about this command is how regex groups are handled: if the search term contains a regex-group, the group will be used for selection. As a nice side effect, this will give us the option to **place the cursor anywhere we want to**.

This Example will select all values inside of the attribute ``name``, the cursor will be placed at the end of the selection. We can place the cursor at the start of the selection by using the ``reverse`` option:

``find name="(.*?)"`` -> name="<b>this value is selected|</b>"


In this example, we will place the cursor at the beginning of the value, without a text selection:

``find name="().*?"`` -> name="<b>|</b><i>this value is not selected</i>"

As we can see, we are now able to place the cursor anywhere we want aswell as creating multiple selections with one regex.

#### add ####

Adds the matches to the current selection. This example will add all words to the current selection.

    add \w+

#### remove ####

Removes the matches form the current selection. This example will remove all non-words from the current selection:

    remove \s+

There are some additional shortcuts for remove:

Comamnd | Action
--- | ---
remove lines | Removes empty lines (lines containing only spaces will be count as empty).
remove leading | Removes leading spaces.
remove trailing | Removes trailing spaces.
remove space | Removes empty lines, leading spaces and trailing spaces.

#### filter ####

The filter command acts as "find in selection". Only matched terms in the curren selection will be selected afterwards.

This example will only keep selections inside of parentheses:

    filter \((.*?)\) 

### Yet Another Focus Mode ###

This mode lets us hide the side bar, tabs and/or status bar. We can configure what to hide in Packages/User/TextPastryAddons.sublime-settings. By default, Focus mode will toggle the side bar, status bar and the tabs:

    {
        "focus": ["toggle_side_bar", "toggle_status_bar", "toggle_tabs"]
    }

In addition, we can toggle the minimap by adding ``"toggle_minimap"`` to the list.

### Shell (experimental) ###

We can pass our selections to a CLI (node, python or ruby) and process them by inline code or a script. _Text Pastry_ will paste the result into the selection.

The script/code will get some basic information like selected text, index, etc. We probably need some context information for additional processing (like whats my scope, surrounding text, etc.)

**Note:** This is highly experimental. The code is prepped for additional CLI's.


## Releases ##
- 1.4.2: Fix range / negative steps [#24](https://github.com/duydao/Text-Pastry/issues/24) - Thanks [@TheClams](https://github.com/TheClams)
- 1.4.1: Hotfix for [#23](https://github.com/duydao/Text-Pastry/issues/23) - Thanks [@dufferzafar](https://github.com/dufferzafar)
- 1.4.0: New Features: command-line, presets and selection modifiers, focus mode
- 1.3.7: Bugfix release [#17](https://github.com/duydao/Text-Pastry/issues/17)
- 1.3.6: Bugfix release [#14](https://github.com/duydao/Text-Pastry/issues/14)
- 1.3.5: History navigation, command shortcuts - Thanks [@JAStanton](https://github.com/JAStanton)
- 1.3.4: Fixed for Sublime Text 3 - Thanks [@forcey](https://github.com/forcey)
- 1.3.3: New commands: \r(regexp) and \r regex
- 1.3.2: Bugfix release

## Installation ##

Thanks for using the excelent [Package Control](http://wbond.net/sublime_packages/package_control) to install _Text Pastry_.

We can do a manuall installation by cloning this repository into our Packages folder. Sublime Text -> Preferences -> Browse Packages...

```git clone git@github.com:duydao/Text-Pastry.git```

## How-To ##

To use _Text Pastry_, we need to open a Document in [Sublime Text](http://www.sublimetext.com/) and use [Multiple Selection](https://www.sublimetext.com/docs/selection) to mark the 
insert locations _(in this document also referred to as selections)_.

Let's keep in mind that the selected text will be replaced when we run the _Text Pastry_ command. To avoid that, we can alway place the cursor between letters by using <kbd>CTRL/CMD</kbd> + **Click** or even select a whole column by using <kbd>ALT</kbd> + **Click**

All we need to do now is to press <kbd>CTRL/CMD</kbd> + <kbd>ALT</kbd> + <kbd>N</kbd> to open the _Text Pastry_ command line. The input panel will show up at the bottom of [Sublime Text](http://www.sublimetext.com/).

Now its time to run our first command. Let's enter `first second third` and hit enter to run the command. _Text Pastry_ will add `first` to our first selection, `second` to the next selection and so on.

_Text Pastry_ will only replace as many words as we type into the command line. So if we have more selections then words, the rest of our selection will remain intact.

## Key Bindings ##
The default key bindings are stored at _<packages>/Text Pastry/Default.sublime-keymap_. As always, you can use your [user keymap file](http://docs.sublimetext.info/en/latest/customization/key_bindings.html) to setup your own key bindings.

<table>
<tr>
    <th>Linux / Windows</th>
    <th>Mac</th>
    <th>Action</th>
</tr>
<tr>
    <td><kbd>CTRL</kbd> + <kbd>ALT</kbd> + <kbd>T</kbd></td>
    <td><kbd>CMD</kbd> + <kbd>ALT</kbd> + <kbd>T</kbd></td>
    <td>Show _Text Pastry_ Menu</td>
</tr>
<tr>
    <td><kbd>CTRL</kbd> + <kbd>ALT</kbd> + <kbd>N</kbd></td>
    <td><kbd>CMD</kbd> + <kbd>ALT</kbd> + <kbd>N</kbd></td>
    <td>Open _Text Pastry_ Command Line</td>
</tr>
</table>

**Note:** The commands from the _Text Pastry_ menu are also available through the Command Palette (<kbd>CTRL/CMD</kbd> + <kbd>SHIFT</kbd> + <kbd>P</kbd>)

## Command Reference ##

### Regular Text ###

Replaces the first selection with **Lorem**, the second selection with **Ipsum**, etc.:
    
    Lorem Ipsum Dolor

**Note:** Since version 1.3.5, there must be at least three words before this command will be executed. This change will make it possible to define commands without escape character.

We can still use a list of any size by prepeinding the words command:

    words Lorem Ipsum


### Incremental Numbers, Numeric Sequence ###

Inserts a sequence, starting at 1:

    i


Inserts a sequence, starting at 0:
    
    i0


Inserts a sequence by defining start index and step size:
    
    i(N,M)

* `N` the start index
* `M` the step size

The step size defines the value to add to the index each time a value was inserted. Start index and step size may be negative.

**Note:** The Number Sequence command uses the syntax from [TextPad](http://www.textpad.com/).

To make it even easier, we can use this style if we want to:

<pre>
<i>start number</i> <i>increment by</i>
</pre>

With this example, the first number will be 1000 and it will be incremented by 250 for each selction:

    1000 250

### Clipboard ###

Inserts the content of the clipboard into our selections by [splitting the words](http://docs.python.org/library/stdtypes.html#str.split):

    p
    
Same as above with a specified [string separator](http://docs.python.org/library/stdtypes.html#str.split):

<pre>
p <i>sep</i>
</pre>

* `sep` the string separator used to split the clipboad data.


**Note:** The Clipboard command uses syntax from [TextPad](http://www.textpad.com/).

### UUID ###

_Text Pastry_ will generate a [UUID](http://en.wikipedia.org/wiki/Universally_unique_identifier) for each selection we have made:

    uuid

This command will generate a _random UUID_ by using pythons [uuid.uuid4() method](http://docs.python.org/2/library/uuid.html#uuid.uuid4):
    
    dbf8326e-5243-406e-abd9-bd0425d3e842

We can this command to generate a _random UUID_ in UPPERCASE:

    UUID

### Regular Expression as separators ###

We're able to define regex separators for the data that we are pasting, which should give us some new possibilities.

We can [split the clipboard data by regex](http://docs.python.org/2/library/re.html#re.split), and paste the resulting items into the selected locations:

<pre>
regex <a href="http://docs.python.org/3/library/re.html#regular-expression-syntax" target="_blank"><i>expression</i></a>
</pre>

* `expression` the [regular expression](http://docs.python.org/3/library/re.html#regular-expression-syntax) used to split the clipboard data.

**Note:** If you managed to get [python-pcre](https://github.com/awahlig/python-pcre) up and running, the library will be preferred over the default python [re](http://docs.python.org/3/library/re.html) library.

### Insert Nums ###

_Text Pastry_ has a build in support for the [Insert Nums](https://github.com/jbrooksuk/InsertNums/) syntax by providing three numbers separated by one space:

    N M P

* `N`: the start index.
* `M` represents the step size which will be added to the index for each selection.
* `P` must be > 0 and will be used to pad the index with leading zeroes.

### Convert to letter case ###

We can convert the selection to upper, lower or title case.

- `uc` or `upper` - Converts selection to uppercase
- `lc` or `lower` - Converts selection to lowercase
- `cap` or `caps` - Converts selection to titlecase

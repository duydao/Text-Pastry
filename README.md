# Text Pastry #

_Text Pastry_ is a plugin for [Sublime Text](http://www.sublimetext.com/) that will give you the necessary tools to insert or paste a bunch of text, a range of numbers or generated UUIDs into your selected locations.

Ever wanted to paste incrementing numbers or five lines from your clipboard into five different locations at once? _Text Pastry_ can help you out!

## What's new ##
- v1.3.4: Fixed for Sublime Text 3 - Thanks [@forcey](https://github.com/forcey)
- v1.3.3: New commands: \r(regexp) and \r regex
- v1.3.2: Bugfix release


## Installation ##

Thanks for using the excelent [Package Control](http://wbond.net/sublime_packages/package_control) to install _Text Pastry_.

We can do a manuall installation by cloning this repository into our Packages folder. Sublime Text -> Preferences -> Browse Packages...

```git clone git@github.com:duydao/Text-Pastry.git```

## Usage ##

To use _Text Pastry_, we need to open a Document in [Sublime Text](http://www.sublimetext.com/) and use [Multiple Selection](http://www.sublimetext.com/docs/2/multiple_selection_with_the_keyboard.html) to mark the 
insert locations _(in this document also refered to as selections)_.

Please keep in mind that the selected text could be replaced when we run the _Text Pastry_ command. To avoid that, we can alway place the cursor between letters by using **CMD + Click** or even select a whole column by using **ALT + Click**

All we need to do now is to press **CMD + ALT + N** to open the _Text Pastry_ command line. The input panel will show up at the bottom of [Sublime Text](http://www.sublimetext.com/).

Now its time to run our first command. Let's enter `first second third` and hit enter to run the command. _Text Pastry_ will add `first` to our first selection, `second` to the next selection and so on.

_Text Pastry_ will only replace as many words as we type into the command line. So if we have more selections then words, the rest of our selection will remain intact.

## Key Bindings ##
The default key bindings are stored at _<packages>/Text Pastry/Default.sublime-keymap_. As always, you can use your [user keymap file](http://www.sublimetext.com/docs/key-bindings) to overrule the default key bindings.

<table>
<tr>
	<th>Shortcut</th>
	<th>Action</th>
</tr>
<tr>
	<td><strong>CMD + ALT + T</strong></td>
	<td>Show Text Pastry Menu</td>
</tr>
<tr>
	<td><strong>CMD + ALT + N</strong></td>
	<td>Open Command Line</td>
</tr>
</table>

**Note:** The commands from the _Text Pastry_ menu are also available through the Command Palete (**CMD + SHIFT + P**)

## Command Reference ##

### Text ###

Replaces the first selection with **Lorem**, the second selection with **Ipsum**, etc.:
	
	Lorem Ipsum Dolor

### Number Sequence ###


Inserts a sequence, starting at 1:

	\i


Inserts a sequence, starting at 0:
	
	\i0


Inserts a sequence by defining start index and step size:
	
	\i(N,M)

* `N` the start index
* `M` the step size

**Note:** The Number Sequence command uses the syntax from [TextPad](http://www.textpad.com/).

Additionally, we can leave the brackets away if we want to:

	\i1000,100

	
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

### REGEX separators ###
**NEW** We're now able to define regex separators for the data that we are pasting, which should give us some new possibilities.

We can split the clipboard data by regex, and paste the resulting items into the selected locations:

	\r(regex)

or
	
	\r regex

* `regex` the regexp used to split the clipboad data.

**Note:** If you managed to get [python-pcre](https://github.com/awahlig/python-pcre) up and running, the library will be prefered over the default python [re](http://docs.python.org/2/library/re.html) library.

### Insert Nums ###

_Text Pastry_ has a build in support for the [Insert Nums](https://github.com/jbrooksuk/InsertNums/) syntax by providing three numbers separated by one space:

	N M P

* `N`: the start index.
* `M` represents the step size which will be added to the index for each selection.
* `P` must be > 0 and will be used to pad the index with leading zeroes.

Note: 

## Examples ##

Here are some examples, assuming we have selected every ocurence of `null` and _Text Pastry_ was called by pressing **CMD + ALT + N**:

### Using a text list ###



Enter a list of words, separated by one space, into the command line:

	INPUT SELECT TEXTAREA DIV P A

#### Text ####

	var a = document.getElementsByTagName('null');
	var b = document.getElementsByTagName('null');
	var c = document.getElementsByTagName('null');
	var d = document.getElementsByTagName('null');
	var e = document.getElementsByTagName('null');
	var f = document.getElementsByTagName('null');
	
#### Result ####

	var a = document.getElementsByTagName('INPUT');
	var b = document.getElementsByTagName('SELECT');
	var c = document.getElementsByTagName('TEXTAREA');
	var d = document.getElementsByTagName('DIV');
	var e = document.getElementsByTagName('P');
	var f = document.getElementsByTagName('A');

***

###Using the Clipboard###

The same as above, but this time we copy the list of words into our clipboard:

#### Clipboard Data ####

	INPUT SELECT TEXTAREA DIV P A
	
#### Command ####

Insert this into the input panel:

	\p

#### Text ####

	var a = document.getElementsByTagName('null');
	var b = document.getElementsByTagName('null');
	var c = document.getElementsByTagName('null');
	var d = document.getElementsByTagName('null');
	var e = document.getElementsByTagName('null');
	var f = document.getElementsByTagName('null');
	
#### Result ####

	var a = document.getElementsByTagName('INPUT');
	var b = document.getElementsByTagName('SELECT');
	var c = document.getElementsByTagName('TEXTAREA');
	var d = document.getElementsByTagName('DIV');
	var e = document.getElementsByTagName('P');
	var f = document.getElementsByTagName('A');

#### Note ####

If we copy following list, we will get the same result:

	INPUT
	SELECT
	TEXTAREA
	DIV
	P
	A

***

### Clipboard Data v2 ###

Lets assume we want to paste some test data into our code:

	71602	White Hall
	71603	Pine Bluff
	71611	Pine Bluff
	71612	White Hall
	71613	Pine Bluff
	71630	Arkansas City
	71631	Banks
	71635	Crossett
	71638	Dermott
	71639	Dumas
	
#### Command ####

This command will tell _Text Pastry_ to split up our clipboard data by using the newline character as separator:

	\p(\n)

#### Text ####

	var a = load('null');
	var b = load('null');
	var c = load('null');
	var d = load('null');
	var e = load('null');
	var f = load('null');
	
#### Result ####

	var a = load('71602	White Hall');
	var b = load('71603	Pine Bluff');
	var c = load('71611	Pine Bluff');
	var d = load('71612	White Hall');
	var e = load('71613	Pine Bluff');
	var f = load('71630	Arkansas City');

#### Note ####

Each line of the clipboard data will be stripped/trimmed,   so there won't be any leading spaces.

The following list would therefore give us the same result when we use \p(\n) as command:

Data without leading/trailing whitespace

	INPUT
	SELECT
	TEXTAREA
	DIV
	P
	A

Data with leading whitespace:

	INPUT
		SELECT
			TEXTAREA
			DIV
		P
	A

We can change this behaviour in the **&lt;Packages&gt;/Text Pastry/TextPastry.sublime-settings** file:

	"clipboard_strip_newline": false

***

### From 1 to 3 ###

Start at 1, adding 1 for each selection:

	\i
	
#### Text ####

	var a = null;
	var b = null;
	var c = null;
	
#### Result ####

	var a = 1;
	var b = 2;
	var c = 3;

***

### From 1000 to 1300 ###

Start at 1000, adding 100 for each selection:

	\i(1000,100)
	
#### Text ####

	var a = null;
	var b = null;
	var c = null;
	
#### Result ####

	var a = 1000;
	var b = 1100;
	var c = 1200;

***

### From 100 to 50 ###

You can also use negative numbers to create a negative sequence:

	\i(100,-10)

#### Text ####

	var a = null;
	var b = null;
	var c = null;
	var d = null;
	var e = null;
	var f = null;
	
#### Result ####

	var a = 100;
	var b = 90;
	var c = 80;
	var d = 70;
	var e = 60;
	var f = 50;

***

### Insert Nums Syntax ###

	1 100 1

#### Text ####

	var a = null;
	var b = null;
	var c = null;
	var d = null;
	var e = null;
	var f = null;
	
#### Result ####

	var a = 1;
	var b = 101;
	var c = 201;
	var d = 301;
	var e = 401;
	var f = 501;

***

### Insert Nums Syntax v2 ###

	1 1 3

#### Text ####

	var a = null;
	var b = null;
	var c = null;
	var d = null;
	var e = null;
	var f = null;
	
#### Result ####

	var a = 001;
	var b = 002;
	var c = 003;
	var d = 004;
	var e = 005;
	var f = 006;

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

Copyright (c) 2013 Duy Dao, https://github.com/duydao/Text-Pastry

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
* Sublime Package Control: http://wbond.net/sublime_packages/package_control
* Insert Nums: https://github.com/jbrooksuk/InsertNums
* TextPad: http://www.textpad.com

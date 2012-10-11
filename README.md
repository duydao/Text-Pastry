# Insert Text #
===

A Sublime Text 2-package to insert a sequence of text or numbers on multiple locations.

Based on [Insert Nums](https://bitbucket.org/markstahler/insert-nums/) by [Mark Stahler](http://blog.markstahler.ca/)

## Installation ##
***


## Usage ##
***

To Insert Text, open a Document in [ST2](http://www.sublimetext.com/) and use [Multiple Selection](http://www.sublimetext.com/docs/2/multiple_selection_with_the_keyboard.html) to select the desired text.

Press **CMD + ALT + T** to show the Insert Text command line at the bottom of ST2.

enter "first second third" (without quotes) and hit enter to run the command. Insert Text will replace our first selection with "first", our second selection with "second" and so on.

Insert Text will only replace as many words as we type into the command line. So if we have more selections then words, the rest of our selection will remain intact.

## Command Reference ##
***

### Text ###

Replaces the first selection with **first**, the second selection with **second**, etc.:
	
	first second third

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
	
### Clipboard ###

Inserts the content of the clipboard into our selections by [splitting the words](http://docs.python.org/library/stdtypes.html#str.split):

	\p
	
Same as above with a specified [string separator](http://docs.python.org/library/stdtypes.html#str.split):

	\p(sep)
* `sep` the string separator used to split the clipboad data.



**Note:** The Clipboard command uses syntax from [TextPad](http://www.textpad.com/).

### Insert Nums ###

Insert Text has a build in support for the [Insert Nums](https://bitbucket.org/markstahler/insert-nums/) syntax by providing three numbers separated by one space:

	N M P

* `N`: the start index.
* `M` represents the step size which will be added to the index for each selection.
* `P` must be > 0 and will be used to pad the index with leading zeroes.


## Examples ##
***

Here are some examples, assuming we have selected every ocurence of `null` and Insert Text was called by pressing **CMD + ALT + T**:

***

### Using words ###



Enter a list of words into the command line of Insert Text:

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

	71602	White Hall	71603	Pine Bluff	71611	Pine Bluff	71612	White Hall	71613	Pine Bluff	71630	Arkansas City	71631	Banks	71635	Crossett	71638	Dermott	71639	Dumas	71640	Eudora	71642	Fountain Hill	71643	Gould	71644	Grady	71646	Hamburg	71647	Hermitage	71651	Jersey	71652	Kingsland	71653	Lake Village	71654	Mc Gehee	71655	Monticello	71656	Monticello	71657	Monticello	71658	Montrose	71659	Moscow	71660	New Edinburg
	
#### Command ####

Let's insert the following command into our input panel. 

This will tell Insert Text to split up our clipboard data  by using the newline character as separator:

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

We can change this behaviour in the **&lt;Packages&gt;/Insert Text/InsertText.sublime-settings** file:

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

### From 100 to 50 ###

You can also use negative numbers to create a negative sequence

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
***
- Clipboard

## See Also ##
***

For further information please take the time to look at following links:

* Sublime Text 2: http://www.sublimetext.com/
* Sublime Package Control: http://wbond.net/sublime_packages/package_control
* Insert Nums: https://bitbucket.org/markstahler/insert-nums/
* TextPad: http://www.textpad.com
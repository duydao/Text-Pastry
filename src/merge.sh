#/bin/sh

echo -e "import sublime, sublime_plugin, re, operator\n"
for file in `ls *.py`
do
	echo "# ========================================"
	echo "# $file"
	echo "# ========================================"
	cat $file | grep -v ^import | grep -v "^\s*$"
	echo ""
done
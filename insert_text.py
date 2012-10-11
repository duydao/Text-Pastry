import sublime, sublime_plugin, re

class PromptInsertTextCommand(sublime_plugin.WindowCommand):

    def run(self, text):
        v = self.window.show_input_panel('Enter a list of items, separated by spaces', text, self.on_done, None, None)

    def on_done(self, text):
        try:
            if self.window.active_view() and len(text) > 0:
                m1 = re.compile('(-?\d+) (-?\d+) (\d+)').match(text)
                m2 = re.compile('\\\\i(\d*)(,(-?\d+))?').match(text)
                m3 = re.compile('\\\\i\((\d*)(,(-?\d+))?\)').match(text)

                m4 = re.compile('\\\\p\((.*?)\)').match(text)
                if m1:
                    sublime.status_message("Inserting Nums: " + text)
                    (current, step, padding) = map(str, text.split(" "))
                    self.window.active_view().run_command("insert_nums", {"current" : current, "step" : step, "padding" : padding})

                elif m2 or m3:
                    m = None
                    if m2: m = m2
                    else: m = m3
                    current = m.group(1)
                    step = m.group(3)

                    if current is None or len(current) == 0: current = "1"
                    if step is None or len(step) == 0: step = "1"

                    sublime.status_message("Inserting #" + text)
                    self.window.active_view().run_command("insert_nums", {"current" : current, "step" : step, "padding" : "1"})
                elif text == "\\p":
                    sublime.status_message("Inserting from clipboard")
                    self.window.active_view().run_command("insert_text", {"text": sublime.get_clipboard()})
                elif m4:
                    separator = m4.group(1)
                    if separator is None or separator == '':
                        separator = None

                    sublime.status_message("Inserting from clipboard with separator: " + str(separator))
                    self.window.active_view().run_command("insert_text", {"text": sublime.get_clipboard(), "separator": separator})
                else:
                    sublime.status_message("Inserting " + text)
                    self.window.active_view().run_command("insert_text", {"text": text})

        except ValueError:
            pass

class OverlaySelectInsertTextCommand(sublime_plugin.WindowCommand):
    def run(self):
        try:
            c = len(self.window.active_view().sel())

            if c > 1 or True:
                x = c
                self.items = [
                    ["\\i", "From 1 to " + str(x)],
                    ["\\i0", "From 0 to " + str(x-1)],
                    ["\\i(N,M)", "From N to X by M"],
                    ["\\p(\\n)", "Paste Line from Clipboard"],
                    ["\\p", "Paste Words from Clipboard"],
                    ["1 1 1", "From 1 to " + str(x)],
                    ["0 1 1", "From 0 to " + str(x-1)],
                    ["a b c", "Text separated by one space"]
                ]

                self.window.show_quick_panel(self.toListItem(self.items, 9), self.on_done, sublime.MONOSPACE_FONT)
            else:
                sublime.status_message("You need to make multiple selections to use Insert Text");
        except ValueError:
            sublime.status_message("Error while showing Insert Text overlay");

    @staticmethod
    def toListItem(items, width):
        a = []
        for item in items:
            listitem = item[0].ljust(width) + item[1]
            a.append(listitem)
        return a

    def on_done(self, index):
        s = ""

        if index >= 0 and index < len(self.items):
            s = self.items[index][0]

            if s == "\\p":
                self.window.active_view().run_command("insert_text", {"text": sublime.get_clipboard()})
            elif s == "\\i":
                self.window.active_view().run_command("insert_nums", {"current": "1", "step": "1", "padding": "1"})
            elif s == "\\i0":
                self.window.active_view().run_command("insert_nums", {"current": "0", "step": "1", "padding": "1"})
            elif len(s):
                self.window.run_command("prompt_insert_text", { "text": s })
            else:
                sublime.status_message("Unknown command: " + s)
                pass
        else:
            sublime.status_message("No item selected")

class InsertTextCommand(sublime_plugin.TextCommand):

    def run(self, edit, text=None, separator=None, clipboard=False):
        try:
            regions = []
            sel = self.view.sel()

            if separator: separator = separator.encode('utf8').decode("string-escape")
            if (clipboard): text = sublime.get_clipboard()

            if True or text is not None and len(text) > 0:
                items = text.split(separator)

                strip = False
                settings = sublime.load_settings("InsertText.sublime-settings")
                if separator == "\n" and settings.has("clipboard_strip_newline"): strip = settings.get("clipboard_strip_newline")

                for idx, region in enumerate(sel):
                    if idx < len(items):
                        current = items[idx]
                        if (strip): current = current.strip()
                        self.view.replace(edit, region, current)
                    else:
                        regions.append(region)

                sel.clear()

                for region in regions:
                    sel.add(sublime.Region(region.begin(), region.end()))
            else:
                sublime.status_message("No text found for Insert Text, canceled")

        except ValueError:
            sublime.status_message("Error while executing Insert Text, canceled")
            pass

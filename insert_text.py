import sublime, sublime_plugin, re

class PromptInsertTextCommand(sublime_plugin.WindowCommand):

    def run(self, text):
        v = self.window.show_input_panel('Enter a list of items, separated by spaces', text, self.on_done, None, None)

    def on_done(self, text):
        try:
            #sublime.status_message("Text: " + str(text))
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
                    else:
                        separator = separator.encode('utf8').decode("string-escape")

                    sublime.status_message("Inserting from clipboard with separator: " + str(separator))
                    self.window.active_view().run_command("insert_text", {"text": sublime.get_clipboard(), "separator": separator})
                else:
                    sublime.status_message("Inserting " + text)
                    self.window.active_view().run_command("insert_text", {"text": text})

        except ValueError:
            pass

class OverlaySelectInsertTextCommand(sublime_plugin.WindowCommand):
    def run(self):
        c = len(self.window.active_view().sel())

        if c > 1 or True:
            x = str(c)
            self.items = [
                    ["Sequence: From 1 to " + x, "Command: \\i"],
                    ["Sequence: From 0 to " + x, "Command: \\i0"],
                    ["Sequence: From N to " + x + " by M", "Command: \\i(N,M)"],
                    ["Clipboard: Paste", "Command: \\p"],
                    ["Clipboard: Paste NewLine", "Command: \\p"],
                    ["Insert Nums: From 1 to " + x, "Command: 1 1 1"],
                    ["Insert Nums: From 0 to " + x, "Command: 0 1 1"],
                    ["Text", "Command: first second third"]
                ]
            self.window.show_quick_panel(self.items, self.on_done)
        else:
            sublime.status_message("You need to make multiple selections to use Insert Text");

    def on_done(self, index):
        s = ""

        if index >= 0 and index < len(self.items):
            item = self.items[index]
            s = item[1].replace("Command: ", "")
            if s == "\\p":
                self.window.active_view().run_command("insert_text", {"text": sublime.get_clipboard()})
            elif s == "\\i":
                self.window.active_view().run_command("insert_nums", {"current": "1", "step": "1", "padding": "1"})
            elif s == "\\i0":
                self.window.active_view().run_command("insert_nums", {"current": "0", "step": "1", "padding": "1"})
            elif len(s):
                self.window.run_command("prompt_insert_text", { "text": s })
            else:
                pass

class InsertTextCommand(sublime_plugin.TextCommand):

    def run(self, edit, text, separator=None):
        regions = []
        sel = self.view.sel()
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

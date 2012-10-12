import sublime, sublime_plugin, re, operator

class PromptInsertTextCommand(sublime_plugin.WindowCommand):

    def run(self, text):
        v = self.window.show_input_panel('Enter a list of items, separated by spaces', text, self.on_done, None, None)

    def on_done(self, text):
        try:
            if self.window.active_view() and text:
                m1 = re.compile('(-?\d+) (-?\d+) (\d+)').match(text)
                m2 = re.compile('\\\\i(\d*)(,(-?\d+))?').match(text)
                m3 = re.compile('\\\\i\((\d*)(,(-?\d+))?\)').match(text)

                m4 = re.compile('\\\\p\((.*?)\)').match(text)
                if m1:
                    (current, step, padding) = map(str, text.split(" "))

                    InsertTextHistory.save_history("insert_nums", text)
                    sublime.status_message("Inserting Nums: " + text)
                    self.window.active_view().run_command("insert_nums", {"current" : current, "step" : step, "padding" : padding})

                elif m2 or m3:
                    m = None
                    if m2: m = m2
                    else: m = m3
                    current = m.group(1)
                    step = m.group(3)

                    if not current: current = "1"
                    if not step: step = "1"

                    InsertTextHistory.save_history("insert_nums", text)
                    sublime.status_message("Inserting #" + text)
                    self.window.active_view().run_command("insert_nums", {"current" : current, "step" : step, "padding" : "1"})
                
                elif text == "\\p":
                    InsertTextHistory.save_history("insert_text", text=sublime.get_clipboard(), label=text)
                    sublime.status_message("Inserting from clipboard")
                    self.window.active_view().run_command("insert_text", {"text": sublime.get_clipboard()})
                
                elif m4:
                    separator = m4.group(1)
                    if not separator: separator = None

                    InsertTextHistory.save_history("insert_text", text=sublime.get_clipboard(), label=text, separator=separator)
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
            selection_count = len(self.window.active_view().sel())

            if selection_count > 1 or True:
                x = selection_count
                self.items = []

                entries = InsertTextHistory.load_history()
                history_items = []
                history_index = 1
                for entry in entries:
                    command = entry.get("command", None)
                    text = entry.get("text", None).decode("unicode-escape").decode("string-escape")
                    separator = entry.get("separator", None)
                    label = entry.get("label", None)
                    if not label: label = ""

                    if text and command:
                        self.items.append(["history", command, text, separator])

                        s = ('hist' + str(history_index)).ljust(9)
                        if len(text) > 50: text = text[0:50] + "..."
                        s += ' '.join((label + " " + text).split())
                        history_items.append(s)

                        history_index += 1

                default_items = [
                    ["\\i", "From 1 to " + str(x)],
                    ["\\i0", "From 0 to " + str(x-1)],
                    ["\\i(N,M)", "From N to X by M"],
                    ["\\p(\\n)", "Paste Line from Clipboard"],
                    ["\\p", "Paste Words from Clipboard"],
                    #["1 1 1", "From 1 to " + str(x)],
                    #["0 1 1", "From 0 to " + str(x-1)],
                    #["a b c", "Text separated by one space"],
                    ["clear", "Clear history"],
                    ["cancel", "Cancel"]
                ]

                self.items.extend(default_items)
                overlay_items = history_items + self.toListItem(default_items, 9);
                self.window.show_quick_panel(overlay_items, self.on_done, sublime.MONOSPACE_FONT)
            
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
        if index >= 0 and index < len(self.items):
            item = self.items[index]
            s = item[0]

            sublime.status_message(s)
            if (s == "history"):
                sublime.status_message("history")
                command = item[1]
                text = item[2]
                separator = item[3]

                if command == "insert_nums":
                    (current, step, padding) = map(str, text.split(" "))
                    self.window.active_view().run_command(command, {"current": current, "step": step, "padding": padding})

                elif command == "insert_text":
                    self.window.active_view().run_command(command, {"text": text, "separator": separator})

                else:
                    self.window.run_command("prompt_insert_text", { "text": text })

            elif s == "clear":
                InsertTextHistory.clear_history()
            
            elif s == "cancel":
                pass

            elif s == "\\p":
                self.window.active_view().run_command("insert_text", {"text": sublime.get_clipboard()})

            elif s == "\\p":
                InsertTextHistory.save_history("insert_text", text=sublime.get_clipboard(), label=s)
                self.window.active_view().run_command("insert_text", {"text": sublime.get_clipboard()})

            elif s == "\\p(\\n)":
                InsertTextHistory.save_history("insert_text", text=sublime.get_clipboard(), label=s)
                self.window.active_view().run_command("insert_text", {"text": sublime.get_clipboard(), "separator": "\\n"})

            elif s == "\\i":
                InsertTextHistory.save_history("insert_nums", text="1 1 1", label=s)
                self.window.active_view().run_command("insert_nums", {"current": "1", "step": "1", "padding": "1"})

            elif s == "\\i0":
                InsertTextHistory.save_history("insert_nums", text="0 1 1", label=s)
                self.window.active_view().run_command("insert_nums", {"current": "0", "step": "1", "padding": "1"})

            elif len(s):
                self.window.run_command("prompt_insert_text", { "text": s })

            else:
                sublime.status_message("Unknown command: " + s)

        else:
            sublime.status_message("No item selected")

class InsertTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, text=None, separator=None, clipboard=False):
        try:
            if True or text is not None and len(text) > 0:
                regions = []
                sel = self.view.sel()

                if separator: separator = separator.encode('utf8').decode("string-escape")
                if clipboard: text = sublime.get_clipboard()

                InsertTextHistory.save_history("insert_text", text, separator)
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

class InsertTextHistory:

    @staticmethod
    def save_history(command, text, separator=None, label=None):
        name = "InsertTextHistory.sublime-settings"
        hs = sublime.load_settings(name);
        history = hs.get("history", {})

        text = text.encode('unicode-escape')

        key = str(hash(text+str(separator)))
        if not key in history:
            history[key] = dict(command=command, text=text, separator=separator, index=len(history), label=label)

        hs.set("history", history)

        # last command
        hs.set("last_command", dict(key=key, command=command, text=text, separator=separator, index=len(history), label=label));

        sublime.save_settings(name)
        #sublime.message_dialog("saved: " + str(key))

    @staticmethod
    def load_history():
        name = "InsertTextHistory.sublime-settings"
        hs = sublime.load_settings(name);
        history = hs.get("history", {})

        entries = []
        for key, item in history.iteritems():
            command = None
            text = None
            separator = None

            if item.has_key("command") and item.has_key("text") and item["command"] and item["text"]:
                entries.append(item)
            else:
                InsertTextHistory.remove_history(key)

            #sublime.message_dialog(str(type(entry)))

            # for key, value in entry.iteritems():
            #     if key == "text": text = value.decode('unicode-escape')
            #     elif key == "separator": separator = value
            #     elif key == "command": command = value
            
            # if text and command:
            #     entries.append([command, text, separator])

        sorted_x = sorted(entries, key=operator.itemgetter("index"), reverse=True)


        return sorted_x

    @staticmethod
    def remove_history(id):
        removed = False
        name = "InsertTextHistory.sublime-settings"
        hs = sublime.load_settings(name);
        history = hs.get("history", {})

        sublime.status_message("Deleting item from history: " + str(id))

        if history.has_key(id):
            del history[id]
            hs.set("history", history)
            sublime.save_settings(name)
            removed = True

        return removed

    @staticmethod
    def clear_history():
        name = "InsertTextHistory.sublime-settings"
        hs = sublime.load_settings(name);
        history = hs.set("history", {})
        sublime.save_settings(name)
        sublime.status_message("History deleted")

    @staticmethod
    def last_command():
        name = "InsertTextHistory.sublime-settings"
        hs = sublime.load_settings(name);
        last_command = hs.get("last_command", {})
        return last_command

class InsertTextRepeatLastCommandCommand(sublime_plugin.WindowCommand):
    def run(self):
        try:
            item = InsertTextHistory.last_command()

            if item.has_key("command") and item.has_key("text") and item["command"] and item["text"]:
                text = item.get("text").decode("unicode-escape").decode("string-escape")
                separator = item.get("separator", None)
                command = item.get("command", None)

                if text and command:
                    sublime.status_message("Running last command")

                    if command == "insert_nums":
                        (current, step, padding) = map(str, text.split(" "))
                        self.window.active_view().run_command(command, {"current": current, "step": step, "padding": padding})

                    elif command == "insert_text":
                        self.window.active_view().run_command(command, {"text": text, "separator": separator})

                    else:
                        #self.window.run_command("prompt_insert_text", { "text": text })
                        pass
        except:
            sublime.status_message("Error while calling last command")

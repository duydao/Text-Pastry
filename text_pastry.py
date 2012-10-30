import sublime, sublime_plugin, re, operator, time, uuid
# ========================================
# history.py
# ========================================
class History:
    FILENAME = "TextPastryHistory.sublime-settings"
    @staticmethod
    def save_history(command, text, separator=None, label=None):
        hs = sublime.load_settings(History.FILENAME)
        history = hs.get("history", {})
        text = text.encode('unicode-escape')
        key = str(hash(text+str(separator)))
        if key in history: del history[key]
        timestamp = time.time()
        history[key] = dict(command=command, text=text, separator=separator, date=timestamp, label=label)
        hs.set("history", history)
        hs.set("last_command", dict(key=key, command=command, text=text, separator=separator, index=len(history), label=label))
        sublime.save_settings(History.FILENAME)
    @staticmethod
    def load_history():
        sublime.status_message("history loaded")
        hs = sublime.load_settings(History.FILENAME)
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
        try:
            sorted_x = sorted(entries, key=lambda h: h["date"], reverse=True)
        except:
            sorted_x = entries
        sublime.status_message("history loaded")
        return sorted_x
    @staticmethod
    def remove_history(id):
        removed = False
        hs = sublime.load_settings(History.FILENAME)
        history = hs.get("history", {})
        sublime.status_message("Deleting item from history: " + str(id))
        if history.has_key(id):
            del history[id]
            hs.set("history", history)
            sublime.save_settings(History.FILENAME)
            removed = True
        return removed
    @staticmethod
    def clear_history():
        hs = sublime.load_settings(History.FILENAME)
        history = hs.set("history", {})
        sublime.save_settings(History.FILENAME)
        sublime.status_message("History deleted")

# ========================================
# overlay.py
# ========================================
class Overlay:
    def __init__(self):
        self.items = []
    def add(self, item):
        if item: self.items.append(item)
    def addMenuItem(self, command, label):
        item = MenuItem(command, label)
        if command and label:
            self.items.append( item )
        return item
    def addSpacer(self):
        item = SpacerItem()
        self.items.append( item )
        return item
    def addHistoryItem(self, command, label, text, separator):
        item = HistoryItem(command, label, text, separator)
        if command and text:
            self.items.append( item )
        return item
    def get(self, index):
        item = None
        if index >= 0 and index < len(self.items): item = self.items[index]
        return item
    def all(self):
        entries = []
        width = 12
        for idx, item in enumerate(self.items):
            entries.append( [item.format(width, idx)] )
        return entries
    def is_valid(self):
        return self.items and len(self.items) > 0
    def length(self):
        return len(self.items)
class MenuItem:
    def __init__(self, command=None, label=None, text=None, separator=None):
        self.command = command
        self.label = label
        self.text = text
        self.separator = separator
        self.type = 1
    def format(self, width, index):
        return self.command.ljust(width).rjust(width + 1) + self.label
class HistoryItem:
    def __init__(self, command=None, label=None, text=None, separator=None):
        self.command = command
        self.label = label
        self.text = text
        self.separator = separator
        self.type = 2
    def format(self, width, index):
        i = str(index + 1)
        s = ('hist' + i).ljust(width).rjust(width + 1)
        text = self.text
        s += self.label
        return s
    def formatText(self, width):
        text = self.text
        if text and len(text) > 50: text = text[0:50] + "..."
        return ' '.ljust(width + 1).rjust(width + 2) + ' '.join((text).split())
class SpacerItem:
    def __init__(self):
        self.type = 3
    def format(self, width, index):
        return ""

# ========================================
# commands.py
# ========================================
class Command:
    def __init__(self, options=None):
        self.counter = 0
        self.options = options
        self.stack = []
        pass
    def set_items(self, items):
        if items: self.stack = items
    def previous(self):
        return self.stack[self.counter-1]
    def current(self):
        return text[self.counter]
    def next(self):
        self.counter += 1
        return self.stack[self.counter]
    def has_next(self):
        return (self.counter + 1) < len(self.stack)
    @staticmethod
    def create(cmd, items=None, options=None):
        command_list = {
            "uuid": UUIDCommand
        }
        return command_list.get(cmd)(items)
class UUIDCommand(Command):
    def next(self):
        text = str(uuid.uuid4())
        if self.is_upper_case():
            text = text.upper()
        self.stack.append(text)
        return text
    def is_upper_case(self):
        upper_case = False
        if self.options:
            upper_case = self.options.get("uppercase", False)
        return upper_case
    def has_next(self): return True

# ========================================
# parser.py
# ========================================
class Parser:
    def parse(self, text):
        result = None
        if not text: return None
        if text:
            m1 = re.compile('(-?\d+) (-?\d+) (\d+)$').match(text)
            m2 = re.compile('\\\\i(\d+)(,(-?\d+))?').match(text)
            m3 = re.compile('\\\\i\((\d+)(,(-?\d+))?').match(text)
            m4 = re.compile('\\\\p\((.*?)\)?').match(text)
            if m1:
                (current, step, padding) = map(str, text.split(" "))
                History.save_history("insert_nums", text, label=text)
                sublime.status_message("Inserting Nums: " + text)
                result = dict(Command="insert_nums", args={"current" : current, "step" : step, "padding" : padding})
            elif text == "\i":
                History.save_history("insert_nums", "1 1 1", label="\i")
                sublime.status_message("Inserting #: " + text)
                result = dict(Command="insert_nums", args={"current" : "1", "step" : "1", "padding" : "1"})
            elif m2 or m3:
                m = None
                if m2: m = m2
                else: m = m3
                current = m.group(1)
                step = m.group(3)
                if not current: current = "1"
                if not step: step = "1"
                History.save_history("insert_nums", text=current + " " + step + " 1", label=text)
                sublime.status_message("Inserting #" + text)
                result = dict(Command="insert_nums", args={"current" : current, "step" : step, "padding" : "1"})
            elif text == "\\p":
                History.save_history("text_pastry_insert_text", text=sublime.get_clipboard(), label=text)
                sublime.status_message("Inserting from clipboard")
                result = dict(Command="text_pastry_insert_text", args={"text": sublime.get_clipboard()})
            elif m4:
                separator = m4.group(1)
                if not separator: separator = None
                History.save_history("text_pastry_insert_text", text=sublime.get_clipboard(), label=text, separator=separator)
                sublime.status_message("Inserting from clipboard with separator: " + str(separator))
                result = dict(Command="text_pastry_insert_text", args={"text": sublime.get_clipboard(), "separator": separator})
            elif text == "\\UUID":
                sublime.status_message("Inserting UUID")
                History.save_history("text_pastry_insert", text=text, label="Generate UUID")
                result = dict(Command="text_pastry_insert", args={"command": "uuid", "options": {"uppercase": True} })
            elif text == "\\uuid":
                sublime.status_message("Inserting UUID")
                History.save_history("text_pastry_insert", text=text, label="Generate uuid")
                result = dict(Command="text_pastry_insert", args={"command": "uuid"})
            else:
                sublime.status_message("Inserting " + text)
                result = dict(Command="text_pastry_insert_text", args={"text": text})
        else:
            pass
        return result

# ========================================
# paste.py
# ========================================
class TextPastryPasteCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        try:
            text = sublime.get_clipboard()
            if text is not None and len(text) > 0:
                regions = []
                sel = self.view.sel()
                items = text.split("\n")
                if len(items) == 1: items = [text];
                strip = True
                settings = sublime.load_settings("TextPastry.sublime-settings")
                for idx, region in enumerate(sel):
                    if idx < len(items):
                        row = items[idx].strip()
                        if region.empty():
                            sublime.status_message("empty")
                            row = self.view.substr(self.view.line(self.view.line(region).begin()-1)) + "\n"
                            i = 0
                            if len(row.strip()): i = self.view.insert(edit, region.end(), row)
                            regions.append( sublime.Region(region.end() + i, region.end() + i) )
                        else:
                            sublime.status_message("selection")
                            self.view.replace(edit, region, row)
                            i = len(row)
                            regions.append( sublime.Region(region.begin() + i, region.begin() + i) )
                sel.clear()
                for region in regions:
                    sel.add(region)
                    pass
            else:
                sublime.status_message("No text found for Insert Text, canceled")
        except ValueError:
            sublime.status_message("Error while executing Insert Text, canceled")
            pass

# ========================================
# redo.py
# ========================================
class TextPastryRedoCommand(sublime_plugin.WindowCommand):
    def run(self):
        hs = sublime.load_settings(TextPastryHistory.file_name)
        item = hs.get("last_command", {})
        if item and item.has_key("command") and item.has_key("text") and item["command"] and item["text"]:
            text = item.get("text").decode("unicode-escape").decode("string-escape")
            separator = item.get("separator", None)
            command = item.get("command", None)
            if text and command:
                sublime.status_message("Running last command")
                if command == "insert_nums":
                    (current, step, padding) = map(str, text.split(" "))
                    self.window.active_view().run_command(command, {"current": current, "step": step, "padding": padding})
                elif command == "text_pastry_insert_text":
                    self.window.active_view().run_command(command, {"text": text, "separator": separator})
                else:
                    pass

# ========================================
# insert_text.py
# ========================================
class TextPastryInsertTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, text=None, separator=None, clipboard=False):
        try:
            if True or text is not None and len(text) > 0:
                regions = []
                sel = self.view.sel()
                if separator: separator = separator.encode('utf8').decode("string-escape")
                if clipboard: text = sublime.get_clipboard()
                items = text.split(separator)
                strip = False
                settings = sublime.load_settings("TextPastry.sublime-settings")
                if separator == "\n" and settings.has("clipboard_strip_newline"): strip = settings.get("clipboard_strip_newline")
                last_region = None
                for idx, region in enumerate(sel):
                    if idx < len(items):
                        current = items[idx]
                        if (strip): current = current.strip()
                        self.view.replace(edit, region, current)
                    else:
                        regions.append(region)
                    last_region = region
                sel.clear()
                for region in regions:
                    sel.add(sublime.Region(region.begin(), region.end()))
                if not sel:
                    sel.add(sublime.Region(last_region.end(), last_region.end()))
            else:
                sublime.status_message("No text found for Insert Text, canceled")
        except ValueError:
            sublime.status_message("Error while executing Insert Text, canceled")
            pass

# ========================================
# insert_command.py
# ========================================
class TextPastryInsertCommand(sublime_plugin.TextCommand):
    def run(self, edit, command, options=None, items=None):
        try:
            cmd = Command.create(command, options)
            if items: cmd.set_items(items)
            if cmd:
                regions = []
                sel = self.view.sel()
                last_region = None
                for region in sel:
                    if cmd.has_next():
                        value = cmd.next()
                        self.view.replace(edit, region, value)
                    else:
                        regions.append(region)
                    last_region = region
                sel.clear()
                for region in regions:
                    sel.add(sublime.Region(region.begin(), region.end()))
                if not sel:
                    sel.add(sublime.Region(last_region.end(), last_region.end()))
            else:
                sublime.status_message("Command not found: " + cmd)
        except ValueError:
            sublime.status_message("Error while executing Text Pastry, canceled")
            pass

# ========================================
# show_command_line.py
# ========================================
class TextPastryShowCommandLine(sublime_plugin.WindowCommand):
    def run(self, text):
        if not self.window.active_view(): return
        v = self.window.show_input_panel('Enter a command or a list of words, separated by spaces', text, self.on_done, None, None)
    def on_done(self, text):
        parser = Parser()
        r = parser.parse(text)
        if r: self.window.active_view().run_command(r["Command"], r["args"])

# ========================================
# show_menu.py
# ========================================
class TextPastryShowMenu(sublime_plugin.WindowCommand):
    def show(self):
        self.overlay = Overlay()
        history = History.load_history()
        self.fill_with_history( history[0:5], self.overlay )
        x = selection_count = len( self.window.active_view().sel() )
        cb = sublime.get_clipboard()
        if len(history) > 5: self.overlay.addMenuItem( "history", "Show history" )
        self.overlay.addMenuItem( "\\i", "From 1 to {0}".format(x) )
        self.overlay.addMenuItem( "\\i0", "From 0 to " + str(x-1) )
        self.overlay.addMenuItem( "\\i(N,M)", "From N to X by M" )
        if cb: self.overlay.addMenuItem( "\\p(\\n)", "Paste Line from Clipboard" )
        if cb: self.overlay.addMenuItem( "\\p", "Paste Words from Clipboard" )
        self.overlay.addMenuItem( "words", "Word list separated by one space" )
        self.overlay.addSpacer( )
        self.overlay.addMenuItem( "clear_hist", "Clear history" )
        self.overlay.addMenuItem( "cancel", "Cancel" )
    def show_history_only(self):
        self.overlay = Overlay()
        history = History.load_history()
        self.fill_with_history( history, self.overlay )
        self.overlay.addMenuItem( "back", "Back" )
    def fill_with_history(self, history, overlay):
        for i, entry in enumerate(history):
            if not entry: continue
            command = entry.get("command", None)
            text = entry.get("text", None).decode("unicode-escape").decode("string-escape")
            separator = entry.get("separator", None)
            label = entry.get("label", None)
            if not label: label = text
            if text and command:
                self.overlay.addHistoryItem(command, label, text, separator)
    def run(self, history_only=False):
        if not self.window.active_view(): return
        sublime.status_message("ShowTextPastryOverlayCommand")
        try:
            selection_count = len(self.window.active_view().sel())
            if selection_count > 1 or True:
                if history_only:
                    self.show_history_only()
                else:
                    self.show()
                if self.overlay and self.overlay.is_valid():
                    self.window.show_quick_panel(self.overlay.all(), self.on_done, sublime.MONOSPACE_FONT)
            else:
                sublime.status_message("You need to make multiple selections to use Insert Text");
        except ValueError:
            sublime.status_message("Error while showing Insert Text overlay");
    def on_done(self, index):
        item = self.overlay.get(index)
        if not item == None and item.command:
            s = item.command
            sublime.status_message("command: " + s)
            if item.type == 2:
                sublime.status_message("redo history")
                command = item.command
                text = item.text
                separator = item.separator
                if command == "insert_nums":
                    sublime.status_message("insert_nums: " + text)
                    (current, step, padding) = map(str, text.split(" "))
                    self.window.active_view().run_command(command, {"current": current, "step": step, "padding": padding})
                elif command == "text_pastry_insert_text":
                    self.window.active_view().run_command(command, {"text": text, "separator": separator})
                else:
                    self.window.run_command("text_pastry_show_command_line", { "text": text })
            elif s == "history":
                self.window.run_command("hide_overlay")
                self.window.run_command("text_pastry_show_menu", {"history_only": True})
                return
            elif s == "clear_hist":
                History.clear_history()
            elif s == "back":
                self.window.run_command("hide_overlay")
                self.window.run_command("text_pastry_show_menu")
            elif s == "cancel":
                pass
            elif s == "\\p":
                cb = sublime.get_clipboard()
                if cb:
                    History.save_history("text_pastry_insert_text", text=cb, label=s)
                    self.window.active_view().run_command("text_pastry_insert_text", {"text": cb})
                else:
                    sublime.message_dialog("No Clipboard Data available")
            elif s == "\\p(\\n)":
                cb = sublime.get_clipboard()
                if cb:
                    History.save_history("text_pastry_insert_text", text=cb, label=s, separator="\\n")
                    self.window.active_view().run_command("text_pastry_insert_text", {"text": cb, "separator": "\\n"})
                else:
                    sublime.message_dialog("No Clipboard Data available")
            elif s == "\\i":
                History.save_history("insert_nums", text="1 1 1", label=s)
                self.window.active_view().run_command("insert_nums", {"current": "1", "step": "1", "padding": "1"})
            elif s == "\\i0":
                History.save_history("insert_nums", text="0 1 1", label=s)
                self.window.active_view().run_command("insert_nums", {"current": "0", "step": "1", "padding": "1"})
            elif s == "words":
                sublime.status_message("words")
                self.window.run_command("text_pastry_show_command_line", { "text": "" })
            elif len(s):
                self.window.run_command("text_pastry_show_command_line", { "text": s })
            else:
                sublime.status_message("Unknown command: " + s)
        else:
            sublime.status_message("No item selected")


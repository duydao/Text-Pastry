import sublime, sublime_plugin, re, operator

# ========================================
# history.py
# ========================================
from datetime import datetime
class History:
    FILENAME = "TextPastryHistory.sublime-settings"
    @staticmethod
    def save_history(command, text, separator=None, label=None):
        hs = sublime.load_settings(History.FILENAME)
        history = hs.get("history", {})
        text = text.encode('unicode-escape')
        key = str(hash(text+str(separator)))
        if key in history: del history[key]
        history[key] = dict(command=command, text=text, separator=separator, date=str(datetime.now()), label=label)
        hs.set("history", history)
        # last command
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
            sorted_x = sorted(entries, key=operator.itemgetter("date"), reverse=True)
        except:
            sorted_x = entries
            pass
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
                #History.save_history("text_pastry_insert_text", text, separator)
                items = text.split(separator)
                strip = False
                settings = sublime.load_settings("TextPastry.sublime-settings")
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
            #if item.text: entries.append( [item.format(width, idx), item.formatText(width)] )
            #else: entries.append( [item.format(width, idx)] )
            entries.append( [item.format(width, idx)] )
        return entries
    def is_valid(self):
        return self.items and len(self.items) > 0
    def length(self):
        return len(self.items)
class Item:
    def __init__(self, command=None, label=None, text=None, separator=None):
        self.command = command
        self.label = label
        self.text = text
        self.separator = separator
    def format(self, width, index):
        pass
class MenuItem(Item):
    def format(self, width, index):
        return self.command.ljust(width).rjust(width + 1) + self.label
class HistoryItem(Item):
    def format(self, width, index):
        i = str(index + 1)
        s = ('hist' + i).ljust(width).rjust(width + 1)
        text = self.text
        #s += ' '.join((self.label + " " + text).split())
        s += self.label
        return s
    def formatText(self, width):
        text = self.text
        if text and len(text) > 50: text = text[0:50] + "..."
        return ' '.ljust(width + 1).rjust(width + 2) + ' '.join((text).split())
class SpacerItem(Item):
    def format(self, width, index):
        return ""

# ========================================
# parser.py
# ========================================
class Parser:
    def Parser():
        sublime.status_message("Creating CommandLineParser")
    def parse(self, text):
        result = None
        if not text: return None
        # start pasing the command string
        if text:
            m1 = re.compile('(-?\d+) (-?\d+) (\d+)').match(text)
            m2 = re.compile('\\\\i(\d*)(,(-?\d+))?').match(text)
            m3 = re.compile('\\\\i\((\d*)(,(-?\d+))?\)').match(text)
            m4 = re.compile('\\\\p\((.*?)\)').match(text)
            if m1:
                (current, step, padding) = map(str, text.split(" "))
                History.save_history("insert_nums", text)
                sublime.status_message("Inserting Nums: " + text)
                result = dict(Command="insert_nums", args={"current" : current, "step" : step, "padding" : padding})
            elif m2 or m3:
                m = None
                if m2: m = m2
                else: m = m3
                current = m.group(1)
                step = m.group(3)
                if not current: current = "1"
                if not step: step = "1"
                History.save_history("insert_nums", text)
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
            else:
                sublime.status_message("Inserting " + text)
                result = dict(Command="text_pastry_insert_text", args={"text": text})
        else:
            pass
        return result

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
                    #self.window.run_command("text_pastry_show_command_line", { "text": text })
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
            if not label: label = command
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
            if s == "redo_hist":
                sublime.status_message("redo history")
                command = item.command
                text = item.text
                separator = item.separator
                if command == "insert_nums":
                    (current, step, padding) = map(str, text.split(" "))
                    self.window.active_view().run_command(command, {"current": current, "step": step, "padding": padding})
                elif command == "text_pastry_insert_text":
                    self.window.active_view().run_command(command, {"text": text, "separator": separator})
                else:
                    self.window.run_command("text_pastry_show_command_line", { "text": text })
            elif s == "history":
                self.window.run_command("hide_overlay")
                self.window.run_command("show_text_pastry_overlay", {"history_only": True})
                return
            elif s == "clear_hist":
                History.clear_history()
            elif s == "back":
                self.window.run_command("hide_overlay")
                self.window.run_command("show_text_pastry_overlay")
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
                self.window.run_command("show_text_pastry", { "text": "" })
            elif len(s):
                self.window.run_command("show_text_pastry", { "text": s })
            else:
                sublime.status_message("Unknown command: " + s)
        else:
            sublime.status_message("No item selected")


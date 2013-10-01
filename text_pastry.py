import sublime, sublime_plugin, re, operator, time, uuid
# ========================================
# history.py
# ========================================
class History:
    FILENAME = "TextPastryHistory.sublime-settings"
    @staticmethod
    def save_history(command, text, separator=None, label=None):
        global_settings = sublime.load_settings("TextPastry.sublime-settings")
        enabled = global_settings.get("history_enabled", False)
        if not enabled: return []
        hs = sublime.load_settings(History.FILENAME)
        history = hs.get("history", {})
        key = str(hash(text+str(separator)))
        if key in history: del history[key]
        timestamp = time.time()
        history[key] = dict(command=command, text=text, separator=separator, date=timestamp, label=label)
        hs.set("history", history)
        hs.set("last_command", dict(key=key, command=command, text=text, separator=separator, index=len(history), label=label))
        sublime.save_settings(History.FILENAME)
    @staticmethod
    def load_history():
        global_settings = sublime.load_settings("TextPastry.sublime-settings")
        enabled = global_settings.get("history_enabled", False)
        if not enabled: return []
        hs = sublime.load_settings(History.FILENAME)
        history = hs.get("history", {})
        entries = []
        for key, item in history.items():
            command = None
            text = None
            separator = None
            if "command" in item and "text" in item and item["command"] and item["text"]:
                entries.append(item)
            else:
                History.remove_history(key)
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
        if id in history:
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
        min_spacing = 2
        width = 12
        for item in self.items:
            if item.type != 3 and len(item.command) > (width - min_spacing):
                width = len(item.command) + min_spacing
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
    def init(self, view, items=None):
        if items: self.stack = items
    def previous(self):
        return self.stack[self.counter-1]
    def current(self):
        return text[self.counter]
    def next(self):
        val = self.stack[self.counter]
        self.counter += 1
        return val
    def has_next(self):
        return (self.counter) < len(self.stack)
    @staticmethod
    def create(cmd, items=None, options=None):
        command_list = {
            "uuid": UUIDCommand,
            "backreference": BackreferenceCommand
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
class BackreferenceCommand(Command):
    def init(self, view, items=None):
        selections = []
        if view.sel(): 
            for region in view.sel():
                selections.append( view.substr(region) )
        values = []
        for idx, index in enumerate(map(int, items)):
            if idx >= len(selections): break;
            i = index - 1
            if i >= 0 and i < len(selections):
                values.append( selections[i] )
            else:
                values.append( None )
        for idx, value in enumerate(selections):
            if len(values) + 1 < idx:
                values.append(value)
        self.stack = values

# ========================================
# parser.py
# ========================================
class Parser:
    def parse(self, text):
        result = None
        if not text: return None
        if text:
            m1 = re.compile('(-?\d+) (-?\d+) (\d+)$').match(text)
            m2 = re.compile('\\\\i(-?\d+)(,(-?\d+))?').match(text)
            m3 = re.compile('\\\\i\((-?\d+)(,(-?\d+))?').match(text)
            m4 = re.compile('\\\\p\((.*?)\)$').match(text)
            m5 = re.compile('^(\$\d+\s?)+$').match(text)
            m6 = re.compile('\\\\r\((.*?)\)$').match(text)
            m7 = re.compile('\\\\r (.*)').match(text)
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
                result = dict(Command="text_pastry_insert_text", args={"text": sublime.get_clipboard(), "clipboard": True})
            elif m4:
                separator = m4.group(1)
                if not separator: separator = None
                History.save_history("text_pastry_insert_text", text=sublime.get_clipboard(), label=text, separator=separator)
                sublime.status_message("Inserting from clipboard with separator: " + str(separator))
                result = dict(Command="text_pastry_insert_text", args={"text": sublime.get_clipboard(), "separator": separator, "clipboard": True})
            elif m6 or m7:
                if (m6): separator = m6.group(1)
                else: separator = m7.group(1)
                if not separator: separator = None
                History.save_history("text_pastry_insert_text", text=sublime.get_clipboard(), label=text, separator=separator)
                sublime.status_message("Inserting from clipboard with separator: " + str(separator))
                result = dict(Command="text_pastry_insert_text", args={"text": sublime.get_clipboard(), "separator": separator, "clipboard": True, "regex": True})
            elif text == "\\UUID":
                sublime.status_message("Inserting UUID")
                History.save_history("text_pastry_insert", text=text, label="Generate UUID")
                result = dict(Command="text_pastry_insert", args={"command": "uuid", "options": {"uppercase": True} })
            elif text == "\\uuid":
                sublime.status_message("Inserting UUID")
                History.save_history("text_pastry_insert", text=text, label="Generate uuid")
                result = dict(Command="text_pastry_insert", args={"command": "uuid"})
            elif m5:
                items = ','.join(filter(None, map(lambda x: x.strip(), text.split("$"))))
                result = dict(Command="text_pastry_insert", args={"command": "backreference", "text": items, "separator": ","})
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
        if item and "command" in item and "text" in item and item["command"] and item["text"]:
            text = item.get("text")
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
    def run(self, edit, text=None, separator=None, clipboard=False, items=None, regex=False):
        try:
            regions = []
            sel = self.view.sel()
            if separator: separator = separator.encode('utf8').decode("unicode-escape")
            if clipboard: text = sublime.get_clipboard()
            if text:
                if regex: items = re.split(separator, text)
                else: items = text.split(separator)
            if items:
                strip = False
                settings = sublime.load_settings("TextPastry.sublime-settings")
                if separator == "\n" and settings.has("clipboard_strip_newline"): strip = settings.get("clipboard_strip_newline")
                repeat = True
                if clipboard and settings.has("repeat_clipboard"):
                    repeat = settings.get("repeat_clipboard")
                elif settings.has("repeat_words"):
                    repeat = settings.get("repeat_words")
                if repeat and items:
                    while (len(items) < len(sel)): 
                        items.extend(items)
                last_region = None
                for idx, region in enumerate(sel):
                    if idx < len(items):
                        current = items[idx]
                        if (strip): current = current.strip()
                        self.view.replace(edit, region, current)
                    else:
                        regions.append(region)
                    last_region = region
                if not settings.get("keep_selection", False):
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
    def run(self, edit, command, options=None, text=None, separator=None):
        try:
            cmd = Command.create(command, options)
            if cmd:
                items = None
                if text: items = text.split(separator)
                cmd.init(self.view, items)
                regions = []
                sel = self.view.sel()
                last_region = None
                for region in sel:
                    if cmd.has_next():
                        value = cmd.next()
                        if value is not None:
                            self.view.replace(edit, region, value)
                            regions.append(region)
                    else:
                        break
                for region in regions:
                    sel.subtract(region)
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
        self.fill_with_history( history[:3], self.overlay )
        if len(history) > 0: self.overlay.addSpacer( )
        x = selection_count = len( self.window.active_view().sel() )
        self.overlay.addMenuItem( "\\i", "From 1 to {0}".format(x) )
        self.overlay.addMenuItem( "\\i0", "From 0 to " + str(x-1) )
        self.overlay.addMenuItem( "\\i(N,M)", "From N to X by M" )
        self.overlay.addSpacer( )
        cb = sublime.get_clipboard()
        if cb: self.overlay.addMenuItem( "\\p(\\n)", "Lines from clipboard" )
        if cb: self.overlay.addMenuItem( "\\p", "Words from clipboard" )
        self.overlay.addMenuItem( "words", "Enter word list" )
        self.overlay.addSpacer( )
        if len(history) > 0: self.overlay.addMenuItem( "history", "Show history" )
        self.overlay.addMenuItem( "settings", "Show settings" )
        self.overlay.addMenuItem( "cancel", "Cancel" )
    def show_history(self):
        self.overlay = Overlay()
        history = History.load_history()
        self.fill_with_history( history, self.overlay )
        self.overlay.addSpacer( )
        self.overlay.addMenuItem( "clear_hist", "Clear history" )
        self.overlay.addMenuItem( "back", "Back to menu" )
    def show_settings(self):
        self.overlay = Overlay()
        settings = sublime.load_settings("TextPastry.sublime-settings")
        repeat_words = settings.get("repeat_words", False)
        repeat_clipboard = settings.get("repeat_clipboard", False)
        strip_newline = settings.get("clipboard_strip_newline", False)
        keep_selection = settings.get("keep_selection", False)
        self.overlay.addMenuItem( "repeat_words", "Repeat words" + self.enabled_string(repeat_words) )
        self.overlay.addMenuItem( "repeat_clipboard", "Repeat clipboard" + self.enabled_string(repeat_clipboard) )
        self.overlay.addMenuItem( "strip_newline", "Remove newline" + self.enabled_string(strip_newline) )
        self.overlay.addMenuItem( "keep_selection", "Keep selection" + self.enabled_string(keep_selection) )
        self.overlay.addSpacer( )
        self.overlay.addMenuItem( "back", "Back to menu" )
    def enabled_string(self, enabled):
        s = " (disabled)"
        if enabled: s = " (enabled)"
        return s
    def fill_with_history(self, history, overlay):
        for i, entry in enumerate(history):
            if not entry: continue
            command = entry.get("command", None)
            text = entry.get("text", None)
            separator = entry.get("separator", None)
            label = entry.get("label", None)
            if not label: label = text
            if text and command:
                self.overlay.addHistoryItem(command, label, text, separator)
    def run(self, show_history=False, show_settings=False):
        if not self.window.active_view(): return
        sublime.status_message("ShowTextPastryOverlayCommand")
        try:
            selection_count = len(self.window.active_view().sel())
            if selection_count > 1 or True:
                if show_history:
                    self.show_history()
                elif show_settings:
                    self.show_settings()
                else:
                    self.show()
                if self.overlay and self.overlay.is_valid():
                    self.show_quick_panel(self.overlay.all(), self.on_done, sublime.MONOSPACE_FONT)
            else:
                sublime.status_message("You need to make multiple selections to use Text Pastry");
        except ValueError:
            sublime.status_message("Error while showing Text Pastry overlay");
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
                self.window.run_command("text_pastry_show_menu", {"show_history": True})
                return
            elif s == "settings":
                self.window.run_command("hide_overlay")
                self.window.run_command("text_pastry_show_menu", {"show_settings": True})
                return
            elif s == "repeat_words":
                self.window.run_command("hide_overlay")
                settings = sublime.load_settings("TextPastry.sublime-settings")
                enabled = not settings.get("repeat_words", False)
                settings.set("repeat_words", enabled)
                sublime.save_settings("TextPastry.sublime-settings")
                return
            elif s == "repeat_clipboard":
                self.window.run_command("hide_overlay")
                settings = sublime.load_settings("TextPastry.sublime-settings")
                enabled = not settings.get("repeat_clipboard", False)
                settings.set("repeat_clipboard", enabled)
                sublime.save_settings("TextPastry.sublime-settings")
                return
            elif s == "strip_newline":
                self.window.run_command("hide_overlay")
                settings = sublime.load_settings("TextPastry.sublime-settings")
                enabled = not settings.get("clipboard_strip_newline", False)
                settings.set("clipboard_strip_newline", enabled)
                sublime.save_settings("TextPastry.sublime-settings")
                return
            elif s == "keep_selection":
                self.window.run_command("hide_overlay")
                settings = sublime.load_settings("TextPastry.sublime-settings")
                enabled = not settings.get("keep_selection", False)
                settings.set("keep_selection", enabled)
                sublime.save_settings("TextPastry.sublime-settings")
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
                    self.window.active_view().run_command("text_pastry_insert_text", {"text": cb, "clipboard": True})
                else:
                    sublime.message_dialog("No Clipboard Data available")
            elif s == "\\p(\\n)":
                cb = sublime.get_clipboard()
                if cb:
                    History.save_history("text_pastry_insert_text", text=cb, label=s, separator="\\n")
                    self.window.active_view().run_command("text_pastry_insert_text", {"text": cb, "separator": "\\n", "clipboard": True})
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
    def show_quick_panel(self, items, on_done, flags):
        # Sublime 3 does not allow calling show_quick_panel from on_done, so we need to set a timeout here.
        sublime.set_timeout(lambda: self.window.show_quick_panel(items, on_done, flags), 10)

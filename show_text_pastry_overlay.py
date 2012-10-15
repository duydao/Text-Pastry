import sublime, sublime_plugin, re
#from text_pastry_history import * as TextPastryHistory
from text_pastry_history import TextPastryHistory

class ShowTextPastryOverlayCommand(sublime_plugin.WindowCommand):

    def show(self):
        self.overlay = Overlay()
        history = TextPastryHistory.load_history()
        self.fill_with_history( history[0:5], self.overlay )

        x = selection_count = len( self.window.active_view().sel() )
        
        self.overlay.addMenuItem( "history", "Show history" )
        self.overlay.addMenuItem( "\\i", "From 1 to " + str(x) )
        self.overlay.addMenuItem( "\\i0", "From 0 to " + str(x-1) )
        self.overlay.addMenuItem( "\\i(N,M)", "From N to X by M" )
        self.overlay.addMenuItem( "\\p(\\n)", "Paste Line from Clipboard" )
        self.overlay.addMenuItem( "\\p", "Paste Words from Clipboard" )
        self.overlay.addMenuItem( "words", "Word list separated by one space" )
        self.overlay.addMenuItem( "clear_hist", "Clear history" )
        self.overlay.addMenuItem( "cancel", "Cancel" )

    def show_history_only(self):
        self.overlay = Overlay()
        history = TextPastryHistory.load_history()
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
        if not item == None:
            s = item.command

            sublime.status_message(s)
            if s == "redo_hist":
                sublime.status_message("redo history")
                command = item.command
                text = item.text
                separator = item.separator

                if command == "insert_nums":
                    (current, step, padding) = map(str, text.split(" "))
                    self.window.active_view().run_command(command, {"current": current, "step": step, "padding": padding})

                elif command == "insert_text":
                    self.window.active_view().run_command(command, {"text": text, "separator": separator})

                else:
                    self.window.run_command("prompt_insert_text", { "text": text })

            elif s == "history":
                self.window.run_command("hide_overlay")
                self.window.run_command("show_text_pastry_overlay", {"history_only": True})
                return

            elif s == "clear_hist":
                TextPastryHistory.clear_history()

            elif s == "back":
                self.window.run_command("hide_overlay")
                self.window.run_command("show_text_pastry_overlay")

            elif s == "cancel":
                pass

            elif s == "\\p":
                self.window.active_view().run_command("insert_text", {"text": sublime.get_clipboard()})

            elif s == "\\p":
                TextPastryHistory.save_history("insert_text", text=sublime.get_clipboard(), label=s)
                self.window.active_view().run_command("insert_text", {"text": sublime.get_clipboard()})

            elif s == "\\p(\\n)":
                TextPastryHistory.save_history("insert_text", text=sublime.get_clipboard(), label=s)
                self.window.active_view().run_command("insert_text", {"text": sublime.get_clipboard(), "separator": "\\n"})

            elif s == "\\i":
                TextPastryHistory.save_history("insert_nums", text="1 1 1", label=s)
                self.window.active_view().run_command("insert_nums", {"current": "1", "step": "1", "padding": "1"})

            elif s == "\\i0":
                TextPastryHistory.save_history("insert_nums", text="0 1 1", label=s)
                self.window.active_view().run_command("insert_nums", {"current": "0", "step": "1", "padding": "1"})

            elif len(s):
                self.window.run_command("prompt_insert_text", { "text": s })

            else:
                sublime.status_message("Unknown command: " + s)

        else:
            sublime.status_message("No item selected")

class Item:
    def __init__(self):
        pass
    def format(self, width, index):
        pass

class MenuItem(Item):
    def __init__(self, command, label, text=None):
        self.command = command
        self.label = label
        self.text = text

    def format(self, width, index):
        return self.command.ljust(width) + self.label

class HistoryItem(Item):
    def __init__(self, command=None, label=None, text=None, separator=None):
        self.command = command
        self.label = label
        self.text = text
        self.separator = separator
    
    def format(self, width, index):
        i = str(index + 1)
        s = ('hist' + i).ljust(width)
        text = self.text
        if text and len(text) > 50: text = text[0:50] + "..."
        else: text = ""
        s += ' '.join((self.label + " " + text).split())

        return s

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

    def addHistoryItem(self, command, label, text, separator):
        item = HistoryItem(command, label)
        if command and text:
            self.items.append( item )
        return item

    def get(self, index):
        item = None
        if index >= 0 and index < len(self.items): item = self.items[index]
        return item

    def all(self):
        entries = []

        width = 9

        for idx, item in enumerate(self.items):
            if item.text: entries.append( item.format(width, idx), item.text )
            else: entries.append( item.format(width, idx) )

        return entries

    def is_valid(self):
        return self.items and len(self.items) > 0

    def length(self):
        return len(self.items)

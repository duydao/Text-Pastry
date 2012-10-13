import sublime, sublime_plugin, re
#from text_pastry_history import * as TextPastryHistory
from text_pastry_history import TextPastryHistory

class ShowTextPastryOverlayCommand(sublime_plugin.WindowCommand):
    def run(self, show_history_only=False):
        sublime.status_message("ShowTextPastryOverlayCommand")
        try:
            selection_count = len(self.window.active_view().sel())

            if selection_count > 1 or True:
                self.items = []

                entries = TextPastryHistory.load_history()
                if not show_history_only: entries = entries[0:5]
                
                history_items = []
                for i, entry in enumerate(entries):
                    command = entry.get("command", None)
                    text = entry.get("text", None).decode("unicode-escape").decode("string-escape")
                    separator = entry.get("separator", None)
                    label = entry.get("label", None)
                    if not label: label = ""

                    if text and command:
                        self.items.append(["redo_hist", command, text, separator])

                        s = ('hist' + str(i + 1)).ljust(9)
                        if len(text) > 50: text = text[0:50] + "..."
                        s += ' '.join((label + " " + text).split())
                        history_items.append(s)


                if show_history_only:
                    default_items = [
                        ["back", "Back"]
                    ]
                else:
                    x = selection_count
                    default_items = [
                        ["show_hist", "Show history entries"],
                        ["\\i", "From 1 to " + str(x)],
                        ["\\i0", "From 0 to " + str(x-1)],
                        ["\\i(N,M)", "From N to X by M"],
                        ["\\p(\\n)", "Paste Line from Clipboard"],
                        ["\\p", "Paste Words from Clipboard"],
                        ["words", "Word list separated by one space"],
                        ["clear_hist", "Clear history"],
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
            if s == "redo_hist":
                sublime.status_message("redo history")
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

            elif s == "show_hist":
                self.window.run_command("hide_overlay")
                self.window.run_command("show_text_pastry_overlay", {"show_history_only": True})
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

import sublime, sublime_plugin
from text_pastry_history import TextPastryHistory

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

                elif command == "insert_text":
                    self.window.active_view().run_command(command, {"text": text, "separator": separator})

                else:
                    #self.window.run_command("prompt_insert_text", { "text": text })
                    pass

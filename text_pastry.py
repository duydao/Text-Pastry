import sublime, sublime_plugin, re
from text_pastry_history import *
from command_line_parser import CommandLineParser

class ShowTextPastryCommand(sublime_plugin.WindowCommand):

    def run(self, text):
        v = self.window.show_input_panel('Enter a list of items, separated by spaces', text, self.on_done, None, None)

    def on_done(self, text):
        parser = CommandLineParser()
        r = parser.parse(text)
        if r: self.window.active_view().run_command(r["command"], r["args"])

class InsertTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, text=None, separator=None, clipboard=False):
        try:
            if True or text is not None and len(text) > 0:
                regions = []
                sel = self.view.sel()

                if separator: separator = separator.encode('utf8').decode("string-escape")
                if clipboard: text = sublime.get_clipboard()

                TextPastryHistory.save_history("insert_text", text, separator)
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

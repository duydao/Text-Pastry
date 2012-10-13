import sublime, sublime_plugin, re
from text_pastry_history import *
from command_line_parser import CommandLineParser

class PromptTextPastryCommand(sublime_plugin.WindowCommand):

    def run(self, text):
        v = self.window.show_input_panel('Enter a list of items, separated by spaces', text, self.on_done, None, None)
        self.clp = CommandLineParser()

    def on_done(self, text):
        try:
            if self.window.active_view() and text:
                m1 = re.compile('(-?\d+) (-?\d+) (\d+)').match(text)
                m2 = re.compile('\\\\i(\d*)(,(-?\d+))?').match(text)
                m3 = re.compile('\\\\i\((\d*)(,(-?\d+))?\)').match(text)

                m4 = re.compile('\\\\p\((.*?)\)').match(text)
                if m1:
                    (current, step, padding) = map(str, text.split(" "))

                    TextPastryHistory.save_history("insert_nums", text)
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

                    TextPastryHistory.save_history("insert_nums", text)
                    sublime.status_message("Inserting #" + text)
                    self.window.active_view().run_command("insert_nums", {"current" : current, "step" : step, "padding" : "1"})
                
                elif text == "\\p":
                    TextPastryHistory.save_history("insert_text", text=sublime.get_clipboard(), label=text)
                    sublime.status_message("Inserting from clipboard")
                    self.window.active_view().run_command("insert_text", {"text": sublime.get_clipboard()})
                
                elif m4:
                    separator = m4.group(1)
                    if not separator: separator = None

                    TextPastryHistory.save_history("insert_text", text=sublime.get_clipboard(), label=text, separator=separator)
                    sublime.status_message("Inserting from clipboard with separator: " + str(separator))
                    self.window.active_view().run_command("insert_text", {"text": sublime.get_clipboard(), "separator": separator})
                
                else:
                    sublime.status_message("Inserting " + text)
                    self.window.active_view().run_command("insert_text", {"text": text})

        except ValueError:
            pass


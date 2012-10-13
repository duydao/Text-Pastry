import sublime, sublime_plugin, re
from text_pastry_history import *
from command_line_parser import CommandLineParser

class PromptTextPastryCommand(sublime_plugin.WindowCommand):

    def run(self, text):
        v = self.window.show_input_panel('Enter a list of items, separated by spaces', text, self.on_done, None, None)

    def on_done(self, text):
        parser = CommandLineParser()
        r = parser.parse(text)
        if r: self.window.active_view().run_command(r["command"], r["args"])

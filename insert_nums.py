import sublime, sublime_plugin

class PromptInsertNumsCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.window.show_input_panel('Enter a starting number, step, and padded width', '1 1 1', self.on_done, None, None)
        pass

    def on_done(self, text):
        try:
            (current, step, padding) = map(str, text.split(" "))
            if self.window.active_view():
                self.window.active_view().run_command("insert_nums", {"current" : current, "step" : step, "padding" : padding} )
        except ValueError:
            pass

class InsertNumsCommand(sublime_plugin.TextCommand):

    def run(self, edit, current, step, padding):
        current = int(current)
        sel = self.view.sel()
        for region in sel:
            sublime.status_message("Inserting #" + str(current))
            self.view.replace(edit, region, format(current, "0" + padding + "d"))
            current = current + int(step)
        for region in sel:
            sel.subtract(region)
            sel.add(sublime.Region(region.end(), region.end()))

import sublime, sublime_plugin

class PromptInsertTextCommand(sublime_plugin.WindowCommand):
    def run(self):
        self.window.show_input_panel('Enter a list of items, separated by spaces', '', self.on_done, None, None)
        pass

    def on_done(self, text):
        try:
            if self.window.active_view():
                self.window.active_view().run_command("insert_text", {"text": text})
        except ValueError:
            pass

class InsertTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        sel = self.view.sel()

        items = text.split()
        regions = []
        
        for idx, region in enumerate(sel):
            if idx < len(items):
                current = items[idx]
                sublime.status_message("Inserting #" + current)
                self.view.replace(edit, region, current)
            else:
                regions.append(region)

        sel.clear()

        for region in regions:
            sel.add(sublime.Region(region.begin(), region.end()))

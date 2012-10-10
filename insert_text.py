import sublime, sublime_plugin, re

class PromptInsertTextCommand(sublime_plugin.WindowCommand):

    def run(self):
        self.window.show_input_panel('Enter a list of items, separated by spaces', '', self.on_done, None, None)
        pass

    def on_done(self, text):
        try:
            if self.window.active_view():
                m1 = re.compile('(-?\d+) (-?\d+) (-?\d+)').match(text)
                m2 = re.compile('\\\\i(\d*)(,(-?\d+))?').match(text)
                m3 = re.compile('\\\\i\((\d*)(,(-?\d+))?\)').match(text)

                if m1:
                    sublime.status_message("Inserting Nums: " + text)
                    (current, step, padding) = map(str, text.split(" "))

                    self.window.active_view().run_command("insert_nums", {"current" : current, "step" : step, "padding" : padding})
                elif m2 or m3:
                    m = None
                    if m2: m = m2
                    else: m = m3
                    current = m.group(1)
                    step = m.group(3)

                    if current is None or len(current) == 0: current = "1"
                    if step is None or len(step) == 0: step = "1"

                    sublime.status_message("Inserting #" + step)
                    self.window.active_view().run_command("insert_nums", {"current" : current, "step" : step, "padding" : "1"})
                elif text == "\\p":
                    sublime.status_message("Inserting from clipboard")
                    self.window.active_view().run_command("insert_text", {"text": sublime.get_clipboard()})
                else:
                    sublime.status_message("Inserting " + text)
                    self.window.active_view().run_command("insert_text", {"text": text})

        except ValueError:
            pass

class InsertTextCommand(sublime_plugin.TextCommand):

    def run(self, edit, text):
        regions = []
        sel = self.view.sel()
        items = text.split()
        
        for idx, region in enumerate(sel):
            if idx < len(items):
                current = items[idx]
                #sublime.status_message("Inserting #" + current)
                self.view.replace(edit, region, current)
            else:
                regions.append(region)

        sel.clear()

        for region in regions:
            sel.add(sublime.Region(region.begin(), region.end()))

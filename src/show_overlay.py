import sublime, sublime_plugin, re, history, overlay
class ShowTextPastryOverlay(sublime_plugin.WindowCommand):

    def show(self):
        self.overlay = Overlay()
        history = History.load_history()
        self.fill_with_history( history[0:5], self.overlay )

        x = selection_count = len( self.window.active_view().sel() )
        cb = sublime.get_clipboard()
        
        if len(history) > 5: self.overlay.addMenuItem( "history", "Show history" )
        self.overlay.addMenuItem( "\\i", "From 1 to {0}".format(x) )
        self.overlay.addMenuItem( "\\i0", "From 0 to " + str(x-1) )
        self.overlay.addMenuItem( "\\i(N,M)", "From N to X by M" )

        if cb: self.overlay.addMenuItem( "\\p(\\n)", "Paste Line from Clipboard" )
        if cb: self.overlay.addMenuItem( "\\p", "Paste Words from Clipboard" )
        self.overlay.addMenuItem( "words", "Word list separated by one space" )
        self.overlay.addSpacer( )
        self.overlay.addMenuItem( "clear_hist", "Clear history" )
        self.overlay.addMenuItem( "cancel", "Cancel" )

    def show_history_only(self):
        self.overlay = Overlay()
        history = History.load_history()
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
        if not self.window.active_view(): return
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
        if not item == None and item.command:
            s = item.command

            sublime.status_message("command: " + s)
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
                History.clear_history()

            elif s == "back":
                self.window.run_command("hide_overlay")
                self.window.run_command("show_text_pastry_overlay")

            elif s == "cancel":
                pass

            elif s == "\\p":
                cb = sublime.get_clipboard()
                if cb:
                    History.save_history("insert_text", text=cb, label=s)
                    self.window.active_view().run_command("insert_text", {"text": cb})
                else:
                    sublime.message_dialog("No Clipboard Data available")

            elif s == "\\p(\\n)":
                cb = sublime.get_clipboard()
                if cb:
                    History.save_history("insert_text", text=cb, label=s, separator="\\n")
                    self.window.active_view().run_command("insert_text", {"text": cb, "separator": "\\n"})
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
                self.window.run_command("show_text_pastry", { "text": "" })

            elif len(s):
                self.window.run_command("show_text_pastry", { "text": s })

            else:
                sublime.status_message("Unknown command: " + s)

        else:
            sublime.status_message("No item selected")

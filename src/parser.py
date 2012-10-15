import sublime, sublime_plugin, re

class Parser:
    def Parser():
        sublime.status_message("Creating CommandLineParser")

    def parse(text):
        if not text:
            return None
        result = None

        # start pasing the command string
        if text:

            m1 = re.compile('(-?\d+) (-?\d+) (\d+)').match(text)
            m2 = re.compile('\\\\i(\d*)(,(-?\d+))?').match(text)
            m3 = re.compile('\\\\i\((\d*)(,(-?\d+))?\)').match(text)

            m4 = re.compile('\\\\p\((.*?)\)').match(text)
            if m1:
                (current, step, padding) = map(str, text.split(" "))

                History.save_history("insert_nums", text)
                sublime.status_message("Inserting Nums: " + text)
                result = dict(Command="insert_nums", args={"current" : current, "step" : step, "padding" : padding})

            elif m2 or m3:
                m = None
                if m2: m = m2
                else: m = m3
                current = m.group(1)
                step = m.group(3)

                if not current: current = "1"
                if not step: step = "1"

                History.save_history("insert_nums", text)
                sublime.status_message("Inserting #" + text)
                result = dict(Command="insert_nums", args={"current" : current, "step" : step, "padding" : "1"})

            elif text == "\\p":
                History.save_history("insert_text", text=sublime.get_clipboard(), label=text)
                sublime.status_message("Inserting from clipboard")
                result = dict(Command="insert_text", args={"text": sublime.get_clipboard()})

            elif m4:
                separator = m4.group(1)
                if not separator: separator = None

                History.save_history("insert_text", text=sublime.get_clipboard(), label=text, separator=separator)
                sublime.status_message("Inserting from clipboard with separator: " + str(separator))
                result = dict(Command="insert_text", args={"text": sublime.get_clipboard(), "separator": separator})
            
            else:
                sublime.status_message("Inserting " + text)
                result = dict(Command="insert_text", args={"text": text})
        else:
            pass
        
        return None
import sublime, sublime_plugin, operator
from datetime import datetime

class History:
    FILENAME = "TextPastryHistory.sublime-settings"
    
    @staticmethod
    def save_history(command, text, separator=None, label=None):
        hs = sublime.load_settings(History.FILENAME)
        history = hs.get("history", {})
        text = text.encode('unicode-escape')

        key = str(hash(text+str(separator)))
        if key in history: del history[key]
        history[key] = dict(command=command, text=text, separator=separator, date=str(datetime.now()), label=label)

        hs.set("history", history)

        # last command
        hs.set("last_command", dict(key=key, command=command, text=text, separator=separator, index=len(history), label=label))

        sublime.save_settings(History.FILENAME)

    @staticmethod
    def load_history():
        sublime.status_message("history loaded")
        hs = sublime.load_settings(History.FILENAME)
        history = hs.get("history", {})

        entries = []
        for key, item in history.iteritems():
            command = None
            text = None
            separator = None

            if item.has_key("command") and item.has_key("text") and item["command"] and item["text"]:
                entries.append(item)
            else:
                InsertTextHistory.remove_history(key)

        try:
            sorted_x = sorted(entries, key=operator.itemgetter("date"), reverse=True)
        except:
            sorted_x = entries
            pass

        sublime.status_message("history loaded")
        return sorted_x

    @staticmethod
    def remove_history(id):
        removed = False
        hs = sublime.load_settings(History.FILENAME)
        history = hs.get("history", {})

        sublime.status_message("Deleting item from history: " + str(id))

        if history.has_key(id):
            del history[id]
            hs.set("history", history)
            sublime.save_settings(History.FILENAME)
            removed = True

        return removed

    @staticmethod
    def clear_history():
        hs = sublime.load_settings(History.FILENAME)
        history = hs.set("history", {})
        sublime.save_settings(History.FILENAME)
        sublime.status_message("History deleted")

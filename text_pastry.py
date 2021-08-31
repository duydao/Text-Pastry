import sublime
import sublime_plugin
import re
import operator
import datetime
import time
import uuid
import subprocess
import tempfile
import os
import json
import sys
import hashlib
import shlex
import unittest
import itertools
from os.path import expanduser, normpath, join, isfile
from decimal import *


SETTINGS_FILE = "TextPastry.sublime-settings"


def is_numeric(s):
    if s is None:
        return False
    try:
        int(s)
        return True
    except ValueError:
        return False
def settings():
    return sublime.load_settings(SETTINGS_FILE)
def global_settings(key, default=None):
    return settings().get(key, default)


class TextPastryTools(object):
    @staticmethod
    def duplicate(view, edit, region, times):
        for i in range(0, times):
            # this code is from sublime text -> packages/default/duplicate.py
            line = view.line(region)
            line_contents = view.substr(line) + '\n'
            view.insert(edit, line.begin(), line_contents)
            view.sel().add(region)


class HistoryHandler(object):
    _stack = None
    index = 0
    @classmethod
    def setup(cls, items):
        cls._stack = [''] + items
        cls.index = 0
    @classmethod
    def append(cls, value):
        # remove duplicate
        cls.remove(value)
        cls._stack.append(value)
        cls.index = 0
    @classmethod
    def remove(cls, value):
        if value in cls._stack:
            index = cls._stack.index(value)
            del cls._stack[index]
    @classmethod
    def set(cls, value, index=None):
        cls._stack[cls.normalize_index(index)] = value
    @classmethod
    def normalize_index(cls, index):
        original = index
        index = cls.index if index is None else index
        if index:
            last = len(cls._stack) - 1 if len(cls._stack) > 0 else 0
            # check if index is in bounds
            if index < 0: index = last
            if index > last: index = 0
        return index
    @classmethod
    def next(cls):
        cls.index = cls.normalize_index(cls.index + 1)
    @classmethod
    def prev(cls):
        cls.index = cls.normalize_index(cls.index - 1)
    @classmethod
    def get(cls, index=None):
        return cls._stack[cls.normalize_index(index)]
    @classmethod
    def empty(cls):
        return cls._stack is None or len(cls._stack) == 0
    @classmethod
    def size(cls):
        return len(cls._stack)
    @classmethod
    def current_index(cls):
        return cls.index


class HistoryManager(object):
    file = None
    def __init__(self, remove_duplicates=True):
        self.settings = sublime.load_settings(self.file)
        self.remove_duplicates = remove_duplicates
    def generate_key(self, data):
        return hashlib.md5(json.dumps(data).encode('UTF-8')).hexdigest()
    def history(self):
        history = self.settings.get("history", [])
        if isinstance(history, dict):
            history = []
        return history
    def items(self):
        entries = [item['data'] for item in self.history() if 'data' in item]
        return entries[-self.max():]
    def max(self):
        return self.settings.get("history_max_entries", 100)
    def save(self, history):
        if history is not None:
            self.settings.set("history", history)
        sublime.save_settings(self.file)
    def append(self, data, label=None):
        if not data:
            return
        history = self.history()
        key = self.generate_key(data)
        # convert
        if isinstance(history, dict):
            history = []
        history[:] = [item for item in history if 'key' in item and not item['key'] == key]
        history.append({'key': key, 'data': data, 'label': label})
        # set as last command
        self.settings.set('last_command', data)
        self.save(history)
    def remove(self, key):
        history = self.history()
        history[:] = [item for item in history if item['key'] == key]
    def clear(self):
        self.save([])


class TextPastryHistoryNavigatorCommand(sublime_plugin.TextCommand):
    def __init__(self, *args, **kwargs):
        super(TextPastryHistoryNavigatorCommand, self).__init__(*args, **kwargs)
        self.current = None
    def run(self, edit, reverse=False):
        HH = HistoryHandler
        if HH.index == 0:
            current = self.view.substr(sublime.Region(0, self.view.size()))
            HH.set(current)
        if reverse: HH.prev()
        else: HH.next()
        self.view.erase(edit, sublime.Region(0, self.view.size()))
        self.view.insert(edit, 0, HH.get())
        if HH.current_index():
            sublime.status_message("History item: " + str(HH.current_index()) + " of " + str(HH.size() - 1))
        else:
            sublime.status_message("Current")
    def is_enabled(self, *args, **kwargs):
        return not HistoryHandler.empty()


class CommandLineHistoryManager(HistoryManager):
    file = "TextPastryHistory.sublime-settings"
    field = 'text'
    def generate_key(self, data):
        return hashlib.md5(data[self.field].encode('UTF-8')).hexdigest()
    def items(self):
        entries = [item['data'][self.field] for item in self.history() if 'data' in item and self.field in item['data']]
        return entries[-self.max():]
    def append(self, data, label=None):
        if self.field in data and len(data[self.field]) > 0:
            super(CommandLineHistoryManager, self).append(data, label)
            HistoryHandler.append(data[self.field])


class OverlayHistoryManager(HistoryManager):
    file = "TextPastryHistory.sublime-settings"
    field = 'text'
    def generate_key(self, data):
        return hashlib.md5(data[self.field].encode('UTF-8')).hexdigest()
    def items(self):
        entries = self.history()[-self.max():]
        entries.reverse()
        return entries
    def append(self, data, label=None):
        if self.field in data and len(data[self.field]) > 0:
            super(CommandLineHistoryManager, self).append(data, label)
            HistoryHandler.append(data[self.field])


class Command(object):
    def __init__(self, options=None, view=None, edit=None, env=None, *args, **kwargs):
        self.counter = 0
        self.options = options
        self.stack = []
        self.view = view
        self.edit = edit
        self.env = env
    def init(self, view, items=None):
        if items: self.stack = items
    def previous(self):
        return self.stack[self.counter - 1]
    def current(self):
        return text[self.counter]
    def next(self, value, index, region):
        val = self.stack[self.counter]
        self.counter += 1
        return val
    def has_next(self):
        return (self.counter) < len(self.stack)
    @staticmethod
    def create(cmd, items=None, options=None):
        return getattr(sys.modules[__name__], cmd)(items)
class InfiniteCommand(Command):
    def has_next(self):
        return True


class BackreferenceCommand(Command):
    def init(self, view, items=None):
        selections = []
        if view.sel():
            for region in view.sel():
                selections.append(view.substr(region))
        values = []
        for idx, index in enumerate(map(int, items)):
            if idx >= len(selections): break
            i = index - 1
            if i >= 0 and i < len(selections):
                values.append(selections[i])
            else:
                values.append(None)
        # fill up
        for idx, value in enumerate(selections):
            if len(values) + 1 < idx:
                values.append(value)
        self.stack = values


class UuidCommand(InfiniteCommand):
    def next(self, value, index, region):
        text = str(uuid.uuid4())
        if self.is_upper_case():
            text = text.upper()
        self.stack.append(text)
        return text
    def is_upper_case(self):
        upper_case = False
        if self.options:
            upper_case = self.options.get("uppercase", False)
        return upper_case


class ShellCommand(InfiniteCommand):
    cmd = '/bin/sh'
    shell = False
    def __init__(self, *args, **kwargs):
        super(ShellCommand, self).__init__(*args, **kwargs)
        if sublime.platform() == 'windows':
            cmd = 'cmd.exe'
            shell = True
    def settings(self):
        return global_settings(self.cmd, {})
    def command(self, script):
        return shlex.split(script)
    def work_dir(self):
        folder = self.options.get("folder", None)
        return folder if folder else expanduser("~")
    def proc(self, env, script):
        command, cwd = self.command(script), self.work_dir()
        if command and cwd and script:
            sp = subprocess
            return sp.Popen(command, env=env, cwd=cwd, stdin=sp.PIPE, stdout=sp.PIPE, stderr=sp.STDOUT)
    def execute(self, script):
        env = os.environ.copy()
        for path in global_settings('path', {}).get(sublime.platform(), []):
            env["PATH"] += os.pathsep + path
        proc = self.proc(env, script)
        if proc:
            print('Running script:', script)
            result = proc.communicate()[0]
            if proc.returncode == 0:
                print('script result:', result.decode('UTF-8'))
                return result.decode('UTF-8')
            else:
                s = 'error while processing script with {CMD}: {RESULT}'
                sublime.error_message(s.format(
                    CMD=self.cmd,
                    RESULT=result.decode('UTF-8')
                ))
    def get_fcontent(self, file):
        path = normpath(join(self.cwd(), file))
        if isfile(path):
            with open(path, "r") as f:
                script = f.read()
                return script
    def script(self):
        script = self.options.get("script", None)
        file = self.options.get("file", None)
        if file:
            script = self.get_fcontent(file)
        elif self.check_wrap(script):
            script = self.wrap(script)
        return script
    def check_wrap(self, script):
        return self.options.get("wrap", True)
    def wrap(self, script):
        return script
    def next(self, value, index, region):
        self.value = value
        self.index = index
        self.begin = region.begin()
        self.end = region.end()
        return self.execute(self.script())


class NodejsCommand(ShellCommand):
    cmd = 'node'
    def command(self, script):
        return [cmd, '-e', script]
    def wrap(self, script):
        # some sugar
        if not 'return ' in script and not ';' in script:
            script = "value = " + script
        # generate context information
        meta = dict(
            value=json.dumps(self.value),
            index=self.index,
            begin=self.begin,
            end=self.end,
            length=value.length,
            row=0,
            column=0,
            selection_type=0
        )
        script = """
            var result = (function(value, index, begin, end) {
                {SCRIPT};
                return value;
            }({VALUE}, {INDEX}, {BEGIN}, {END}));
            process.stdout.write("" + result);
        """.format(
            SCRIPT=script,
            VALUE=json.dumps(self.value),
            INDEX=self.index,
            BEGIN=self.begin,
            END=self.end
        )
        return script


class PythonCommand(ShellCommand):
    cmd = 'python'
    def command(self, script):
        print('executing python', script)
        return [self.cmd, '-B', '-c', script]
    def wrap(self, script):
        # define global imports here
        code = ['import sys']
        # extend syspath with config
        sys_paths = self.settings().get('sys.path.append', [])
        code.extend(['sys.path.append("' + p + '")' for p in sys_paths])
        # custom imports
        code.extend(self.imports())
        # generate wrapper code
        code.extend([
            'def tpscript(value, index, begin, end):',
            ' return ' + script,
            "sys.stdout.write(tpscript('{VALUE}', {INDEX}, {BEGIN}, {END}))".format(
                SCRIPT=script.replace("'", r"\'"),
                VALUE=re.escape(self.value),
                INDEX=self.index,
                BEGIN=self.begin,
                END=self.end
            )
        ])
        return '\n'.join(code)
    def imports(self):
        imports = []
        for i in self.settings().get('import', []):
            if isinstance(i, dict) and len(i) == 1:
                for d in iter(i):
                    print(i)
                    if len(i[d]):
                        imports.append('from ' + d + ' import ' + ','.join(i[d]))
                    else:
                        imports.append('import ' + d)
            else:
                imports.append('import ' + i)
        return imports


class RubyCommand(ShellCommand):
    cmd = 'ruby'
    def command(self, script):
        return [cmd, '-e', script]
    def wrap(self, script):
        wrapper = """
            def tpscript(value, index, begin, end)
               {SCRIPT}
            end
            tpscript('{VALUE}', {INDEX}, {BEGIN}, {END})
        """.format(
            SCRIPT=script,
            VALUE=json.dumps(self.value),
            INDEX=self.index,
            BEGIN=self.begin,
            END=self.end
        )
        return script


class TextPastryShowCommandLine(sublime_plugin.WindowCommand):
    def run(self, text, execute=False):
        if not self.window.active_view():
            return
        if execute:
            self.on_done(text, False)
            return
        if not hasattr(self, 'history'):
            self.history = CommandLineHistoryManager()
            HistoryHandler.setup(self.history.items())
        self.show_input_panel('Text Pastry Command:', text)
    def on_done(self, text, history=True):
        parser = Parser()
        result = parser.parse(text)
        if result and 'command' in result:
            result['text'] = text
            if history:
                self.history.append(data=result, label=text)
            command = result['command']
            args = result['args'] if 'args' in result else None
            if 'context' in result and result['context'] == 'view':
                self.window.active_view().run_command(command, args)
            else:
                self.window.run_command(command, args)
    def show_input_panel(self, label, text):
        HistoryHandler.index = 0
        view = self.window.show_input_panel(label, text, self.on_done, None, None)
        settings = view.settings()
        settings.set('is_widget', False)
        settings.set('gutter', False)
        settings.set('rulers', [])
        settings.set('spell_check', False)
        settings.set('word_wrap', False)
        settings.set('draw_minimap_border', False)
        settings.set('draw_indent_guides', False)
        settings.set('highlight_line', False)
        settings.set('line_padding_top', 0)
        settings.set('line_padding_bottom', 0)
        settings.set('auto_complete', False)
        settings.set('text_pastry_command_line', True)


class TextPastryInsertTextCommand(sublime_plugin.TextCommand):
    def run(self, edit, text=None, separator=None, clipboard=False,
            items=None, regex=False, keep_selection=None, update_selection=None,
            repeat=None, strip=None, threshold=1, align=None, by_rows=False, repeat_word=0):
        if separator: separator = separator.encode('utf8').decode("unicode-escape")
        if clipboard: text = sublime.get_clipboard()
        if text:
            if regex: items = re.split(separator, text)
            else: items = text.split(separator)
        # could make a threshold setting...
        if items and len(items) >= threshold:
            regions = []
            sel = self.view.sel()
            if repeat_word > 1:
                items = list(itertools.chain.from_iterable(itertools.repeat(item, repeat_word) for item in items))
            if by_rows == True:
                items = self.by_rows(items, sel)
            if strip is None:
                strip = False
                if separator == '\\n' and settings().has("clipboard_strip_newline"): strip = settings().get("clipboard_strip_newline")
            # initialize repeat
            if repeat is None:
                if clipboard and settings().has("repeat_clipboard"):
                    repeat = settings().get("repeat_clipboard")
                elif settings().has("repeat_words"):
                    repeat = settings().get("repeat_words")
            if repeat:
                while (len(items) < len(sel)):
                    items.extend(items)
            last_region = None
            for idx, region in enumerate(sel):
                if idx < len(items):
                    current = items[idx]
                    if strip:
                        current = current.strip()
                    if align == 'prepend':
                        self.view.insert(edit, region.begin(), current)
                    elif align == 'append':
                        self.view.insert(edit, region.end(), current)
                    else:
                        self.view.replace(edit, region, current)
                else:
                    regions.append(region)
                last_region = region
            if keep_selection is None:
                keep_selection = settings().get("keep_selection", False)
            if update_selection is None:
                update_selection = settings().get("update_selection", None)
            # clone the selection
            cursorPos = [(r.begin(), r.end()) for r in sel];
            if not keep_selection:
                sel.clear()
                # add untouched regions
                for region in regions:
                    sel.add(sublime.Region(region.begin(), region.end()))
                # add cursor if there is none in the current view
                if len(sel) == 0:
                    (begin, end) = cursorPos[-1]
                    sel.add(sublime.Region(begin, end))
            else:
                if update_selection == "begin":
                    sel.clear()
                    for begin, end in cursorPos:
                        sel.add(sublime.Region(begin, begin))
                elif update_selection == "end":
                    sel.clear()
                    for begin, end in cursorPos:
                        sel.add(sublime.Region(end, end))
        else:
            sublime.status_message("No text found for Insert Text, fall back to auto_step")
            self.view.run_command("text_pastry_auto_step", {"text": text})
    def by_rows(self, data, sel):
        rows = self.create_matrix(sel)
        return self.prep_data(data, rows)
    def create_matrix(self, sel):
        rows = []
        r = None
        c = None
        for region in sel:
            row, col = self.view.rowcol(region.begin())
            if (r == None):
                r = row
                c = [1]
            elif (r != row):
                rows.append(c)
                # new row
                r = row
                c = [1]
            else:
                c.append(1)
        rows.append(c)
        # extend colums of rows
        mc = self.count_cols(rows)
        for r in rows:
            i = mc - len(r)
            if (i > 0):
                r.extend([0]*i)
        return rows
    def count_cols(self, rows):
        # fill rows
        max_cols = 0
        for r in rows:
            cols = 0
            for c in r:
                cols += 1
            if cols > max_cols:
                max_cols = cols
        return max_cols
    def prep_data(self, data, rows):
        prepped_data = []
        t1 = [list(i) for i in zip(*rows)];
        index = 0
        for row in t1:
            for idx, val in enumerate(row):
                if val == 1 and len(data) > index:
                    row[idx] = data[index]
                    index += 1
                else:
                    row[idx] = None
        t2 = [list(i) for i in zip(*t1)]
        for row in t2:
            prepped_data.extend([i for i in row if i != None])
        return prepped_data
class TextPastryWordsCommand(sublime_plugin.TextCommand):
    def run(self, edit, text, repeat=None):
        result = WordsParser(text).parse()
        if result and 'command' in result and 'args' in result:
            if repeat is not None:
                result['args']['repeat'] = repeat
            self.view.run_command(result['command'], result['args'])


class TextPastryShowMenu(sublime_plugin.WindowCommand):
    def create_main(self):
        self.overlay = Overlay()
        history = self.history_manager.items()
        [self.overlay.addHistoryItem(item) for item in history[:2]]
        if len(history) > 0:
            self.overlay.addSpacer()
        x = selection_count = len(self.window.active_view().sel())
        self.overlay.addMenuItem("\\i", "From 1 to {0}".format(x))
        self.overlay.addMenuItem("\\i0", "From 0 to " + str(x - 1))
        self.overlay.addMenuItem("\\i(N,M)", "From N to X by M")
        self.overlay.addSpacer()
        if sublime.get_clipboard():
            self.overlay.addMenuItem("\\p(\\n)", "Paste Lines")
            self.overlay.addMenuItem("\\p", "Paste")
            self.overlay.addSpacer()
        self.overlay.addMenuItem("words", "Enter a list of words")
        uuid_label = 'UUID' if global_settings("force_uppercase_uuid", False) else 'uuid'
        self.overlay.addMenuItem(uuid_label, "Generate UUIDs")
        self.overlay.addSpacer()
        if len(history) > 0: self.overlay.addMenuItem("history", "Show history")
        self.overlay.addMenuItem("settings", "Show settings")
    def create_history(self):
        self.overlay = Overlay()
        history = self.history_manager.items()
        [self.overlay.addHistoryItem(item) for item in history]
        self.overlay.addSpacer()
        self.overlay.addMenuItem("clear_hist", "Clear history")
        self.overlay.addMenuItem("back", "Back to menu")
    def create_settings(self):
        self.overlay = Overlay()
        repeat_words = global_settings("repeat_words", False)
        repeat_clipboard = global_settings("repeat_clipboard", False)
        clipboard_strip_newline = global_settings("clipboard_strip_newline", False)
        keep_selection = global_settings("keep_selection", False)
        force_uppercase_uuid = global_settings("force_uppercase_uuid", False)
        self.overlay.addSetting("repeat_words", repeat_words)
        self.overlay.addSetting("repeat_clipboard", repeat_clipboard)
        self.overlay.addSetting("clipboard_strip_newline", clipboard_strip_newline)
        self.overlay.addSetting("keep_selection", keep_selection)
        self.overlay.addSetting("force_uppercase_uuid", force_uppercase_uuid)
        self.overlay.addSpacer()
        self.overlay.addMenuItem(command="default", args={"file": sublime.packages_path() + "/Text Pastry/TextPastry.sublime-settings"}, label="Open default settings")
        self.overlay.addMenuItem(command="user", args={"file": sublime.packages_path() + "/User/TextPastry.sublime-settings"}, label="Open user settings")
        if self.back:
            self.overlay.addSpacer()
            self.overlay.addMenuItem("back", "Back to menu")
    def run(self, history=False, settings=False, back=True):
        if not self.window.active_view():
            return
        if not hasattr(self, 'history_manager'):
            self.history_manager = OverlayHistoryManager()
        self.back = back
        try:
            selection_count = len(self.window.active_view().sel())
            if history:
                self.create_history()
            elif settings:
                self.create_settings()
            else:
                self.create_main()
            if self.overlay and self.overlay.is_valid():
                self.show_quick_panel(self.overlay.items(), self.on_done, sublime.MONOSPACE_FONT)
        except ValueError:
            sublime.status_message("Error while showing Text Pastry overlay")
    def on_done(self, index):
        self.window.run_command("hide_overlay")
        item = self.overlay.get(index)
        if item and item.command:
            if item.type == HistoryItem.type:
                sublime.status_message("redo history")
                command = item.command
                text = item.text
                separator = item.separator
                # insert nums for history compatibility
                if command == "insert_nums":
                    sublime.status_message("text_pastry_range: " + text)
                    (start, step, padding) = map(str, text.split(" "))
                    self.window.run_command("text_pastry_range", {"start": start, "step": step, "padding": padding})
                elif command == "text_pastry_insert_text":
                    self.window.run_command(command, {"text": text, "separator": separator})
                else:
                    self.window.run_command(item.command, item.args)
            elif item.command == "history":
                self.window.run_command("text_pastry_show_menu", {"history": True})
                return
            elif item.command == "settings":
                self.window.run_command("text_pastry_show_menu", {"settings": True})
                return
            elif item.command == "clear_hist":
                self.history_manager.clear()
            elif item.command == "back":
                self.window.run_command("text_pastry_show_menu")
            elif item.command == "cancel" or item.command == "close":
                pass
            elif item.command == "\\p":
                cb = sublime.get_clipboard()
                if cb:
                    self.history_manager.append(data={"command": "text_pastry_insert_text", "args": {"clipboard": True}}, label=item.label)
                    self.window.run_command("text_pastry_insert_text", {"text": cb, "clipboard": True})
                else:
                    sublime.message_dialog("No Clipboard Data available")
            elif item.command == "\\p(\\n)":
                cb = sublime.get_clipboard()
                if cb:
                    self.history_manager.append(data={"command": "text_pastry_insert_text", "args": {"text": cb, "separator": "\\n", "clipboard": True}}, label=item.label)
                    self.window.run_command("text_pastry_insert_text", {"text": cb, "separator": "\\n", "clipboard": True})
                else:
                    sublime.message_dialog("No Clipboard Data available")
            elif item.command == "\\i":
                self.history_manager.append(data={"command": "text_pastry_range", "args": {"start": 1, "step": 1, "padding": 1}}, label=item.label)
                self.window.run_command("text_pastry_range", {"start": 1, "step": 1, "padding": 1})
            elif item.command == "\\i0":
                self.history_manager.append(data={"command": "text_pastry_range", "args": {"start": 0, "step": 1, "padding": 1}}, label=item.label)
                self.window.run_command("text_pastry_range", {"start": 0, "step": 1, "padding": 1})
            elif item.command.lower() == "uuid":
                self.history_manager.append(data={"command": "text_pastry_uuid", "args": {"uppercase": False}}, label=item.label)
                self.window.run_command("text_pastry_uuid", {"uppercase": False})
            elif item.command == "words":
                self.window.run_command("text_pastry_show_command_line", {"text": item.command + " "})
            elif item.command == "text_pastry_setting":
                item.args['value'] = not item.args.get('value', False)
                self.window.run_command("text_pastry_setting", item.args)
                self.window.run_command("text_pastry_show_menu", {"settings": True, "back": self.back})
            elif item.command == "user" or item.command == "default":
                self.window.run_command("open_file", item.args)
            elif item.command == "\\i(N,M)":
                self.window.run_command("text_pastry_show_command_line", {"text": item.command})
            elif len(item.command):
                self.window.run_command(item.command, item.args)
            else:
                sublime.status_message("Unknown command: " + item.command)
        else:
            sublime.status_message("No item selected")
    def show_quick_panel(self, items, on_done, flags):
        # Sublime 3 does not allow calling show_quick_panel from on_done, so we need to set a timeout here.
        sublime.set_timeout(lambda: self.window.show_quick_panel(items, on_done, flags), 10)


class TextPastryPasteCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        try:
            text = sublime.get_clipboard()
            if text is not None and len(text) > 0:
                regions = []
                sel = self.view.sel()
                items = text.split("\n")
                if len(items) == 1: items = [text]
                strip = True
                for idx, region in enumerate(sel):
                    if idx < len(items):
                        row = items[idx].strip()
                        if region.empty():
                            sublime.status_message("empty")
                            row = self.view.substr(self.view.line(self.view.line(region).begin() - 1)) + "\n"
                            i = 0
                            if len(row.strip()): i = self.view.insert(edit, region.end(), row)
                            regions.append(sublime.Region(region.end() + i, region.end() + i))
                        else:
                            sublime.status_message("selection")
                            self.view.replace(edit, region, row)
                            i = len(row)
                            regions.append(sublime.Region(region.begin() + i, region.begin() + i))
                sel.clear()
                for region in regions:
                    sel.add(region)
                    pass
            else:
                sublime.status_message("No text found for Insert Text, canceled")
        except ValueError:
            sublime.status_message("Error while executing Insert Text, canceled")
            pass


class TextPastryRangeParserCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        result = RangeCommandParser(text).parse()
        self.view.run_command(result['command'], result['args'])
class TextPastryRangeCommand(sublime_plugin.TextCommand):
    def run(self, edit, start=None, stop=None, step=1, padding=1, fillchar='0', justify=None,
            align=None, prefix=None, suffix=None, repeat_increment=None, loop=None, **kwargs):
        print('found range command', start, stop, step)
        start = int(start) if is_numeric(start) else None
        stop = int(stop) if is_numeric(stop) else None
        step = int(step) if is_numeric(step) else 1
        padding = int(padding) if is_numeric(padding) else 0
        # duplicate lines and add to selection on repeat
        if stop is not None:
            if start is None:
                if stop == 1:
                    start = len(self.view.sel())
                elif stop == 0:
                    start = len(self.view.sel()) - 1
            multiplier = 1
            if is_numeric(repeat_increment):
                multiplier *= int(repeat_increment)
            if is_numeric(loop):
                multiplier *= int(loop)
            repeat = len(range(start, stop, step))
            if multiplier > 1:
                repeat = (repeat + 1) * multiplier - 1
            sel = self.view.sel()
            if len(sel) == 1:
                TextPastryTools.duplicate(self.view, edit, sel[0], repeat)
        if start is None:
            start = 0
        # adjust stop if none was given
        if stop is None:
            stop = start + (len(self.view.sel()) + 1) * step
        if global_settings('range_include_end_index', True):
            stop += step
        # if stop is negative, step needs to be negative aswell
        if (start > stop and step > 0):
            step = step * -1
        items = [str(x) for x in range(start, stop, step)]
        if repeat_increment and repeat_increment > 0:
            tmp = items
            items = []
            for val in tmp:
                for x in range(repeat_increment):
                    items.append(val)
        if padding > 1:
            fillchar = fillchar if fillchar is not None else '0'
            just = str.ljust if justify == 'left' else str.rjust
            items = [self.pad(x, just, padding, fillchar) for x in items]
        # apply prefix/suffix
        if prefix:
            items = [prefix + x for x in items]
        if suffix:
            items = [x + suffix for x in items]
        self.view.run_command("text_pastry_insert_text", {"items": items, "align": align})
    def pad(self, s, just, padding, fillchar):
        if s.startswith('-'):
            return '-' + just(s[1:], padding, fillchar)
        else:
            return just(s, padding, fillchar)

class TextPastryBinCommand(sublime_plugin.TextCommand):
    def run(self, edit, start=None, stop=None, step=1, padding=1, fillchar='0', justify=None,
            align=None, prefix=None, suffix=None, repeat_increment=None, loop=None, **kwargs):
        print('found bin command', start, stop, step)
        start = int(start) if is_numeric(start) else None
        stop = int(stop) if is_numeric(stop) else None
        step = int(step) if is_numeric(step) else 1
        padding = int(padding) if is_numeric(padding) else 0
        # duplicate lines and add to selection on repeat
        if stop is not None:
            if start is None:
                if stop == 1:
                    start = len(self.view.sel())
                elif stop == 0:
                    start = len(self.view.sel()) - 1
            multiplier = 1
            if is_numeric(repeat_increment):
                multiplier *= int(repeat_increment)
            if is_numeric(loop):
                multiplier *= int(loop)
            repeat = len(range(start, stop, step))
            if multiplier > 1:
                repeat = (repeat + 1) * multiplier - 1
            sel = self.view.sel()
            if len(sel) == 1:
                TextPastryTools.duplicate(self.view, edit, sel[0], repeat)
        if start is None:
            start = 0
        # adjust stop if none was given
        if stop is None:
            stop = start + (len(self.view.sel()) + 1) * step
        if global_settings('range_include_end_index', True):
            stop += step
        # if stop is negative, step needs to be negative aswell
        if (start > stop and step > 0):
            step = step * -1
        items = [str(bin(x)).split("b")[1] for x in range(start, stop, step)]
        if repeat_increment and repeat_increment > 0:
            tmp = items
            items = []
            for val in tmp:
                for x in range(repeat_increment):
                    items.append(val)
        if padding > 1:
            fillchar = fillchar if fillchar is not None else '0'
            just = str.ljust if justify == 'left' else str.rjust
            items = [self.pad(x, just, padding, fillchar) for x in items]
        # apply prefix/suffix
        if prefix:
            items = [prefix + x for x in items]
        if suffix:
            items = [x + suffix for x in items]
        self.view.run_command("text_pastry_insert_text", {"items": items, "align": align})
    def pad(self, s, just, padding, fillchar):
        if s.startswith('-'):
            return '-' + just(s[1:], padding, fillchar)
        else:
            return just(s, padding, fillchar)

class TextPastryDecimalRangeCommand(sublime_plugin.TextCommand):
    def run(self, edit, start=None, stop=None, step=1, padding=1, fillchar='0', justify=None,
            align=None, prefix=None, suffix=None, repeat_increment=None, loop=None, precision=0,
            **kwargs):
        print('found range command', start, stop, step, padding, precision, justify)
        start = Decimal(start) if self.is_decimal(start) else None
        stop = Decimal(stop) if self.is_decimal(stop) else None
        step = Decimal(step) if self.is_decimal(step) else 1
        padding = int(padding) if is_numeric(padding) else 0
        precision = int(precision) if is_numeric(precision) else 0
        # duplicate lines and add to selection on repeat
        if stop is not None:
            if start is None:
                if stop == 1:
                    start = Decimal(len(self.view.sel()))
                elif stop == 0:
                    start = Decimal(len(self.view.sel()) - 1)
            multiplier = 1
            if is_numeric(repeat_increment):
                multiplier *= repeat_increment
            if is_numeric(loop):
                multiplier *= loop
            repeat = len(list(self.drange(start, stop, step)))
            if multiplier > 1:
                repeat = (repeat + 1) * multiplier - 1
            sel = self.view.sel()
            if len(sel) == 1:
                TextPastryTools.duplicate(self.view, edit, sel[0], repeat)
        if start is None:
            start = Decimal(0)
        # adjust stop if none was given
        if stop is None:
            stop = start + Decimal(len(self.view.sel()) + 1) * step
        if global_settings('range_include_end_index', True):
            stop += step
        items = [x for x in self.drange(start, stop, step)]
        if repeat_increment and repeat_increment > 0:
            tmp = items
            items = []
            for val in tmp:
                for x in range(repeat_increment):
                    items.append(val)
        print('range command args', start, stop, step, "items", items)
        if precision > 1:
            items = ["{:.{}f}".format(x, precision) for x in items]
            if not justify:
                justify = 'right'
        if padding > 1:
            fillchar = fillchar if fillchar is not None else '0'
            just = str.ljust if justify == 'left' else str.rjust
            items = [self.pad(str(x), just, padding, fillchar) for x in items]
        # apply prefix/suffix
        if prefix:
            items = [prefix + x for x in items]
        if suffix:
            items = [x + suffix for x in items]
        # make sure we deliver strings
        items = [str(x) for x in items]
        self.view.run_command("text_pastry_insert_text", {"items": items, "align": align})
    def pad(self, s, just, padding, fillchar):
        if s.startswith('-'):
            return '-' + just(s[1:], padding, fillchar)
        else:
            return just(s, padding, fillchar)
    def drange(self, start, stop, step):
        r = start
        if start <= stop:
            while r <= stop:
                yield r
                r += getcontext().abs(step)
        if start > stop:
            while r >= stop:
                yield r
                r -= getcontext().abs(step)
    def is_decimal(self, s):
        if s is None:
            return False
        try:
            Decimal(s)
            return True
        except ValueError:
            return False

class TextPastryDecimalGeometricSequenceCommand(sublime_plugin.TextCommand):
    def run(self, edit, start=None, stop=None, faktor=2, padding=1, fillchar='0', justify=None,
            align=None, prefix=None, suffix=None, repeat_increment=None, loop=None, precision=0,
            **kwargs):
        print('found faktor command', start, stop, faktor, padding, precision, justify)
        start = Decimal(start) if self.is_decimal(start) else None
        stop = Decimal(stop) if self.is_decimal(stop) else None
        faktor = Decimal(faktor) if self.is_decimal(faktor) else 1
        padding = int(padding) if is_numeric(padding) else 0
        precision = int(precision) if is_numeric(precision) else 0
        # duplicate lines and add to selection on repeat
        if stop is not None:
            if start is None:
                if stop == 1:
                    start = Decimal(len(self.view.sel()))
                elif stop == 0:
                    start = Decimal(len(self.view.sel()) - 1)
            multiplier = 1
            if is_numeric(repeat_increment):
                multiplier *= repeat_increment
            if is_numeric(loop):
                multiplier *= loop
            repeat = len(list(self.gsequence(start, stop, faktor)))
            if multiplier > 1:
                repeat = (repeat + 1) * multiplier - 1
            sel = self.view.sel()
            if len(sel) == 1:
                TextPastryTools.duplicate(self.view, edit, sel[0], repeat)
        if start is None:
            start = Decimal(1)
        # adjust stop if none was given
        if stop is None:
            stop = start + Decimal(len(self.view.sel()) + 1) * faktor
        if global_settings('range_include_end_index', True):
            stop *= faktor
        items = [x for x in self.gsequence(start, stop, faktor)]
        if repeat_increment and repeat_increment > 0:
            tmp = items
            items = []
            for val in tmp:
                for x in range(repeat_increment):
                    items.append(val)
        print('faktor command args', start, stop, faktor, "items", items)
        if precision > 1:
            items = ["{:.{}f}".format(x, precision) for x in items]
            if not justify:
                justify = 'right'
        if padding > 1:
            fillchar = fillchar if fillchar is not None else '0'
            just = str.ljust if justify == 'left' else str.rjust
            items = [self.pad(str(x), just, padding, fillchar) for x in items]
        # apply prefix/suffix
        if prefix:
            items = [prefix + x for x in items]
        if suffix:
            items = [x + suffix for x in items]
        # make sure we deliver strings
        items = [str(x) for x in items]
        self.view.run_command("text_pastry_insert_text", {"items": items, "align": align})
    def pad(self, s, just, padding, fillchar):
        if s.startswith('-'):
            return '-' + just(s[1:], padding, fillchar)
        else:
            return just(s, padding, fillchar)
    def gsequence(self, start, stop, faktor):
        r = start
        if start == 0:
            return
        if faktor > 1:
            if start <= stop:
                while r <= stop:
                    yield r
                    r = r*getcontext().abs(faktor)
            if start > stop:
                while r >= stop:
                    yield r
                    r = r/getcontext().abs(faktor)
        elif 0 < faktor < 1:
            if start > stop:
                while r >= stop:
                    yield r
                    r = r*getcontext().abs(faktor)
            if start <= stop:
                while r <= stop:
                    yield r
                    r = r/getcontext().abs(faktor)
    def is_decimal(self, s):
        if s is None:
            return False
        try:
            Decimal(s)
            return True
        except ValueError:
            return False


class TextPastryHexRangeCommand(sublime_plugin.TextCommand):
    def run(self, edit, start=0, stop=None, step=None, width=2,
        repeat_increment=None, loop=None, prefix='0x', hexFormatFlag='x', **kwargs):
        print('found hex range command', start, stop, step)
        start = int(start, 16) if self.is_hex(start) else 0
        stop = int(stop, 16) if self.is_hex(stop) else None
        # check if steps are in hexadecimal notation
        # use numeric otherwise
        step = int(step, 16) if self.is_hex(step) else None
        step = step if is_numeric(step) else 1
        width = int(width) if is_numeric(width) else 2
        # duplicate lines and add to selection on repeat
        if stop is not None:
            multiplier = 1
            if is_numeric(repeat_increment):
                multiplier *= int(repeat_increment)
            if is_numeric(loop):
                multiplier *= int(loop)
            repeat = len(list(self.hrange(start, stop, step)))
            if multiplier > 1:
                repeat = (repeat + 1) * multiplier - 1
            sel = self.view.sel()
            if len(sel) == 1:
                TextPastryTools.duplicate(self.view, edit, sel[0], repeat)
        # adjust stop if none was given
        if stop is None:
            stop = start + (len(self.view.sel()) + 1) * step
        if global_settings('range_include_end_index', True):
            stop += step
        items = [x for x in self.hrange(start, stop, step)]
        if repeat_increment and repeat_increment > 0:
            tmp = items
            items = []
            for val in tmp:
                for x in range(repeat_increment):
                    items.append(val)
        # make sure we print in hex
        items = [prefix + '{:0{}}'.format(x, str(width) + hexFormatFlag) for x in items]
        self.view.run_command("text_pastry_insert_text", {"items": items})
    def hrange(self, start, stop, step):
        r = start
        if start <= stop:
            while r <= stop:
                yield r
                r += step
        if start > stop:
            while r >= stop:
                yield r
                r -= step
    def is_hex(self, s):
        if s is None:
            return False
        try:
            int(s, 16)
            return True
        except ValueError:
            return False


class TextPastryRomanCommand(sublime_plugin.TextCommand):
    ints = (1000, 900, 500, 400, 100, 90, 50, 40, 10, 9, 5, 4, 1)
    nums = ('M',  'CM', 'D', 'CD','C', 'XC','L','XL','X','IX','V','IV','I')
    def run(self, edit, start=1, stop=None, step=None,
        repeat_increment=None, loop=None, lowercase=False):
        start = int(start) if is_numeric(start) else None
        stop = int(stop) if is_numeric(stop) else None
        step = int(step) if is_numeric(step) else 1
        # duplicate lines and add to selection on repeat
        if stop is not None:
            if start is None:
                if stop == 1:
                    start = len(self.view.sel())
                elif stop == 0:
                    start = len(self.view.sel()) - 1
            multiplier = 1
            if is_numeric(repeat_increment):
                multiplier *= int(repeat_increment)
            if is_numeric(loop):
                multiplier *= int(loop)
            repeat = len(range(start, stop, step))
            if multiplier > 1:
                repeat = (repeat + 1) * multiplier - 1
            sel = self.view.sel()
            if len(sel) == 1:
                TextPastryTools.duplicate(self.view, edit, sel[0], repeat)
        # adjust stop if none was given
        if stop is None:
            stop = start + (len(self.view.sel()) + 1) * step
        # Roman value caps
        start = start if start > 0 else 1
        stop = stop if stop < 4000 else 3999
        # adjust if include end
        if global_settings('range_include_end_index', True):
            stop += step
        items = [self.roman_numeral(r, lowercase) for r in range(start, stop, step)]
        if repeat_increment and repeat_increment > 0:
            tmp = items
            items = []
            for val in tmp:
                for x in range(repeat_increment):
                    items.append(val)
        self.view.run_command("text_pastry_insert_text", {"items": items})
    def roman_numeral(self, value, lowercase):
        if not 0 < value < 4000:
            return ''
        result = []
        for index, int_value in enumerate(self.ints):
            count = int(value / int_value)
            result.append(self.nums[index] * count)
            value -= int_value * count
        roman = ''.join(result)
        if lowercase: roman = roman.lower()
        return roman


class TextPastryRedoCommand(sublime_plugin.WindowCommand):
    def run(self):
        hs = sublime.load_settings("TextPastryHistory.sublime-settings")
        item = hs.get("last_command", {})
        if item and "command" in item and "text" in item and item["command"] and item["text"]:
            text = item.get("text")
            separator = item.get("separator", None)
            command = item.get("command", None)
            if text and command:
                sublime.status_message("Running last command")
                if command == "insert_nums":
                    (start, step, padding) = map(str, text.split(" "))
                    self.window.active_view().run_command("text_pastry_range", {"start": start, "step": step, "padding": padding})
                elif command == "text_pastry_insert_text":
                    self.window.active_view().run_command(command, {"text": text, "separator": separator})
                else:
                    pass


class TextPastrySettingCommand(sublime_plugin.TextCommand):
    def run(self, edit, name, value):
        settings().set(name, value)
        sublime.save_settings("TextPastry.sublime-settings")


class TextPastryCommandWrapperCommand(sublime_plugin.TextCommand):
    def run(self, edit, command, args=None, text=None, separator=None, items=None):
        try:
            cmd = Command.create(command, args)
            if cmd:
                items = items
                if text: items = text.split(separator)
                cmd.init(self.view, items)
                regions = []
                sel = self.view.sel()
                index = 0
                last_region = None
                for region in sel:
                    if cmd.has_next():
                        value = cmd.next(self.view.substr(region), index, region)
                        if value is not None:
                            self.view.replace(edit, region, value)
                            regions.append(region)
                    else:
                        break
                    last_region = region
                    index += 1
                if not global_settings("keep_selection", False):
                    [sel.subtract(region) for region in regions]
                # add cursor if there is none in the current view
                if len(sel) == 0:
                    sel.add(sublime.Region(last_region.end(), last_region.end()))
                sublime.status_message("Command done: " + command)
            else:
                sublime.error_message("Command not found: " + command)
        except ValueError:
            sublime.status_message("Error while executing Text Pastry Command, canceled")
            pass


class TextPastryStepCommand(sublime_plugin.TextCommand):
    def run(self, edit, text):
        result = StepCommandParser(text).parse()
        if result and 'command' in result and 'args' in result:
            self.view.run_command(result['command'], result['args'])


class TextPastryUuidCommand(sublime_plugin.TextCommand):
    def run(self, edit, uppercase=False, repeat=None):
        uppercase = global_settings("force_uppercase_uuid", False) or uppercase
        repeat = int(repeat) - 1 if repeat else len(self.view.sel()) - 1
        if len(self.view.sel()) == 1 and repeat:
            TextPastryTools.duplicate(self.view, edit, self.view.sel()[0], repeat)
        self.view.run_command("text_pastry_command_wrapper", {
            "command": "UuidCommand",
            "args": {"uppercase": uppercase}
        })


class TextPastryDateRangeCommand(sublime_plugin.TextCommand):
    def run(self, edit, text, date=None, step_size="day", count=None, date_format=None, last_day_of_month=False, repeat=None):
        # support repeats
        repeat = int(repeat) - 1 if repeat else len(self.view.sel()) - 1
        if len(self.view.sel()) == 1 and repeat:
            TextPastryTools.duplicate(self.view, edit, self.view.sel()[0], repeat)
        selection_count = len(self.view.sel())
        match = re.search('^\\d+$', text)
        if count is None and match:
            count = int(match.group(0))
        match = re.search('^([\\d]{1,2}[\\.-/][\\d]{1,2}[\\.-/][\\d]{1,4}) ?(.+)?$', text)
        if match:
            date = self.parse_date(match.group(1))
            fmt = match.group(2)
            if fmt and '%' in fmt:
                date_format = fmt
        if date is None:
            # try to see if text is a date
            if text:
                date = self.parse_date(text)
        if date is None:
            s = None
            # check if selection is a date
            if selection_count == 1:
                s = self.view.substr(self.view.sel()[0]).strip()
            if s:
                date = self.parse_date(s)
        if date is None:
            # use today as date
            date = datetime.datetime.now()
            date = date + datetime.timedelta(hours=-date.hour, minutes=-date.minute, seconds=-date.second, microseconds=-date.microsecond)
        if count is None:
            # use selection count if no count was given/found
            count = selection_count
        else:
            # set boundaries of count
            if count > selection_count and selection_count > 1:
                count = selection_count
        if date_format is None:
            date_format = global_settings('date_format', '%x')
        # generate item list
        items = [self.date(date, step_size, x, last_day_of_month).strftime(date_format) for x in range(count)]
        # create one text entry if single selection
        if selection_count == 1:
            newline = '\r\n' if self.view.line_endings() == 'windows' else '\n'
            items = [newline.join(items)]
        for idx, region in enumerate(self.view.sel()):
            self.view.replace(edit, region, items[idx])
    def parse_date(self, s):
        date = None
        parse_date_formats = global_settings("parse_date_formats", [])
        for fmt in parse_date_formats:
            try:
                date = datetime.datetime.strptime(s, fmt)
            except ValueError:
                pass
        return date
    def date(self, start, step_size, value, last_day_of_month):
        date = start
        if step_size == 'week':
            date = date + datetime.timedelta(weeks=value)
        elif step_size == 'month':
            date = self.add_months(date, value)
            if last_day_of_month:
                date = self.adjust_to_last_day_of_month(date)
        elif step_size == 'year':
            date = self.add_years(date, value)
        elif step_size == 'hour':
            date = date + datetime.timedelta(hours = value)
        elif step_size == 'minute':
            date = date + datetime.timedelta(minutes = value)
        elif step_size == 'second':
            date = date + datetime.timedelta(seconds = value)
        else:
            date = date + datetime.timedelta(days = value)
        return date
    def adjust_to_last_day_of_month(self, date):
        if date.month == 12:
            return date.replace(day = 31)
        else:
            return date.replace(day = 1).replace(month = date.month + 1) - datetime.timedelta(days = 1)
    def add_years(self, d, years):
        if years == 0:
            return d
        try:
            return d.replace(year = d.year + years)
        except ValueError:
            return d.replace(day = 28).replace(year = d.year + years)
    def add_months(self, d, m):
        if m == 0:
            return d
        years = 0
        months = m + d.month
        years = int(months / 12)
        months = int(months % 12)
        if months == 0:
            years -= 1
            months = 12
        try:
            return self.add_years(d, years).replace(month = months)
        except ValueError:
            years = 0
            months = m + d.month + 1
            years = int(months / 12)
            months = int(months % 12)
            if months == 0:
                years -= 1
                months = 12
            return self.add_years(d, years).replace(day = 1).replace(month = months) - datetime.timedelta(days = 1)


class TextPastryAutoStepCommand(sublime_plugin.TextCommand):
    def run(self, edit, text=None, step_size=None, repeat=None):
        step = int(step_size) if step_size and is_numeric(step_size) else 1
        if text and step:
            padding = 1
            sublime.status_message("text_pastry_auto_step")
            # match continuous digits/non-digits
            parts = [m for m in re.findall("([\d]+|[^\d]+)", text)]
            # find integer parts
            numbers = [idx for idx, val in enumerate(parts) if is_numeric(val)]
            repeat = int(repeat) - 1 if repeat else len(self.view.sel()) - 1
            if len(self.view.sel()) == 1 and repeat:
                TextPastryTools.duplicate(self.view, edit, self.view.sel()[0], repeat)
            sel = self.view.sel()
            for region in sel:
                self.view.replace(edit, region, ''.join(parts))
                # increment
                for i in numbers:
                    parts[i] = str(int(parts[i]) + step)
            # keep selection
            for region in sel:
                pass


class TextPastryNumberGeneratorCommand(sublime_plugin.TextCommand):
    def run(self, edit, start=1, stop=10, step=1):
        self.view.run_command('text_pastry_range', {'start': start, 'stop': stop, 'step': step})
    def is_enabled(self):
        return len(self.view.sel()) == 1


class Parser(object):
    def parse(self, text):
        if not text:
            return None
        # start pasing the command string
        result = None
        m5 = re.match('^(\$\d+\s?)+$', text)
        m8 = re.match('^cmd ([\w_]+)(.*?)', text)
        if m5:
            # backref
            items = ','.join(filter(None, map(lambda x: x.strip(), text.split('$'))))
            result = dict(command='text_pastry_insert', args={'command': 'backreference', 'text': items, 'separator': ','})
        elif m8:
            cmd = m8.group(1)
            args = m8.group(2)
            if args:
                args = ast.literal_eval('dict(' + args + ')')
            result = {'command': cmd, 'args': args}
        else:
            # check command
            if not result:
                result = self.parse_command(text)
            # check preset
            if not result:
                result = self.parse_preset(text)
            if not result:
                # default is words
                sublime.status_message('Inserting text: ' + text)
                result = dict(command='text_pastry_insert_text', args={'text': text, 'threshold': global_settings('insert_text_threshold', 3)})
        # Parser is done
        if result:
            sublime.status_message('Running ' + result['command'])
        else:
            sublime.status_message('Text Pastry: no match found, doing nothing')
        return result
    def parse_command(self, text):
        result = None
        builtin_commands = sublime.load_settings('TextPastryCommands.json')
        cmd_shortcuts = global_settings('commands', [])
        cmd_shortcuts.extend(builtin_commands.get('commands', []))
        for item in cmd_shortcuts:
            # if parser
            if 'parser' in item:
                class_ = globals()[item['parser']]
                result = class_(text).parse()
            elif 'match' in item:
                # if match
                comp = re.compile(item['match'])
                match = comp.match(text)
                if match:
                    # create dict with backreferences
                    refs = {}
                    for (key, value) in enumerate(match.groups()):
                        refs['$' + str(key + 1)] = value
                    refs['$0'] = match.group(0)
                    # add other stuff to references
                    refs['$clipbord'] = sublime.get_clipboard()
                    result = self.create_command(item, refs)
            if result:
                break
        return result
    def parse_preset(self, input_text):
        result = None
        builtin_presets = sublime.load_settings('TextPastryPresets.json')
        presets = builtin_presets.get('presets', {})
        presets.update(global_settings('presets', {}))
        name, start, end, options = PresetCommandParser(input_text).parse()
        if name in presets:
            items = presets[name]
            if 'repeat' not in options:
                options['repeat'] = global_settings('repeat_preset', True)
            if 'to_upper_case' not in options:
                options['to_upper_case'] = start and start.isupper()
            if start or end:
                items = self.create_preset_command(start, end, options, items)
            items = self.format(items, options)
            result = dict(command='text_pastry_insert_text', args={
                'items': items,
                'repeat': options.get('repeat'),
                'keep_selection': options.get('keep_selection'),
                'repeat_word': options.get('repeat_word', 0)
            })
        return result
    def format(self, items, options):
        if options.get('reverse'):
            items.reverse()
        # format list
        if options.get('to_lower_case'):
            items = [item.lower() for item in items]
        elif options.get('to_upper_case'):
            items = [item.upper() for item in items]
        elif options.get('capitalize'):
            items = [item.capitalize() for item in items]
        return items
    def create_preset_command(self, start, end, options, items):
        zero_based = False
        if start and is_numeric(start):
            start = int(start)
        elif start:
            lower_items = [x.lower() for x in items]
            start = lower_items.index(start.lower()) if start.lower() in lower_items else None
            zero_based = start is not None
        if end and is_numeric(end):
            end = int(end)
        elif end:
            end = lower_items.index(end.lower()) if end.lower() in lower_items else None
            zero_based = end is not None
        if not zero_based and not settings().get('preset_zero_based_index', False):
            if start and start > 0:
                start -= 1
            if end and end > 0:
                end -= 1
        if start is not None and end is not None and start > end:
            end += len(items)
            items.extend(items)
        if end is not None and end > len(items):
            while len(items) < end:
                items.extend(items)
        if start is not None and end is None:
            # we have a start index, but no end index
            items.extend(items[:start])
        if end and global_settings('preset_include_end_index', True):
            end += 1
        return items[start:end]
    def create_command(self, shortcut, refs=None):
        cmd = shortcut['command']
        args = None
        if 'args' in shortcut:
            args = shortcut['args']
        if refs and args:
            # text = re.sub(r'([^\\])\$(\d+)', r'(\2)', json.dumps(args)))
            # args = json.loads(text)
            return CommandParser(cmd, args, refs).create_command()
        return dict(command=cmd, args=args)
class CommandParser(object):
    def __init__(self, command, args, refs=None):
        self.command = command
        self.args = args
        self.refs = refs
    def parse(self, args):
        arr = {}
        for key, value in args.items():
            if isinstance(value, dict):
                arr[key] = self.parse(value)
            elif value:
                arr[key] = self.inject(value)
            else:
                arr[key] = value
        return arr
    def inject(self, value):
        if str(value) in self.refs:
            value = self.refs[str(value)]
        return value
    def create_command(self):
        args = self.args
        if self.refs:
            args = self.parse(self.args)
        return dict(command=self.command, args=args)


class CommandLineParser(object):
    def __init__(self, input_text):
        self.input_text = input_text
        self.remains = None
    def parse(self):
        return self.input_text
    def split(self, command_line):
        if command_line:
            return command_line.split()
        else:
            return []


class OptionsParser(CommandLineParser):
    def add(self, key, value):
        if key not in self.options:
            self.options[key] = value
            return True
        else:
            return False
    def enable(self, key):
        return self.add(key, True)
    def disable(self, key):
        return self.add(key, False)
    def parse(self):
        self.options = {}
        remains = []
        args = self.split(self.input_text)
        if not args:
            return self.input_text
        for value in args:
            arg = value.lower()
            if arg in ['reverse', 'rev']:
                if not self.enable("reverse"):
                    remains.append(value)
            elif arg in ['clear-selection', 'clear']:
                if not self.disable("keep_selection"):
                    remains.append(value)
            elif arg in ['keep-selection', 'keep']:
                if not self.enable("keep_selection"):
                    remains.append(value)
            elif arg in ['repeat', 'rep']:
                if not self.enable("repeat"):
                    remains.append(value)
            elif arg in ['norepeat', 'norep', 'no-repeat', 'no-rep']:
                if not self.disable("repeat"):
                    remains.append(value)
            elif arg in ['upper', 'upper-case', 'uc']:
                if not self.enable("to_upper_case"):
                    remains.append(value)
            elif arg in ['lower', 'lower-case', 'lc']:
                if not self.enable("to_lower_case"):
                    remains.append(value)
            elif arg in ['capitalize', 'capitals', 'caps', 'cap']:
                if not self.enable("capitalize"):
                    remains.append(value)
            elif arg.lower().startswith('each='):
                if not self.add('repeat_word', int(arg[5:])):
                    remains.append(value)
            elif arg.lower().startswith('padding='):
                if not self.add('padding', int(arg[8:])):
                    remains.append(value)
            elif arg.lower().startswith('loop='):
                if not self.add('loop', int(arg[5:])):
                    remains.append(value)
            elif arg.startswith('x') and re.match(r"^x\d+$", arg) is not None:
                if not self.add('repeat_word', int(arg[1:])):
                    remains.append(value)
            else:
                remains.append(value)
        if len(self.options) == 0:
            self.remains = self.input_text
        elif remains:
            # this will eat double spaces
            self.remains = ' '.join(remains)
        return self.remains


class PresetCommandParser(OptionsParser):
    def parse(self):
        s = super(PresetCommandParser, self).parse()
        name = None
        start = None
        end = None
        remains = []
        for arg in s.split():
            if arg in '-:,':
                pass
            elif name is None:
                # first will always be the name of the preset
                name = arg
            elif start is None:
                start = arg
            elif end is None:
                end = arg
            else:
                remains.append(arg)
        if remains:
            self.remains = ' '.join(remains)
            print('remaining commands found:', self.remains)
        return (name, start, end, self.options)


class RangeCommandParser(OptionsParser):
    def parse(self):
        s = super(RangeCommandParser, self).parse()
        name = None
        start = None
        stop = None
        step = None
        padding = None
        remains = []
        for pos, arg in enumerate(s.split()):
            if arg in '-:,':
                pass
            elif name is None:
                # first will always be the name
                name = arg
            elif start is None and is_numeric(arg):
                start = int(arg)
            elif stop is None and is_numeric(arg):
                stop = int(arg)
            elif step is None and is_numeric(arg):
                step = int(arg)
            elif padding is None and is_numeric(arg):
                padding = int(arg)
            else:
                remains.append(arg)
        if remains:
            self.remains = ' '.join(remains)
            print('remaining commands found:', self.remains)
            return None
        args = self.options
        args.update({'start': start, 'stop': stop, 'step': step})
        if padding:
            args['padding'] = padding
        if 'repeat_word' in args and args['repeat_word']:
            args['repeat_increment'] = args['repeat_word']
        return dict(command='text_pastry_range', args=args)


class StepCommandParser(OptionsParser):
    def parse(self):
        current = None
        step = None
        padding = None
        fillchar = None
        justify = None
        align = None
        prefix = None
        suffix = None
        repeat = None
        repeat_increment = None
        end = None
        loop = None
        flags = {}
        remains = []
        for pos, arg in enumerate(self.input_text.split()):
            if arg in ['-o', '--option', '--options']:
                flags['options'] = True
                continue
            elif arg.lower() in ['ls', 'sl']:
                fillchar = ' '
                justify = 'right'
            elif arg.lower() in ['lz', 'zl', 'l0', '0l']:
                fillchar = '0'
                justify = 'right'
            elif arg.lower() in ['rs', 'sr']:
                fillchar = ' '
                justify = 'left'
            elif arg.lower() in ['rz', 'zr', 'r0', '0r']:
                fillchar = '0'
                justify = 'left'
            elif arg.lower() in ['space', 's']:
                fillchar = ' '
            elif arg.lower() in ['zero', 'z']:
                fillchar = '0'
            elif arg.lower() in ['padleft', 'rjust', 'left', 'l']:
                justify = 'right'
            elif arg.lower() in ['padright', 'ljust', 'right', 'r']:
                justify = 'left'
            elif arg.lower() in ['prepend', 'append']:
                align = arg.lower()
            elif arg.lower().startswith('prefix='):
                prefix = arg[7:]
            elif arg.lower().startswith('suffix='):
                suffix = arg[7:]
            elif arg.lower().startswith('each='):
                repeat_increment = int(arg[5:])
            elif arg.lower().startswith('end='):
                end = int(arg[4:])
            elif arg.lower().startswith('loop='):
                loop = int(arg[5:])
            elif arg.lower().startswith('x') and re.match(r"^x\d+$", arg) is not None:
                repeat_increment = int(arg[1:])
            else:
                remains.append(arg)
        # regex matchers
        if len(remains) > 0:
            s = ' '.join(remains)
            regex = r'^(?:\\?[iI])?[\s(]*(-?\d+)(?:[\s,]*(-?\d+))?(?:[\s,]*(-?\d+))?(?:[\s,]*(-?\d+))?[\s)]*$'
            m1 = re.match(regex, s)
            if m1:
                current = int(m1.group(1))
                if m1.group(2):
                    step = int(m1.group(2))
                if m1.group(3):
                    padding = int(m1.group(3))
                if m1.group(4):
                    repeat_increment = int(m1.group(4))
                remains = []
        if len(remains) == 0 and current is not None:
            # default values if valid
            start = current
            stop = None
            step = 1 if step is None else step
            padding = 1 if padding is None else padding
            if repeat is not None and step is not None and step != 0:
                stop = start + ((repeat -1) * step)
            if end:
                stop = int(end)
            return dict(command='text_pastry_range', args={'start': start, 'stop': stop, 'step': step, 'padding': padding, 'fillchar': fillchar,
                        'justify': justify, 'align': align, 'prefix': prefix, 'suffix': suffix, 'repeat_increment': repeat_increment, 'loop': loop})


class WordsParser(OptionsParser):
    def parse(self):
        text=None
        separator=None
        clipboard=False
        items=None
        regex=False
        keep_selection=None
        update_selection=None
        repeat=None
        strip=None
        threshold=1
        align=None
        by_rows=False
        repeat_word=0
        SEPARATOR_TOKEN=False
        REPEAT_TOKEN=False
        flags = {}
        remains = []
        for pos, arg in enumerate(self.input_text.split()):
            if arg in ['-o', '--option', '--options']:
                flags['options'] = True
                continue
            elif arg in ['--separator', '--sep']:
                SEPARATOR_TOKEN = True
                continue
            elif SEPARATOR_TOKEN:
                separator = arg
                SEPARATOR_TOKEN = False
            elif arg in ['--clipboard']:
                clipboard = True
            elif arg in ['--no-clipboard']:
                clipboard = False
            elif arg in ['--regex']:
                regex = True
            elif arg in ['--no-regex']:
                regex = False
            elif arg in ['--keep-selection']:
                keep_selection = True
            elif arg in ['--no-keep-selection']:
                keep_selection = False
            elif arg in ['--update-selection']:
                update_selection = True
            elif arg in ['--no-update-selection']:
                update_selection = False
            elif arg in ['--repeat']:
                repeat = True
            elif arg in ['--no-repeat']:
                repeat = False
            elif arg in ['--repeat-word']:
                REPEAT_TOKEN = True
            elif REPEAT_TOKEN and is_numeric(arg):
                repeat_word = int(arg)
                REPEAT_TOKEN = False
            elif arg in ['--no-repeat-word']:
                repeat_word = 0
            elif arg in ['--strip']:
                strip = True
            elif arg in ['--no-strip']:
                strip = False
            elif arg in ['--align']:
                align = True
            elif arg in ['--no-align']:
                align = False
            elif arg in ['--by-row']:
                by_rows = True
            elif arg in ['--no-by-row']:
                by_rows = False
            elif arg.startswith('x') and re.match(r"^x\d+$", arg) is not None:
                repeat_word = int(arg[1:])
            else:
                remains.append(arg)
        text = ' '.join(remains)
        return dict(command='text_pastry_insert_text', args={
            'text': text, 'separator': separator, 'clipboard': clipboard, 
            'items': items, 'regex': regex, 'keep_selection': keep_selection, 
            'update_selection': update_selection, 'repeat': repeat, 'strip': strip, 
            'threshold': threshold, 'align': align, 'by_rows': by_rows, 'repeat_word': repeat_word})


class Overlay(object):
    def __init__(self):
        self._items = []
    def addMenuItem(self, command, label, args=None):
        self._items.append(
            MenuItem(command=command, args=args, label=label)
        )
    def addSpacer(self):
        self._items.append(SpacerItem())
    def addHistoryItem(self, item):
        self._items.append(HistoryItem.from_item(item))
    def addSetting(self, name, value):
        self._items.append(SettingItem(
            'text_pastry_setting',
            {"name": name, "value": value}, name))
    def get(self, index):
        item = None
        if index >= 0 and index < len(self._items): item = self._items[index]
        return item
    def items(self):
        min_size = 0
        command_column_size = label_column_size = min_size
        # check width
        for idx, item in enumerate(self._items):
            (command_width, label_width) = item.width(idx)
            if command_width > command_column_size:
                command_column_size = command_width
            if label_width > label_column_size:
                label_column_size = label_width
        return [item.format(command_column_size, label_column_size, idx) for idx, item in enumerate(self._items)]
    def is_valid(self):
        return self._items and len(self._items) > 0
    def length(self):
        return len(self._items)
class OverlayItem(object):
    type = 0
    def __init__(self, command=None, args=None, label=None, text=None, separator=None):
        self.command = command
        self.args = args
        self.label = label
        self.text = text
        self.separator = separator
    def width(self, width):
        padding = 2
        command_width = len(self.command) + padding if self.command else 0
        label_width = len(self.label) + padding if self.label else 0
        return (command_width, label_width)
class MenuItem(OverlayItem):
    def format(self, command_width, label_width, index):
        text = self.command.ljust(command_width, ' ')
        text += self.label
        return text
class SettingItem(OverlayItem):
    def enabled(self):
        return self.args.get('value', False)
    def checkbox(self):
        return "[ X ]" if self.enabled() else "[   ]"
    def format(self, command_width, label_width, index):
        return self.checkbox() + "  " + self.label
    def width(self, index):
        return (len(self.checkbox()) + 2, 0)
class HistoryItem(OverlayItem):
    type = 2
    @classmethod
    def from_item(cls, item):
        data = item.get('data')
        if data and 'command' in data:
            return cls(command=data["command"], args=data["args"], label=item["label"], text=data["text"])
        return None
    def command_name(self, index):
        return '!hist_' + str(index + 1)
    def format(self, command_size, label_size, index):
        text = self.command_name(index).ljust(command_size, ' ')
        text += self.label
        return text
    def width(self, index):
        command = self.command_name(index)
        command_width = len(command) if command else 0
        label_width = len(self.label) if self.label else 0
        return (command_width, label_width)
class SpacerItem(OverlayItem):
    type = 3
    def format(self, command_width, label_width, index):
        return ""
    def width(self, index):
        return (0, 0)

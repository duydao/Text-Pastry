import sublime
import sublime_plugin
import re
import time
import hashlib
import json
import shlex
import threading
import time
import gc
import unittest
from bisect import bisect, bisect_left

SETTINGS_FILE = "TextPastrySelection.sublime-settings"


def perf_counter():
    if hasattr(time, 'perf_counter'):
        return time.perf_counter()
    else:
        return time.clock()


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


class SelectionCommandParser(OptionsParser):
    quoted_text = None
    def parse_quotes(self, command_line):
        if not command_line:
            return []
        # handle double space
        matches = re.finditer(r'(?:^| )(?<!\\)("|\')(?P<pattern>.+?)(?<!\\)\1(?: |$)', command_line)
        quoted = []
        for m in matches:
            # remove from line, use as remains
            quoted.append(m.group('pattern'))
            # strip quoted text from command line
            command_line = command_line[0:m.start()] + command_line[m.end():-1]
        self.quoted_text = ' '.join(quoted)
        if command_line:
            return command_line.split()
        else:
            return []
    def parse(self):
        s = super(SelectionCommandParser, self).parse()
        command = None
        context = None
        scope = None
        flags = {}
        remains = []
        # remove double space from args
        for value in self.parse_quotes(s):
            arg = value.lower()
            is_option = False
            if 'options' in flags and flags['options']:
                is_option = True
            elif arg.startswith('--'):
                is_option = True
                arg = arg[2:]
            if arg in ['-', ':', ',', '--']:
                pass
            elif arg in ['from', 'by', 'in']:
                flags[arg] = True
                continue
            elif arg in ['-o', '--option', '--options']:
                flags['options'] = True
                continue
            elif is_option and arg in ['no-regex', 'noregex', 'no-regexp', 'noregexp', 'no-re', 'nore', 'lit', 'literal', 'nr', 'text']:
                self.options["use_regex"] = False
            elif is_option and arg in ['regex', 'regexp', 're']:
                self.options["use_regex"] = True
            elif is_option and arg in ['no-ignore', 'noignore', 'case-sensitive', 'cs', 'compare-case', 'comparecase', 'cc']:
                self.options["ignore_case"] = False
            elif is_option and arg in ['ignore', 'case-insensitive', 'ci', 'ignore-case', 'ignorecase', 'ic']:
                self.options["ignore_case"] = True
            elif command is None and arg in ['find', 'filter', 'add', 'remove', 'reduce', 'subtract', 'search']:
                command = arg
            elif context is None and 'in' in flags and arg in ['file', 'selection', 'all', 'both']:
                context = arg
                self.options['context'] = context
            elif scope is None and 'by' in flags and arg in ['line', 'lines', 'word', 'words', 'bound', 'bounds', 'view']:
                scope = arg
                self.options['scope'] = scope
            else:
                remains.append(value)
            # reset flags
            flags = {}
        if (self.options or command) and remains:
            self.remains = ' '.join(remains)
        elif command is None:
            self.remains = self.input_text
        if not (self.remains.isupper() or self.remains.islower()):
            self.options['mixed_case'] = True
        if self.quoted_text:
            self.remains = self.quoted_text
        # treat remains as expression
        return dict(command=command, args=self.options)


class SelectionHelper():
    @classmethod
    def scroll_into_view(cls, view, regions):
        if regions and len(regions) > 0:
            # scroll to the first selection if no selections in viewport
            found_region = False
            visible_region = view.visible_region()
            for region in regions:
                if region.intersects(visible_region):
                    # we have found a selection in the visible region, do nothing
                    found_region = True
                    break
            if not found_region:
                view.show(regions[0], True)


class SelectionHistoryManager(HistoryManager):
    file = "TextPastrySelectionHistory.sublime-settings"
    field = 'pattern'
    def generate_key(self, data):
        return hashlib.md5(data[self.field].encode('UTF-8')).hexdigest()
    def items(self):
        entries = [item['data'][self.field] for item in self.history() if 'data' in item and self.field in item['data']]
        return entries
    def append(self, data, label=None):
        if self.field in data and len(data[self.field]) > 0:
            super(SelectionHistoryManager, self).append(data, label)
            HistoryHandler.append(data[self.field])
class TextPastrySelectionHistoryNavigatorCommand(sublime_plugin.TextCommand):
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


class TextPastrySelectionCommand(sublime_plugin.WindowCommand):
    label = 'Find by Regex'
    use_regex = True
    keep = True
    context = 'file'
    operator = None
    def get_args(self, pattern):
        return {
            'pattern': pattern,
            'keep': self.keep,
            'context': self.context,
            'operator': self.operator,
            'use_regex': self.use_regex
        }
    def setup(self):
        if not hasattr(self, 'history'):
            self.history = SelectionHistoryManager()
            HistoryHandler.setup(self.history.items())
    def run(self, *args, **kwargs):
        if not self.window.active_view():
            return
        self.setup()
        self.use_regex = global_settings('selection_use_regex', True)
        # kwargs takes precedence
        self.use_regex = kwargs.get('use_regex', self.use_regex)
        self.keep = kwargs.get('keep', self.keep)
        self.context = kwargs.get('context', self.context)
        self.operator = kwargs.get('operator', self.operator)
        self.show_input_panel(self.label)
    def show_input_panel(self, label, last_pattern=''):
        view = self.window.show_input_panel(label, last_pattern, self.on_done, None, None)
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
        settings.set('text_pastry_selection_command_line', True)
        color_scheme = settings.get('color_scheme')
        if color_scheme:
            settings.set('color_scheme', color_scheme)
    def is_enabled(self, *args, **kwargs):
        enabled = True
        if 'context' in kwargs and kwargs['context'] == 'selection':
            enabled = False
            sel = self.window.active_view().sel()
            if len(sel) and not sel[0].empty() or len(sel) > 1:
                enabled = True
        return enabled
    def on_done(self, pattern):
        if pattern:
            args = self.get_args(pattern)
            self.history.append(data={'pattern': pattern, 'command': 'text_pastry_modify_selection', 'args': args}, label=pattern)
            view = self.window.active_view()
            view.run_command('text_pastry_modify_selection', args)
            SelectionPreview.clear()
class TextPastryKeepSelectionCommand(TextPastrySelectionCommand):
    def run(self, keep):
        view = self.window.active_view()
        self.pattern = view.substr(sublime.Region(0, view.size()))
        args = self.get_args(pattern)
        SelectionHistoryManager().append(data={'pattern': pattern, 'command': 'text_pastry_modify_selection', 'args': args}, label=pattern)
        self.window.run_command('hide_panel', {"cancel": True})
        # active window
        self.window.run_command('text_pastry_modify_selection', args)
class TextPastrySelectionAdd(TextPastrySelectionCommand):
    """
    Add to selection
    """
    label = 'Add Selection'
    context = 'file'
    keep = True
    operator = 'add'
class TextPastrySelectionSubtract(TextPastrySelectionCommand):
    """
    Remove from selection
    """
    label = 'Reduce Selection'
    context = 'selection'
    keep = True
    operator = 'subtract'
class TextPastrySelectionFilter(TextPastrySelectionCommand):
    """
    Find in selection
    """
    label = 'Filter Selection'
    context = 'selection'
    keep = True
class TextPastrySelectionFind(TextPastrySelectionCommand):
    """
    Default find
    """
    label = 'Find for Selection'
    context = 'both'
    keep = True
    def is_enabled(self, *args, **kwargs):
        return True


class TextPastryModifySelectionCommand(sublime_plugin.TextCommand):
    keep = None
    context = None
    operator = None
    scope = None
    use_regex = False
    threshold = 0
    ignore_case = 0
    _options = None
    cancel = False
    def parse_options(self, input_text):
        parser = SelectionCommandParser(input_text)
        result = parser.parse()
        self._options = result.get('args', {})
        if self._options:
            self.keep = self.option('keep', self.keep)
            self.context = self.option('context', self.context)
            self.scope = self.option('scope', self.use_regex)
            self.use_regex = self.option('use_regex', self.use_regex)
            self.ignore_case = self.option('ignore_case', self.ignore_case)
            self.mixed_case = self.option('mixed_case', False)
        return parser.remains
    def option(self, key, default=None):
        if self._options is None or key not in self._options:
            return default
        return self._options[key]
    def run(self, edit, pattern=None, patterns=None, keep=True, context=None, operator=None, use_regex=None, inline=False):
        if pattern:
            self.modify(edit, pattern, keep, context, operator, use_regex, inline)
        elif patterns:
            for pattern in patterns:
                self.modify(edit, pattern, keep, context, operator, use_regex, inline)
        SelectionHelper.scroll_into_view(self.view, self.view.sel())
    def modify(self, edit, pattern, keep=True, context=None, operator=None, use_regex=None, inline=False):
        # cancel if no pattern
        if not pattern:
            return
        if not inline:
            if len(SelectionPreview.marks) > 0:
                self.view.sel().add_all(SelectionPreview.marks)
                SelectionPreview.clear_marks()
                return
            elif SelectionPreview.dirty(self.view):
                SelectionPreview.marks_to_selection(self.view)
                return
            else:
                pass
        self.keep = keep
        self.context = context
        self.operator = operator
        self.smart_case = False
        self.mixed_case = False
        self.use_regex = use_regex
        if self.use_regex is None:
            self.use_regex = global_settings('use_regex', True)
        self.ignore_case = global_settings('ignore_case', True)
        if self.ignore_case:
            # enable if ignore case
            self.smart_case = global_settings('smart_case', True)
        self.threshold = global_settings('threshold')
        # parse options, those take precedence over command args and setting
        pattern = self.parse_options(pattern)
        # cancel if only options and no search expression
        if not pattern:
            return
        # disable ignore_case if smart_cast is enabled and string has mixed case
        if self.smart_case and self.mixed_case:
            self.ignore_case = False
        # used in find_all
        find_flags = sublime.IGNORECASE if self.ignore_case else 0
        if self.use_regex:
            sublime.status_message('Find by regular expression')
        else:
            # escape regular expression string
            find_flags = sublime.LITERAL | find_flags
            sublime.status_message('Find text')
        # keep selection?
        if not (self.keep or self.context == 'selection'):
            self.sel().clear()
        # print("pattern", pattern, "keep", self.keep, "context", self.context,
        # find_flags)
        regions = self.find(pattern, find_flags)
        if regions:
            start = perf_counter()
            sel = self.sel()
            # check if we only need to filter the current selection
            # CAUTION: should do this afterwards when we use an iterator
            if self.selection_only():
                new_regions = []
                for match in regions:
                    for region in sel:
                        if region.intersects(match):
                            new_regions.append(match)
                regions = new_regions
            has_regex_groups = False
            if self.use_regex:
                try:
                    has_regex_groups = True if re.compile(pattern).groups > 0 else False
                except:
                    self.use_regex = False
                    print('invalid regex, use regular text search')
            if has_regex_groups:
                # reduce selection to regex groups
                # operator is none if its the default find operation
                if self.operator is None:
                    # force clear selection if groups were found
                    sel.clear()
                # filter selection by matches
                for region in regions:
                    if self.cancel:
                        break
                    self.add_all(self.reduce_selection(pattern, region))
            else:
                # add or subtract from selection?
                if self.operator == 'subtract':
                    self.remove_selection(sel, regions)
                else:
                    # operator is None if its a "clean" find operation
                    if self.operator is None:
                        sel.clear()
                    self.add_all(regions)
        else:
            pass
    def add_all(self, regions):
        # add_all is buggy in ST2
        sel = self.sel()
        if int(sublime.version()) > 3000 or hasattr(self, 'preview'):
            sel.add_all(regions)
        else:
            gc.disable()
            [sel.add(region) for region in regions if not self.cancel]
            gc.enable()
    def find(self, pattern, flags):
        file_size = self.view.size()
        threshold = global_settings('preview_file_size_threshold', 10)
        if file_size > 1024 * 1024 * threshold:
            print('threshold reached', threshold, 'MB')
            # render vislble region +/- 4096 chars
            return self.find_in_region(pattern, flags, self.get_visible_region())
        else:
            return self.find_in_region(pattern, flags, sublime.Region(0, file_size))
    def get_visible_region(self):
        chunk_size = global_settings('preview_chunk_size', 10)
        file_size = self.view.size()
        # adjust range by chunk size
        visible_region = self.view.visible_region()
        visible_region.a = max(visible_region.begin() - chunk_size, 0)
        visible_region.b = min(visible_region.end() + chunk_size, file_size)
        return visible_region
    def find_in_region(self, pattern, flags, region):
        text, offset = self.view.substr(region), region.begin()
        timeout = global_settings("preview_find_timeout", 2)
        # function references for readability
        R, tpc = sublime.Region, perf_counter
        # convert sublime flags to regex flags
        re_flags = 0
        if flags & sublime.IGNORECASE:
            re_flags = re.IGNORECASE
        if flags & sublime.LITERAL:
            pattern = re.escape(pattern)
        # compile regex with flags
        try:
            regex = re.compile(pattern, re_flags)
        except:
            regex = re.compile(re.escape(pattern), re_flags)
        matches = regex.finditer(text)
        start_time = tpc()
        return [sublime.Region(m.start() + offset, m.end() + offset) for m in matches if tpc() - start_time < timeout and not self.cancel]
    def remove_selection(self, sel, regions):
        if len(sel) > 0 and len(regions) > 0:
            # workarounds for bug #251 (https://github.com/SublimeText/Issues/issues/251)
            # we need the beginning of all the selections
            # we can savely remove regions where begin == end (e.g. cursors)
            selection_start_list = [region.begin() for region in sel if region.begin() is not region.end()]
            # reverse worklist or it won't work
            regions.reverse()
            for region in regions:
                if region.begin() in selection_start_list:
                    # workarounds for bug #251 (https://github.com/SublimeText/Issues/issues/251)
                    sel.subtract(sublime.Region(region.begin() + 1, region.end()))
                    sel.subtract(sublime.Region(region.begin(), region.begin() + 1))
                else:
                    sel.subtract(region)
    def reduce_selection(self, pattern, region):
        new_regions = []
        text = self.view.substr(region)
        match = re.match(pattern, text)
        if match:
            for index in range(1, len(match.groups()) + 1):
                # if (match.group(index)):
                start = region.a + match.start(index)
                end = region.a + match.end(index)
                if self.option('reverse', False):
                    start, end = end, start
                new_regions.append(sublime.Region(start, end))
        return new_regions
    def selection_only(self):
        selection_only = False
        sel = self.sel()
        if (self.context == 'selection' or self.context == 'both') and len(sel):
            # if multiple lines, always true
            if len(sel) > 1:
                selection_only = True
            # check threshold
            elif self.threshold and not sel[0].empty():
                text = self.view.substr(sel[0])
                match = re.search(self.threshold, text)
                if match:
                    selection_only = True
            # no valid selection
            else:
                selection_only = False
        return selection_only
    def sel(self):
        return self.view.sel()
class TextPastryPreviewSelectionCommand(TextPastryModifySelectionCommand):
    selection = None
    commands = []
    @classmethod
    def create(cls, view):
        # stop all selection commands
        TextPastryPreviewSelectionCommand.cancel_all()
        # create a new one
        command = TextPastryPreviewSelectionCommand(view)
        TextPastryPreviewSelectionCommand.append(command)
        return command
    @classmethod
    def cancel_all(cls):
        for item in commands:
            item.cancel
        commands = []
    def sel(self):
        if self.selection is None:
            self.selection = Selection()
            currentselection = self.view.get_regions(SelectionPreview.KEY)
            self.selection.add_all(currentselection)
        return self.selection


class SelectionListener(sublime_plugin.EventListener):
    view = None
    last_view_id = 0
    def is_command_line(self, view):
        return view.settings().get('text_pastry_command_line', False)
    def on_modified_async(self, view):
        if self.is_command_line(view):
            if view.size() > 6 and view.substr(sublime.Region(0, 6)).lower() == 'search':
                view.run_command('text_pastry_selection_preview')
    def on_window_command(self, window, command_name, args):
        if command_name == 'hide_panel':
            SelectionPreview.clear()
            SelectionPreview.clear_marks()
    def on_deactivated(self, view):
        self.last_view_id = view.id()
        if self.is_command_line(view) and SelectionPreview.dirty(sublime.active_window().active_view()):
            self.view = view
            # save marks
            SelectionPreview.save_marks(sublime.active_window().active_view())
    def on_activated(self, view):
        if self.view:
            is_main_view = True if view == sublime.active_window().active_view() else False
            came_from_command_line = True if self.last_view_id == self.view.id() else False
            if (view == self.view and view.size() > 0) or (is_main_view and came_from_command_line):
                # either focus back to command line or switch to main view from command line
                SelectionPreview.restore_marks(sublime.active_window().active_view())
            elif view == self.view and view.size() == 0:
                # new command line
                SelectionPreview.clear_marks()


class Selection(list):
    def is_valid(self):
        return True
    def merge(self):
        last = None
        a = []
        for current in self:
            # print('merge', a)
            if last is None:
                a.append(current)
                last = current
            elif last.contains(current):
                pass
            elif current.contains(last):
                a[-1] = current
                last = current
            elif last.intersects(current):
                a[-1] = last.cover(current)
                last = a[-1]
            elif last.end() > current.begin():
                # merge
                a[-1] = sublime.Region(last.a, current.b)
                last = a[-1]
            else:
                # doesn't intersect, so add
                a.append(current)
                last = current
        # print('before', self[:], 'after', a)
        self[:] = a
    def add(self, region):
        if len(self) == 0:
            self.append(region)
            return
        # merge the rest
        check_items = self
        tmp = []
        start = bisect(self, sublime.Region(region.begin(), region.begin())) - 1
        start = 0 if start < 0 else start
        end = bisect(self, sublime.Region(region.end(), region.end()))
        end = 0 if end < 0 else end
        if end == 0:
            self.insert(0, region)
            return
        elif start == len(self):
            self.append(region)
            return
        check_items = self[start:end]
        start_time = perf_counter()
        for item in check_items:
            if region.intersects(item):
                region = region.cover(item)
            else:
                tmp.append(item)
        self[start:end] = tmp
        # insert new region
        i = bisect_left(self, region)
        self.insert(i, region)
    def add_all(self, regions):
        if len(self):
            # swap target for performance, since regions should be sorted and unique
            if len(self) < len(regions):
                self[:], regions = regions, self[:]
            gc.disable()
            timeout = global_settings("preview_process_timeout", 2)
            tpc, start_time = perf_counter, perf_counter()
            [self.add(region) for region in regions if region is not None and tpc() - start_time < timeout]
            gc.enable()
        else:
            self[:] = regions
    def subtract(self, region):
        a = []
        for current in self:
            c1, c2 = c = (current.begin(), current.end())
            r1, r2 = r = (region.begin(), region.end())
            if c == r or region.contains(current):
                # don't add
                pass
            elif current.contains(region):
                if r1 > c1:
                    a.append(sublime.Region(c1, r1))
                if r2 < c2:
                    a.append(sublime.Region(r2, c2))
            elif c1 <= r1 <= c2:
                # adjust end
                a.append(sublime.Region(c1, r1))
            elif c1 <= r2 <= c2:
                # adjust start
                a.append(sublime.Region(r2, c2))
            else:
                a.append(current)
        # print('subtract', region, 'from', self)
        # print('result', a)
        # print('=======================================')
        self[:] = a
    def contains(self, region):
        regions = [r for r in self if r.contains(region.begin()) or r.contains(region.end())]
        # print(self, region, regions)
        return True if len(regions) >= 1 else False
    def clear(self):
        del self[:]


class SelectionPreview(threading.Thread):
    KEY = 'text_pastry_selection'
    selections = []
    marks = []
    def __init__(self, view=None, regions=None):
        self.view = view
        self.regions = regions
    def run(self):
        if self.view and self.regions:
            self.draw(self.view, self.regions)
    @classmethod
    def draw(cls, view, regions):
        if regions is None:
            cls.clear()
            return
        flags = 0
        flags = sublime.DRAW_NO_OUTLINE
        scope = ['text', SelectionPreview.KEY]
        if flags == sublime.DRAW_NO_OUTLINE:
            scope.append('fill')
        elif flags == sublime.DRAW_NO_FILL:
            scope.append('outline')
        view.add_regions(SelectionPreview.KEY, regions, '.'.join(scope), '', flags)
        SelectionHelper.scroll_into_view(view, regions)
    @classmethod
    def dirty(cls, view):
        return len(view.get_regions(SelectionPreview.KEY)) > 0
    @classmethod
    def clear(cls):
        view = sublime.active_window().active_view()
        view.erase_regions(SelectionPreview.KEY)
        cls.restore_selection(view)
    @classmethod
    def save_selection(cls, view):
        if len(view.sel()) > 0:
            cls.selections.append(view.sel())
            view.sel().clear()
    @classmethod
    def restore_selection(cls, view):
        # restore_selection
        if cls.selections and len(view.sel()) == 0:
            view.sel().add_all(cls.selections.pop())
    @classmethod
    def marks_to_selection(cls, view):
        marks = cls.marks
        if len(cls.marks) == 0:
            marks = view.get_regions(cls.KEY)
        view.sel().add_all(marks)
        cls.clear()
        cls.clear_marks()
    @classmethod
    def save_marks(cls, view):
        cls.marks = view.get_regions(cls.KEY)
        cls.clear()
    @classmethod
    def get_marks(cls):
        return cls.marks
    @classmethod
    def restore_marks(cls, view):
        # restore_selection
        if cls.marks:
            cls.draw(view, cls.marks)
            del cls.marks[:]
    @classmethod
    def clear_marks(cls):
        del cls.marks[:]
class TextPastrySelectionPreviewCommand(sublime_plugin.TextCommand):
    def run(self, edit, *args, **kwargs):
            command = 'search'
            size = len(command)
            min_length = global_settings('preview_min_length', 0)
            if self.view.size() > 6 + min_length:
                start = perf_counter()
                pattern = self.view.substr(sublime.Region(0, self.view.size()))
                active_view = sublime.active_window().active_view()
                SelectionPreview.save_selection(active_view)
                separator_pattern = r'\s*\|\s*'
                command_list = 'find|search|add|remove|reduce|subtract|filter|live'
                sre = r'(?P<sep>{sep})?\b(?P<command>{command}) (?P<content>.*?)\s*?(?=(?:{sep})|(?:{command})|$)'.format(sep=separator_pattern, command=command_list)
                command_pattern = re.compile(sre, re.IGNORECASE)
                selection = Selection()
                for match in command_pattern.finditer(self.view.substr(sublime.Region(0, self.view.size()))):
                    command = TextPastryPreviewSelectionCommand(active_view)
                    command.selection = selection
                    command.run(None, match.group('content'), **self.command_options(match.group('command')))
                    command.selection = None
                selection_preview = SelectionPreview()
                selection_preview.draw(active_view, selection)
                selection = None
                sublime.status_message('done: ' + str(perf_counter() - start) + 's')
            else:
                print('clearing', self.view.size())
                SelectionPreview.clear()
    def command_options(self, command):
        context = None
        operator = None
        if command in ['reduce', 'remove', 'subtract']:
            context = "selection"
            operator = "subtract"
        elif command in ['find', 'search']:
            context = None
            operator = None
        elif command in ['add']:
            context = 'file'
            operator = 'add'
        elif command in ['filter']:
            context = 'selection'
            operator = None
        return {"context": context, "operator": operator, "inline": True}

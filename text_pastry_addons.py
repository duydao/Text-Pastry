import sublime
import sublime_plugin
import threading
import time
import os

SETTINGS_FILE = "TextPastryAddons.sublime-settings"

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


class TextPastryFocusCommand(sublime_plugin.WindowCommand):
    state = 0
    enabled = False
    def run(self):
        enable_focus = False if TextPastryFocusCommand.enabled else True
        run = self.window.run_command
        for command in global_settings("focus", []):
            visible = TextPastryPanelListener.visibility.get(command, True)
            if enable_focus and visible:
                run(command)
            elif not enable_focus and not visible:
                run(command)
        ref = TextPastryFocusCommand
        ref.enabled = True if enable_focus else False
        if ref.enabled:
            # focus mode enabled
            run('hide_panel', {'cancel': True})
class TextPastryPanelListener(sublime_plugin.EventListener):
    #listener = ['toggle_side_bar', 'toggle_status_bar', 'toggle_tabs', 'toggle_minimap']
    listener = []
    running = False
    visibility = {}
    def on_window_command(self, window, command, args):
        if command in self.listener and not self.running:
            self.running = True
            TextPastryPanelListener.visibility[command] = self.is_visible(window, command, args)
            self.running = False
            return ('text_pastry_cancel', None)
    def is_visible(self, window, command, args=None):
        view = window.active_view()
        w1, h1 = view.viewport_extent()
        window.run_command(command, args)
        w2, h2 = view.viewport_extent()
        w, h = w2 - w1, h2 - h1
        return True if w < 0 or h < 0 else False
class TextPastryCancelCommand(sublime_plugin.TextCommand):
    def run(self, *args, **kwargs):
        pass


class TextPastryKeyBindingCommand(sublime_plugin.TextCommand):
    def run(self, edit, key=None, command=None):
        if command:
            settings().set(key, command)
            sublime.status_message('bound ' + key + ' to ' + command)
        elif key:
            command = settings().get(key)
            if command:
                if command not in ['text_pastry_prev_view', 'text_pastry_next_view']:
                    print('running', command)
                self.view.window().run_command(command)
        else:
            print('up:', settings().get('up'))
            print('down:', settings().get('up'))


class Delay(threading.Thread):
    cancel = False
    def __init__(self):
        super(Delay, self).__init__()
    def run(self):
        hide_tab_delay = global_settings("hide_tab_delay", 3)
        time.sleep(hide_tab_delay)
        if not self.cancel and TextPastryFocusCommand.enabled:
            sublime.active_window().run_command('toggle_tabs')
    def stop(self):
        self.cancel = True
class TextPastryPrevViewNextViewCommand(sublime_plugin.TextCommand):
    command = None
    timer_id = None
    _delay = None
    @classmethod
    def clear_delay(cls):
        if cls._delay is not None:
            cls._delay.stop()
            cls._delay = None
    def run(self, edit):
        commands = global_settings("focus")
        if 'toggle_tabs' in commands and TextPastryFocusCommand.enabled:
            if not self.visible():
                # toggle if not visible
                self.view.window().run_command('toggle_tabs')
            # start a new delay
            self.delay()
        self.view.window().run_command(self.command)
    def delay(self):
        ref = TextPastryPrevViewNextViewCommand
        if ref._delay:
            ref._delay.stop()
        ref._delay = Delay()
        ref._delay.start()
    def visible(self):
        return TextPastryPanelListener.visibility.get('toggle_tabs', True)
class TextPastryPrevViewCommand(TextPastryPrevViewNextViewCommand):
    command = 'prev_view'
class TextPastryNextViewCommand(TextPastryPrevViewNextViewCommand):
    command = 'next_view'


class TextPastryScopeNameCommand(sublime_plugin.TextCommand):
    def run(self, edit):
        for sel in self.view.sel():
            name = self.view.scope_name(sel.begin())
            print(name)


class TextPastryStyleCommand(sublime_plugin.WindowCommand):
    def run(self, toggle=None, index=None):
        if toggle:
            index = settings().get('style_index')
            self.change_style(index + 1)
        elif index:
            settings().set('style', kwargs.get('style'))
            self.change_style(index + 1)
            settings().set('style_index', 0)
    def change_style(self, index=0):
        name = settings().get('style')
        styles = settings().get('styles', {}).get(name, [])
        if len(styles):
            i = index if index < len(styles) else 0
            config = styles[i]
            # update settings of view
            view_settings = self.window.active_view().settings()
            [view_settings.set(key, config[key]) for key in config]
            # set current group name
            settings().set('style_index', i)
            print('settings updated to', i, config, styles)
        else:
            print('no set found', name, styles)


class TextPastryOpenFileCommand(sublime_plugin.WindowCommand):
    def run(self, key=None):
        if key is None:
            return
        settings = sublime.load_settings('Preferences.sublime-settings')
        prefix = sublime.packages_path()
        prefix += '/User/' if 'user' in key else '/Text Pastry/'
        text_pastry_settings_file = 'TextPastry.sublime-settings'
        selection_settings_file = 'TextPastrySelection.sublime-settings'
        addons_settings_file = 'TextPastryAddons.sublime-settings'
        if key == 'color scheme':
            color_scheme = settings.get('color_scheme')
            path = os.path.abspath(sublime.packages_path() + '/../' + color_scheme)
        elif 'selelection settings' in key:
            path = os.path.abspath(prefix + selection_settings_file)
        elif 'addon settings' in key:
            path = os.path.abspath(prefix + addons_settings_file)
        elif 'settings' == key or 'user settings' == key:
            path = os.path.abspath(prefix + text_pastry_settings_file)
        if path:
            self.window.run_command("open_file", {'file': path})

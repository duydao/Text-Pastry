import sublime
import sublime_plugin
import threading
import time
import os
import hashlib
import threading
import uuid

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


def plugin_loaded():
    if global_settings("tracker_autostart", False):
        ClipboardTracker.start_tracker()
    elif global_settings("tracker_enabled", True):
        view = ClipboardHelper.ammo_view()
        if view and view.settings().get("tp_append", False):
            ClipboardTracker.add_listener(AmmoViewClipboardListener.get_instance())
            pass
def plugin_unloaded():
    pass


class ClipboardHelper():
    @staticmethod
    def create_view(name, settings):
        view = sublime.active_window().new_file()
        view.set_name(name)
        view.set_scratch(True)
        view.set_syntax_file("Packages/Text/Plain Text.tmLanguage")
        # apply settings
        for key in settings:
            view.settings().set(key, settings[key])
        return view
    @staticmethod
    def view():
        for view in sublime.active_window().views():
            if view.settings().get("tp_clipboard", False):
                return view
        return None
    @staticmethod
    def template_view():
        for view in sublime.active_window().views():
            if view.settings().get("tp_template", False):
                return view
        return None
    @staticmethod
    def ammo_view():
        for view in sublime.active_window().views():
            if view.settings().get("tp_ammo", False):
                return view
        return None
    @staticmethod
    def is_clipboard(view):
        return view and view.settings().get("tp_clipboard", False)
    @staticmethod
    def create_hash(data):
        m = hashlib.md5()
        m.update(data)
        return m.hexdigest()


class ClipboardTracker(threading.Thread):
    tracker = None
    listeners = []
    counter = 1
    valid_id_list = []
    def __init__(self):
        super(ClipboardTracker, self).__init__()
        self.latest = {}
        self.listeners = []
        self.stop = False
        self.id = "ClipboardTracker-" + str(uuid.uuid4())
        ClipboardTracker.valid_id_list.append(self.id)
    def run(self):
        # init
        self.update_latest(sublime.get_clipboard())
        # check is_enabled in loop so we can deactivate it at any time
        while self.is_valid():
            # load inverval setting here, so we can mess with the settings while it's running
            interval = ClipboardTracker.interval()
            # let's assign since this method can be time consuming
            data = sublime.get_clipboard()
            if self.has_changed(data):
                self.trigger_event("change", data)
            if ClipboardTracker.is_log_enabled():
                ClipboardTracker.log(self)
            # sleep
            time.sleep(interval)
        if self.stop:
            print(self.id, 'Stop set, ClipboardTracker stopped')
        elif len(self.get_listeners()) == 0:
            print(self.id, 'No listeners left, ClipboardTracker stopped')
        elif not self.id in ClipboardTracker.valid_id_list:
            print(self.id, 'Clipboardtracker not in valid ID list, stopped')
        else:
            print(self.id, 'ClipboardTracker stopped')
        if self.id in ClipboardTracker.valid_id_list:
            ClipboardTracker.valid_id_list.remove(self.id)
    def has_changed(self, data):
        changed = False
        # compare length before using hash (for speed)
        if len(data) != self.latest["size"]:
            changed = True
            self.update_latest(data)
        else:
            # compare hash
            data_hash = ClipboardHelper.create_hash(data.encode("utf8"))
            if data_hash != self.latest["hash"]:
                changed = True
                # store current as latest for comparison
                self.update_latest(data)
        return changed
    def is_valid(self):
        return not self.stop and ClipboardTracker.is_enabled() and self.id in ClipboardTracker.valid_id_list
    def get_listeners(self):
        global_listeners = []
        local_listeners = []
        if ClipboardTracker.listeners:
            global_listeners = ClipboardTracker.listeners
        if self.tracker and self.tracker.listeners:
            local_listeners = self.tracker.listeners
        return global_listeners + local_listeners
    @classmethod
    def add_listener(cls, listener):
        if not listener in cls.listeners:
            cls.listeners.append(listener)
        if not ClipboardTracker.is_running():
            ClipboardTracker.start_tracker()
    @classmethod
    def remove_listener(cls, listener):
        if listener in cls.listeners:
            cls.listeners.remove(listener)
        if len(cls.listeners) == 0:
            ClipboardTracker.stop_tracker()
    @classmethod
    def has_listener(cls, listener):
        return listener in cls.listeners
    def trigger_event(self, event, data):
        for listener in self.get_listeners():
            try:
                getattr(listener, "on_" + event)(data)
            except:
                print("Couldn't find listener")
                raise
    def update_latest(self, data):
        # init
        self.latest = {
            'hash': ClipboardHelper.create_hash(data.encode("utf-8")),
            'size': len(data)
        }
    @classmethod
    def log(cls, tracker):
        # load inverval setting here, so we can mess with the settings while it's running
        interval = cls.interval()
        # internal counter
        cls.counter += 1
        # print message every 10 seconds (10 / interval)
        if cls.counter == 1 or cls.counter % (10 / interval) == 0:
            print(cls.counter, tracker.id, "running")
    @classmethod
    def start_tracker(cls):
        if cls.is_enabled():
            if not cls.is_running() or (cls.is_running() and cls.tracker.stop):
                cls.tracker = cls()
                print("Start ClipboardTracker", cls.tracker.id)
                cls.tracker.start()
            else:
                print("ClipboardTracker is already running")
        else:
            print("ClipboardTracker is disabled")
    @classmethod
    def stop_tracker(cls):
        if cls.is_running():
            print("Stop ClipboardTracker", cls.tracker.id)
            cls.tracker.stop = True
            cls.tracker.join(cls.interval())
    @staticmethod
    def interval():
        # make sure we don't go crazy, minimum interval is 0.1
        interval = float(settings().get("tracker_interval", 1))
        return max(interval, 0.1)
    @classmethod
    def is_enabled(cls):
        return settings().get("tracker_enabled", False)
    @staticmethod
    def is_log_enabled():
        return settings().get("tracker_log_enabled", False)
    @classmethod
    def is_running(cls):
        return cls.tracker != None and cls.tracker.is_alive()


class TextPastryClipboardEventListener(sublime_plugin.EventListener):
    def is_valid(self, view):
        file_name = view.file_name()
        return file_name and self.extension() and file_name.endswith( self.extension() )
    def update_clipboard_by_selection(self, view):
        selections = [view.substr(region) for region in view.sel()]
        if selections:
            sublime.set_clipboard("\n".join(selections))
    def update_clipboard(self, view):
        text = view.substr(sublime.Region(0, view.size()))
        sublime.set_clipboard(text)
    def extension(self):
        return None


class TextPastryRangeCommandEventListener(sublime_plugin.EventListener):
    def on_text_command(self, view, command_name, args):
        if self.is_valid(view, command_name):
            # check setting
            end = settings().get("paste_gun_ammo_xarg", 1)
            # extend selection when criterias were met
            if end > 1 and len(view.sel()) == 1:
                region = view.sel()[0]
                if region.begin() == region.end():
                    return ("text_pastry_extend_selection", {"command_name": command_name, "args": args})
    def on_post_text_command(self, view, command_name, args):
        if command_name == "text_pastry_extend_selection" and self.is_valid(view):
            if view.settings().get("tp_ammo_extend_selection", False):
                # clear setting
                view.settings().set("tp_ammo_extend_selection", False)
                # store last
                last = view.sel()[-1]
                # clear selections
                view.sel().clear()
                # add last selection
                view.sel().add(last.end())
    def is_valid(self, view, command_name="text_pastry_range"):
        return command_name == "text_pastry_range" and view.settings().get("tp_ammo", False)
class TextPastryExtendSelectionCommand(sublime_plugin.TextCommand):
    def run(self, edit, command_name, args):
        # add selections
        end = settings().get("paste_gun_ammo_xarg", 1) + 1
        if len(self.view.sel()) == 1 and end > 1:
            region = self.view.sel()[0]    
            if region.begin() == region.end():
                pos = region.begin()
                for i in range(1, end):
                    self.view.sel().add(pos)
                    self.view.insert(edit, pos, "\n")
        # mark
        self.view.settings().set("tp_ammo_extend_selection", True)
        self.view.run_command(command_name, args)


class ClipboardListener():
    instance = None
    @classmethod
    def get_instance(cls):
        if not cls.instance:
            cls.instance = ClipboardListener()
        return cls.instance
    def on_change(self, data):
        # loop over tp_clipboard views
        for window in sublime.windows():
            for view in window.views():
                if view.get_status('inactive'):
                    file_name = view.file_name()
                    # clipboard
                    if view.settings().get("tp_clipboard", False):
                        self.update_clipboard_view(view)
                    elif file_name and file_name.endswith(global_settings("clipboard_file_extension", ".clipboard")):
                        self.update_clipboard_view(view)
                    # template
                    elif view.settings().get("tp_template", False):
                        self.update_template_view(view)
                    elif file_name and file_name.endswith(global_settings("template_file_extension", ".template")):
                        self.update_template_view(view)
    def update_clipboard_view(self, view):
        view.run_command("text_pastry_update_clipboard_view")
    def update_template_view(self, view):
        pass
    def is_valid(self):
        view = ClipboardHelper.view()
        return view and view.window()
class AmmoViewClipboardListener():
    instance = None
    @classmethod
    def get_instance(cls):
        if not cls.instance:
            cls.instance = AmmoViewClipboardListener()
        return cls.instance
    def on_change(self, data):
        # loop over tp_clipboard views
        for window in sublime.windows():
            for view in window.views():
                if view.get_status('inactive') and view.settings().get("tp_append", False):
                    file_name = view.file_name()
                    # ammo
                    if view.settings().get("tp_ammo", False):
                        self.update(view)
                    elif file_name and file_name.endswith(global_settings("ammo_file_extension", ".ammo")):
                        self.update(view)
    def update(self, view):
        if view.settings().get("tp_append", False):
            view.run_command("text_pastry_update_view", {"content": sublime.get_clipboard(), "insert_mode": "append"})


class TextPastryClipboardViewListener(TextPastryClipboardEventListener):
    def on_activated(self, view):
        if self.is_valid(view):
            view.run_command("text_pastry_update_clipboard_view", {"force": True})
            view.erase_status("inactive")
    def on_deactivated(self, view):
        if self.is_valid(view):
            view.set_status("inactive", "True")
            self.update_clipboard(view)
    def on_close(self, view):
        if self.is_valid(view):
            # this will prevent on_deactivated_async
            view.settings().set("tp_clipboard", False)
            ClipboardTracker.remove_listener(ClipboardListener.get_instance())
    def on_modified_async(self, view):
        if self.is_valid(view) and ClipboardHelper.is_live_edit():
            self.update_clipboard(view)
    def is_valid(self, view):
        return view.settings().get("tp_clipboard", False)


class TextPastryClipboardFileViewListener(TextPastryClipboardEventListener):
    def extension(self):
        return global_settings("clipboard_file_extension")
    def on_load(self, view):
        if self.is_valid(view):
            view.set_scratch(True)
    def on_activated_async(self, view):
        if self.is_valid(view):
            self.view.run_command("text_pastry_update_clipboard_view")
    def on_deactivated_async(self, view):
        if self.is_valid(view):
            self.update_clipboard(view)


class TextPastryClipboardTemplateViewListener(TextPastryClipboardEventListener):
    def on_activated(self, view):
        if self.is_valid(view):
            view.erase_status("inactive")
    def on_deactivated(self, view):
        if self.is_valid(view):
            view.set_status("inactive", "True")
    def on_close(self, view):
        if self.is_valid(view):
            # this will prevent on_deactivated_async
            view.settings().set("tp_template", False)
    def on_modified_async(self, view):
        if self.is_valid(view):
            pass
    def is_valid(self, view):
        return view.settings().get("tp_template", False)


class TextPastryTemplateViewListener(TextPastryClipboardEventListener):
    def extension(self):
        return global_settings("template_file_extension")
    def on_activated_async(self, view):
        if self.is_valid(view):
            TextPastryPasteGunCommand.template_selected = view.id()


class TextPastryClipboardAmmoViewListener(TextPastryClipboardEventListener):
    def on_activated(self, view):
        if self.is_valid(view):
            view.erase_status("inactive")
            # mark the current index
            index = view.settings().get('tp_ammo_index', 0)
            view.run_command('text_pastry_paste_gun_marker', {'index': index})
    def on_deactivated(self, view):
        if self.is_valid(view):
            view.set_status("inactive", "True")
    def on_close_async(self, view):
        if self.is_valid(view):
            # this will prevent on_deactivated_async
            ClipboardTracker.remove_listener(AmmoViewClipboardListener.get_instance())
    def is_valid(self, view):
        return view.settings().get("tp_ammo", False)


class TextPastryOpenClipboardCommand(sublime_plugin.WindowCommand):
    NAME = "Clipboard Viewer"
    def run(self):
        view = ClipboardHelper.view()
        if view == None:
            view = ClipboardHelper.create_view("Clipboard Viewer", {"tp_clipboard": True})
            # set initial content
            view.run_command("text_pastry_update_clipboard_view", {"force": True})
        else:
            sublime.active_window().focus_view(view)
    def is_checked(self):
        return ClipboardHelper.view() != None
class TextPastryOpenClipboardTemplateCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = ClipboardHelper.template_view()
        if view == None:
            ClipboardHelper.create_view("Clipboard Template", {"tp_template": True})
        else:
            sublime.active_window().focus_view(view)
    def is_checked(self):
        return ClipboardHelper.template_view() != None
class TextPastryOpenClipboardAmmoCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = ClipboardHelper.ammo_view()
        if view == None:
            settings = {"tp_ammo": True}
            if global_settings("paste_gun_append_clipboard_to_ammo", False):
                settings["tp_append"] = True
                ClipboardTracker.add_listener(AmmoViewClipboardListener.get_instance())
            ClipboardHelper.create_view("Piping Bag", settings)
        else:
            sublime.active_window().focus_view(view)
    def is_checked(self):
        return ClipboardHelper.ammo_view() != None
class TextPastryAppendClipboardToAmmoCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = ClipboardHelper.ammo_view()
        if view:
            if not self.is_checked():
                view.settings().set("tp_append", True)
                ClipboardTracker.add_listener(AmmoViewClipboardListener.get_instance())
            else:
                ClipboardTracker.remove_listener(AmmoViewClipboardListener.get_instance())
                view.settings().erase("tp_append")
    def is_checked(self):
        checked = False
        view = ClipboardHelper.ammo_view()
        has_listener = ClipboardTracker.has_listener(AmmoViewClipboardListener.get_instance())
        if view and has_listener and ClipboardTracker.is_running() and view.settings().get("tp_append", False):
            checked = True
        return checked
    def is_enabled(self):
        return ClipboardHelper.ammo_view() != None
class TextPastryClipboardTrackerActiveCommand(sublime_plugin.WindowCommand):
    def run(self):
        # start if we are NOT in a clipboard view
        if not self.is_checked():
            ClipboardTracker.start_tracker()
        else:
            ClipboardTracker.stop_tracker()
    def is_checked(self):
        return ClipboardTracker.tracker != None and ClipboardTracker.tracker.is_alive()
    def is_enabled(self):
        return False
class TextPastryClipboardLiveEditCommand(sublime_plugin.WindowCommand):
    def run(self):
        view = ClipboardHelper.view()
        if view:
            # toggle
            enabled = not view.settings().get("tp_continuous", False)
            view.settings().set("tp_continuous", enabled)
    def is_checked(self):
        enabled = False
        view = ClipboardHelper.view()
        if view:
            enabled = view.settings().get("tp_continuous", False)
        return enabled
    def is_enabled(self):
        return ClipboardHelper.view() != None


class TextPastryPasteGunKeepSelectionCommand(sublime_plugin.WindowCommand):
    def run(self):
        enabled = not settings().get("paste_gun_keep_selection", True)
        # toggle
        settings().set("paste_gun_keep_selection", enabled)
    def is_checked(self):
        return settings().get("paste_gun_keep_selection", settings().get("keep_selection", True))
class TextPastryClipboardTrackerEnabledCommand(sublime_plugin.WindowCommand):
    def run(self):
        enabled = not settings().get("tracker_enabled", True)
        # toggle
        settings().set("tracker_enabled", enabled)
    def is_checked(self):
        return settings().get("tracker_enabled", True)


class TextPastryResetAmmoPositionCommand(sublime_plugin.WindowCommand):
    def run(self, edit):
        TextPastryPasteGunCommand.reset()
    def is_enabled(self):
        isAmmoViewEnabled = ClipboardHelper.ammo_view() != None
        hasHash = TextPastryPasteGunCommand.hash is not None
        return isAmmoViewEnabled and hasHash


class TextPastryUpdateClipboardViewCommand(sublime_plugin.TextCommand):
    def run(self, edit, force=False):
        if self.has_changed() or force:
            content = sublime.get_clipboard()
            self.view.replace(edit, sublime.Region(0, self.view.size()), content)
            # store md5 hash so we can compare changes
            hash = ClipboardHelper.create_hash(content.encode('utf-8'))
            self.view.settings().set("tp_clipboard_hash", hash)
    def set_running(self, value):
        self.view.settings().set("tp_update_clipboard_view_running", value)
    def is_running(self):
        return self.view.settings().get("tp_update_clipboard_view_running", False)
    def is_enabled(self):
        return not self.is_running() and ClipboardHelper.is_clipboard(self.view)
    def has_changed(self):
        changed = False
        # let's assign value since this method could be time consuming. Limit?
        clipboard = sublime.get_clipboard()
        # compare length before using hash (for speed)
        if len(clipboard) != self.view.size():
            changed = True
        else:
            # compare hash
            clipboard_hash = ClipboardHelper.create_hash(clipboard.encode("utf8"))
            content = self.view.substr(sublime.Region(0, self.view.size()))
            content_hash = ClipboardHelper.create_hash(content.encode('utf-8'))
            if clipboard_hash != content_hash:
                changed = True
        return changed


class TextPastryUpdateViewCommand(sublime_plugin.TextCommand):
    def run(self, edit, content=None, insert_mode="replace"):
        if content:
            if insert_mode == "append":
                prefix = ""
                if self.view.size() > 0:
                    prefix = "\n"
                self.view.insert(edit, self.view.size(), prefix + content)
            else:
                self.view.replace(edit, sublime.Region(0, self.view.size()), content)
            # store md5 hash so we can compare changes
            hash = ClipboardHelper.create_hash(content.encode('utf-8'))
            self.view.settings().set("tp_content_hash", hash)
    def set_running(self, value):
        self.view.settings().set("tp_update_view_running", value)
    def is_running(self):
        return self.view.settings().get("tp_update_view_running", False)
    def is_enabled(self):
        return not self.is_running()


class TextPastryPasteGunMultiSelectCommand(sublime_plugin.TextCommand):
    def run(self, edit, separator=None, rotate=True, repeat=True, keep_selection=True):
        if TextPastryPasteGunCommand.index is None:
            TextPastryPasteGunCommand.index = 0
        for idx, region in enumerate(self.view.sel()):
            self.view.run_command("text_pastry_paste_gun", {
                "index": TextPastryPasteGunCommand.index + 1, "selection_index": idx,
                "separator": separator, "rotate": rotate, "repeat": repeat, "keep_selection": keep_selection})
class TextPastryPasteGunCommand(sublime_plugin.TextCommand):
    panel_name = "tp_clipboard"
    hash = None
    index = None
    done = False
    template_selected = None
    def run(self, edit, index=1, selection_index=0, separator=None, rotate=False, repeat=True, keep_selection=None):
        if index is None:
            return
        # setup index
        idx = int(index) - 1
        # prepare data
        data, index = self.get_data()
        # check hash
        current_hash = TextPastryPasteGunCommand.create_hash(data.encode("utf8"))
        if TextPastryPasteGunCommand.hash != current_hash:
            # let's start fresh
            TextPastryPasteGunCommand.reset()
            idx = index
            TextPastryPasteGunCommand.hash = current_hash
            TextPastryPasteGunCommand.index = idx
        elif TextPastryPasteGunCommand.done:
            # cancel if we're done
            TextPastryPasteGunCommand.reset()
            return
        elif rotate:
            # take next
            idx = TextPastryPasteGunCommand.index
        if separator:
            # format separator
            separator = separator.encode("utf8").decode("unicode-escape")
        elif "\n" in data:
            # use newline if multiple lines
            separator = "\n"
        # setup data, filter empty
        items = list(filter(None, data.split(separator)))
        # check index
        if len(items) <= idx:
            # cancel if index out of bounds
            return
        # get formatted item
        item = self.format(items[idx])
        # replace selection
        region = self.view.sel()[selection_index]
        self.view.replace(edit, region, item)
        # keep selection setting
        if keep_selection is None:
            default_value = settings().get("keep_selection", True)
            keep_selection = settings().get("paste_gun_keep_selection", default_value)
        # clear selection, set cursor to the end
        if not keep_selection:
            sel = self.view.sel()
            region = sel[selection_index]
            sel.clear()
            sel.add(sublime.Region(region.end(), region.end()))
        # check rotate flag
        if rotate:
            if TextPastryPasteGunCommand.index + 1 < len(items):
                # increment static index
                TextPastryPasteGunCommand.index += 1
            elif repeat:
                # reset to 0
                TextPastryPasteGunCommand.index = 0
            else:
                # we're done, mark as done
                TextPastryPasteGunCommand.done = True
        self.save_index();
    def save_index(self):
        # store the index into the view as setting
        view = ClipboardHelper.ammo_view()
        view.settings().set('tp_ammo_index', TextPastryPasteGunCommand.index)
    @staticmethod
    def reset():
        TextPastryPasteGunCommand.index = None
        TextPastryPasteGunCommand.hash = None
        TextPastryPasteGunCommand.done = False
    @staticmethod
    def create_hash(data):
        m = hashlib.md5()
        m.update(data)
        return m.hexdigest()
    def format(self, text):
        formatted = text
        # check for template to apply
        if TextPastryPasteGunCommand.template_selected:
            for view in sublime.active_window().views():
                if view.id == TextPastryPasteGunCommand.template_selected:
                    pass
        return formatted
    def regions(self, view):
        text = view.substr(0, view.size())
        regions = view.get_regions("tp_placeholder")
        for region in regions:
            view.replace()
    def get_data(self):
        data = None
        index = 0
        view = ClipboardHelper.ammo_view()
        if view:
            data = view.substr(sublime.Region(0, view.size()))
            index = view.settings().get('tp_ammo_index', 0)
        else:
            data = sublime.get_clipboard()
        return (data, index)
class TextPastryPasteGunMarkerCommand(sublime_plugin.TextCommand):
    def run(self, edit, index=0):
        region = self.view.line(self.view.text_point(index, 0))
        self.view.add_regions("tp_placeholder", [region], "text_pastry.marker", "bookmark", sublime.DRAW_NO_FILL)
    def is_enabled(self):
        hasClipboard = self.view.file_name() and self.view.file_name().endswith("clipboard")
        isAmmoView = self.view.settings().get('tp_ammo')
        return hasClipboard or isAmmoView

import sublime, sublime_plugin

class Overlay:
    def __init__(self):
        self.items = []

    def add(self, item):
        if item: self.items.append(item)

    def addMenuItem(self, command, label):
        item = MenuItem(command, label)
        if command and label:
            self.items.append( item )
        return item

    def addSpacer(self):
        item = SpacerItem()
        self.items.append( item )
        return item

    def addHistoryItem(self, command, label, text, separator):
        item = HistoryItem(command, label, text, separator)
        if command and text:
            self.items.append( item )
        return item

    def get(self, index):
        item = None
        if index >= 0 and index < len(self.items): item = self.items[index]
        return item

    def all(self):
        entries = []

        width = 12

        for idx, item in enumerate(self.items):
            #if item.text: entries.append( [item.format(width, idx), item.formatText(width)] )
            #else: entries.append( [item.format(width, idx)] )
            entries.append( [item.format(width, idx)] )

        return entries

    def is_valid(self):
        return self.items and len(self.items) > 0

    def length(self):
        return len(self.items)

class Item:
    def __init__(self, command=None, label=None, text=None, separator=None):
        self.command = command
        self.label = label
        self.text = text
        self.separator = separator
    
    def format(self, width, index):
        pass

class MenuItem(Item):
    def format(self, width, index):
        return self.command.ljust(width).rjust(width + 1) + self.label

class HistoryItem(Item):
    def format(self, width, index):
        i = str(index + 1)
        s = ('hist' + i).ljust(width).rjust(width + 1)
        text = self.text
        #s += ' '.join((self.label + " " + text).split())
        s += self.label

        return s
    
    def formatText(self, width):
        text = self.text
        if text and len(text) > 50: text = text[0:50] + "..."
        return ' '.ljust(width + 1).rjust(width + 2) + ' '.join((text).split())

class SpacerItem(Item):
    def format(self, width, index):
        return ""

import sublime, sublime_plugin, re

class CommandLineParser:
	def CommandLineParser():
		sublime.status_message("Creating CommandLineParser")

	def run(command):
		if not command: return None
		
		# start pasing the command string
		



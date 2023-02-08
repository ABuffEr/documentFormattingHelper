# -*- coding: UTF-8 -*-
from globalPluginHandler import GlobalPlugin
import addonHandler
from scriptHandler import script

addonHandler.initTranslation()

class GlobalPlugin(GlobalPlugin):

	scriptCategory = addonHandler.getCodeAddon().manifest['summary']

	@script(
		description=_(
			# Translators: Describes the formatting helper command.
			"Launches formatting helper"
		),
		gesture="kb:NVDA+shift+control+o"
	)
	def script_formattingHelper(self, gesture):
		from . import formattingHelper as helper
		if not helper.analyzer or not helper.analyzer.is_alive():
			helper.filterView()
		else:
			helper.stop()

# -*- coding: UTF-8 -*-
import config
import wx
import textInfos
from logHandler import log
import ui
from textInfos.offsets import Offsets
from threading import Thread, Event
from NVDAObjects.IAccessible import getNVDAObjectFromEvent
import winUser
from time import sleep
from tones import beep
from queueHandler import queueFunction, flushQueue, eventQueue
import wx
import gui
from gui import guiHelper
from gui.nvdaControls import CustomCheckListBox
from collections import OrderedDict
import colors
import addonHandler
from math import ceil
import speech
import api
import weakref

"""
Useful stuff:
- from globalCommands.py/_reportFormattingHelper:
		# These are the options we want reported when reporting formatting manually.
		# for full list of options that may be reported see the "documentFormatting" section of L{config.configSpec}
		reportFormattingOptions = (
			"reportFontName",
			"reportFontSize",
			"reportFontAttributes",
			"reportSuperscriptsAndSubscripts",
			"reportColor",
			"reportStyle",
			"reportAlignment",
			"reportSpellingErrors",
			"reportLineIndentation",
			"reportParagraphIndentation",
			"reportLineSpacing",
			"reportBorderStyle",
			"reportBorderColor",
		)
- all attrs.get values from speech.py/getFormatFieldSpeech:
table-info
page-number
section-number
text-column-count
text-column-number
section-break
column-break
heading-level
style
border-style
font-family
font-name
font-size
color
background-color
background-color2
background-pattern
line-number
revision-insertion
revision-deletion
revision
marked
strong
emphasised
bold
italic
strikethrough
underline
hidden
text-position
text-align
vertical-align
left-indent
right-indent
hanging-indent
first-line-indent
line-spacing
link
comment
bookmark
invalid-spelling
invalid-grammar
line-prefix_speakAlways
line-prefix
"""

NVDALocale = _
addonHandler.initTranslation()
# some required strings
# Translators: description of centered text
_("center")
# Translators: description of justified text
_("justified")
# Translators: description of text aligned to left
_("left")
# Translators: description of text aligned to right
_("right")

DEBUG=False
EOL_CHARS = ("\r", "\n", "\r\n")
analyzer = None
fixedKeyProps = set([
	"bold",
	"bookmark",
	"comment",
	"emphasised",
	"hidden",
	"invalid-grammar",
	"invalid-spelling",
	"italic",
	"link",
	"marked",
	"revision",
	"strikethrough",
	"strong",
	"underline"
])
formatConfig = {}.fromkeys(config.conf["documentFormatting"].dict().keys(), False)
formatConfig.update({}.fromkeys([
	"detectFormatAfterCursor",
	"reportAlignment",
	"reportBookmarks",
	"reportBorderColor",
	"reportBorderStyle",
	"reportColor",
	"reportComments",
	"reportEmphasis",
	"reportFontAttributes",
	"reportFontName",
	"reportFontSize",
	"reportHighlight",
	"reportLineIndentation",
	"reportLinks",
	"reportParagraphIndentation",
	"reportSpellingErrors",
	"reportStyle",
	"reportSuperscriptsAndSubscripts",
	"reportTransparentColor",
	"reportRevisions"
], True))
fakeProp = ('fakeProperty', 1,)

def debugLog(message):
	if DEBUG:
		log.info(message)

def filterView():
	docObj = api.getFocusObject()
	if hasattr(docObj, "UIAElement"):
		ui.message(_("Sorry, formatting helper is not available yet in UIA context"))
		return
	docTitle = getattr(api.getForegroundObject(), "name", "")
	instanceID = ':'.join([str(getattr(docObj, ID, "")) for ID in ("processID", "windowHandle", "windowControlID")])
	# Translators: message when document analyzer starts
	ui.message(_("Analyzing..."))
	Thread(target=launchAnalyzer, args=(instanceID, docObj, docTitle, getUserProps)).start()

def launchAnalyzer(instanceID, docObj, docTitle, postFunc):
	global analyzer
	analyzer = Analyzer(instanceID, docObj, docTitle)
	i = 0
	analyzer.start()
	while analyzer.is_alive():
		sleep(0.1)
		i += 1
		if i == 10:
			beep(500, 100)
			i = 0
	analyzer.join()
	if not analyzer.specificProps:
		queueFunction(eventQueue, ui.message, _("No result"))
		return
	postFunc(analyzer)

def stop():
	# Translators: message when user asks to stop analyzer
	ui.message(_("Stop!"))
	if analyzer and analyzer.is_alive():
		analyzer.stop()

def getUserProps(analyzer):
	gui.mainFrame.prePopup()
	speech.cancelSpeech()
	wx.CallAfter(FilterViewDialog, gui.mainFrame, analyzer)
	gui.mainFrame.postPopup()


class Analyzer(Thread):

	STATUS_NOT_STARTED = 1
	STATUS_RUNNING = 2
	STATUS_COMPLETE = 3
	STATUS_ABORTED = 4
	_instanceMap = weakref.WeakValueDictionary()

	def __new__(cls, *args, **kwargs):
		instanceID = args[0]
#		if Analyzer._instanceMap.get(instanceID, False):
#			debugLog("Reuse old instance")
#			return Analyzer._instanceMap[instanceID]
		newInstance = super(Analyzer, cls).__new__(cls)
		Analyzer._instanceMap[instanceID] = newInstance
		debugLog("creating new instance")
		return newInstance

	def __init__(self, instanceID, docObj, docTitle, *args, **kwargs):
		super(Analyzer, self).__init__(*args, **kwargs)
		if hasattr(self, "docObj"):
			return
		# reacquire object in this thread
		self.docObj = getNVDAObjectFromEvent(docObj.windowHandle, winUser.OBJID_CLIENT, docObj.IAccessibleChildID)
		self.docTitle = docTitle
		self.docPos = None
		self.allProps = set()
		self.commonProps = set()
		self.specificProps = set()
		self.wordTupleList = []
		# renamed from _stop to _stopEvent, to avoid Py3 conflicts
		self._stopEvent = Event()
		self.status = Analyzer.STATUS_NOT_STARTED

	def stop(self):
		self._stopEvent.set()
		self.status = Analyzer.STATUS_ABORTED

	def stopped(self):
		return self._stopEvent.is_set()

	def run(self):
		if self.status != Analyzer.STATUS_NOT_STARTED:
			return
		self.status = Analyzer.STATUS_RUNNING
		self.analyze()
		if self.status == Analyzer.STATUS_RUNNING:
			self.status = Analyzer.STATUS_COMPLETE

	def analyze(self):
		if self.docPos is None:
			info1 = self.docObj.makeTextInfo(textInfos.POSITION_CARET)
			self.docPos = info1.bookmark.startOffset
		info2 = self.docObj.makeTextInfo(textInfos.POSITION_LAST)
		docLen = info2.bookmark.endOffset
		oldStatus = 0
		increment = 1800
		for startOffset in range(self.docPos, docLen, increment):
			if self.stopped(): break
			info = self.docObj.makeTextInfo(Offsets(startOffset, startOffset+increment))
			startTextOffset = startOffset
			memorizeText = False
			matchedProps = set()
			for field in info.getTextWithFields(formatConfig):
				if self.stopped(): break
				# status rounded at the smallest next integer, mod 101 to ensure it's <§ 100
				status = ceil(startTextOffset/docLen*100)%101
				# announce status only if increased at least of
				# +5%, and document is still in foreground
				if status-oldStatus >= 5 and self.docObj.hasFocus:
					statusMsg = ''.join([str(status), "%"])
					# avoid announcement of expired status
#					queueFunction(eventQueue, flushQueue, eventQueue)
					queueFunction(eventQueue, ui.message, statusMsg)
					oldStatus = status
				if isinstance(field, textInfos.FieldCommand) and field.command == "formatChange":
					fieldProps = set(field.field.items())
					self.allProps.update(fieldProps)
					self.commonProps = self.commonProps.intersection(fieldProps) if self.commonProps else fieldProps.copy()
					self.specificProps = self.cleanProps(self.allProps.difference(self.commonProps))
					matchedProps = self.specificProps.intersection(fieldProps)
					fixedProps = set(field.field.keys()).intersection(fixedKeyProps)
					if matchedProps:
						memorizeText = True
						if fixedProps:
							matchedProps = matchedProps.union([(prop, field.field[prop]) for prop in fixedProps])
					elif fixedProps:
						memorizeText = True
						fieldProps.add(fakeProp)
						matchedProps = fieldProps
					else:
						memorizeText = False
				elif memorizeText and isinstance(field, str):
					newTuple = (startTextOffset, startTextOffset+len(field), matchedProps, field,)
					self.wordTupleList.append(newTuple)
				elif not memorizeText and isinstance(field, str) and field.endswith(EOL_CHARS):
					try:
						isToAdd = not self.wordTupleList[-1][3].endswith(field)
					except IndexError:
						isToAdd = False
					if isToAdd:
						newTuple = (startTextOffset, startTextOffset+len(field), set(), field,)
						self.wordTupleList.append(newTuple)
				if isinstance(field, str):
					startTextOffset += len(field)
			# force cleaning of memory
			del info
		self.cleanWordTupleList()

	def cleanProps(self, props):
		tempProps = props.copy()
		for k,v in props:
			if k == "color" and (v == NVDALocale("automatic color") or v == NVDALocale("default color") or "default" in v):
				tempProps.remove((k, v,))
			elif v in (True, False, 1, 0) and bool(v) and (k, v) in tempProps and (k, not v) in tempProps:
					tempProps.remove((k, not v,))
		return tempProps

	def cleanWordTupleList(self):
		tempList = []
		for item in self.wordTupleList:
			start, end, props, text = item
			if fakeProp in props:
				newProps = self.specificProps.intersection(props)
				if newProps or text in EOL_CHARS:
					tempList.append((start, end, newProps, text,))
			else:
				tempList.append(item)
		self.wordTupleList = tempList


class FilterViewDialog(wx.Dialog):

	def __init__(self, parent, analyzer):
		# Translators: window title of the formatting helper feature
		title = _("Formatting helper for {docTitle}").format(docTitle=analyzer.docTitle)
		super(FilterViewDialog, self).__init__(parent, title=title)
		self.analyzer = analyzer
		self.userProps = set()
		self.propDict = self.mapPropTupleToString()
		self.origDocMap = self.curDocMap = self.getDocMap(analyzer.wordTupleList)
		self.origDocText = self.getText(self.origDocMap)
		mainSizer = wx.BoxSizer(wx.VERTICAL)
		propSizer = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		self.propList = CustomCheckListBox(self, choices=list(self.propDict.keys()), name=_("Desired formatting"))
		self.propList.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
		self.propList.Bind(wx.EVT_CHECKLISTBOX, self.onCheck)
		self.propList.Select(0)
		propSizer.addItem(self.propList)
		mainSizer.Add(propSizer.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		textSizer = guiHelper.BoxSizerHelper(self, orientation=wx.VERTICAL)
		self.filteredText = wx.TextCtrl(self, wx.ID_ANY, value=self.origDocText,
			style=wx.TE_PROCESS_ENTER | wx.TE_MULTILINE | wx.TE_READONLY | wx.TE_RICH2 | wx.TE_CENTRE | wx.TE_DONTWRAP)
		self.filteredText.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
		self.filteredText.Bind(wx.EVT_TEXT_ENTER, self.onTextEnter)
		self.filteredText.SetInsertionPoint(0)
		textSizer.sizer.Add(self.filteredText, proportion=1, flag=wx.EXPAND)
		mainSizer.Add(textSizer.sizer, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
#		self.refreshButton = wx.Button(self, wx.ID_ANY, label=_("Sync again with document"))
#		self.refreshButton.Bind(wx.EVT_KEY_DOWN, self.onKeyDown)
#		self.refreshButton.Bind(wx.EVT_BUTTON, self.onSyncAgain)
#		mainSizer.Add(self.refreshButton, border=guiHelper.BORDER_FOR_DIALOGS, flag=wx.ALL)
		self.SetSizer(mainSizer)
		mainSizer.Fit(self)
		self.Bind(wx.EVT_CLOSE, self.onClose)
		self.CenterOnScreen()
		self.propList.SetFocus()
		wx.CallAfter(self.Show)

	def getDocMap(self, wordTupleList):
		tempDict = OrderedDict()
		newStart = 0
		for item in wordTupleList:
			origStart, origEnd, props, text = item
			newText = text.replace("\r\n", "\n").replace("\r", "\n")
			newEnd = newStart+len(newText)
			tempDict[(newStart, newEnd)] = (origStart, origEnd, props, newText)
			newStart = newEnd
		return tempDict

	def getText(self, docMap):
		tempList = []
		for value in docMap.values():
			tempText = value[3]
			tempList.append(tempText)
		return ''.join(tempList)

	def mapPropTupleToString(self):
		tempDict = OrderedDict()
		tempProps = []
		for origPropTuple in self.analyzer.specificProps:
			name, value = origPropTuple
			name = name.replace("-", " ")
			if name == "color":
				newName = _("color")
				newValue = value.name if isinstance(value, colors.RGB) else value
			elif name == "invalid grammar":
				newName = NVDALocale("grammar error")
				newValue = value
			elif name == "invalid spelling":
				newName = NVDALocale("spelling error")
				newValue = value
			elif name == "text align":
				newName = NVDALocale("&Alignment").replace("&", "")
				newValue = _(value)
			else:
				newName = NVDALocale(name)
				newValue = NVDALocale(value)
			tempProps.append((newName, newValue, origPropTuple,))
		tempProps.sort()
		for prop in tempProps:
			name, value, tuple = prop
			if tuple[0] in fixedKeyProps and value in ('1', True):
				key = name
			elif isinstance(value, bool):
				key = name
			else:
				key = ': '.join([name, value])
			countMsg = self.countPropMessage(tuple)
			key = ''.join([key, countMsg])
			tempDict[key] = tuple
		return tempDict

	def countPropMessage(self, prop):
		count = 0
		validBlock = False
		for item in self.analyzer.wordTupleList:
			start, end, props, text = item
			# avoid strings like full stop and EOL chars
			if prop in props and (len(text) > 1 or text.isalpha()):
				validBlock = True
			elif prop not in props and validBlock:
				count += 1
				validBlock = False
		# ensure closing
		if validBlock:
			count += 1
		if count:
			text = str(count)
		else:
			# Translators: message presented when a property is only of a non-textual element
			text = _("no text")
		message = ''.join([" (", text, ")"])
		return message

	def onClose(self, evt):
		self.Destroy()

	def onKeyDown(self, evt):
		key = evt.GetKeyCode()
		if key == wx.WXK_ESCAPE:
			self.Close()
			return
		evt.Skip()

	def onCheck(self, evt):
		# for accessibility issues of CheckListBox
		self.propList.notifyIAccessible(evt)
		self.userProps.clear()
		for propString in self.propList.GetCheckedStrings():
			propTuple = self.propDict[propString]
			self.userProps.add(propTuple)
		self.refreshDocMap()
		self.refreshText()

	def refreshDocMap(self):
		tempList = []
		for item in self.origDocMap.values():
			start, end, props, text = item
			if self.userProps.intersection(props):
				tempList.append(item)
			elif text.endswith(EOL_CHARS):
				try:
					isToAdd = not tempList[-1][3].endswith(text)
				except IndexError:
					isToAdd = False
				if isToAdd:
					tempList.append(item)
		self.curDocMap = self.getDocMap(tempList)

	def refreshText(self):
		if self.userProps:
			newText = self.getText(self.curDocMap)
		else:
			newText = self.origDocText
		self.filteredText.ChangeValue(newText)

	def onSyncAgain(self, evt):
		self.analyzer.reset()
		self.analyzer = Analyzer(self.analyzer.instanceID, self.analyzer.docObj, self.analyzer.docTitle)
		i = 0
		self.analyzer.start()
		while self.analyzer.is_alive():
			sleep(0.1)
			i += 1
			if i == 10:
				beep(500, 100)
				i = 0
		self.analyzer.join()
		if not self.analyzer.specificProps:
			queueFunction(eventQueue, ui.message, _("No result"))
			self.Destroy()
			return
		self.userProps.clear()
		self.propDict = self.mapPropTupleToString()
		self.origDocMap = self.curDocMap = self.getDocMap(self.analyzer.wordTupleList)
		self.origDocText = self.getText(self.origDocMap)
		self.propList.Clear()
		self.propList.Append(list(self.propDict.keys()))
		self.propList.Select(0)
		self.refreshText()
		self.filteredText.SetInsertionPoint(0)

	def onTextEnter(self, evt):
		selPos = self.filteredText.GetSelection()
		selStart = selPos[0]
		docPos = self.getDocPos(selStart)
		origDocObj = getNVDAObjectFromEvent(self.analyzer.docObj.windowHandle, winUser.OBJID_CLIENT, self.analyzer.docObj.IAccessibleChildID)
		info = origDocObj.makeTextInfo(Offsets(*docPos))
		origDocObj.setFocus()
		speech.cancelSpeech()
		info.updateCaret()
#		info.move(textInfos.UNIT_LINE, 1, endPoint="end")

	def getDocPos(self, pos):
		for key in self.curDocMap.keys():
			curStart, curEnd = key
			if curStart <= pos < curEnd:
				origStart, origEnd, props, text = self.curDocMap[key]
				return (origStart, origEnd)

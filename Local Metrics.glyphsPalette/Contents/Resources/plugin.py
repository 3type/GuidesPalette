# encoding: utf-8

###########################################################################################################
#
#
#	Palette Plugin: Local Metrics
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Palette
#
#
###########################################################################################################

import objc
# import traceback
from GlyphsApp import *
from GlyphsApp.plugins import *
from vanilla import *


GS_METRIC_TYPE_OTHER        = 0
GS_METRIC_TYPE_ASCENDER     = 1
GS_METRIC_TYPE_CAP_HEIGHT   = 2
GS_METRIC_TYPE_SLANT_HEIGHT = 3
GS_METRIC_TYPE_X_HEIGHT     = 4
GS_METRIC_TYPE_MIDHEIGHT    = 5
GS_METRIC_TYPE_BODYHEIGHT   = 6
GS_METRIC_TYPE_DESCENDER    = 7
GS_METRIC_TYPE_BASELINE     = 8
GS_METRIC_TYPE_ITALIC_ANGLE = 9


class LocalMetrics(PalettePlugin):

	@objc.python_method
	def settings(self):
		self.name = 'Local Metrics'

		self.checkboxes = {
			(i, name): newCheckBox(name)
			for i, name in enumerate(customMetrics(Glyphs.font.metrics))
		}

		self.paletteView                   = Window((200, 100))
		self.paletteView.verticalStackView = VerticalStackView('auto', self.checkboxes.values(), alignment='leading', spacing=3)

		# Set dialog to NSView
		self.dialog = self.paletteView.verticalStackView.getNSStackView()

	@objc.python_method
	def start(self):
		Glyphs.addCallback(self.update, UPDATEINTERFACE)

	@objc.python_method
	def __del__(self):
		Glyphs.removeCallback(self.update)

	@objc.python_method
	def update(self, sender):
		if font := sender.object().parent:
			newMetrics     = list(enumerate(customMetrics(font.metrics)))
			removedMetrics = list(set(self.checkboxes.keys()) - set(newMetrics))
			addedMetrics   = list(set(newMetrics) - set(self.checkboxes.keys()))
			for i, name in removedMetrics:
				# print('-', i, name)
				self.paletteView.verticalStackView.removeView(self.checkboxes[(i, name)])
				del self.checkboxes[(i, name)]
			for i, name in sorted(addedMetrics, key=lambda t: t[0]):
				# print('+', i, name)
				self.checkboxes[(i, name)] = newCheckBox(name)
				self.paletteView.verticalStackView.insertView(i, self.checkboxes[(i, name)])

	@objc.python_method
	def __file__(self):
		return __file__

def customMetrics(metrics):
	return (m.name for m in metrics if m.type() == GS_METRIC_TYPE_OTHER)

def newCheckBox(name):
	return CheckBox('auto', name, sizeStyle='mini')

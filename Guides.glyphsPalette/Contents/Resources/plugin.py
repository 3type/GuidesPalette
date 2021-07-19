# encoding: utf-8

###########################################################################################################
#
#
#	Palette Plugin: Guides Palette
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/master/Python%20Templates/Palette
#
#
###########################################################################################################

import objc
import traceback

from AppKit import NSPredicate
from vanilla import CheckBox, VerticalStackView, Window

from GlyphsApp import *
from GlyphsApp.plugins import *


class GuidesPalette(PalettePlugin):

	@objc.python_method
	def settings(self):
		self.name = 'Guides'

		self.checkBoxes = {
			(i, metric): self.newCheckBox(metric)
			for i, metric in enumerate(customMetrics(Glyphs.font.metrics))
		}

		self.paletteView = Window(posSize=(200, 100))
		self.paletteView.verticalStackView = VerticalStackView(
			posSize='auto',
			views=self.checkBoxes.values(),
			alignment='leading',
			spacing=3,
			edgeInsets=(2, 8, 8, 1),
		)

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
			# Update the palette view
			newMetrics     = list(enumerate(customMetrics(font.metrics)))
			removedMetrics = list(set(self.checkBoxes.keys()) - set(newMetrics))
			addedMetrics   = list(set(newMetrics) - set(self.checkBoxes.keys()))
			for i, metric in removedMetrics:
				self.paletteView.verticalStackView.removeView(self.checkBoxes[(i, metric)])
				del self.checkBoxes[(i, metric)]
			for i, metric in sorted(addedMetrics, key=lambda t: t[0]):
				self.checkBoxes[(i, metric)] = self.newCheckBox(metric)
				self.paletteView.verticalStackView.insertView(i, self.checkBoxes[(i, metric)])

			# Update the state of checkboxes
			if glyphs := selectedGlyphs(font):
				for (_, metric), checkBox in self.checkBoxes.items():
					if metric.filter:
						isInFilter = list(map(metric.filter.evaluateWithObject_, glyphs))
						if all(isInFilter):
							state = ONSTATE
						elif not any(isInFilter):
							state = OFFSTATE
						else:
							state = MIXEDSTATE
					else:
						state = ONSTATE
					checkBox.enable(True)
					checkBox.set(state)
			else:
				for checkBox in self.checkBoxes.values():
					checkBox.enable(False)

	@objc.python_method
	def checkBoxToggle(self, sender):
		# Ensure that the checkbox becomes either ON of OFF after click
		if sender.get() == MIXEDSTATE:
			sender.set(ONSTATE)
		try:
			tagName = metricName(next(m[1] for m, c in self.checkBoxes.items() if c is sender))
			for glyph in selectedGlyphs(Glyphs.font):
				if sender.get() == ONSTATE:
					# OFF -> ON
					glyph.tags.append(tagName)
				else:
					# ON -> OFF
					glyph.tags.remove(tagName)
		except:
			print(traceback.format_exc())

	@objc.python_method
	def newCheckBox(self, metric):
		checkBox = CheckBox(
			posSize='auto',
			title=metricName(metric),
			sizeStyle='mini',
			callback=self.checkBoxToggle,
		)
		checkBox._nsObject.setAllowsMixedState_(True)
		return checkBox

	@objc.python_method
	def __file__(self):
		return __file__


def metricName(metric):
	return str(metric.filter.rightExpression()).replace('"', '')


def customMetrics(metrics):
	# Metric types:
	#   Other:        0
	#   Ascender:     1
	#   Cap Height:   2
	#   Slant Height: 3
	#   x-Height:     4
	#   Midheight:    5
	#   Bodyheight:   6
	#   Descender:    7
	#   Baseline:     8
	#   Italic Angle: 9
	res = []
	for metric in (
		m for m in metrics
		if m.type() == 0 and m.filter.predicateFormat().startswith('tags CONTAINS')
	):
		metric.filter = NSPredicate.predicateWithFormat_(f'tags CONTAINS "{metric.name}"')
		res.append(metric)
	return res


def selectedGlyphs(font):
	if layers := font.selectedLayers:
		return [l.parent for l in layers if not isinstance(l, GSControlLayer)]
	return []

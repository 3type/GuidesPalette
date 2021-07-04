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
import traceback

from AppKit import NSCompoundPredicate, NSOrPredicateType, NSPredicate
from vanilla import CheckBox, VerticalStackView, Window

from GlyphsApp import *
from GlyphsApp.plugins import *


class LocalMetrics(PalettePlugin):

	@objc.python_method
	def settings(self):
		self.name = 'Local Metrics'

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
			metric = next(m[1] for m, c in self.checkBoxes.items() if c is sender)
			selectedGlyphNames = [g.name for g in selectedGlyphs(Glyphs.font)]
			if metric.filter:
				# We only use OR predicate type
				assert metric.filter.compoundPredicateType() == NSOrPredicateType
				names = set(
					p.predicateFormat().split('"')[-2]  # Parse from `name == "<NAME>"`
					for p in metric.filter.subpredicates()
				)
				if sender.get() == ONSTATE:
					names = names.union(selectedGlyphNames)
				else:
					names = names.difference(selectedGlyphNames)
			else:
				# If there's no filter, then the state must be ON -> OFF
				assert sender.get() == OFFSTATE
				names = set(g.name for g in Glyphs.font.glyphs).difference(selectedGlyphNames)
			metric.filter = NSCompoundPredicate.orPredicateWithSubpredicates_([
				NSPredicate.predicateWithFormat_(f'name == "{name}"') for name in names
			])
		except:
			print(traceback.format_exc())

	@objc.python_method
	def newCheckBox(self, metric):
		checkBox = CheckBox(
			posSize='auto',
			title=metric.name[1:],  # Remove the leading `_`
			sizeStyle='mini',
			callback=self.checkBoxToggle,
		)
		checkBox._nsObject.setAllowsMixedState_(True)
		return checkBox

	@objc.python_method
	def __file__(self):
		return __file__


def customMetrics(metrics):
	# GS_METRIC_TYPE_OTHER        = 0
	# GS_METRIC_TYPE_ASCENDER     = 1
	# GS_METRIC_TYPE_CAP_HEIGHT   = 2
	# GS_METRIC_TYPE_SLANT_HEIGHT = 3
	# GS_METRIC_TYPE_X_HEIGHT     = 4
	# GS_METRIC_TYPE_MIDHEIGHT    = 5
	# GS_METRIC_TYPE_BODYHEIGHT   = 6
	# GS_METRIC_TYPE_DESCENDER    = 7
	# GS_METRIC_TYPE_BASELINE     = 8
	# GS_METRIC_TYPE_ITALIC_ANGLE = 9
	return [m for m in metrics if m.type() == 0 and m.name.startswith('_')]


def selectedGlyphs(font):
	if layers := font.selectedLayers:
		return [l.parent for l in layers if not isinstance(l, GSControlLayer)]
	return []

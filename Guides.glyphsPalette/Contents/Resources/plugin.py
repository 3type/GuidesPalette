# encoding: utf-8

###########################################################################################################
#
#
#	Palette Plugin: Guides Palette
#
#	Read the docs:
#	https://github.com/schriftgestalt/GlyphsSDK/tree/Glyphs3/Python%20Templates/Palette
#
#
###########################################################################################################

import objc
import traceback

from AppKit import NSFont, NSFontWeightRegular, NSMiniControlSize, NSPredicate
from vanilla import CheckBox, VerticalStackView, Window

from GlyphsApp import *
from GlyphsApp.plugins import *


class GuidesPalette(PalettePlugin):

	@objc.python_method
	def settings(self):
		self.name = Glyphs.localize({
			'en': 'Guides',
			'zh': '参考线',
		})

		self.checkBoxes = {
			guide: self.newCheckBox(guide)
			for guide in globalGuides(Glyphs.font.selectedFontMaster)
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
			# Update the checkBox list
			newGuides     = globalGuides(font.selectedFontMaster)
			removedGuides = list(set(self.checkBoxes.keys()) - set(newGuides))
			addedGuides   = list(set(newGuides) - set(self.checkBoxes.keys()))
			for guide in removedGuides:
				del self.checkBoxes[guide]
			for guide in addedGuides:
				self.checkBoxes[guide] = self.newCheckBox(guide)

			# Update the palette view (sorted by guide's name)
			for view in self.paletteView.verticalStackView.getNSStackView().views():
				self.paletteView.verticalStackView.removeView(view)
			for guide, checkBox in sorted(self.checkBoxes.items(), key=lambda p: p[0].name):
				checkBox.setTitle(guideName(guide))
				self.paletteView.verticalStackView.appendView(checkBox)
			
			# Update the state of checkboxes
			if glyphs := selectedGlyphs(font):
				for guide, checkBox in self.checkBoxes.items():
					if guide.filter:
						isInFilter = list(map(guide.filter.evaluateWithObject_, glyphs))
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
			pass
			tag = next(tagName(g) for g, c in self.checkBoxes.items() if c is sender)
			for glyph in selectedGlyphs(Glyphs.font):
				if sender.get() == ONSTATE:
					# OFF -> ON
					glyph.tags.append(tag)
				else:
					# ON -> OFF
					glyph.tags.remove(tag)
		except:
			print(traceback.format_exc())

	@objc.python_method
	def newCheckBox(self, guide):
		checkBox = CheckBox(
			posSize='auto',
			title=guideName(guide),
			sizeStyle='mini',
			callback=self.checkBoxToggle,
		)
		font = NSFont.monospacedDigitSystemFontOfSize_weight_(
			NSFont.systemFontSizeForControlSize_(NSMiniControlSize),
			NSFontWeightRegular,
		)
		checkBox._nsObject.setFont_(font)
		checkBox._nsObject.setAllowsMixedState_(True)
		return checkBox

	@objc.python_method
	def __file__(self):
		return __file__


def globalGuides(master):
	res = []
	for guide in (g for g in master.guides if g.name):
		guide.filter = NSPredicate.predicateWithFormat_(f'tags CONTAINS "{tagName(guide)}"')
		res.append(guide)
	return res


def guideName(guide):
	x = round(guide.position.x)
	y = round(guide.position.y)
	return f'{guide.name}  ({x}, {y}), {guide.angle:.1f}\xB0'  # `\xB0` is the degree symbol


def tagName(guide):
	return 'guide_' + guide.name


def selectedGlyphs(font):
	if layers := font.selectedLayers:
		return [l.parent for l in layers if not isinstance(l, GSControlLayer)]
	return []

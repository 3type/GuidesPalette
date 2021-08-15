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
from vanilla import CheckBox, EditText, HorizontalStackView, TextBox, VerticalStackView, Window

from GlyphsApp import *
from GlyphsApp.plugins import *


class GuidesPalette(PalettePlugin):

	CUSTOM_PARAMETER_NAME = 'Guides Palette Config'

	@objc.python_method
	def settings(self):
		self.name = Glyphs.localize({
			'en': 'Guides',
			'ar': 'الأدلة',
			'cs': 'Vodítka',
			'de': 'Hilfslinien',
			'es': 'Guías',
			'fr': 'Les Repères',
			'it': 'Linee Guida',
			'ja': 'ガイドライン',
			'ko': '가이드라인',
			'pt': 'Guias',
			'ru': 'Гайды',
			'tr': 'Kılavuz Çizgileri',
			'zh-Hans-CN': '参考线',
			'zh-Hant-CN': '參考線',
		})
		self.initConfig()
		self.checkBoxes = {
			guide: self.newCheckBox(guide)
			for guide in globalGuides(Glyphs.font.selectedFontMaster)
		}
		self.paletteView = Window(posSize=(200, 100))
		self.paletteView.verticalStackView = VerticalStackView(
			posSize='auto',
			views=[c.view() for c in self.checkBoxes.values()],
			alignment='leading',
			spacing=3,
			edgeInsets=(2, 8, 8, 1),
		)
		# Set dialog to NSView
		self.dialog = self.paletteView.verticalStackView.getNSStackView()

	@objc.python_method
	def initConfig(self):
		self.sortBy          = None
		self.showCoordinates = True
		self.showAngle       = True

	@objc.python_method
	def start(self):
		Glyphs.addCallback(self.update, UPDATEINTERFACE)

	@objc.python_method
	def __del__(self):
		Glyphs.removeCallback(self.update)
		Glyphs.removeCallback(self.checkBoxToggle)
		Glyphs.removeCallback(self.checkBoxEdit)

	@objc.python_method
	def update(self, sender):
		if font := sender.object().parent:
			self.updateConfig(font)

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
			if sortBy := self.checkBoxesSortBy():
				self.checkBoxes = dict(sorted(
					self.checkBoxes.items(), key=sortBy[0], reverse=sortBy[1]))
			for guide, checkBox in self.checkBoxes.items():
				guideName, guidePos, guideAngle = self.guideNamePosAngle(guide)
				checkBox.name.set(guideName)
				checkBox.pos.set(guidePos)
				checkBox.angle.set(guideAngle)
				self.paletteView.verticalStackView.appendView(checkBox.view())

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
					checkBox.check.enable(True)
					checkBox.check.set(state)
			else:
				for checkBox in self.checkBoxes.values():
					checkBox.check.enable(False)

	@objc.python_method
	def updateConfig(self, font):
		try:
			if config := font.customParameters[self.CUSTOM_PARAMETER_NAME]:
				self.sortBy          = config.get('sortBy', None)
				self.showCoordinates = bool(int(config.get('showCoordinates', 1)))
				self.showAngle       = bool(int(config.get('showAngle', 1)))
			else:
				self.initConfig()
		except:
			print(traceback.format_exc())

	@objc.python_method
	def checkBoxesSortBy(self):
		dispatch = {
			'name': (lambda p: p[0].name, False),
			'x':    (lambda p: p[0].x, False),
			'y':    (lambda p: p[0].y, False),
			'-x':   (lambda p: p[0].x, True),
			'-y':   (lambda p: p[0].y, True),
		}
		return dispatch.get(self.sortBy, None)

	@objc.python_method
	def checkBoxToggle(self, sender):
		# Ensure that the checkbox becomes either ON of OFF after click
		if sender.get() == MIXEDSTATE:
			sender.set(ONSTATE)
		try:
			tag = next(tagName(g) for g, c in self.checkBoxes.items() if c.check is sender)
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
	def checkBoxEdit(self, sender):
		try:
			guide = next(g for g, c in self.checkBoxes.items() if c.name is sender)
			oldTag = tagName(guide)
			guide.name = sender.get()
			newTag = tagName(guide)
			for glyph in selectedGlyphs(Glyphs.font):
				if oldTag in glyph.tags:
					glyph.tags.remove(oldTag)
					glyph.tags.append(newTag)
		except:
			print(traceback.format_exc())

	@objc.python_method
	def newCheckBox(self, guide):
		guideName, guidePos, guideAngle = self.guideNamePosAngle(guide)
		return CompositeCheckBox(
			check=CheckBox(
				posSize='auto',
				title=None,
				sizeStyle='mini',
				callback=self.checkBoxToggle,
			),
			name=EditText(
				posSize='auto',
				text=guideName,
				sizeStyle='mini',
				continuous=False,
				callback=self.checkBoxEdit,
			),
			pos=TextBox(
				posSize='auto',
				text=guidePos,
				sizeStyle='mini',
			),
			angle=TextBox(
				posSize='auto',
				text=guideAngle,
				sizeStyle='mini',
			),
		)

	@objc.python_method
	def guideNamePosAngle(self, guide):
		name, pos, angle = f'{guide.name}', '', ''
		if self.showCoordinates:
			pos = f'({round(guide.position.x)}, {round(guide.position.y)})'
		if self.showAngle:
			angle = f'{guide.angle:.1f}\xB0'
		return name, pos, angle

	@objc.python_method
	def __file__(self):
		return __file__


class CompositeCheckBox:
	font = NSFont.monospacedDigitSystemFontOfSize_weight_(
		NSFont.systemFontSizeForControlSize_(NSMiniControlSize),
		NSFontWeightRegular,
	)

	def __init__(self, check, name, pos, angle):
		self.check = check
		self.name  = name
		self.pos   = pos
		self.angle = angle
		self.check._nsObject.setAllowsMixedState_(True)
		self.pos._nsObject.setFont_(self.font)
		self.angle._nsObject.setFont_(self.font)

	def view(self):
		return HorizontalStackView(
			posSize='auto',
			views=[
				{'view': self.check, 'width': 10},
				{'view': self.name,  'width': 80},
				{'view': self.pos,   'width': 60},
				{'view': self.angle, 'width': 40},
			],
			spacing=6,
		)


def globalGuides(master):
	res = []
	for guide in (g for g in master.guides if g.name):
		guide.filter = NSPredicate.predicateWithFormat_(f'tags CONTAINS "{tagName(guide)}"')
		res.append(guide)
	return res


def tagName(guide):
	return 'guide_' + guide.name


def selectedGlyphs(font):
	if layers := font.selectedLayers:
		return [l.parent for l in layers if not isinstance(l, GSControlLayer)]
	return []

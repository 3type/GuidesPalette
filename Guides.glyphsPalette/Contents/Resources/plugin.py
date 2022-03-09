# encoding: utf-8

###########################################################################################################
#
#
#	Palette Plugin: Guides Palette
#
#	Read the docs:
#	https://github.com/3type/GuidesPalette/blob/main/README.md
#
#
###########################################################################################################

import objc
import traceback

from AppKit import NSFont, NSFontWeightRegular, NSMiniControlSize, NSPredicate
from vanilla import CheckBox, EditText, Group, TextBox, VerticalStackView, Window

from GlyphsApp import Glyphs, GSControlLayer, UPDATEINTERFACE, ONSTATE, OFFSTATE, MIXEDSTATE
from GlyphsApp.plugins import PalettePlugin


class GuidesPalette(PalettePlugin):

	CUSTOM_PARAMETER_NAME = 'Guides Palette Config'


	@objc.python_method
	def settings(self):
		self.name = Glyphs.localize({
			'en': 'Assign Guides',
			'ja': 'ガイドラインを指定',
			'zh-Hans-CN': '指定参考线',
			'zh-Hant-CN': '指定參考線',
		})
		self.updateConfig(Glyphs.font)
		self.nowPrefix = self.tagPrefix
		self.checkBoxes = {
			guide: self.newCheckBox(guide)
			for guide in self.globalGuides(Glyphs.font.selectedFontMaster)
		}
		self.paletteView = Window(posSize=(200, 100))
		self.paletteView.verticalStackView = VerticalStackView(
			posSize='auto',
			views=[c.getNSView() for c in self.checkBoxes.values()],
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
		self.tagPrefix       = 'guide_'


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
		# Do not update in case the palette is collapsed
		if self.dialog.frame().origin.y != 0:
			return

		if font := sender.object().parent:
			self.updateConfig(font)
			if self.renamePrefix(self.nowPrefix, self.tagPrefix):
				self.nowPrefix = self.tagPrefix

			# Update the checkBox list
			newGuides     = self.globalGuides(font.selectedFontMaster)
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
				self.paletteView.verticalStackView.appendView(checkBox.getNSView())

			# Update the state of checkboxes
			if glyphs := self.selectedGlyphs(font):
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
				self.tagPrefix       = config.get('tagPrefix', 'guide_')
			else:
				self.initConfig()
				font.customParameters[self.CUSTOM_PARAMETER_NAME] = {
					'sortBy' 			: self.sortBy,
					'showCoordinates' 	: self.showCoordinates,
					'showAngle'			: self.showAngle,
					'tagPrefix'			: self.tagPrefix,}
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
			tag = next(self.tagName(g) for g, c in self.checkBoxes.items() if c.check is sender)
			for glyph in self.selectedGlyphs(Glyphs.font):
				if sender.get() == ONSTATE:
					# OFF -> ON
					glyph.tags.append(tag)
				else:
					# ON -> OFF
					glyph.tags.remove(tag)
			if view := Glyphs.font.currentTab:
				view.redraw()
		except:
			print(traceback.format_exc())


	@objc.python_method
	def checkBoxEdit(self, sender):
		font = Glyphs.font
		try:
			font.disableUpdateInterface()
			guide = next(g for g, c in self.checkBoxes.items() if c.name is sender)
			oldName = guide.name
			newName = sender.get()
			oldTag = self.tagName(guide)
			# Sync guide name between masters
			for m in font.masters:
				for g in (x for x in m.guides if oldName == x.name):
					g.name = newName
			newTag = self.tagName(guide)
			# Update oldTag in each glyph & Clean up Guideless tags
			tagSet = set()
			for glyph in font.glyphs:
				if oldTag in glyph.tags:
					glyph.tags.append(newTag)
					glyph.tags.remove(oldTag)	
				for t in glyph.tags:
					if t.startswith(self.tagPrefix):
						tagSet.add(t)
			guide.filter = NSPredicate.predicateWithFormat_(f'tags CONTAINS "{self.tagName(guide)}"')

			guideTagSet = set()
			for m in font.masters:
				for g in m.guides:
					guideTagSet.add(self.tagName(g))
			for t in tagSet.difference(guideTagSet):
				print(tagSet.difference(guideTagSet))
				for glyph in font.glyphs:
					if t in glyph.tags:
						glyph.tags.remove(t)
				print(f'GuidesPalette: Removed guideless tag "{t}".')

			font.enableUpdateInterface()
			if view := font.currentTab:
				view.redraw()
		except:
			print(traceback.format_exc())


	@objc.python_method
	def newCheckBox(self, guide):
		# Create elements
		guideName, guidePos, guideAngle = self.guideNamePosAngle(guide)
		group = Group(posSize='auto')
		group.check = CheckBox(
			posSize='auto',
			title=None,
			sizeStyle='mini',
			callback=self.checkBoxToggle,
		)
		group.name = EditText(
			posSize='auto',
			text=guideName,
			sizeStyle='mini',
			continuous=False,
			callback=self.checkBoxEdit,
		)
		group.pos = TextBox(
			posSize='auto',
			text=guidePos,
			sizeStyle='mini',
		)
		group.angle = TextBox(
			posSize='auto',
			text=guideAngle,
			sizeStyle='mini',
		)

		# Update style
		font = NSFont.monospacedDigitSystemFontOfSize_weight_(
			NSFont.systemFontSizeForControlSize_(NSMiniControlSize),
			NSFontWeightRegular,
		)
		group.check._nsObject.setAllowsMixedState_(True)
		group.pos._nsObject.setFont_(font)
		group.angle._nsObject.setFont_(font)
		group.addAutoPosSizeRules([
			'H:|[check(==10)]-[name]-[pos(==60)]-[angle(==40)]|',
			'V:|-1-[check]|',
			'V:|[name(==15)]|',
			'V:|-2-[pos]|',
			'V:|-2-[angle]|',
		])
		return group


	@objc.python_method
	def guideNamePosAngle(self, guide):
		name, pos, angle = f'{guide.name}', '', ''
		if self.showCoordinates:
			pos = f'({round(guide.position.x)}, {round(guide.position.y)})'
		if self.showAngle:
			angle = f'{guide.angle:.1f}\xB0'
		return name, pos, angle


	@objc.python_method
	def globalGuides(self, master):
		res = []
		for guide in (g for g in master.guides if g.name):
			guide.filter = NSPredicate.predicateWithFormat_(f'tags CONTAINS "{self.tagName(guide)}"')
			res.append(guide)
		return res


	@objc.python_method
	def tagName(self, guide):
		if guide.name:
			return self.tagPrefix + guide.name
		else:
			return None


	@objc.python_method
	def selectedGlyphs(self, font):
		if layers := font.selectedLayers:
			return [l.parent for l in layers if not isinstance(l, GSControlLayer)]
		return []


	@objc.python_method
	def renamePrefix(self, old, new):
		font = Glyphs.font
		if old == new:
			return False
		else:
			font.disableUpdateInterface()
			# Rename tags
			for glyph in font.glyphs:
				for t in glyph.tags:
					if t.startswith(old):
						newT = new + t.removeprefix(old)
						glyph.tags.append(newT)
						glyph.tags.remove(t)
			# Update guides filter
			target = f'tags CONTAINS "{old}'
			for m in font.masters:
				for g in m.guides:
					predOld = str(g.filter)
					if predOld.startswith(target):
						predNew = predOld.replace(target, f'tags CONTAINS "{new}', 1)
						g.filter = NSPredicate.predicateWithFormat_(predNew)
			font.enableUpdateInterface()
			return True


	@objc.python_method
	def __file__(self):
		return __file__
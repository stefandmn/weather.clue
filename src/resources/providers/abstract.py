# -*- coding: utf-8 -*-

import sys
import abc
import Commons as commons

if hasattr(sys.modules["__main__"], "xbmc"):
	xbmc = sys.modules["__main__"].xbmc
else:
	import xbmc

if hasattr(sys.modules["__main__"], "xbmcgui"):
	xbmcgui = sys.modules["__main__"].xbmcgui
else:
	import xbmcgui

if hasattr(sys.modules["__main__"], "xbmcaddon"):
	xbmcaddon = sys.modules["__main__"].xbmcaddon
else:
	import xbmcaddon


class DataProvider(object):
	__metaclass__ = abc.ABCMeta
	NODAYS = 6
	FORMAT = 'json'
	WINDOW = xbmcgui.Window(12600)
	ICON = xbmc.translatePath('special://temp/weather/%s.png').decode("utf-8")
	LANG = xbmc.getLanguage().lower()
	USPEED = xbmc.getRegion('speedunit')
	UTMPRT = unicode(xbmc.getRegion('tempunit'), encoding='utf-8')
	FTIME = xbmc.getRegion('meridiem')
	FDATE = xbmc.getRegion('dateshort')

	def __repr__(self):
		return str(self.__class__) + " (" + str(self.code()) + ")"

	@abc.abstractmethod
	def code(self):
		pass

	@abc.abstractmethod
	def forecast(self, location, locationid):
		pass

	@abc.abstractmethod
	def location(self, string):
		pass

	@abc.abstractmethod
	def geoip(self):
		pass

	def property(self, name, value=None):
		if value is None:
			value = ''
		self.WINDOW.setProperty(name, value)

	def refresh(self ):
		locations = 0
		for count in range(1, 6):
			loc_name = commons.setting('Location%s' % count)
			if loc_name != '':
				locations += 1
			else:
				xbmcaddon.Addon().setSetting('Location%sid' % count, '')
			self.property('Location%s' % count, loc_name)
		self.property('Locations', str(locations))
		commons.debug('Available locations: %s' % str(locations))

	def clear(self):
		self.property('Current.Condition', 'N/A')
		self.property('Current.Temperature', '0')
		self.property('Current.Wind', '0')
		self.property('Current.WindDirection', 'N/A')
		self.property('Current.Humidity', '0')
		self.property('Current.FeelsLike', '0')
		self.property('Current.UVIndex', '0')
		self.property('Current.DewPoint', '0')
		self.property('Current.OutlookIcon', 'na.png')
		self.property('Current.FanartCode', 'na')
		for count in range(0, self.NODAYS + 1):
			self.property('Day%i.Title' % count, 'N/A')
			self.property('Day%i.HighTemp' % count, '0')
			self.property('Day%i.LowTemp' % count, '0')
			self.property('Day%i.Outlook' % count, 'N/A')
			self.property('Day%i.OutlookIcon' % count, 'na.png')
			self.property('Day%i.FanartCode' % count, 'na')

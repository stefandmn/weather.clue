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
		xbmcgui.Window(12600).setProperty(name, value)

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
		commons.debug('Clear all data')
		self.property('Current.Condition', '')
		self.property('Current.Temperature', '')
		self.property('Current.Wind', '')
		self.property('Current.WindSpeed', '')
		self.property('Current.WindDirection', '')
		self.property('Current.Humidity', '')
		self.property('Current.FeelsLike', '')
		self.property('Current.UVIndex', '')
		self.property('Current.DewPoint', '')
		self.property('Current.OutlookIcon', '')
		self.property('Current.FanartCode', '')
		self.property('Today.Sunrise', '')
		self.property('Today.Sunset', '')
		for index in range(0, self.NODAYS + 1):
			self.property('Day%i.Title' % index, '')
			self.property('Day%i.HighTemp' % index, '')
			self.property('Day%i.LowTemp' % index, '')
			self.property('Day%i.Outlook' % index, '')
			self.property('Day%i.OutlookIcon' % index, '')
			self.property('Day%i.FanartCode' % index, '')

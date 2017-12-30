# -*- coding: utf-8 -*-

import os
import sys
import Commons as commons
from resources.providers import DataProvider

if hasattr(sys.modules["__main__"], "xbmc"):
	xbmc = sys.modules["__main__"].xbmc
else:
	import xbmc

if hasattr(sys.modules["__main__"], "xbmcgui"):
	xbmcgui = sys.modules["__main__"].xbmcgui
else:
	import xbmcgui


class ClueWeather:
	PROVIDERS = {}

	def __init__(self):
		commons.debug('%s v%s has been started' %(commons.AddonName(), commons.AddonVersion()))
		self.provider = self.getProvider(commons.getSetting('Provider'))
		if self.provider is None:
			commons.error("No weather data provider found")
		else:
			commons.debug('Selected weather data provider: %s' %str(self.provider))
			self.provider.property('WeatherProvider', commons.AddonName() + " @ " + str(self.provider.code()).capitalize())
			self.provider.property('WeatherProviderLogo', xbmc.translatePath(os.path.join(commons.AddonPath().decode("utf-8"), 'icon.png')))

	def __del__(self):
		commons.debug('%s v%s has been terminated' %(commons.AddonName(), commons.AddonVersion()))
		del self

	def getProvider(self, code='default'):
		if not self.PROVIDERS:
			for cls in DataProvider.__subclasses__():
				try:
					provider = cls()
					if not self.PROVIDERS.has_key(provider.code()):
						self.PROVIDERS[provider.code()] = provider
				except BaseException as be:
					commons.error('Unexpected error while loading [%s] plugin: %s' %(str(cls),str(be)))
		if code is None or code == '' or code == 'default':
			return self.PROVIDERS.itervalues().next()
		else:
			if self.PROVIDERS.has_key(code):
				return self.PROVIDERS[code]
			else:
				return None

	def execute(self, data=''):
		# evaluate input argument and depends on run add-on event/action
		if data.startswith('Location'):
			keyboard = xbmc.Keyboard('', xbmc.getLocalizedString(14024), False)
			keyboard.doModal()
			if keyboard.isConfirmed() and keyboard.getText() != '':
				text = keyboard.getText()
				locationNames, locationIds = self.provider.location(text)
				dialog = xbmcgui.Dialog()
				if locationNames != []:
					selected = dialog.select(xbmc.getLocalizedString(396), locationNames)
					if selected != -1:
						commons.setSetting('Enabled', 'true')
						commons.setSetting(data, locationNames[selected])
						commons.debug('Selected location: %s' % locationNames[selected])
						commons.setSetting(data + 'id', locationIds[selected])
						commons.debug('Selected location id: %s' % locationIds[selected])
				else:
					dialog.ok(commons.AddonName(), commons.translate(284))
		elif commons.setting('Enabled'):
			location = commons.setting('Location%s' % data)
			locationid = commons.setting('Location%sid' % data)
			if (locationid == '') and (data != '1'):
				location = commons.setting('Location1')
				locationid = commons.setting('Location1id')
				commons.debug('Trying first location instead: %s (%s)' % (location, locationid))
			if locationid == '':
				commons.debug('Fallback to GeoIP')
				location, locationid = self.provider.geoip()
			if not locationid == '':
				commons.debug('Call forecast for location %s (%s)' % (location, locationid))
				self.provider.forecast(location, locationid)
			else:
				commons.debug('No location found')
				self.provider.clear()
			self.provider.refresh()
		else:
			commons.debug('You need to enable weather retrieval in the weather underground add-on settings')
			self.provider.clear()


if __name__ == "__main__":
	weather = ClueWeather()
	weather.execute(sys.argv[1])
	del weather
	del xbmcgui

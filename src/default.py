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
			commons.error("No weather data provider detected")
		else:
			commons.debug('Selected data provider: %s' %str(self.provider))
			self.provider.property('WeatherProvider', commons.AddonName() + " @ " + str(self.provider.code()).capitalize())
			self.provider.property('WeatherProviderLogo', xbmc.translatePath(os.path.join(commons.AddonPath().decode("utf-8"), 'icon.png')))
			# evaluate input argument and depends on run add-on event/action
			if sys.argv[1].startswith('Location'):
				keyboard = xbmc.Keyboard('', xbmc.getLocalizedString(14024), False)
				keyboard.doModal()
				if keyboard.isConfirmed() and keyboard.getText() != '':
					text = keyboard.getText()
					locations, locationids = self.provider.location(text)
					dialog = xbmcgui.Dialog()
					if locations != []:
						selected = dialog.select(xbmc.getLocalizedString(396), locations)
						if selected != -1:
							commons.setSetting('Enabled', 'true')
							commons.setSetting(sys.argv[1], locations[selected])
							commons.debug('Selected location: %s' % locations[selected])
							commons.setSetting(sys.argv[1] + 'id', locationids[selected])
							commons.debug('Selected location id: %s' % locationids[selected])
					else:
						dialog.ok(commons.AddonName(), commons.translate(284))
			elif commons.setting('Enabled'):
				location = commons.setting('Location%s' % sys.argv[1])
				locationid = commons.setting('Location%sid' % sys.argv[1])
				if (locationid == '') and (sys.argv[1] != '1'):
					location = commons.setting('Location1')
					locationid = commons.setting('Location1id')
					commons.debug('Trying location 1 instead')
				if locationid == '':
					commons.debug('Fallback to GeoIP')
					location, locationid = self.provider.geoip()
				if not locationid == '':
					self.provider.forecast(location, locationid)
				else:
					commons.debug('No location found')
					self.provider.clear()
				self.provider.refresh()
			else:
				commons.debug('You need to enable weather retrieval in the weather underground add-on settings')
				self.provider.clear()
		commons.debug('%s v%s has been terminated' %(commons.AddonName(), commons.AddonVersion()))

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


if (__name__ == "__main__"):
	ClueWeather()

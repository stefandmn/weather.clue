# -*- coding: utf-8 -*-

import os
import sys
import commons
from resources.providers import ContentProvider



class ClueWeather:
	PROVIDERS = {}

	def __init__(self):
		commons.debug('%s v%s has been started' %(commons.AddonName(), commons.AddonVersion()))


	def __del__(self):
		commons.debug('%s v%s has been terminated' %(commons.AddonName(), commons.AddonVersion()))
		del self


	def readProviders(self):
		"""Detect all implemented and declared providers and build up the corresponding dictionary"""
		self.PROVIDERS.clear()
		for cls in ContentProvider.__subclasses__():
			try:
				provider = cls()
				if not self.PROVIDERS.has_key(provider.code()):
					self.PROVIDERS[provider.code()] = provider
				else:
					commons.error("Invalid signature of content provider, it has the same name or id with another one: %s " %provider)
			except BaseException as be:
				commons.error('Unexpected error while reading [%s] content provider: %s' %(str(cls),str(be)))


	def getProviderByCode(self, code):
		"""Returns the content provider having the specified signature """
		provider = None
		if not self.PROVIDERS:
			self.readProviders()
		if code is not None and self.PROVIDERS.has_key(code):
			provider = self.PROVIDERS[code]
		return provider


	def getProviderByName(self, name):
		"""Returns the content provider having the specified name """
		provider = None
		if not self.PROVIDERS:
			self.readProviders()
		for obj in self.PROVIDERS.values():
			if obj.name() == name:
				provider = obj
				break
		return provider


	def getProviderNames(self):
		"""Returns the list of provider names or the registered provider instances"""
		names = []
		if not self.PROVIDERS:
			self.readProviders()
		for obj in self.PROVIDERS.values():
			names.append(obj.name())
		return names


	def setProvider(self, config):
		"""Runs configuration flow to setup or to change the provider"""
		if str(config) == "ProviderCode":
			commons.debug("Setting new provider")
			options = self.getProviderNames()
			index = commons.SelectDialog(32201, options)
			if index >= 0:
				provider = self.getProviderByName(options[index])
				commons.setAddonSetting("Enabled", "true")
				if provider is not None:
					provider.clear()
					commons.setAddonSetting("Provider", provider.code())
					commons.setAddonSetting("ProviderAction", provider.name())
				else:
					commons.setAddonSetting("Provider")
					commons.setAddonSetting("ProviderAction")
				# reset dependent settings
				commons.setAddonSetting("APIKey")
				commons.setAddonSetting("APIKeyAction")
				for index in range(1,6):
					commons.setAddonSetting("Location%iAction" % index)
					commons.setAddonSetting("Location%i" % index)
					commons.debug('Reset location %i' %index)
				# trigger provider validation
				commons.debug("Asking for provider validation")
				commons.setAddonSetting("Validate", "true")
				# trigger normalization
				commons.setSkinProperty(12600, 'WeatherProvider')
			else:
				commons.debug("Provider configuration was cancelled")
		elif str(config) == "ProviderKey":
			commons.debug("Setting new provider API key")
			inputval = commons.StringInputDialog(32122, commons.getAddonSetting("APIKey"))
			if inputval is not None and inputval != '':
				commons.setAddonSetting("APIKey", inputval)
				commons.setAddonSetting("APIKeyAction", "".rjust(len(inputval), "*"))
				# trigger provider validation
				commons.debug("Asking for provider validation")
				commons.setAddonSetting("Validate", "true")
			else:
				commons.debug("Provider API key configuration was cancelled")
		else:
			commons.debug("Unknown provider configuration option: %s" %config)


	def setLocation(self, config):
		"""Runs configuration flow to setup new location"""
		commons.debug("Setting new location (%s)" %config)
		provider = self.getProviderByCode(commons.getAddonSetting('Provider'))
		if provider is None:
			raise StandardError("No content provider selected for configuration")
		inputval = commons.StringInputDialog(14024, commons.getAddonSetting(config + "Action"))
		if inputval is not None and inputval != '':
			locnames, locids = provider.location(inputval)
			if locnames:
				selindex = commons.SelectDialog(396, locnames)
				if selindex >= 0:
					commons.setAddonSetting(config + "Action", locnames[selindex])
					commons.setAddonSetting(config, locids[selindex])
					commons.debug('Selected location: (%s - %s)' %(locnames[selindex], locids[selindex]))
			else:
				commons.OkDialog(284)
			# trigger normalization
			commons.setSkinProperty(12600, 'WeatherProvider')
		else:
			commons.debug("Location configuration was cancelled")


	def PublishProvider(self):
		commons.debug("Publishing provider through initialization")
		provider = self.getProviderByCode(commons.getAddonSetting('Provider'))
		if provider is not None:
			provider.skinproperty('WeatherProvider', provider.name())
			if os.path.isfile(commons.path('resources', 'media', provider.code() + '.png')):
				provider.skinproperty('WeatherProviderLogo', commons.path('resources', 'media', provider.code() + '.png'))
			else:
				provider.skinproperty('WeatherProviderLogo', commons.path('icon.png'))
			commons.debug("Active provider: %s" % provider)


	def NormalizeLocations(self,):
		commons.debug("Normalizing locations through initialization")
		count = 0
		found = False
		for index in range(1, 6):
			locname = commons.setting('Location%iAction' %index)
			locid = commons.setting('Location%i' % index)
			if not found and (locname != '' and locid != ''):
				count += 1
			elif not found and (locname == '' or locid == ''):
				found = True
			if found:
				commons.setSkinProperty(12600, 'Location%i' % index)
				commons.setAddonSetting('Location%iAction' % index)
				commons.setAddonSetting('Location%i' % index)
			else:
				commons.setSkinProperty(12600, 'Location%i' % index, locname)
		commons.setSkinProperty(12600, 'Locations', str(count))
		commons.debug("Active locations: %s" % str(count))


	def settings(self, config):
		if str(config).startswith("Location"):
			self.setLocation(config)
		elif str(config).startswith("Provider"):
			self.setProvider(config)


	def run(self, index):
		""" Runs package for content discovery and processing"""
		if not commons.setting('Enabled'):
			return
		provider = self.getProviderByCode(commons.getAddonSetting('Provider'))
		commons.debug("Found provider for running: %s" %provider)
		if provider is None:
			commons.NotificationMsg(32202, 15000)
			return
		if provider is not None and (commons.setting('APIKey') == '' or commons.setting('APIKey') is None):
			commons.NotificationMsg(32123, 15000)
			return
		if commons.any2bool(commons.getAddonSetting("Validate")):
			commons.debug("Validating configured content provider")
			try:
				provider.validate()
				commons.setAddonSetting("Validate", "false")
				commons.debug("Content provider is validated, running weather forecast workflow")
			except BaseException as be:
				commons.debug("Content provider is invalid, reset forecast skin properties: %s" %str(be))
				commons.NotificationMsg(32203, 20000)
				provider.clear()
				return
		if commons.isempty(commons.getSkinProperty(12600, 'WeatherProvider')):
			self.NormalizeLocations()
			self.PublishProvider()
		if index is None:
			commons.debug('Run GeoIP location discovery due to missing configuration')
			locname, locid = provider.geoip()
		else:
			commons.debug("Using location index: %s" %str(index))
			locname = commons.setting('Location%sAction' % str(index))
			locid = commons.setting('Location%s' % str(index))
		if locid == '' and commons.any2int(index) > 1:
			commons.debug('Trying first location instead, due to invalid index defined in previous configuration')
			locname = commons.setting('Location1Action')
			locid = commons.setting('Location1')
		if locid == '':
			commons.debug('Run GeoIP location discovery due to wrong configuration')
			locname, locid = provider.geoip()
		if locname != '':
			if locid != provider.skininfo("Current.Location"):
				provider.clear()
			commons.debug('Call forecast for location %s (%s)' % (locname, locid))
			provider.forecast(locname, locid)
		else:
			commons.warn('No location found or configured')
			provider.clear()



if __name__ == "__main__":
	weather = ClueWeather()
	if str(sys.argv[1]).strip() == "setup":
		weather.settings(str(sys.argv[2]).strip())
	else:
		weather.run(str(sys.argv[1]).strip())
	del weather

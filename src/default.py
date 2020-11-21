# -*- coding: utf-8 -*-

import os
import sys
import common
from resources.providers import ContentProvider



class ClueWeather:
	PROVIDERS = {}

	def __init__(self):
		common.debug('%s v%s has been started' %(common.AddonName(), common.AddonVersion()))


	def __del__(self):
		common.debug('%s v%s has been terminated' %(common.AddonName(), common.AddonVersion()))
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
					common.error("Invalid signature of content provider, it has the same name or id with another one: %s " %provider)
			except BaseException as be:
				common.error('Unexpected error while reading [%s] content provider: %s' %(str(cls),str(be)))


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
			common.debug("Setting new provider")
			options = self.getProviderNames()
			index = common.SelectDialog(32201, options)
			if index >= 0:
				provider = self.getProviderByName(options[index])
				common.setAddonSetting("Enabled", "true")
				if provider is not None:
					provider.clear()
					common.setAddonSetting("Provider", provider.code())
					common.setAddonSetting("ProviderAction", provider.name())
				else:
					common.setAddonSetting("Provider")
					common.setAddonSetting("ProviderAction")
				# reset dependent settings
				common.setAddonSetting("APIKey")
				common.setAddonSetting("APIKeyAction")
				for index in range(1,6):
					common.setAddonSetting("Location%iAction" % index)
					common.setAddonSetting("Location%i" % index)
					common.debug('Reset location %i' %index)
				# trigger provider validation
				common.debug("Asking for provider validation")
				common.setAddonSetting("Validate", "true")
			else:
				common.debug("Provider configuration was cancelled")
		elif str(config) == "ProviderKey":
			common.debug("Setting new provider API key")
			inputval = common.StringInputDialog(32122, common.getAddonSetting("APIKey"))
			if inputval is not None and inputval != '':
				common.setAddonSetting("APIKey", inputval)
				common.setAddonSetting("APIKeyAction", "".rjust(len(inputval), "*"))
				# trigger provider validation
				common.debug("Asking for provider validation")
				common.setAddonSetting("Validate", "true")
			else:
				common.debug("Provider API key configuration was cancelled")
		else:
			common.debug("Unknown provider configuration option: %s" %config)


	def setLocation(self, config):
		"""Runs configuration flow to setup new location"""
		common.debug("Setting new location (%s)" %config)
		provider = self.getProviderByCode(common.getAddonSetting('Provider'))
		if provider is None:
			raise RuntimeError("No content provider selected for configuration")
		inputval = common.StringInputDialog(14024, common.getAddonSetting(config + "Action"))
		if inputval is not None and inputval != '':
			locnames, locids = provider.location(inputval)
			if locnames:
				selindex = common.SelectDialog(396, locnames)
				if selindex >= 0:
					common.setAddonSetting(config + "Action", locnames[selindex])
					common.setAddonSetting(config, locids[selindex])
					common.debug('Selected location: (%s - %s)' %(locnames[selindex], locids[selindex]))
			else:
				common.OkDialog(284)
		else:
			common.debug("Location configuration was cancelled")


	def settings(self, config):
		if str(config).startswith("Location"):
			self.setLocation(config)
		elif str(config).startswith("Provider"):
			self.setProvider(config)


	def run(self, index):
		""" Runs package for content discovery and processing"""
		# check if forecast workflow is enabled
		if not common.setting('Enabled'):
			return
		# check provider configuration
		provider = self.getProviderByCode(common.getAddonSetting('Provider'))
		common.debug("Found provider to run forecast workflow: %s" %provider)
		if provider is None:
			common.NotificationMsg(32202, 15000)
			return
		if provider is not None and (common.setting('APIKey') == '' or common.setting('APIKey') is None):
			common.NotificationMsg(32123, 15000)
			return
		# validate provider configuration
		if common.any2bool(common.getAddonSetting("Validate")):
			try:
				provider.validate()
				common.setAddonSetting("Validate", "false")
				common.debug("Content provider is valid, running weather forecast workflow")
			except:
				common.debug("Content provider is invalid, reset forecast skin properties")
				common.NotificationMsg(32203, 20000)
				provider.clear()
				return
		# normalize locations
		count = 0
		found = False
		for id in range(1, 6):
			locname = common.setting('Location%iAction' %id)
			locid = common.setting('Location%i' % id)
			if not found and (locname != '' and locid != ''):
				count += 1
			elif not found and (locname == '' or locid == ''):
				found = True
			if found:
				common.setSkinProperty(12600, 'Location%i' %id)
				common.setAddonSetting('Location%iAction' %id)
				common.setAddonSetting('Location%i' %id)
			else:
				common.setSkinProperty(12600, 'Location%i' %id, locname)
		common.setSkinProperty(12600, 'Locations', str(count))
		common.debug("Active locations: %s" % str(count))
		# identify the right location
		if index is None:
			common.debug('Run GeoIP location discovery due to missing configuration')
			locname, locid = provider.geoip()
		else:
			common.debug("Using location index: %s" %str(index))
			locname = common.setting('Location%sAction' % str(index))
			locid = common.setting('Location%s' % str(index))
		if locid == '' and common.any2int(index) > 1:
			common.debug('Trying first location instead, due to invalid index defined in previous configuration')
			locname = common.setting('Location1Action')
			locid = common.setting('Location1')
		if locid == '':
			common.debug('Run GeoIP location discovery due to wrong configuration')
			locname, locid = provider.geoip()
		# run forecast workflow
		if locname != '':
			# reset skin properties when the location is changed
			if locid != provider.skininfo("Current.Location"):
				provider.clear()
			# publish provider details
			provider.skinproperty('WeatherProvider', provider.name())
			if os.path.isfile(common.path('resources', 'media', provider.code() + '.png')):
				provider.skinproperty('WeatherProviderLogo', common.path('resources', 'media', provider.code() + '.png'))
			else:
				provider.skinproperty('WeatherProviderLogo', common.path('icon.png'))
			# call provider forecast
			common.debug('Call forecast for location %s (%s)' % (locname, locid))
			provider.forecast(locname, locid)
		else:
			common.warn('No location found or configured')
			provider.clear()



if __name__ == "__main__":
	weather = ClueWeather()
	if str(sys.argv[1]).strip() == "setup":
		weather.settings(str(sys.argv[2]).strip())
	else:
		weather.run(str(sys.argv[1]).strip())
	del weather

# -*- coding: utf-8 -*-

import os
import sys
import abc
import json
import time
import base64
import commons
import urllib2

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

if hasattr(sys.modules["__main__"], "xbmcvfs"):
	xbmcvfs = sys.modules["__main__"].xbmcvfs
else:
	import xbmcvfs



class ContentProvider(object):
	__metaclass__ = abc.ABCMeta
	LANGUAGE = xbmc.getLanguage().lower()
	UM_SPEED = xbmc.getRegion('speedunit')
	UM_TEMPR = xbmc.getRegion('tempunit')
	ART_BASE = {"Clear/Day": 101,
				"Clear/Night": 102,
				"Sunny/Day": 101,
				"Cloudy/Neutral": 200,
				"Cloudy/Mostly/Neutral": 210,
				"Cloudy/Mostly/Day": 211,
				"Cloudy/Mostly Night": 212,
				"Cloudy/Partly/Neutral": 220,
				"Cloudy/Partly/Day": 221,
				"Cloudy/Partly/Night": 222,
				"Cloudy/Windy/Neutral": 230,
				"Cloudy/Windy/Day": 231,
				"Cloudy/Windy/Night": 232,
				"Cloudy/Gust/Neutral": 240,
				"Cloudy/Gust/Day": 241,
				"Cloudy/Gust/Night": 242,
				"Rain/Neutral": 300,
				"Rain/Day": 301,
				"Rain/Night": 302,
				"Rain/Windy/Neutral": 310,
				"Rain/Windy/Day": 311,
				"Rain/Windy/Night": 312,
				"Rain/Showers/Neutral": 320,
				"Rain/Showers/Day": 321,
				"Rain/Showers/Night": 322,
				"Rain/Thunderstorm/Neutral": 330,
				"Rain/Thunderstorm/Day": 331,
				"Rain/Thunderstorm/Night": 332,
				"Rain/Mix/Neutral": 340,
				"Rain/Mix/Day": 341,
				"Rain/Mix/Night": 342,
				"Snow/Neutral": 400,
				"Snow/Day": 401,
				"Snow/Night": 402,
				"Snow/Windy/Neutral": 410,
				"Snow/Windy/Day": 411,
				"Snow/Windy/Night": 412,
				"Snow/Thunderstorm/Neutral": 420,
				"Snow/Thunderstorm/Day": 421,
				"Snow/Thunderstorm/Night": 422,
				"Fog/Neutral": 500,
				"Fog/Day": 501,
				"Fog/Night": 502,
				"Others/Heat": 1010,
				"Others/Raindrops": 1020,
				"Others/Windy": 1030,
				"Others/StrongWind": 1040,
				"Others/Lightning": 1050,
				"Others/Tornado": 1060,
				"Others/Hurricane": 1070
				}


	def __repr__(self):
		return str(self.__class__) + " - " + str(self.name()) + " (" + str(self.code()) + ")"


	@abc.abstractmethod
	def name(self):
		pass

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


	@abc.abstractmethod
	def validate(self):
		pass


	@property
	def apikey(self):
		return commons.setting("APIKey")


	def _parse(self, content):
		if content is not None:
			commons.debug("Parsing content: %s" % content)
			try:
				raw = content.replace('<br>', ' ')
				raw = raw.replace('"NA"', '""')
				output = json.loads(raw)
			except BaseException as be:
				commons.debug('Failed to parse weather data: %s' %be)
				output = None
			return output
		else:
			return json.loads('')


	def skinproperty(self, name, value=None, um=None):
		if value is None:
			value = ''
		if isinstance(value, float):
			value = "{:.1f}".format(value)
		if um is None or um == '':
			xbmcgui.Window(12600).setProperty(name, str(value))
		else:
			xbmcgui.Window(12600).setProperty(name, str(value) + str(um))


	def skininfo(self, name):
		try:
			value = xbmc.getInfoLabel("Window(%i).Property(%s)" % (12600, str(name)))
		except:
			value = ''
		return value


	def clear(self):
		commons.debug('Clear all data')
		self.skinproperty('WeatherProvider')
		self.skinproperty('WeatherProviderLogo')
		self.skinproperty('Current.IsFetched')
		self.skinproperty('Current.Location')
		self.skinproperty('Current.Latitude')
		self.skinproperty('Current.Longitude')
		self.skinproperty('Current.Condition')
		self.skinproperty('Current.Temperature')
		self.skinproperty('Current.Wind')
		self.skinproperty('Current.WindSpeed')
		self.skinproperty('Current.WindDirection')
		self.skinproperty('Current.Pressure')
		self.skinproperty('Current.Humidity')
		self.skinproperty('Current.FeelsLike')
		self.skinproperty('Current.UVIndex')
		self.skinproperty('Current.DewPoint')
		self.skinproperty('Current.Visibility')
		self.skinproperty('Current.OutlookIcon')
		self.skinproperty('Current.FanartCode')
		self.skinproperty('Today.Sunrise')
		self.skinproperty('Today.Sunset')
		self.skinproperty('Today.HighTemperature')
		self.skinproperty('Today.LowTemperature')
		self.skinproperty('Daily.IsFetched')
		for index in range(0, 6):
			self.skinproperty('Day.%i.Title' % index)
			self.skinproperty('Day.%i.HighTemp' % index)
			self.skinproperty('Day.%i.LowTemp' % index)
			self.skinproperty('Day.%i.Outlook' % index)
			self.skinproperty('Day.%i.OutlookIcon' % index)
			self.skinproperty('Day.%i.FanartCode' % index)
			self.skinproperty('Day.%i.Pressure' % index)
			self.skinproperty('Day.%i.Humidity' % index)
			self.skinproperty('Day.%i.UVIndex' % index)
			self.skinproperty('Day.%i.DewPoint' % index)
			self.skinproperty('Day.%i.Visibility' % index)
		self.skinproperty('Hourly.IsFetched')
		for index in range(0, 16):
			self.skinproperty('Hourly.%i.Time' % index)
			self.skinproperty('Hourly.%i.ShortDate' % index)
			self.skinproperty('Hourly.%i.FanartCode' % index)
			self.skinproperty('Hourly.%i.Temperature' % index)
			self.skinproperty('Hourly.%i.Outlook' % index)
			self.skinproperty('Hourly.%i.Pressure' % index)
			self.skinproperty('Hourly.%i.Humidity' % index)
			self.skinproperty('Hourly.%i.UVIndex' % index)
			self.skinproperty('Hourly.%i.DewPoint' % index)
			self.skinproperty('Hourly.%i.Visibility' % index)
		self.skinproperty('Alerts.IsFetched')
		self.skinproperty('Alerts.Text')
		for index in range(0, 5):
			self.skinproperty('Alerts.%i.Title' % index)
			self.skinproperty('Alerts.%i.Description' % index)
			self.skinproperty('Alerts.%i.Expires' % index)


	def ipinfo(self):
		"""
		Get IP Geolocation in JSON format. The message contains the following data: country,
		countryCode, region, regionName, city, zip, lat, lon, timezone, isp, status
		:return: a JSON message containing the specified message parts.
		"""
		url = "http://ip-api.com/json/"
		try:
			req = urllib2.urlopen(url)
			data = req.read()
			req.close()
		except:
			data = ''
		return self._parse(data)


	@property
	def lang(self):
		return str(xbmc.getLanguage(xbmc.ISO_639_1)).lower()


	def feelslike(self, temp, wind, hum):
		"""
		Calculates Feels Like temperature based on Heat index and chill wind properties
		:param temp: temperature (should be in °C)
		:param wind: wind speed (should be in Km/h)
		:param hum: humidity (%)
		:return: feels like temperature (converted in °C)
		"""
		if temp <= 10 and wind >= 8:
			output = (13.12 + (0.6215 * temp) - (11.37 * wind ** 0.16) + (0.3965 * temp * wind ** 0.16))
		elif temp >= 26:
			temp = temp * 1.8 + 32  # calculation is done in F
			output = -42.379 + (2.04901523 * temp) + (10.14333127 * hum) + (-0.22475541 * temp * hum) + (-0.00683783 * temp ** 2) + (-0.05481717 * hum ** 2) + (0.00122874 * temp ** 2 * hum) + (0.00085282 * temp * hum ** 2) + (-0.00000199 * temp ** 2 * hum ** 2)
			output = (output - 32) / 1.8  # convert to C
		else:
			output = temp
		return output


	def _fanart(self, code):
		"""Detect and return fanart code"""
		return self.ART_BASE[code]


	def _2shday(self, value):
		return time.strftime('%A', time.localtime(value))


	def _2shtime(self, value):
		return time.strftime('%H:%M', time.localtime(value))


	def _2shdate(self, value):
		return time.strftime('%d %b', time.localtime(value))


	def _2shdatetime(self, value):
		return time.strftime('%d %b %H:%M', time.localtime(value))


	def coordinates(self, lat, long):
		self._latitude = lat
		self._longitude = long


	@property
	def latitude(self):
		return self._latitude


	@property
	def longitude(self):
		return self._longitude


	def _2temp(self, value):
		"""
		Calculates and returns the temperature in unit described by the system
		:param value: temperature received in C
		:return: transformed temperature
		"""
		if len(self.UM_TEMPR) > 1:
			if self.UM_TEMPR[1:].lower() == 'c':
				temp = value
			elif self.UM_TEMPR[1:].lower() == 'f':
				temp = ((5 * value) / 9) + 32
			elif self.UM_TEMPR[1:].lower() == 'k':
				temp = value + 273.15
			else:
				temp = value
		elif len(self.UM_TEMPR) == 1:
			if self.UM_TEMPR.lower() == 'c':
				temp = value
			elif self.UM_TEMPR.lower() == 'f':
				temp = ((5 * value) / 9) + 32
			elif self.UM_TEMPR.lower() == 'k':
				temp = value + 273.15
			else:
				temp = value
		else:
			temp = value
		return temp


	def _2wind(self, value):
		"""
		Calculates and returns the wind speed in unit described by the system
		:param value: wind speed received in mps
		:return: transformed speed
		"""
		if self.UM_SPEED.lower() == 'mps':
			wind = value
		elif self.UM_SPEED.lower() == 'km/h' or self.UM_SPEED.lower() == 'kmph' or self.UM_SPEED.lower() == 'kph':
			wind = value * 3.6
		elif self.UM_SPEED.lower() == 'mph':
			wind = value * 2.236934
		else:
			wind = value
		return wind


	def _2c(self, value, um='c'):
		"""
		Calculates and return temperature in °C
		:param value: value read from provider
		:return: transformed temperature based on detected units
		"""
		if len(um) > 1:
			if um[1:].lower() == 'c':
				temp = value
			elif um[1:].lower() == 'f':
				temp = 5 * (value - 32) / 9
			elif um[1:].lower() == 'k':
				temp = value - 273.15
			else:
				temp = value
		elif len(um) == 1:
			if um.lower() == 'c':
				temp = value
			elif um.lower() == 'f':
				temp = 5 * (value - 32) / 9
			elif um.lower() == 'k':
				temp = value - 273.15
			else:
				temp = value
		else:
			temp = value
		return temp

	def _2kph(self, value, um='mps'):
		"""
		Get wind speed in km/h
		:param value: value read from provider
		:return: transformed wind speed based on detected units
		"""
		if um.lower() == 'mps':
			speed = value * 3.6
		elif um.lower() == 'km/h' or um.lower() == 'kmph' or um.lower() == 'kph':
			speed = value
		elif um.lower() == 'mph':
			speed = value * 1.609344
		else:
			speed = value
		return speed


	def _2km(self, value, um='m'):
		"""
		Get distance in km
		:param value: value read from provider
		:return: transformed distance based on detected units
		"""
		if um.lower() == 'm':
			speed = value / 1000
		elif um.lower() == 'km' or um.lower() == 'k':
			speed = value
		elif um.lower() == 'ml' or um.lower() == 'mile' or um.lower() == 'miles':
			speed = value * 1.609344
		else:
			speed = value
		return speed


	@property
	def UM_DSTNC(self):
		if self.UM_SPEED.lower() == 'mps':
			return "m"
		elif self.UM_SPEED.lower() == 'km/h' or self.UM_SPEED.lower() == 'kmph' or self.UM_SPEED.lower() == 'kph':
			return "km"
		elif self.UM_SPEED.lower() == 'mph':
			return "miles"
		else:
			return ""

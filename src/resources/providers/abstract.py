# -*- coding: utf-8 -*-

import sys
import abc
import json
import time
import math
import common

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
		return common.setting("APIKey") if common.setting("APIKey") is not None else common.getSkinProperty(12600, "SkinProviderAPIKey")


	def _call(self, url):
		response = common.urlcall(url)
		return self._parse(response.decode('utf-8'))


	def _parse(self, content):
		if content is not None:
			common.debug("Parsing content: %s" % content)
			try:
				raw = content.replace('<br>', ' ')
				raw = raw.replace('"NA"', '""')
				output = json.loads(raw)
			except BaseException as be:
				common.debug('Failed to parse weather data: %s' %be)
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
		common.debug('Clear all data')
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
		self.skinproperty('Forecast.City')
		self.skinproperty('Forecast.Country')
		self.skinproperty('Forecast.Latitude')
		self.skinproperty('Forecast.Longitude')
		self.skinproperty('Forecast.Updated')
		self.skinproperty('Today.IsFetched')
		self.skinproperty('Today.Sunrise')
		self.skinproperty('Today.Sunset')
		self.skinproperty('Today.HighTemperature')
		self.skinproperty('Today.LowTemperature')
		self.skinproperty('Daily.IsFetched')
		for index in range(0, 6):
			# Standard
			self.skinproperty('Day%i.Title' % index)
			self.skinproperty('Day%i.HighTemp' % index)
			self.skinproperty('Day%i.LowTemp' % index)
			self.skinproperty('Day%i.Outlook' % index)
			self.skinproperty('Day%i.OutlookIcon' % index)
			self.skinproperty('Day%i.FanartCode' % index)
			# Extended
			self.skinproperty('Daily.%i.ShortDay' % index)
			self.skinproperty('Daily.%i.LongDay' % index)
			self.skinproperty('Daily.%i.ShortDate' % index)
			self.skinproperty('Daily.%i.LongDate' % index)
			self.skinproperty('Daily.%i.Outlook' % index)
			self.skinproperty('Daily.%i.OutlookIcon' % index)
			self.skinproperty('Daily.%i.FanartCode' % index)
			self.skinproperty('Daily.%i.Pressure' % index)
			self.skinproperty('Daily.%i.Humidity' % index)
			self.skinproperty('Daily.%i.UVIndex' % index)
			self.skinproperty('Daily.%i.DewPoint' % index)
			self.skinproperty('Daily.%i.Visibility' % index)
			self.skinproperty('Daily.%i.HighTemperature' % index)
			self.skinproperty('Daily.%i.LowTemperature' % index)
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
		return self._call(url)


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
		if not isinstance(value, int):
			return time.strftime('%a', time.localtime(value))
		if value == 0:
			return xbmc.getLocalizedString(47)
		elif value == 1:
			return xbmc.getLocalizedString(41)
		elif value == 2:
			return xbmc.getLocalizedString(42)
		elif value == 3:
			return xbmc.getLocalizedString(43)
		elif value == 4:
			return xbmc.getLocalizedString(44)
		elif value == 5:
			return xbmc.getLocalizedString(45)
		elif value == 6:
			return xbmc.getLocalizedString(46)

	def _2lnday(self, value):
		if not isinstance(value, int):
			value = time.strftime('%w', time.localtime(value))
		if value == 0:
			return xbmc.getLocalizedString(17)
		elif value == 1:
			return xbmc.getLocalizedString(11)
		elif value == 2:
			return xbmc.getLocalizedString(12)
		elif value == 3:
			return xbmc.getLocalizedString(13)
		elif value == 4:
			return xbmc.getLocalizedString(14)
		elif value == 5:
			return xbmc.getLocalizedString(15)
		elif value == 6:
			return xbmc.getLocalizedString(16)


	def _2shtime(self, value):
		return time.strftime('%H:%M', time.localtime(value))


	def _2shdate(self, value):
		return time.strftime('%d %b', time.localtime(value))


	def _2lndate(self, value):
		return time.strftime('%d %B %Y', time.localtime(value))


	def _2shdatetime(self, value):
		return time.strftime('%d %b %H:%M', time.localtime(value))


	def _dewpoint(self, Tc=0, RH=93, minRH=(0, 0.075)[0]):
		""" Dewpoint from relative humidity and temperature. using relative
		humidity and the air temperature
		"""
		# 1) Obtain the saturation vapor pressure (Es) using this formula as before when air temperature is known.
		Es = 6.11 * 10.0 ** (7.5 * Tc/(237.7 + Tc))
		# 2) Use the saturation vapor pressure and the relative humidity to compute the actual vapor pressure (E) of the air.
		# RH=relative humidity of air expressed as a percent. or except minimum(.075) humidity to abort error with math.log.
		RH = int(RH) or minRH  # 0.075
		E = (RH * Es)/100
		# 3) Obtain the dewpoint temperature.
		try:
			DewPoint = (-430.22 + 237.7 * math.log(E)) / (-math.log(E) + 19.08)
		except ValueError:
			# math domain error, because RH = 0%, returns "N/A"
			DewPoint = 0  # minRH
		# Note: Due to the rounding of decimal places, your answer may be slightly different from the above answer, but it should be within two degrees.
		return str(int(round(DewPoint)))


	def coordinates(self, lat, long):
		self._latitude = lat
		self._longitude = long


	@property
	def latitude(self):
		return self._latitude


	@property
	def longitude(self):
		return self._longitude


	@property
	def UM_TEMPERATURE(self):
		return xbmc.getRegion('tempunit')


	def _2temperature(self, value, iu=None, ou=None, um=False):
		"""
		Calculates and returns the temperature based on input and output unit measure.
		In case input and/or output are null then the system default unit is considered.
		When the output unit is null means that the conversion is done and returned using
		system unit.
		:param value: temperature received in input unit
		:param iu: specify unit of the input value
		:param ou: specify the unit of the output value (converted value)
		:param um: specify if the unit measure representation to be included in the output
		:return: transformed temperature in output unit measure
		"""
		value = float(value)
		default = str(self.UM_TEMPERATURE).replace('°', '').strip().lower()
		iu = default if iu is None else iu.lower()
		ou = default if ou is None else ou.lower()
		if (iu is not None and len(iu) > 1):
			iu = iu[0:]
		if (ou is not None and len(ou) > 1):
			ou = ou[0:]
		if iu == ou:
			temp = value
		else:
			if iu == 'f' and ou == 'c':
				temp = 5 * (value - 32) / 9
			elif iu == 'k' and ou == 'c':
				temp = value - 273.15
			elif iu == 'c' and ou == 'f':
				temp = (9 * value / 5) + 32
			elif iu == 'k' and ou == 'f':
				temp = (9 * value / 5) - 459.67
			elif iu == 'c' and ou == 'k':
				temp = value + 273.15
			elif iu == 'f' and ou == 'k':
				temp = 5 * (value + 459.67) / 9
			else:
				temp = value
		if um:
			if ou is None:
				return str(round(temp, 1)) + " " + self.UM_TEMPERATURE
			elif ou == 'c':
				return str(round(temp, 1)) + " °C"
			elif ou == 'f':
				return str(round(temp, 1)) + " °F"
			elif ou == 'k':
				return str(round(temp, 1)) + " K"
			else:
				return str(round(temp, 1))
		else:
			return round(temp, 1)


	@property
	def UM_SPEED(self):
		speed = xbmc.getRegion('speedunit')
		if speed.lower() == 'mps':
			return "mps"
		elif speed.lower() == 'km/h' or speed.lower() == 'kmph' or speed.lower() == 'kph':
			return "kmh"
		elif speed.lower() == 'mph':
			return "mph"
		else:
			return ""


	def _2speed(self, value, iu=None, ou=None, um=False):
		"""
		Calculates and returns the wind speed in unit described by the system
		:param value: current wind speed
		:param iu: specify unit of the input value
		:param ou: specify the unit of the output value (converted value)
		:param um: specify if the unit measure representation to be included in the output
		:return: transformed speed
		"""
		value = float(value)
		default = str(self.UM_SPEED).lower()
		iu = default if iu is None else iu.lower()
		ou = default if ou is None else ou.lower()
		if iu == ou:
			speed = value
		else:
			if iu == 'mps' and ou == 'kph':
				speed = value * 3.6
			elif iu == 'mph' and ou == 'kph':
				speed = value * 1.609344
			elif iu == 'kph' and ou == 'mps':
				speed = value * 0.277778
			elif iu == 'mph' and ou == 'mps':
				speed = value * 0.44704
			elif iu == 'kph' and ou == 'mph':
				speed = value * 0.621371
			elif iu == 'mps' and ou == 'mph':
				speed = value * 2.236936
			else:
				speed = value
		if um:
			if ou is None:
				return str(round(speed, 1)) + " " + self.UM_SPEED
			elif ou == 'kph':
				return str(round(speed, 1)) + " kph"
			elif ou == 'mps':
				return str(round(speed, 1)) + " mps"
			elif ou == 'mph':
				return str(round(speed, 1)) + " mps"
			else:
				return str(round(speed, 1))
		else:
			return round(speed, 1)


	@property
	def UM_DISTANCE(self):
		speed = xbmc.getRegion('speedunit')
		if speed.lower() == 'mps':
			return "m"
		elif speed.lower() == 'km/h' or speed.lower() == 'kmph' or speed.lower() == 'kph':
			return "km"
		elif speed.lower() == 'mph':
			return "mi"
		else:
			return ""


	def _2distance(self, value, iu=None, ou=None, um=False):
		"""
		Calculate and convert distance based on input value and transformed using input and output units
		:param value: value read from provider
		:param iu: specify unit of the input value
		:param ou: specify the unit of the output value (converted value)
		:param um: specify if the unit measure representation to be included in the output
		:return: transformed distance based on detected units
		"""
		value = float(value)
		default = str(self.UM_DISTANCE).lower()
		iu = default if iu is None else iu.lower()
		ou = default if ou is None else ou.lower()
		if iu == ou:
			dist = value
		else:
			if iu == 'km' and ou == 'm':
				dist = value * 1000
			elif iu == 'mi' and ou == 'm':
				dist = value * 1609.34
			elif iu == 'm' and ou == 'km':
				dist = value / 1000
			elif iu == 'mi' and ou == 'km':
				dist = value * 1.60934
			elif iu == 'm' and ou == 'mi':
				dist = value / 1609.34
			elif iu == 'km' and ou == 'mi':
				dist = value / 1.60934
			else:
				dist = value
		if um:
			if ou is None:
				return str(round(dist, 1)) + " " + self.UM_DISTANCE
			elif ou == 'm':
				return str(round(dist, 1)) + " m"
			elif ou == 'km':
				return str(round(dist, 1)) + " km"
			elif ou == 'mi':
				return str(round(dist, 1)) + " mi"
			else:
				return str(round(dist, 1))
		else:
			return round(dist, 1)


	def _2pressure(self, value, iu=None, ou=None, um=False):
		"""
		Calculates pressure and converted based on input and output units
		:param value: value read from provider
		:param iu: specify unit of the input value
		:param ou: specify the unit of the output value (converted value)
		:param um: specify if the unit measure representation to be included in the output
		:return: transformed pressure based on detected units
		"""
		value = float(value)
		default = str('hPa').lower()
		iu = default if iu is None else iu.lower()
		ou = default if ou is None else ou.lower()
		if iu == ou:
			dist = value
		else:
			if iu == 'hpa' and ou == 'bar':
				dist = value * 1000
			elif iu == 'hpa' and ou == 'psi':
				dist = value * 0.0145038
			elif iu == 'bar' and ou == 'hpa':
				dist = value / 1000
			elif iu == 'bar' and ou == 'psi':
				dist = value * 14.5038
			elif iu == 'psi' and ou == 'hpa':
				dist = value * 68.9476
			elif iu == 'psi' and ou == 'bar':
				dist = value * 0.0689476
			else:
				dist = value
		if um:
			if ou is None:
				return str(round(dist, 1)) + " hPa"
			elif ou == 'hpa':
				return str(round(dist, 1)) + " hPa"
			elif ou == 'bar':
				return str(round(dist, 1)) + " Bar"
			elif ou == 'psi':
				return str(round(dist, 1)) + " Psi"
			else:
				return str(round(dist, 1))
		else:
			return round(dist, 1)



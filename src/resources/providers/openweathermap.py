# -*- coding: utf-8 -*-

import sys
import gzip
import socket
import commons
import urllib2
import unicodedata
from StringIO import StringIO
from abstract import ContentProvider

if hasattr(sys.modules["__main__"], "xbmc"):
	xbmc = sys.modules["__main__"].xbmc
else:
	import xbmc


class OpenWeatherMap(ContentProvider):
	LOCATION = 'https://api.openweathermap.org/data/2.5/find?q=%s&type=like&sort=population&cnt=10&appid=%s'
	FORECAST = 'https://api.openweathermap.org/data/2.5/%s?id=%s&appid=%s&units=%s&lang=%s'
	ART_DATA = {"01d": "Clear/Day",
				"01n": "Clear/Night",
				"02d": "Cloudy/Partly/Day",
				"02n": "Cloudy/Partly/Night",
				"03d": "Cloudy/Mostly/Day",
				"03n": "Cloudy/Mostly Night",
				"04d": "Cloudy/Windy/Day",
				"04n": "Cloudy/Windy/Night",
				"09d": "Rain/Showers/Day",
				"09n": "Rain/Showers/Night",
				"10d": "Rain/Day",
				"10n": "Rain/Night",
				"11d": "Rain/Thunderstorm/Day",
				"11n": "Rain/Thunderstorm/Night",
				"13d": "Snow/Day",
				"13n": "Snow/Night",
				"50d": "Fog/Day",
				"50n": "Fog/Night"
				}


	def __init__(self):
		socket.setdefaulttimeout(10)


	def name(self):
		return "OpenWeatherMap"


	def code(self):
		return "openweathermap"


	def validate(self):
		_url = "https://api.openweathermap.org/data/2.5/weather?id=2172797&appid=%s" %self.apikey
		try:
			req = urllib2.urlopen(_url)
			req.close()
		except:
			raise StandardError("Invalid provider configuration")


	def _find(self, loc):
		url = self.LOCATION %(urllib2.quote(loc), self.apikey)
		commons.debug("Calling URL: %s" % url, self.code())
		try:
			req = urllib2.urlopen(url)
			response = req.read()
			req.close()
		except:
			response = ''
		return self._parse(response)


	def location(self, string):
		locs = []
		locids = []
		loc = unicodedata.normalize('NFKD', unicode(string, 'utf-8')).encode('ascii', 'ignore')
		commons.debug('Searching for location: %s' % loc, self.code())
		data = self._find(loc)
		commons.debug('Found location data: %s' % data, self.code())
		if data is not None and data.has_key("list"):
			for item in data["list"]:
				location = item["name"]
				if item.has_key("sys") and item["sys"].has_key("country"):
					location += "-" + item["sys"]["country"]
				locationid = item["id"]
				locs.append(location)
				locids.append(str(locationid))
		return locs, locids


	def geoip(self):
		data = self.ipinfo()
		location = ''
		locationid = ''
		if data is not None and data.has_key("city"):
			code = data["city"]
			if data.has_key("countryCode"):
				code += "," + data["countryCode"]
				commons.debug('Identifying GeoIP location: %s' % code, self.code())
				data = self._find(code)
				commons.debug('Found location data: %s' % data, self.code())
				if data is not None and data.has_key("list"):
					item = data["list"][0]
					location = item["name"]
					if item.has_key("sys") and item["sys"].has_key("country"):
						location += "-" + item["sys"]["country"]
					locationid = item["id"]
		return location, str(locationid)


	def forecast(self, loc, locid):
		commons.debug('Weather forecast for location: %s' % locid, self.code())
		# Current weather forecast
		data = self.call('weather', locid)
		if data is not None and data.has_key('weather') and data.has_key("cod") and data["cod"] == 200:
			self.skinproperty('Current.IsFetched', 'true')
			self.skinproperty('Current.Location', loc)
			self.skinproperty('Current.Latitude', data['coord']['lat'])
			self.skinproperty('Current.Longitude', data['coord']['lon'])
			self.skinproperty('Current.Condition', data['weather'][0]["description"].capitalize())
			self.skinproperty('Current.Temperature', self._2c(data['main']['temp']))
			self.skinproperty('Current.Wind', self._2kph(data['wind']['speed']))
			self.skinproperty('Current.WindDirection', data['wind']['deg'], '°') if data['wind'].has_key('deg') else self.skinproperty('Current.WindDirection')
			self.skinproperty('Current.Humidity', data['main']['humidity'])
			self.skinproperty('Current.Pressure', data['main']['pressure'], "hPa")
			self.skinproperty('Current.OutlookIcon', '%s.png' % self._fanart(data['weather'][0]["icon"]))
			self.skinproperty('Current.FanartCode', self._fanart(data['weather'][0]["icon"]))
			#self.skinproperty('Current.Visibility', self._2km(self._2km(data['visibility']), self.UM_DSTNC), self.UM_DSTNC)
			self.skinproperty('Current.LocalTime', self._2shtime(data['dt']))
			self.skinproperty('Current.LocalDate', self._2shdate(data['dt']))
			self.skinproperty('Current.FeelsLike', self.feelslike(self._2c(data['main']['temp']), self._2kph(data['wind']['speed']), data['main']['humidity']))
			self.skinproperty('Today.IsFetched', 'true')
			# Today forecast
			self.skinproperty('Today.Sunrise', self._2shtime(data['sys']['sunrise']))
			self.skinproperty('Today.Sunset', self._2shtime(data['sys']['sunset']))
			self.skinproperty('Today.HighTemperature', self._2c(data['main']['temp_max']), self.UM_TEMPR)
			self.skinproperty('Today.LowTemperature', self._2c(data['main']['temp_min']), self.UM_TEMPR)
			# Hourly weather forecast
			data = self.call('forecast', locid)
			if data['list'] is not None and len(data['list']) >= 1:
				count = 0
				self.skinproperty('Hourly.IsFetched', 'true')
				for item in data['list']:
					self.skinproperty('Hourly.%i.Time' % count, self._2shtime(item['dt']))
					self.skinproperty('Hourly.%i.ShortDate' % count, self._2shdate(item['dt']))
					self.skinproperty('Hourly.%i.Condition' % count, item['weather'][0]["description"].capitalize())
					self.skinproperty('Hourly.%i.Temperature' % count, self._2temp(item['main']['temp']), self.UM_TEMPR)
					self.skinproperty('Hourly.%i.Outlook' % count, item['weather'][0]["description"].capitalize())
					self.skinproperty('Hourly.%i.OutlookIcon' % count, '%s.png' % self._fanart(item['weather'][0]["icon"]))
					self.skinproperty('Hourly.%i.FanartCode' % count, self._fanart(item['weather'][0]["icon"]))
					self.skinproperty('Hourly.%i.Wind' % count, self._2wind(item['wind']['speed']))
					self.skinproperty('Hourly.%i.WindDirection' % count, item['wind']['deg'], '°') if item['wind'].has_key('deg') else self.skinproperty('Hourly%i.WindDirection' % count)
					self.skinproperty('Hourly.%i.Humidity' % count, item['main']['humidity'])
					self.skinproperty('Hourly.%i.Pressure' % count, item['main']['pressure'], "hPa")
					self.skinproperty('Hourly.%i.HighTemp' % count, self._2temp(item['main']['temp_max']))
					self.skinproperty('Hourly.%i.LowTemp' % count, self._2temp(item['main']['temp_min']))
					count += 1
			# Daily weather forecast
			self.skinproperty('Daily.IsFetched')
			self.skinproperty('Alerts.IsFetched')


	def call(self, feature, id):
		retry = 0
		data = None
		url = self.FORECAST % (feature, id, self.apikey, "metric", self.lang)
		while data is None and retry < 6 and not xbmc.abortRequested:
			try:
				commons.debug("Calling URL: %s" %url, self.code())
				req = urllib2.Request(url)
				req.add_header('Accept-encoding', 'gzip')
				response = urllib2.urlopen(req)
				if response.info().get('Content-Encoding') == 'gzip':
					buf = StringIO(response.read())
					compr = gzip.GzipFile(fileobj=buf)
					data = compr.read()
				else:
					data = response.read()
				response.close()
			except:
				data = None
				retry += 1
		return self._parse(data)


	def _fanart(self, code):
		"""Detect and return fanart code"""
		return self.ART_BASE[self.ART_DATA[code]]

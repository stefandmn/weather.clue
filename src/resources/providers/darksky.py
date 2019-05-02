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


class DarkSky(ContentProvider):
	LOCATION = 'https://darksky.net/geo?q=%s'
	FORECAST = 'https://api.darksky.net/forecast/%s/%s?exclude=minutely&lang=%s&units=%s'
	ART_DATA = {"clear-day": "Clear/Day",
				"clear-night": "Clear/Night",
				"rain": "Rain/Neutral",
				"snow": "Snow/Neutral",
				"sleet": "Rain/Showers/Neutral",
				"wind":	"Others/Windy",
				"fog": "Fog/Neutral",
				"cloudy": "Cloudy/Neutral",
				"partly-cloudy-day": "Cloudy/Partly/Day",
				"partly-cloudy-night": "Cloudy/Partly/Night",
				"hail": "Rain/Mix/Neutral",
				"thunderstorm": "Rain/Night",
				"tornado": "Others/Tornado"
				}


	def __init__(self):
		socket.setdefaulttimeout(10)


	def name(self):
		return "Dark Sky"


	def code(self):
		return "darksky"


	def validate(self):
		_url = "https://api.darksky.net/forecast/%s/37.8267,-122.4233?exclude=minutely,hourly,daily,alerts,flags" %self.apikey
		try:
			req = urllib2.urlopen(_url)
			req.close()
		except:
			raise StandardError("Invalid provider configuration")


	def _find(self, loc):
		url = self.LOCATION %(urllib2.quote(loc))
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
		if data is not None and data.has_key("latitude"):
			self.coordinates(data["latitude"], data["longitude"])
			location = string.replace(",", "-")
			locationid = str(self.latitude) + "," + str(self.longitude)
			locs.append(location)
			locids.append(str(locationid))
		return locs, locids


	def geoip(self):
		data = self.ipinfo()
		location = ''
		locationid = ''
		if data is not None and data.has_key("city"):
			code = data["city"]
			if data.has_key("country"):
				code += "," + data["country"]
				commons.debug('Identifying GeoIP location: %s' % code, self.code())
				data = self._find(code)
				commons.debug('Found location data: %s' % data, self.code())
				if data is not None and data.has_key("latitude"):
					self.coordinates(data["latitude"], data["longitude"])
					location = code.replace(",", "-")
					locationid = str(self.latitude) + "," + str(self.longitude)
		return location, str(locationid)


	def forecast(self, loc, locid):
		commons.debug('Weather forecast for location: %s' % locid, self.code())
		data = self.call(locid)
		# Current weather forecast
		if data is not None and data.has_key('currently'):
			item = data['currently']
			self.skinproperty('Current.IsFetched', 'true')
			self.skinproperty('Current.Latitude', data['latitude'])
			self.skinproperty('Current.Longitude', data['longitude'])
			self.skinproperty('Current.Location', loc)
			self.skinproperty('Current.Condition', item["summary"].capitalize())
			self.skinproperty('Current.Temperature', self._2c(item['temperature']))
			self.skinproperty('Current.Wind', self._2kph(item['windSpeed']))
			self.skinproperty('Current.WindDirection', item['windBearing'], '°') if item.has_key('windBearing') else self.skinproperty('Current.WindDirection')
			self.skinproperty('Current.Humidity', 100*item['humidity'])
			self.skinproperty('Current.Pressure', item['pressure'], "hPa")
			self.skinproperty('Current.OutlookIcon', '%s.png' % self._fanart(item["icon"]))
			self.skinproperty('Current.FanartCode', self._fanart(item["icon"]))
			self.skinproperty('Current.LocalTime', self._2shtime(item['time']))
			self.skinproperty('Current.LocalDate', self._2shdate(item['time']))
			self.skinproperty('Current.FeelsLike', self._2c(item['apparentTemperature']), self.UM_TEMPR)
			self.skinproperty('Current.Visibility', self._2km(self._2km(item['visibility'], 'km'), self.UM_DSTNC), self.UM_DSTNC)
			self.skinproperty('Current.DewPoint', item['dewPoint'])
			self.skinproperty('Current.UVIndex', item['uvIndex'])
		# Today forecast
		if data is not None and data.has_key('daily') and data['daily'].has_key('data') and len(data['daily']['data']) > 0:
			item = data['daily']['data'][0]
			self.skinproperty('Today.IsFetched', 'true')
			self.skinproperty('Today.Sunrise', self._2shtime(item['sunriseTime']))
			self.skinproperty('Today.Sunset', self._2shtime(item['sunsetTime']))
			self.skinproperty('Today.HighTemperature', self._2c(item['temperatureHigh']), self.UM_TEMPR)
			self.skinproperty('Today.LowTemperature', self._2c(item['temperatureLow']), self.UM_TEMPR)
		# Daily weather forecast
		if data is not None and data.has_key('daily') and data['daily'].has_key('data') and len(data['daily']['data']) > 1:
			count = 0
			index = 0
			self.skinproperty('Daily.IsFetched', 'true')
			for item in data['daily']['data']:
				if index >= 1:
					self.skinproperty('Day.%i.Title' % count, self._2shday(item['time']))
					self.skinproperty('Day.%i.Condition' % count, item["summary"].capitalize())
					self.skinproperty('Day.%i.Outlook' % count, item["summary"].capitalize())
					self.skinproperty('Day.%i.OutlookIcon' % count, '%s.png' % self._fanart(item["icon"]))
					self.skinproperty('Day.%i.FanartCode' % count, self._fanart(item["icon"]))
					self.skinproperty('Day.%i.Wind' % count, self._2wind(item['windSpeed']))
					self.skinproperty('Day.%i.WindDirection' % count, item['windBearing'], '°') if item.has_key('windBearing') else self.skinproperty('Day.%i.WindDirection' % count)
					self.skinproperty('Day.%i.Humidity' % count, 100*item['humidity'])
					self.skinproperty('Day.%i.Pressure' % count, item['pressure'], "hPa")
					self.skinproperty('Day.%i.DewPoint' % count, item['dewPoint'])
					self.skinproperty('Day.%i.UVIndex' % count, item['uvIndex'])
					self.skinproperty('Day.%i.HighTemp' % count, self._2temp(int(item['temperatureHigh'])), self.UM_TEMPR)
					self.skinproperty('Day.%i.LowTemp' % count, self._2temp(int(item['temperatureLow'])), self.UM_TEMPR)
					count += 1
				index += 1
		# Hourly weather forecast
		if data is not None and data.has_key('hourly') and data['hourly'].has_key('data') and len(data['hourly']['data']) > 0:
			count = 0
			self.skinproperty('Hourly.IsFetched', 'true')
			for item in data['hourly']['data']:
				self.skinproperty('Hourly.%i.Time' % count, self._2shtime(item['time']))
				self.skinproperty('Hourly.%i.ShortDate' % count, self._2shdate(item['time']))
				self.skinproperty('Hourly.%i.Condition' % count, item["summary"].capitalize())
				self.skinproperty('Hourly.%i.Temperature' % count, self._2temp(item['temperature']), self.UM_TEMPR)
				self.skinproperty('Hourly.%i.Outlook' % count, item["summary"].capitalize())
				self.skinproperty('Hourly.%i.OutlookIcon' % count, '%s.png' % self._fanart(item["icon"]))
				self.skinproperty('Hourly.%i.FanartCode' % count, self._fanart(item["icon"]))
				self.skinproperty('Hourly.%i.Wind' % count, self._2wind(item['windSpeed']))
				self.skinproperty('Hourly.%i.WindDirection' % count, item['windBearing'], '°') if item.has_key('windBearing') else self.skinproperty('Hourly%i.WindDirection' % count)
				self.skinproperty('Hourly.%i.Humidity' % count, 100*item['humidity'])
				self.skinproperty('Hourly.%i.Pressure' % count, item['pressure'], "hPa")
				self.skinproperty('Hourly.%i.DewPoint' % count, item['dewPoint'])
				self.skinproperty('Hourly.%i.UVIndex' % count, item['uvIndex'])
				count += 1
		# Alerts weather forecast
		if data is not None and data.has_key('alerts') and len(data['alerts']) > 0:
			count = 0
			text = ''
			self.skinproperty('Alerts.IsFetched', 'true')
			for item in data['alerts']:
				title = item['title'].encode('utf-8', 'ignore').replace('\n', ' ')
				description = item['description'].encode('utf-8', 'ignore').replace('\n', ' ')
				expire = self._2shdatetime(item['expires'])
				self.skinproperty('Alerts.%i.Title' % count, title)
				self.skinproperty('Alerts.%i.Description' % count, description)
				self.skinproperty('Alerts.%i.Expires' % count, expire)
				text += " • " if text != "" else ""
				text += "[B]" + title + "[/B] - " + description + " (" + expire + ")"
				count += 1
			self.skinproperty('Alerts.Text', text)


	def call(self, id):
		retry = 0
		data = None
		url = self.FORECAST % (self.apikey, id, self.lang, "si")
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
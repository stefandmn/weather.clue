# -*- coding: utf-8 -*-

import sys
import time
import socket
import commons
import unicodedata
from datetime import datetime
from urllib import request as urllib2
from .abstract import ContentProvider

if hasattr(sys.modules["__main__"], "xbmc"):
	xbmc = sys.modules["__main__"].xbmc
else:
	import xbmc


class Yahoo(ContentProvider):
	LOCATION = 'https://www.yahoo.com/news/_tdnews/api/resource/WeatherSearch;text=%s'
	FORECAST = 'https://www.yahoo.com/news/_tdnews/api/resource/WeatherService;woeids=%s'


	def __init__(self):
		socket.setdefaulttimeout(10)


	def name(self):
		return "Yahoo"


	def code(self):
		return "yahoo"


	def validate(self):
		pass

	def _2shdate(self, value):
		ts = time.strptime(value, "%Y-%m-%dT%H:%M:%S.%zZ")
		dt = datetime.fromtimestamp(time.mktime(ts))
		return super(ContentProvider, self)._2shdate(dt.timestamp())


	def _2lndate(self, value):
		ts = time.strptime(value, "%Y-%m-%dT%H:%M:%S.%zZ")
		dt = datetime.fromtimestamp(time.mktime(ts))
		return super(ContentProvider, self)._2lndate(dt.timestamp())


	def _find(self, loc):
		url = self.LOCATION % (urllib2.quote(loc))
		return super(ContentProvider, self)._find(url)


	def _call(self, id):
		url = self.FORECAST % id
		return super(ContentProvider, self)._call(url)


	def geoip(self):
		data = self.ipinfo()
		location = ''
		locationid = ''
		if data is not None and data.has_key("city"):
			code = data["city"]
			if data.has_key("regionName"):
				code += "," + data["regionName"]
				if data.has_key("country"):
					code += "," + data["country"]
				commons.debug('Identifying GeoIP location: %s' % code, self.code())
				data = self._find(code)
				commons.debug('Found location data: %s' % data, self.code())
				if data is not None and data.has_key("woeid"):
					self.coordinates(data["lat"], data["lon"])
					locationid = data["woeid"]
					if data.has_key("qualifiedName"):
						location = data["qualifiedName"]
					else:
						location = code
		return location, str(locationid)


	def location(self, string):
		locs = []
		locids = []
		loc = unicodedata.normalize('NFKD', str(string)).encode('ascii', 'ignore')
		commons.debug('Searching for location: %s' % loc, self.code())
		data = self._find(loc)
		commons.debug('Found location data: %s' % data, self.code())
		if data is not None and isinstance(data, list):
			for item in data:
				locationid = item["woeid"]
				if item.has_key("qualifiedName"):
					location = item["qualifiedName"]
				else:
					location = item["city"] + "," + item["country"]

				locs.append(location)
				locids.append(str(locationid))
		return locs, locids


	def forecast(self, loc, locid):
		commons.debug('Weather forecast for location: %s' % locid, self.code())
		# Current weather forecast
		data = self._call(locid)
		if data is not None and data.has_key('weather') and data.has_key("cod") and data["cod"] == 200:
			data = data['weathers'][0]
			# Current - standard
			self.skinproperty('Current.IsFetched', 'true')
			self.skinproperty('Current.Location', data['location']['displayName'])
			self.skinproperty('Current.Condition', data['observation']['conditionDescription'])
			self.skinproperty('Current.Temperature', self._2c(data['observation']['temperature']['now']))
			self.skinproperty('Current.UVIndex', str(data['observation']['uvIndex']))
			self.skinproperty('Current.OutlookIcon', '%s.png' % str(data['observation']['conditionCode']))  # Kodi translates it to Current.ConditionIcon
			self.skinproperty('Current.FanartCode', str(data['observation']['conditionCode']))
			self.skinproperty('Current.Wind', self._2kph(data['observation']['windSpeed']))
			self.skinproperty('Current.WindDirection', data['observation']['windDirection'], '°') if data['observation'].has_key('windBearing') else self.skinproperty('Current.WindDirection')
			self.skinproperty('Current.Humidity', str(data['observation']['humidity']))
			self.skinproperty('Current.DewPoint', self._dewpoint(int(self._2c(data['observation']['temperature']['now'])), data['observation']['humidity']))
			self.skinproperty('Current.FeelsLike', self._2c(data['observation']['temperature']['feelsLike']))
			self.skinproperty('Current.Visibility', self._2km(self._2km(data['observation']['visibility'], 'km'), self.UM_DSTNC), self.UM_DSTNC)
			self.skinproperty('Current.Pressure', data['observation']['barometricPressure'], "hPa")
			# Forecast - extended
			self.skinproperty('Forecast.City', data['location']['displayName'])
			self.skinproperty('Forecast.Country', data['location']['countryName'])
			self.skinproperty('Forecast.Latitude', data['location']['latitude'])
			self.skinproperty('Forecast.Longitude', data['location']['longitude'])
			self.skinproperty('Forecast.Updated', self._2shdatetime(data['observation']['observationTime']['timestamp']))
			# Today - extended
			self.skinproperty('Today.IsFetched', 'true')
			self.skinproperty('Today.Sunrise', self._2shtime(data['sunAndMoon']['sunrise']))
			self.skinproperty('Today.Sunset', self._2shtime(data['sunAndMoon']['sunset']))
			self.skinproperty('Today.HighTemperature', self._2c(data['observation']['temperature']['high']), self.UM_TEMPR)
			self.skinproperty('Today.LowTemperature', self._2c(data['observation']['temperature']['low']), self.UM_TEMPR)
			# Hourly - extended
			if data['forecasts'] is not None and data['forecasts']['hourly'] is not None and len(data['forecasts']['hourly']) >= 1:
				self.skinproperty('Hourly.IsFetched', 'true')
				for count, item in enumerate(data['forecasts']['hourly']):
					self.skinproperty('Hourly.%i.Time' %count, self._2shtime(item['observationTime']['timestamp']))
					self.skinproperty('Hourly.%i.LongDate' %count, self._2lndate(item['observationTime']['timestamp']))
					self.skinproperty('Hourly.%i.ShortDate' %count, self._2shdate(item['observationTime']['timestamp']))
					self.skinproperty('Hourly.%i.Temperature' %count, self._2c(item['temperature']['now']), self.UM_TEMPR)
					self.skinproperty('Hourly.%i.FeelsLike' %count, self._2c(item['temperature']['feelsLike']), self.UM_TEMPR)
					self.skinproperty('Hourly.%i.Outlook' %count, item['conditionDescription'])
					self.skinproperty('Hourly.%i.OutlookIcon' %count, '%s.png' % str(item['conditionCode']))
					self.skinproperty('Hourly.%i.FanartCode' %count, item['conditionCode'])
					self.skinproperty('Hourly.%i.Humidity' %count, item['humidity'])
					self.skinproperty('Hourly.%i.Precipitation' %count, item['precipitationProbability'])
					self.skinproperty('Hourly.%i.WindDirection' %count, item['windDirection'], '°')
					self.skinproperty('Hourly.%i.WindSpeed' %count, self._2wind(item['windSpeed']))
					self.skinproperty('Hourly.%i.WindDegree' %count, str(item['windDirection']), '°')
					self.skinproperty('Hourly.%i.DewPoint' %count, self._dewpoint(self._2c(item['temperature']['now']), item['humidity']), self.UM_TEMPR)
			# Daily - standard
			if data['forecasts'] is not None and data['forecasts']['daily'] is not None and len(data['forecasts']['daily']) >= 1:
				for count, item in enumerate(data['forecasts']['daily']):
					# Standard
					self.skinproperty('Day%i.Title' %count, self._2lnday(item['observationTime']['weekday']))
					self.skinproperty('Day%i.HighTemp' %count, self._2c(item['temperature']['high']), self.UM_TEMPR)
					self.skinproperty('Day%i.LowTemp' %count, self._2c(item['temperature']['low']), self.UM_TEMPR)
					self.skinproperty('Day%i.Outlook' %count, item['conditionDescription'])
					self.skinproperty('Day%i.OutlookIcon' %count, '%s.png' % item['conditionCode'])
					self.skinproperty('Day%i.FanartCode' %count, item['conditionCode'])
					# Extended
					self.skinproperty('Daily.%i.ShortDay' %count, self._2shday(item['observationTime']['weekday']))
					self.skinproperty('Daily.%i.LongDay' %count, self._2lnday(item['observationTime']['weekday']))
					self.skinproperty('Daily.%i.ShortDate' %count, self._2shdate(item['observationTime']['timestamp']))
					self.skinproperty('Daily.%i.LongDate' %count, self._2lndate(item['observationTime']['timestamp']))
					self.skinproperty('Daily.%i.HighTemperature' %count, self._2c(item['temperature']['high']) + self.UM_TEMPR)
					self.skinproperty('Daily.%i.LowTemperature' %count, self._2c(item['temperature']['low']) + self.UM_TEMPR)
					self.skinproperty('Daily.%i.Outlook' %count, str(item['conditionDescription']))
					self.skinproperty('Daily.%i.OutlookIcon' %count, '%s.png' % str(item['conditionCode']))
					self.skinproperty('Daily.%i.FanartCode' %count, str(item['conditionCode']))
					self.skinproperty('Daily.%i.Humidity' %count, str(item['humidity']) + '%')
					self.skinproperty('Daily.%i.Precipitation' %count, str(item['precipitationProbability']) + '%')
					self.skinproperty('Daily.%i.DewPoint' %count, self._dewpoint(self._2c(item['temperature']['low']), item['humidity']))


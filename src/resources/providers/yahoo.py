# -*- coding: utf-8 -*-

import sys
import time
import socket
import common
from datetime import datetime
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


	def _timestamp(self, value):
		ts = time.strptime(value, "%Y-%m-%dT%H:%M:%S.%fZ")
		dt = datetime.fromtimestamp(time.mktime(ts))
		if sys.version_info[0] == 3:
			return dt.timestamp()
		else:
			return time.mktime(dt.timetuple()) + dt.microsecond / 1e6


	def _2shtime(self, value):
		if isinstance(value, int):
			m, s = divmod(value, 60)
			h, m = divmod(m, 60)
			d = datetime.now()
			value = "%d-%d-%dT%02d:%02d:00.088Z" % (d.year, d.month, d.day, h, m)
		value = self._timestamp(value)
		return ContentProvider._2shtime(self, value)


	def _2shdate(self, value):
		if not isinstance(value, int):
			value = self._timestamp(value)
		return ContentProvider._2shdate(self, value)


	def _2lndate(self, value):
		if not isinstance(value, int):
			value = self._timestamp(value)
		return ContentProvider._2lndate(self, value)


	def _2shdatetime(self, value):
		if not isinstance(value, int):
			value = self._timestamp(value)
		return ContentProvider._2shdatetime(self, value)


	def geoip(self):
		loc = ''
		locid = ''
		data = self.ipinfo()
		if data is not None and data.has_key("city"):
			geoloc = data["city"]
			if data.has_key("regionName"):
				geoloc += "," + data["regionName"]
			if data.has_key("country"):
				geoloc += "," + data["country"]
			common.debug('Identifying GeoIP location: %s' % geoloc, self.code())
			url = self.LOCATION % ("\"" + geoloc + "\"")
			data = self._call(url)
			common.debug('Found location data: %s' % data, self.code())
			if data is not None and isinstance(data, list) and data[0].has_key("woeid"):
				data = data[0]
				self.coordinates(data["lat"], data["lon"])
				locid = data["woeid"]
				if data.has_key("qualifiedName"):
					loc = data["qualifiedName"]
				else:
					loc = geoloc
		return loc, str(locid)


	def location(self, loc):
		locs = []
		locids = []
		common.debug('Searching for location: %s' % loc, self.code())
		url = self.LOCATION % ("\"" + loc + "\"")
		data = self._call(url)
		common.debug('Found location data: %s' % data, self.code())
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
		common.debug('Weather forecast for location: %s' % locid, self.code())
		url = self.FORECAST % locid
		data = self._call(url)
		# Current weather forecast
		if data is not None and data.has_key('weathers'):
			data = data['weathers'][0]
			# Current - standard
			self.skinproperty('Current.IsFetched', 'true')
			self.skinproperty('Current.Location', data['location']['displayName'])
			self.skinproperty('Current.Condition', data['observation']['conditionDescription'])
			self.skinproperty('Current.Temperature', self._2c(data['observation']['temperature']['now'],um='f'))
			self.skinproperty('Current.UVIndex', str(data['observation']['uvIndex']))
			self.skinproperty('Current.OutlookIcon', '%s.png' % str(data['observation']['conditionCode']))  # Kodi translates it to Current.ConditionIcon
			self.skinproperty('Current.FanartCode', str(data['observation']['conditionCode']))
			self.skinproperty('Current.Wind', self._2kph(data['observation']['windSpeed'],um='mph'))
			self.skinproperty('Current.WindDirection', data['observation']['windDirection'], '°') if data['observation'].has_key('windBearing') else self.skinproperty('Current.WindDirection')
			self.skinproperty('Current.Humidity', str(data['observation']['humidity']))
			self.skinproperty('Current.DewPoint', self._dewpoint(self._2c(data['observation']['temperature']['now'],um='f'), int(data['observation']['humidity'])))
			self.skinproperty('Current.FeelsLike', self._2c(data['observation']['temperature']['feelsLike'],um='f'))
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
			self.skinproperty('Today.HighTemperature', self._2c(data['observation']['temperature']['high'],um='f'), self.UM_TEMPR)
			self.skinproperty('Today.LowTemperature', self._2c(data['observation']['temperature']['low'],um='f'), self.UM_TEMPR)
			# Hourly - extended
			if data['forecasts'] is not None and data['forecasts']['hourly'] is not None and len(data['forecasts']['hourly']) >= 1:
				self.skinproperty('Hourly.IsFetched', 'true')
				for count, item in enumerate(data['forecasts']['hourly']):
					self.skinproperty('Hourly.%i.Time' %count, self._2shtime(item['observationTime']['timestamp']))
					self.skinproperty('Hourly.%i.LongDate' %count, self._2lndate(item['observationTime']['timestamp']))
					self.skinproperty('Hourly.%i.ShortDate' %count, self._2shdate(item['observationTime']['timestamp']))
					self.skinproperty('Hourly.%i.Temperature' %count, self._2c(item['temperature']['now'],um='f'), self.UM_TEMPR)
					self.skinproperty('Hourly.%i.FeelsLike' %count, self._2c(item['temperature']['feelsLike'],um='f'), self.UM_TEMPR)
					self.skinproperty('Hourly.%i.Outlook' %count, item['conditionDescription'])
					self.skinproperty('Hourly.%i.OutlookIcon' %count, '%s.png' % str(item['conditionCode']))
					self.skinproperty('Hourly.%i.FanartCode' %count, item['conditionCode'])
					self.skinproperty('Hourly.%i.Humidity' %count, item['humidity'])
					self.skinproperty('Hourly.%i.Precipitation' %count, item['precipitationProbability'])
					self.skinproperty('Hourly.%i.WindDirection' %count, item['windDirection'], '°')
					self.skinproperty('Hourly.%i.WindSpeed' %count, self._2wind(self._2kph(item['windSpeed'],um='mph')))
					self.skinproperty('Hourly.%i.WindDegree' %count, str(item['windDirection']), '°')
					self.skinproperty('Hourly.%i.DewPoint' %count, self._dewpoint(self._2c(item['temperature']['now']), item['humidity']), self.UM_TEMPR)
			# Daily - standard
			if data['forecasts'] is not None and data['forecasts']['daily'] is not None and len(data['forecasts']['daily']) >= 1:
				self.skinproperty('Daily.IsFetched', 'true')
				for count, item in enumerate(data['forecasts']['daily']):
					# Standard
					self.skinproperty('Day%i.Title' %count, self._2lnday(item['observationTime']['weekday']))
					self.skinproperty('Day%i.HighTemp' %count, self._2c(item['temperature']['high'],um='f'), self.UM_TEMPR)
					self.skinproperty('Day%i.LowTemp' %count, self._2c(item['temperature']['low'],um='f'), self.UM_TEMPR)
					self.skinproperty('Day%i.Outlook' %count, item['conditionDescription'])
					self.skinproperty('Day%i.OutlookIcon' %count, '%s.png' % item['conditionCode'])
					self.skinproperty('Day%i.FanartCode' %count, item['conditionCode'])
					# Extended
					self.skinproperty('Daily.%i.ShortDay' %count, self._2shday(item['observationTime']['weekday']))
					self.skinproperty('Daily.%i.LongDay' %count, self._2lnday(item['observationTime']['weekday']))
					self.skinproperty('Daily.%i.ShortDate' %count, self._2shdate(item['observationTime']['timestamp']))
					self.skinproperty('Daily.%i.LongDate' %count, self._2lndate(item['observationTime']['timestamp']))
					self.skinproperty('Daily.%i.HighTemperature' %count, self._2c(item['temperature']['high'],um='f'), self.UM_TEMPR)
					self.skinproperty('Daily.%i.LowTemperature' %count, self._2c(item['temperature']['low'],um='f'), self.UM_TEMPR)
					self.skinproperty('Daily.%i.Outlook' %count, str(item['conditionDescription']))
					self.skinproperty('Daily.%i.OutlookIcon' %count, '%s.png' % str(item['conditionCode']))
					self.skinproperty('Daily.%i.FanartCode' %count, str(item['conditionCode']))
					self.skinproperty('Daily.%i.Humidity' %count, str(item['humidity']), '%')
					self.skinproperty('Daily.%i.Precipitation' %count, str(item['precipitationProbability']), '%')
					self.skinproperty('Daily.%i.DewPoint' %count, self._dewpoint(self._2c(item['temperature']['low'],um='f'), item['humidity']))


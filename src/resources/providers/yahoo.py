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
	ART_DATA = {
		0: "Others/Tornado",  # tornado
		1: "Rain/Thunderstorm/Neutral",  # tropical storm
		2: "Others/Hurricane",  # hurricane
		3: "Rain/Thunderstorm/Neutral",  # severe thunderstorms
		4: "Rain/Thunderstorm/Neutral",  # thunderstorms
		5: "Rain/Mix/Neutral",  # mixed rain and snow
		6: "Rain/Mix/Neutral",  # mixed rain and sleet
		7: "Rain/Mix/Neutral",  # mixed snow and sleet
		8: "Snow/Windy/Neutral",  # freezing drizzle
		9: "Rain/Showers/Neutral",  # drizzle
		10: "Rain/Mix/Neutral",  # freezing rain
		11: "Rain/Showers/Neutral",  # showers
		12: "Rain/Showers/Neutral",  # showers
		13: "Snow/Neutral",  # snow flurries
		14: "Snow/Windy/Neutral",  # light snow showers
		15: "Snow/Thunderstorm/Neutral",  # blowing snow
		16: "Snow/Neutral",  # snow
		17: "Others/Raindrops",  # hail
		18: "Others/Raindrops",  # sleet
		19: "Fog/Neutral",  # dust
		20: "Fog/Neutral",  # foggy
		21: "Fog/Neutral",  # haze
		22: "Fog/Neutral",  # smoky
		23: "Fog/Neutral",  # blustery
		24: "Cloudy/Windy/Neutral",  # windy
		25: "Snow/Neutral",  # cold
		26: "Cloudy/Neutral",  # cloudy
		27: "Cloudy/Mostly Night",  # mostly cloudy (night)
		28: "Cloudy/Mostly/Day",  # mostly cloudy (day)
		29: "Cloudy/Partly/Night",  # partly cloudy (night)
		30: "Cloudy/Partly/Day",  # partly cloudy (day)
		31: "Clear/Night",  # clear (night)
		32: "Sunny/Day",  # sunny
		33: "Clear/Night",  # fair (night)
		34: "Clear/Day",  # fair (day)
		35: "Rain/Mix/Neutral",  # mixed rain and hail
		36: "Others/Heat",  # hot
		37: "Rain/Thunderstorm/Neutral",  # isolated thunderstorms
		38: "Rain/Thunderstorm/Neutral",  # scattered thunderstorms
		39: "Rain/Thunderstorm/Neutral",  # scattered thunderstorms
		40: "Rain/Showers/Neutral",  # scattered showers
		41: "Snow/Thunderstorm/Neutral",  # heavy snow
		42: "Snow/Windy/Neutral",  # scattered snow showers
		43: "Snow/Thunderstorm/Neutral",  # heavy snow
		44: "Cloudy/Partly/Neutral",  # partly cloudy
		45: "Rain/Showers/Neutral",  # thundershowers
		46: "Snow/Neutral",  # snow showers
		47: "Rain/Showers/Neutral"   # isolated thundershowers"
	}


	def __init__(self):
		socket.setdefaulttimeout(10)


	def _fanart(self, code):
		"""Detect and return fanart code"""
		return self.ART_BASE[self.ART_DATA[int(code)]]


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
		if data is not None and "city" in data:
			geoloc = data["city"]
			if "regionName" in data:
				geoloc += "," + data["regionName"]
			if "country" in data:
				geoloc += "," + data["country"]
			common.debug('Identifying GeoIP location: %s' % geoloc, self.code())
			url = self.LOCATION % ("\"" + geoloc + "\"")
			data = self._call(url)
			common.debug('Found location data: %s' % data, self.code())
			if data is not None and isinstance(data, list) and "woeid" in data[0]:
				data = data[0]
				self.coordinates(data["lat"], data["lon"])
				locid = data["woeid"]
				if "qualifiedName" in data:
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
				if "qualifiedName" in item:
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
		if data is not None and "weathers" in data:
			data = data['weathers'][0]
			# Current - standard
			self.skinproperty('Current.IsFetched', 'true')
			self.skinproperty('Current.Location', data['location']['displayName'])
			self.skinproperty('Current.Condition', common.ustr(data['observation']['conditionDescription']).capitalize())
			self.skinproperty('Current.Temperature', self._2temperature(data['observation']['temperature']['now'], iu='f', ou='c'))
			self.skinproperty('Current.UVIndex', str(data['observation']['uvIndex']))
			self.skinproperty('Current.OutlookIcon', '%s.png' % self._fanart(data['observation']['conditionCode']))
			self.skinproperty('Current.FanartCode', self._fanart(data['observation']['conditionCode']))
			self.skinproperty('Current.Wind', self._2speed(data['observation']['windSpeed'], iu='mph'))
			self.skinproperty('Current.WindDirection', data['observation']['windDirection'], '°') if "windBearing" in data['observation'] else self.skinproperty('Current.WindDirection')
			self.skinproperty('Current.Humidity', str(data['observation']['humidity']))
			self.skinproperty('Current.DewPoint', self._dewpoint(self._2temperature(data['observation']['temperature']['now'], iu='f', ou='c'), int(data['observation']['humidity'])))
			self.skinproperty('Current.FeelsLike', self._2temperature(data['observation']['temperature']['feelsLike'], iu='f', ou='c'))
			self.skinproperty('Current.Visibility', self._2distance(data['observation']['visibility'], iu='mi', um=True))
			self.skinproperty('Current.Pressure', self._2pressure(data['observation']['barometricPressure'],iu='psi',um=True))
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
			self.skinproperty('Today.HighTemperature', self._2temperature(data['observation']['temperature']['high'], iu='f', um=True))
			self.skinproperty('Today.LowTemperature', self._2temperature(data['observation']['temperature']['low'], iu='f', um=True))
			# Hourly - extended
			if data['forecasts'] is not None and data['forecasts']['hourly'] is not None and len(data['forecasts']['hourly']) >= 1:
				self.skinproperty('Hourly.IsFetched', 'true')
				for count, item in enumerate(data['forecasts']['hourly']):
					self.skinproperty('Hourly.%i.Time' %count, self._2shtime(item['observationTime']['timestamp']))
					self.skinproperty('Hourly.%i.LongDate' %count, self._2lndate(item['observationTime']['timestamp']))
					self.skinproperty('Hourly.%i.ShortDate' %count, self._2shdate(item['observationTime']['timestamp']))
					self.skinproperty('Hourly.%i.Temperature' % count, self._2temperature(item['temperature']['now'], iu='f', um=True))
					self.skinproperty('Hourly.%i.FeelsLike' % count, self._2temperature(item['temperature']['feelsLike'], iu='f', um=True))
					self.skinproperty('Hourly.%i.Outlook' % count, common.ustr(item['conditionDescription']).capitalize())
					self.skinproperty('Hourly.%i.OutlookIcon' %count, '%s.png' % self._fanart(str(item['conditionCode'])))
					self.skinproperty('Hourly.%i.FanartCode' %count, self._fanart(item['conditionCode']))
					self.skinproperty('Hourly.%i.Humidity' %count, item['humidity'])
					self.skinproperty('Hourly.%i.Precipitation' %count, item['precipitationProbability'])
					self.skinproperty('Hourly.%i.WindDirection' %count, item['windDirection'], '°')
					self.skinproperty('Hourly.%i.WindSpeed' % count, self._2speed(self._2speed(item['windSpeed'], iu='mph')))
					self.skinproperty('Hourly.%i.WindDegree' %count, str(item['windDirection']), '°')
					self.skinproperty('Hourly.%i.DewPoint' % count, self._dewpoint(self._2temperature(item['temperature']['now'], iu='f', ou='c'), item['humidity']), self.UM_TEMPERATURE)
			# Daily - standard
			if data['forecasts'] is not None and data['forecasts']['daily'] is not None and len(data['forecasts']['daily']) >= 1:
				self.skinproperty('Daily.IsFetched', 'true')
				for count, item in enumerate(data['forecasts']['daily']):
					# Standard
					self.skinproperty('Day%i.Title' %count, self._2lnday(item['observationTime']['weekday']))
					self.skinproperty('Day%i.HighTemp' % count, self._2temperature(item['temperature']['high'], iu='f', um=True))
					self.skinproperty('Day%i.LowTemp' % count, self._2temperature(item['temperature']['low'], iu='f', um=True))
					self.skinproperty('Day%i.Outlook' % count, common.ustr(item['conditionDescription']).capitalize())
					self.skinproperty('Day%i.OutlookIcon' %count, '%s.png' % self._fanart(item['conditionCode']))
					self.skinproperty('Day%i.FanartCode' %count, self._fanart(item['conditionCode']))
					# Extended
					self.skinproperty('Daily.%i.ShortDay' %count, self._2shday(item['observationTime']['weekday']))
					self.skinproperty('Daily.%i.LongDay' %count, self._2lnday(item['observationTime']['weekday']))
					self.skinproperty('Daily.%i.ShortDate' %count, self._2shdate(item['observationTime']['timestamp']))
					self.skinproperty('Daily.%i.LongDate' %count, self._2lndate(item['observationTime']['timestamp']))
					self.skinproperty('Daily.%i.HighTemperature' % count, self._2temperature(item['temperature']['high'], iu='f', um=True))
					self.skinproperty('Daily.%i.LowTemperature' % count, self._2temperature(item['temperature']['low'], iu='f', um=True))
					self.skinproperty('Daily.%i.Outlook' % count, common.ustr(item['conditionDescription']).capitalize())
					self.skinproperty('Daily.%i.OutlookIcon' %count, '%s.png' % self._fanart(item['conditionCode']))
					self.skinproperty('Daily.%i.FanartCode' %count, self._fanart(item['conditionCode']))
					self.skinproperty('Daily.%i.Humidity' %count, str(item['humidity']), '%')
					self.skinproperty('Daily.%i.Precipitation' %count, str(item['precipitationProbability']), '%')
					self.skinproperty('Daily.%i.DewPoint' % count, self._dewpoint(self._2temperature(item['temperature']['low'], iu='f', ou='c'), item['humidity']))


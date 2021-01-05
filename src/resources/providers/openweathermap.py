# -*- coding: utf-8 -*-

import sys
import socket
import common
from .abstract import ContentProvider



class OpenWeatherMap(ContentProvider):
	LOCATION = 'https://api.openweathermap.org/data/2.5/find?q=%s&type=like&sort=population&cnt=10&appid=%s'
	FORECAST = 'https://api.openweathermap.org/data/2.5/%s?id=%s&appid=%s&units=%s&lang=%s'
	ART_DATA = {
		"01d": "Clear/Day",
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


	def _fanart(self, code):
		"""Detect and return fanart code"""
		return self.ART_BASE[self.ART_DATA[code]]


	def name(self):
		return "OpenWeatherMap"


	def code(self):
		return "openweathermap"


	def validate(self):
		response = self._parse(common.urlcall("https://api.openweathermap.org/data/2.5/weather?id=2172797&appid=%s" %self.apikey))
		if response is not None and response["cod"] != 200:
			raise RuntimeError(response["message"])
		elif response is None:
			raise RuntimeError("No content provided")


	def geoip(self):
		loc = ''
		locid = ''
		data = self.ipinfo()
		if data is not None and "city" in data:
			geoloc = data["city"]
			if "countryCode" in data:
				geoloc += "," + data["countryCode"]
			common.debug('Identifying GeoIP location: %s' % geoloc, self.code())
			url = self.LOCATION % (geoloc, self.apikey)
			data = self._call(url)
			common.debug('Found location data: %s' % data, self.code())
			if data is not None and "list" in data:
				item = data["list"][0]
				loc = item["name"]
				if "sys" in item and "country" in item["sys"]:
					loc += "-" + item["sys"]["country"]
				locid = item["id"]
		return loc, str(locid)


	def location(self, loc):
		locs = []
		locids = []
		common.debug('Searching for location: %s' % loc, self.code())
		url = self.LOCATION % (loc, self.apikey)
		data = self._call(url)
		common.debug('Found location data: %s' % data, self.code())
		if data is not None and "list" in data:
			for item in data["list"]:
				location = item["name"]
				if "sys" in item and "country" in item["sys"]:
					location += "-" + item["sys"]["country"]
				locationid = item["id"]
				locs.append(location)
				locids.append(str(locationid))
		return locs, locids


	def forecast(self, loc, locid):
		common.debug('Weather forecast for location: %s' % locid, self.code())
		url = self.FORECAST % ('weather', locid, self.apikey, "metric", self.lang)
		data = self._call(url)
		# Current weather forecast
		if data is not None and "weather" in data and "cod" in data and data["cod"] == 200:
			# current - standard
			self.skinproperty('Current.IsFetched', 'true')
			self.skinproperty('Current.Location', loc)
			self.skinproperty('Current.Latitude', data['coord']['lat'])
			self.skinproperty('Current.Longitude', data['coord']['lon'])
			self.skinproperty('Current.Condition', common.utf8(data['weather'][0]["description"]).capitalize())
			self.skinproperty('Current.Temperature', self._2temperature(data['main']['temp']))
			self.skinproperty('Current.Wind', self._2speed(data['wind']['speed'], iu='mps'))
			self.skinproperty('Current.WindDirection', data['wind']['deg'], '°') if "deg" in data['wind'] else self.skinproperty('Current.WindDirection')
			self.skinproperty('Current.Humidity', data['main']['humidity'])
			self.skinproperty('Current.Pressure', self._2pressure(data['main']['pressure'],um=True))
			self.skinproperty('Current.OutlookIcon', '%s.png' % self._fanart(data['weather'][0]["icon"]))
			self.skinproperty('Current.FanartCode', self._fanart(data['weather'][0]["icon"]))
			self.skinproperty('Current.Visibility', self._2distance(data['visibility'],iu='m',um=True))
			self.skinproperty('Current.LocalTime', self._2shtime(data['dt']))
			self.skinproperty('Current.LocalDate', self._2shdate(data['dt']))
			self.skinproperty('Current.FeelsLike', self.feelslike(self._2temperature(data['main']['temp']), self._2speed(data['wind']['speed'], iu='mps'), data['main']['humidity']))
			# Forecast - extended
			self.skinproperty('Forecast.City', loc)
			self.skinproperty('Forecast.Country', data['sys']['country'])
			self.skinproperty('Forecast.Latitude', data['coord']['lat'])
			self.skinproperty('Forecast.Longitude', data['coord']['lon'])
			self.skinproperty('Forecast.Updated', self._2shdatetime(data['dt']))
			# Today forecast
			self.skinproperty('Today.IsFetched', 'true')
			self.skinproperty('Today.Sunrise', self._2shtime(data['sys']['sunrise']))
			self.skinproperty('Today.Sunset', self._2shtime(data['sys']['sunset']))
			self.skinproperty('Today.HighTemperature', self._2temperature(data['main']['temp_max'], um=True))
			self.skinproperty('Today.LowTemperature', self._2temperature(data['main']['temp_min'], um=True))
			# Hourly weather forecast
			url = self.FORECAST % ('forecast', locid, self.apikey, "metric", self.lang)
			data = self._call(url)
			if data['list'] is not None and len(data['list']) >= 1:
				count = 0
				self.skinproperty('Hourly.IsFetched', 'true')
				for item in data['list']:
					self.skinproperty('Hourly.%i.Time' % count, self._2shtime(item['dt']))
					self.skinproperty('Hourly.%i.ShortDate' % count, self._2shdate(item['dt']))
					self.skinproperty('Hourly.%i.Condition' % count, common.utf8(item['weather'][0]["description"]).capitalize())
					self.skinproperty('Hourly.%i.Temperature' % count, self._2temperature(item['main']['temp'], iu='c',um=True))
					self.skinproperty('Hourly.%i.Outlook' % count, common.utf8(item['weather'][0]["description"]).capitalize())
					self.skinproperty('Hourly.%i.OutlookIcon' % count, '%s.png' % self._fanart(item['weather'][0]["icon"]))
					self.skinproperty('Hourly.%i.FanartCode' % count, self._fanart(item['weather'][0]["icon"]))
					self.skinproperty('Hourly.%i.Wind' % count, self._2speed(item['wind']['speed']))
					self.skinproperty('Hourly.%i.WindDirection' % count, item['wind']['deg'], '°') if "deg" in item['wind'] else self.skinproperty('Hourly%i.WindDirection' % count)
					self.skinproperty('Hourly.%i.Humidity' % count, item['main']['humidity'])
					self.skinproperty('Hourly.%i.Pressure' % count, self._2pressure(item['main']['pressure'],um=True))
					self.skinproperty('Hourly.%i.HighTemp' % count, self._2temperature(item['main']['temp_max'], iu='c'))
					self.skinproperty('Hourly.%i.LowTemp' % count, self._2temperature(item['main']['temp_min'], iu='c'))
					count += 1
			# Daily weather forecast
			self.skinproperty('Daily.IsFetched')
			self.skinproperty('Alerts.IsFetched')

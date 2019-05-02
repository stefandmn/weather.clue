# Clue Weather for MCPi and/or Kodi

**Clue Weather** package is designed to become main weather plugin for 
MCPi and an alternative weather add-on for Kodi. The package comes with 
two content providers the default one being **OpenWeatherMap** and the 
secondary one is **Dark Sky**. Additionally, can be developed and plugged 
other sources using built-in plugin object model (see `DataProvider` class
definition).

Below are described the main skin properties published by the content provides
through their lifecycle. 

## Details for Skinners or Plugin Developers

All values returned by the addon will include their units.


### Weather Labels

#### Current

* Current.IsFetched
* Current.Location
* Current.Latitude
* Current.Longitude
* Current.Condition
* Current.Temperature
* Current.Wind
* Current.WindDirection
* Current.Humidity
* Current.FeelsLike
* Current.DewPoint
* Current.UVIndex
* Current.FanartCode
* Current.LowTemperature
* Current.HighTemperature
* Current.Pressure
* Current.OutlookIcon
* Current.Visibility

#### Today

* Today.IsFetched
* Today.Sunrise
* Today.Sunset
* Today.HighTemperature
* Today.LowTemperature

#### Day [0-6]

* Day.%i.IsFetched
* Day.%i.Title
* Day.%i.HighTemp
* Day.%i.LowTemp
* Day.%i.Outlook
* Day.%i.OutlookIcon
* Day.%i.FanartCode
* Day.%i.WindSpeed
* Day.%i.WindDirection
* Day.%i.Humidity
* Day.%i.DewPoint
* Day.%i.UVIndex
* Day.%i.Visibility
* Day.%i.HighTemperature
* Day.%i.LowTemperature


#### Hourly[0-16] 

* Hourly.IsFetched
* Hourly.%i.Time
* Hourly.%i.LongDate
* Hourly.%i.ShortDate
* Hourly.%i.Outlook
* Hourly.%i.OutlookIcon
* Hourly.%i.FanartCode
* Hourly.%i.WindSpeed
* Hourly.%i.WindDirection
* Hourly.%i.Humidity
* Hourly.%i.Pressure
* Hourly.%i.FeelsLike
* Hourly.%i.Temperature
* Hourly.%i.DewPoint
* Hourly.%i.UVIndex
* Hourly.%i.Visibility

#### Alerts [1-5]

* Alerts.IsFetched
* Alerts.Text
* Alerts.%i.Title
* Alerts.%i.Description
* Alerts.%i.Expires

#### Weather provider

* WeatherProvider
* WeatherProviderLogo

# Hcalory BLE
Control Hcalory Bluetooth-enabled heaters using Home Assistant!

### What it does
This integration lets Home Assistant do many of the things the Hcalory app does. You can:
* Turn the heater on and off
* Set the heater mode (either thermostat, or "gear", which is really just a 1-6 power scale)
* Change the heater mode's setting (either degrees if you're in thermostat mode, or which "gear" you're in)
* View the built-in thermometer's temperature
* View the temperature of the heat exchanger
* View the battery voltage
* View error conditions (*right now, that's only E08*)

### What it probably doesn't do
* Work with any Hcalory heater model beyond the [one I tested](https://www.amazon.com/gp/product/B0D4529QY2)
    * It's possible it could work, but I only own the heater I own, so I can't reverse engineer anything else.
    * If that link dies, [here's an archive link](https://web.archive.org/web/20241125231404/https://www.amazon.com/gp/product/B0D4529QY2)
    * Additionally, here's what I assume is the same model on [Hcalory's website](https://hcalory.com/collections/diesel-heater/products/w1-diesel-heater-handy-se-8kw-12v-all-in-one-bluetooth?variant=41155845849131), plus a [Wayback Machine link](https://web.archive.org/web/20241125231708/https://hcalory.com/collections/diesel-heater/products/w1-diesel-heater-handy-se-8kw-12v-all-in-one-bluetooth?variant=41155845849131)
    * If _all of those_ links die or fail to work, it's the Hcalory "short-app" (ridiculous model "name"). The model number listed on the Amazon page is SKUK63125. The model listed on Hcalory's website is "W1". The "variant" on the Hcalory website is 41155845849131

### What it doesn't do
Currently, this integration doesn't support these doing things:
* Changing the units. In fact, you should probably set the units on your heater to °F because that's the unit I assumed. I believe Home Assistant should let you convert to °C on the frontend if you'd like
* Setting timers. Just use Home Assistant to set these, or send a PR to [hcalory-control](https://github.com/evanfoster/hcalory-control/) if you'd like to add support for this feature
* Using the "Blow Wind" (AKA "just turn on the fan") feature
* Toggling high plateau mode. If anyone besides me uses this integration and has a need for it, submit an issue and I'll go reverse engineer it myself

### What you need
* Some way for your Home Assistant instance to use Bluetooth
    * While this integration _can_ be used with something like a USB Bluetooth dongle, I wouldn't recommend it. Instead, an ESPHome Bluetooth Proxy should be used, which lets you get a Bluetooth antenna anywhere you have wifi reception. Don't be scared off by the thought of flashing microcontrollers because it's [shockingly easy.](https://esphome.io/projects/index.html) You can literally do everything you need from within your web browser
* Install the Hcalory BLE integration using this handy button: [![Open your Home Assistant instance and open a repository inside the Home Assistant Community Store.](https://my.home-assistant.io/badges/hacs_repository.svg)](https://my.home-assistant.io/redirect/hacs_repository/?owner=evanfoster&repository=&category=Integration)

### A note on safety
Please be careful. These heaters are relatively safe, but they're still _on fire_ and they still produce horribly toxic exhaust products. You're trusting your control over your heater to _Bluetooth_ and code written by some random idiot on the internet. Please ensure you have carbon monoxide detectors and fire alarms installed where you plan to use your heater.

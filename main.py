#!/usr/bin/env python

import webapp2, jinja2, os, logging
from google.appengine.api import memcache

j = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

class Status:
	"""Enum for river statuses"""
	OK, Vest, Permit = range(3)

class MainHandler(webapp2.RequestHandler):
	"""Handles web requests for the main page of the application"""
	def get(self):
		try:
			k = 'MAIN_OUTPUT_KEY'
			output = memcache.get(k)
			if output is None:
				logging.info("Regenerating main page")
				status = self.get_status()
				if status == Status.Permit:
					logging.info("Status is Permit")
					text = "not without a permit"
				elif status == Status.Vest:
					logging.info("Status is Vest")
					text = "yes, but bring a vest"
				else:
					logging.info("Status is OK")
					text = "sure, go for it"

				v = {
					'text': text,
					'class': 'status'+str(status)
					}
				t = j.get_template('main.html')
				output = t.render(v)
				memcache.add(k, output, 1800) # 0.5 hours
				logging.info("Cache regenerated")
			self.response.out.write(output)
		except:
			logging.exception('Error occurred while processing the request')
			self.response.out.write(
				"""Something went wrong, sorry. Check the 
				<a href="http://water.weather.gov/ahps2/hydrograph.php?wfo=akq&gage=rmdv2">river levels</a>
				and bring a vest if the water is higher than 5 feet. If it's over 9, you can't go without a
				permit.
				""")

	def get_status(self):
		"""Determines the current status based the maximum of all data points
		from the current date."""
		import urllib2, datetime
		from xml.dom.minidom import parseString
		from datetime import datetime
		from decimal import Decimal
		# fetch
		result = urllib2.urlopen("http://water.weather.gov/ahps2/hydrograph_to_xml.php?gage=rmdv2&output=xml");
		# parse
		doc = parseString(result.read())
		todaystr = datetime.utcnow().date().isoformat()
		logging.info("Matching on " + todaystr)
		values = [Decimal(n.parentNode.getElementsByTagName('primary')[0].childNodes[0].nodeValue)
								for n in doc.getElementsByTagName('valid')
								if todaystr in n.childNodes[0].nodeValue]
		logging.info("Got " + str(len(values)) + " data points")
		# decide
		maximum = max(values)
		logging.info("Maximum is " + str(maximum))
		if maximum >= 9:
			return Status.Permit
		elif maximum >= 5:
			return Status.Vest
		else:
			return Status.OK

app = webapp2.WSGIApplication([
	('/', MainHandler)
	], debug=True)

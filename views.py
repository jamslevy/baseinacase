import logging
from google.appengine.ext.webapp import template
from google.appengine.ext import webapp
from google.appengine.ext.webapp.util import run_wsgi_app

from google.appengine.api import urlfetch



## User name constants
_TWITTERBOT_USER = "mytwitterbot" # The username you use in twitter to login to http://twitter.com/mytwitterbot
_TWITTERBOTDEV_USER = "autotip" # # The username you use in twitter to login to your "dev" twitter account http://twitter.com/mydevtwitterbot
_TWITTERBOT_PWD = "buttbutt" # I'm lazy, I use the same password for both accounts, you probably shouldn't do this!

## URLS used for Twitter API calls - stored as constants for easy update later.
_TWIT_UPDATE = "https://twitter.com/statuses/update.json"


class MainPage(webapp.RequestHandler):

	def perform_search(self):
		query = self.request.get('user')
		if len(query) == 0: return []
		search_url = 'http://search.twitter.com/search.json?q=%s' % query
		timeline_url = 'http://twitter.com/statuses/user_timeline/' + query + '.json'
		results = urlfetch.fetch(url=timeline_url)        
		return  self.decode(results.content)
		
		# a website is two characters surrounded by a dot. (.*)/.(.*)
		# ([a-zA-Z0-9///:]*)\.([a-zA-Z0-9///:]*)
		

	def decode(self, results):
		def transform(result):
			return {
				'title':"Twitter: %s" % result['from_user'],
				'image':result['profile_image_url'],
				'url':"http://twitter.com/%s/" % result['from_user'],
				'text':result['text'],
				}

		import simplejson
		data = simplejson.loads(results)
		print ""
		import re
		for update in data:
			link_pattern = re.compile(".([/.a-zA-Z0-9///:]*)[a-zA-Z0-9]\.[a-zA-Z0-9]([/.a-zA-Z0-9///:]*)")
			r = link_pattern.search(update['text'])
			if r: print "link: " + r.group()
			print "text " + update['text']
			print "date " + update['created_at']
		if data.get('error', False): return "error!"
		print data
		return [ transform(x) for x in data['results'] ]



	def get(self):	
		template_values = {'results': self.perform_search()}
		self.response.out.write(template.render('templates/teaser.html', template_values))


class TwitterBot(webapp.RequestHandler):

	def get(self):
		import os
		if os.environ.get('SERVER_SOFTWARE','').startswith('Devel'): DEBUG = True
		else: DEBUG = False 
		# Do some stuff - what ever it is you want to tweet about!
		import datetime
		msg = str(datetime.datetime.now())

		if DEBUG == True: username = _TWITTERBOTDEV_USER
		else: username = _TWITTERBOT_USER

		response = self.TwitterPost(msg, username)

		if response != 200:
			status = "Whoops. Twitter was down or your code stuffed up"
		else:
			status = "Hooray! Tweeted: %s " % msg

		template_values={'status': status}
		self.response.out.write(template.render('templates/bot.html', template_values))


	def TwitterPost(self, msg, username):

	  password = _TWITTERBOT_PWD

	  form_fields = {
		"status": msg,
		"source": "twendly"  # If you register your bot with Twitter, this is how posts know to show "from Twendly" with a link back to the Twendly site.
		}

	  import base64
	  import urllib
	  authheader =  "Basic %s" % base64.encodestring('%s:%s' % (username, password))

	  base64string = base64.encodestring('%s:%s' % (username, password))[:-1]
	  authheader =  "Basic %s" % base64string

	  payload = urllib.urlencode(form_fields)

	  # Note the URL is using HTTPS which is supported by AppEngine so the call should be secured.
	  url = _TWIT_UPDATE

	  result = urlfetch.fetch(url=url,payload=payload,method=urlfetch.POST, headers={"Authorization": authheader})

	  if int(result.status_code) != 200:
		# You could get fancy and put some error handling in here if you're inclined.
		return int(result.status_code)

	  return 200
      
      
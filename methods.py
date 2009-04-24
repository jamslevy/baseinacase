"""

API Methods

As of March 17 2009, the two implemented API methods are a fuzzy
legislator name search and zip by zip code.

Please register an API key and replace the API_KEY with your new key value. 
Register at http://services.sunlightlabs.com/api/register/

You can get more info about the API methods at 
http://wiki.sunlightlabs.com/Sunlight_API_Documentation


"""
import logging
from google.appengine.api import urlfetch
from google.appengine.ext import db

SUNLIGHT_BASE_URL = "http://services.sunlightlabs.com/api/"
FUZZY_SEARCH = "legislators.search"
ZIP_SEARCH = "legislators.allForZip"
API_KEY = "06b192d4ec3fd9de2d7a21cdf1b67ec8" # Enter Your Own API Key Here 
CACHE_TIME = 2629700
 # Responses cached for almost 4 weeks
 # The cache can be reset through the GAE dashboard
# search_url = 'http://search.twitter.com/search.json?q=%s' % query


status_COUNT = '10'

class Links():

  def __init__(self, this_user, news_source=False):
      self.this_user = this_user
      self.news_source = news_source
  
  
  def twitter_retrieve(self, platform="twitter"):
        self.save = []
        from utils import twitter
        api = twitter.Api() # username, password
        statuses = api.GetUserTimeline(self.this_user.twitter_username, count=status_COUNT)
        import re
        import datetime
        link_pattern = re.compile(".([/.a-zA-Z0-9///:][/.a-zA-Z0-9///:]*)[a-zA-Z0-9]\.[a-zA-Z0-9///:][/.a-zA-Z0-9///:]([/.a-zA-Z0-9///:]*)")
        for status in statuses:
            status.date = datetime.datetime.strptime(status.created_at, '%a %b %d %H:%M:%S +0000 %Y')
            linkmatch = link_pattern.search(status.text)
            if not linkmatch: continue # no links found
            # create real date object from status['created_at']
            status.link = linkmatch.group().strip()
            self.save_link(status.link, status.text, status.date, platform=platform, id=status.id)
        db.put(self.save)


  def save_link(self, url, text, publish_date, platform=None, id=None):
      
      link_key_name = self.get_link_key_name(url, platform)
      from datastore import Link
      existing_link = Link.get_by_key_name(link_key_name)
      if existing_link: 
          logging.warning('save_link found match for key_name %s' % link_key_name)
          return "link already exists"
      text = db.Text(text)
      new_link = Link(key_name = link_key_name,
                      url = url, 
                      text = text,
                      publish_date = publish_date)
      new_link.is_news_source = self.news_source
      if self.news_source: new_link.news_source = self.this_user
      else: new_link.user = self.this_user
      #link location, platform, date
      self.save.append(new_link)


  def get_link_key_name(self, url, platform):
      return self.this_user.name + "_" + url + "_" + platform
  
  
  def find_scoops(self):
    self.save_scoops = []
    # Analyze link patterns compared to media outlets 
    if self.news_source: return "cannot analyze news source" 
    from datastore import Link
    for link in self.this_user.links: 
      news_stories = Link.gql("WHERE story = :1 AND is_news_source = True", link.story).fetch(1000)
      time_deltas = []
      # map out a list of time deltas between link and each news story, and then rank and cutoff
      from datastore import Scoop 
      for story in news_stories:
          time_delta = int( (link.publish_date - story.publish_date).seconds)
          # still don't completely understand how the timedeltas work 
          if time_delta < -20000: continue        
          new_scoop = Scoop(time_delta = time_delta, 
                            user = self.this_user,
                            news_source = story.news_source,
                            user_link = link,
                            news_link = story
                            )
          self.save_scoops.append(new_scoop)
    db.put(self.save_scoops)
    print "found " + str(len(self.save_scoops)) + " scoops"




def get_scoops(User, news_source=False):
    pass



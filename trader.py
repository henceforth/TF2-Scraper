import requests
import logging
import pdb
from bs4 import BeautifulSoup
import re
import shelve
import HTMLParser

logging.basicConfig()
l = logging.getLogger(__name__)
l.setLevel(logging.DEBUG)

def writePage(content):
  with file("/media/tmp/out.html", "w") as f:
    l.debug("writing page content")
    f.write(content.encode("utf8"))

class ScrapTfScraper(object):
  SCRAP_BASE_URL = "http://scrap.tf"
  PERSIST_TO_SHELVE = True
  SHELVE_NAME = "items.db"
  STEAM_LOGIN_POST_URL = "https://steamcommunity.com/openid/login"

  regLvl = re.compile("Level: (?P<level>[0-9]*[0-9]*[0-9]+)")
  regCost = re.compile(".*Costs:? (?P<cost>.+)<br/>")

  session = requests.Session()
  items = {}

  def __init__(self):
    self.session.cookies["steamLogin"] = "76561197960710974%7C%7C0FFC75DC5F2151BCB52D9B945E78C31BA6DE4B84"
    self.session.cookies["steamLoginSecure"] = "76561197960710974%7C%7C8E9D8F235B4D350E2BD8A562758C6D77E29CA5DF"
    self.session.cookies["steamMachineAuth76561197960710974"] = "F2FCF7794033272A414D5348F15D2B6DEC2A14D2"
    self.__login()
    self.scrapeItems()

    if self.PERSIST_TO_SHELVE:
      self.persistItems()

    l.info("%i items" % len(self.items))

  def persistItems(self):
    l.info("persisting as %s" % self.SHELVE_NAME) 
    d = shelve.open(self.SHELVE_NAME)
    d["items"] = self.items
    d.close()

  def dumpItems(self):
    for k, v in self.items.iteritems():
      print "%s: %s, %ix" % (k, v["cost"], v["quanitity"])

  def scrapeItems(self):
    pages = []
    l.info("looking for pages...")
    r = self.session.get(self.SCRAP_BASE_URL + "/stranges")

    soup = BeautifulSoup(r.text)
    for n in soup.find_all(class_="bank-selector-box"):
      pages.append(n.find("a")["href"])

    l.debug("found %i pages" % len(pages))

    for page in pages:
      r = self.session.get(self.SCRAP_BASE_URL + page)
      soup = BeautifulSoup(r.text)

      for n in soup.find_all("div"):
        if "data-title" in n.attrs.keys():
          if n["data-title"] not in self.items.keys():
            lvl = self.regLvl.match(n["data-content"]).group("level")
            cost = self.regCost.match(n["data-content"]).group("cost")
            self.items[n["data-title"]] = {"cost": cost, "quanitity": 1}
          else:
            self.items[n["data-title"]]["quanitity"] += 1

  def __login(self):
    l.info("getting log-in page")
    r = self.session.get(self.SCRAP_BASE_URL + "/login")
    soup = BeautifulSoup(r.text)
    openIdForm = soup.find(id="openidForm")

    if openIdForm == None:
      l.error("can't find the login form, aborting")
      quit()

    payload = {}
    for n in openIdForm.find_all("input"):
      if "name" in n.attrs.keys():
        l.debug("adding to payload: %s -  %s" % (n["name"], n["value"]))
        payload[n["name"]] = n["value"]

    r = self.session.post(self.STEAM_LOGIN_POST_URL, data=payload)

    if r.url.startswith(self.SCRAP_BASE_URL):
      l.info("LOGIN SUCCESS!")
    else:
      l.error("LOGIN FAIL, url is not %s, but %s" % (self.SCRAP_BASE_URL, r.url))
      quit()

class  TradeTfScraper(object):
  TRADE_BASE_URL = "http://trade.tf/classifieds/search/Sell/Strange/%s/all/All/1"
  session = requests.Session()

  def getPrices(self, itemName):
    itemName = itemName.replace("Strange ", "")
    r = self.session.get(self.TRADE_BASE_URL % itemName)
    l.debug("trade.tf status code: %i" % r.status_code)
    writePage(r.text)
    soup = BeautifulSoup(r.text)

    table = soup.find(class_="price-summary")

    if(table == None):
      l.error("%s not found!" % itemName)
      return {"tradetf": None, "web": None, "backpack": None}

    tradetfPrice = table.find(class_="price-price")
    webPrice = tradetfPrice.find_next(class_="price-price")
    backpacktfPrice = webPrice.find_next(class_="price-price")

    l.debug("%s: %s, %s, %s" % (itemName, tradetfPrice.text, webPrice.text, backpacktfPrice.text))
    return {"tradetf": tradetfPrice.text, "web": webPrice.text, "backpack": backpacktfPrice.text}


if __name__ == "__main__":
  a = ScrapTfScraper()
  a.dumpItems()
  
  #a = shelve.open("items.db")
  #items = a["items"]
  #a.close()

  #b = TradeTfScraper()

  #for k, v in items.iteritems():
    #print "%s, %s" % (v["cost"], b.getPrices(k))

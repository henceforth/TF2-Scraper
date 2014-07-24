import requests
import logging
import pdb
from bs4 import BeautifulSoup
import re
import shelve

logging.basicConfig()
l = logging.getLogger(__name__)
l.setLevel(logging.DEBUG)

SCRAP_BASE_URL = "http://scrap.tf"
PERSIST_TO_SHELVE = True
SHELVE_NAME = "items.db"

def writePage(content):
  with file("/media/tmp/out.html", "w") as f:
    l.debug("writing page content")
    f.write(content.encode("utf8"))

if __name__ == "__main__":
  regLvl = re.compile("Level: (?P<level>[0-9]*[0-9]*[0-9]+)")
  regCost = re.compile(".*Costs: (?P<cost>.+)<br/>")

  l.info("getting log-in page")

  s = requests.Session()
  s.cookies["steamLogin"] = "76561197960710974%7C%7C0FFC75DC5F2151BCB52D9B945E78C31BA6DE4B84"
  s.cookies["steamLoginSecure"] = "76561197960710974%7C%7C8E9D8F235B4D350E2BD8A562758C6D77E29CA5DF"
  s.cookies["steamMachineAuth76561197960710974"] = "F2FCF7794033272A414D5348F15D2B6DEC2A14D2"

  r = s.get(SCRAP_BASE_URL + "/login")
  payload = {}

  soup = BeautifulSoup(r.text)
  openIdForm = soup.find(id="openidForm")

  if openIdForm == None:
    l.error("can't find the login form, aborting")
    quit()

  for n in openIdForm.find_all("input"):
    if "name" in n.attrs.keys():
      l.debug("adding to payload: %s -  %s" % (n["name"], n["value"]))
      payload[n["name"]] = n["value"]

  r = s.post("https://steamcommunity.com/openid/login", data=payload)
  l.info("url: %s" % r.url)

  if r.url.startswith(SCRAP_BASE_URL):
    l.info("LOGIN SUCCESS!")
  else:
    l.error("LOGIN FAIL, url doesn't seem to be scrap.tf")
    quit()

  pages = []
  l.info("looking for pages...")
  r = s.get(SCRAP_BASE_URL + "/stranges")

  soup = BeautifulSoup(r.text)
  for n in soup.find_all(class_="bank-selector-box"):
    pages.append(n.find("a")["href"])

  l.debug("found %i pages" % len(pages))

  objects = {}
  for page in pages:
    r = s.get(SCRAP_BASE_URL + page)
    soup = BeautifulSoup(r.text)

    for n in soup.find_all("div"):
      if "data-title" in n.attrs.keys():
        if n["data-title"] not in objects.keys():
          lvl = regLvl.match(n["data-content"]).group("level")
          cost = regCost.match(n["data-content"]).group("cost")
          objects[n["data-title"]] = {"cost": cost, "quanitity": 1}
        else:
          objects[n["data-title"]]["quanitity"] += 1

  for k, v in objects.iteritems():
    print "%s: %s, %ix" % (k, v["cost"], v["quanitity"])

  if PERSIST_TO_SHELVE:
    l.info("persisting")
    d = shelve.open(SHELVE_NAME)
    d["items"] = objects
    d.close()

  l.info("%i items" % len(objects))

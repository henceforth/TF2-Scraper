import requests
import logging
import pdb
from bs4 import BeautifulSoup
import re

logging.basicConfig()
l = logging.getLogger(__name__)
l.setLevel(logging.DEBUG)

def writePage(content):
  with file("/media/tmp/out.html", "w") as f:
    l.debug("writing page content")
    f.write(content.encode("utf8"))

if __name__ == "__main__":
  regLvl = re.compile("Level: (?P<level>[0-9]*[0-9]*[0-9]+)")
  regCost = re.compile(".*Costs: (?P<cost>.+)<br/>")

  l.info("getting loging page")

  cookies = {"steamLogin": "76561197960710974%7C%7C0FFC75DC5F2151BCB52D9B945E78C31BA6DE4B84"}
  cookies["steamLoginSecure"] = "76561197960710974%7C%7C8E9D8F235B4D350E2BD8A562758C6D77E29CA5DF"
  cookies["steamMachineAuth76561197960710974"] = "F2FCF7794033272A414D5348F15D2B6DEC2A14D2"

  s = requests.Session()
  r = s.get("http://scrap.tf/login", cookies=cookies)
  writePage(r.text)

  payload = {}

  l.info("calling BS")
  soup = BeautifulSoup(r.text)
  openIdForm = soup.find(id="openidForm")
  for n in openIdForm.find_all("input"):
    if "name" in n.attrs.keys():
      l.debug("adding to payload: %s -  %s" % (n["name"], n["value"]))
      payload[n["name"]] = n["value"]

  r = s.post("https://steamcommunity.com/openid/login", data=payload, cookies=cookies)
  writePage(r.text)
  l.info("url: %s" % r.url)

  if r.url.startswith("http://scrap.tf"):
    l.info("LOGIN SUCCESS!")
  else:
    l.error("LOGIN FAIL, url doesn't seem to be scrap.tf")
    quit()

  l.info("fetching strange weapon page...")
  r = s.get("http://scrap.tf/stranges/50")
  writePage(r.text)

  l.info("parsing strange weapon page")
  soup = BeautifulSoup(r.text)

  shown = []
  for n in soup.find_all("div"):
    if "data-title" in n.attrs.keys() and n["data-title"] not in shown:
      lvl = regLvl.match(n["data-content"]).group("level")
      cost = regCost.match(n["data-content"]).group("cost")
      l.info("%s - %s - %s" % (n["data-title"], lvl, cost))
      shown.append(n["data-title"]) #TODO: add lvl/price to table







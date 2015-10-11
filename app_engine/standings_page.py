import collections
import re
from datetime import datetime
from lxml import etree


def _GetNodeText(node):
  text = etree.tostring(node, method="text", encoding='utf-8')
  if text is not None:
    text = text.replace("\xc2\xa0", " ").strip()
  return text

def _GetCleanName(node):
  return " ".join(_GetNodeText(node).split())

Division = collections.namedtuple('Division', ['name', 'teams'])
TeamEntry = collections.namedtuple('TeamEntry', ['name', 'wins', 'ties', 'losses', 'points'])

class ScrapedStandings(object):
  def __init__(self, page_html):
    self._last_update = None
    self._divisions = []

    html_parser = etree.HTMLParser()
    tree = etree.parse(page_html, parser=html_parser)
    current_division = None
    last_update_str = re.search("\S+ [0-9]{1,2}",
        _GetNodeText(tree.xpath("//table[col]//tr")[0])).group(0)
    self._last_update = datetime.strptime(last_update_str, "%B %d").date().replace(year=datetime.now().year)
    for row in tree.xpath("//table[col]//tr")[1:]:
      cells = row.xpath(".//td")
      if len(cells) == 1:
        division_name = _GetCleanName(cells[0])
        if not division_name: continue
        current_division = Division(name=division_name, teams=[])
        self._divisions.append(current_division)
      else:
        team_name = _GetCleanName(cells[0])
        if not team_name or team_name == 'TEAM': continue
        wins = int(_GetNodeText(cells[1]))
        ties = int(_GetNodeText(cells[5]))
        losses = int(_GetNodeText(cells[3]))
        points = int(_GetNodeText(cells[6]))
        current_division.teams.append(TeamEntry(
          name=team_name, wins=wins, ties=ties, losses=losses, points=points
        ))
        
  def LastUpdate(self):
    return self._last_update

  def Divisions(self):
    return self._divisions

if __name__ == "__main__":
  import urllib
  page = ScrapedStandings(urllib.urlopen("http://corporateleague.com/soccer/corpstandings.html"))
  print page.LastUpdate()
  print page.Divisions()
  

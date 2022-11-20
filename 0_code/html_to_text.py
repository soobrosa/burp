import sys
from bs4 import BeautifulSoup
import re

webContent = ''
for line in sys.stdin:
    webContent += line

webContent = webContent.\
  replace('\r', ' ').\
  replace('\n', ' ').\
  replace('</p>', '\n').\
  replace('<br>', '\n')

soup = BeautifulSoup(webContent, features="lxml")

_MULTIPLE_SPACES = re.compile(r"(?:(?!\n)\s)+")

print (_MULTIPLE_SPACES.sub(" ", soup.text).strip())
# https://github.com/soobrosa/slurp/tree/main

# should run on Sundays, the day before weekly menu change

from datetime import datetime, timedelta

import urllib.request, urllib.error, urllib.parse

def save_page(url, filename):

  response = urllib.request.urlopen(url)
  webContent = response.read().decode('windows-1250')
  f = open(filename, 'w')
  f.write(webContent)
  f.close

day_names = ['vasarnap', 'szombat', 'pentek', 'csutortok', 'szerda', 'kedd', 'hetfo']

if datetime.today().weekday() == 6:
  for day in range(0, 7):
    filename = '1_html/' + (datetime.today() - timedelta(days=day)).strftime('%Y-%m-%d') + '.html'
    save_page('http://www.holmenuzzek.hu/' + day_names[day] + '.htm', filename)

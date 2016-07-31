#!/usr/bin/python
# -*- coding: utf-8 -*-
from urllib2 import urlopen
from bs4 import BeautifulSoup, Tag
from datetime import datetime
import re

MONTH_NAMES = [
    u'JANEIRO',
    u'FEVEREIRO',
    u'MARÇO',
    u'ABRIL',
    u'MAIO',
    u'JUNHO',
    u'JULHO',
    u'AGOSTO',
    u'SETEMBRO',
    u'OUTUBRO',
    u'NOVEMBRO',
    u'DEZEMBRO'
]

MONTH_TO_NUMBER = dict(zip(MONTH_NAMES, range(1, len(MONTH_NAMES)+1)))

YEAR_MONTH_REGEX = re.compile(r'(?:(?P<month>[^\W\d_]+) ?/? ?)?(?P<year>\d{4})?', re.UNICODE)

def parse_year_month(candidates):
    year = None
    month = None
    for p in candidates:
        if not isinstance(p, Tag) or p.name != u'p':
            continue
        matches = YEAR_MONTH_REGEX.search(p.text)
        if matches:
            try:
                if year is None:
                    year = matches.group('year')
                if month is None:
                    month = matches.group('month')
                if year is not None and month is not None:
                    return year, month
            except IndexError:
                pass

TIME_RANGE_REGEX = re.compile(r"(\d{1,2}) *(a|e) *(\d{1,2})")

def parse_time(elem, month, year):
    isrange = TIME_RANGE_REGEX.match(elem.string)

    end = None
    datestr = "%d%.2d%%.2d" % (year, month)

    if isrange:
        start = int(isrange.group(1))
        end = int(isrange.group(3))
        return (datestr % start, datestr % end, False)

    istwodays = False
    if isrange:
        istwodays = isrange.group(2) == "e"
    
    if istwodays:
        day1 = int(istwodays.group(1))
        day2 = int(istwodays.group(3))
        if day2 == day1+1:
            return (datestr % day1, datestr % day2, False)
        return (datestr % day1, datestr % day2, True)

    day = int(elem.string)
    return (datestr % day, datestr % day, False)

NOW = datetime.utcnow().strftime('%Y%m%dT%H%M%SZ')

def create_event(soup, start, end, summary):
    return u'''
BEGIN:VEVENT
DTSTAMP:{}
SUMMARY;LANGUAGE=pt-BR:{}
DTSTART;VALUE=DATE:{}
DTEND;VALUE=DATE:{}
END:VEVENT
'''.format(NOW, summary.replace('\n', '\\n'), start, end)

page = BeautifulSoup(urlopen('https://www.ufmg.br/conheca/calendario.shtml'), 'html.parser')
out = u'''BEGIN:VCALENDAR
PRODID:https://github.com/reuben/silly_hacks/calendar/convert.py
X-WR-CALNAME:{}
VERSION:2.0
METHOD:PUBLISH
'''.format(page.title.string)

for month_table in page.find_all('table'):
    (year, month) = parse_year_month(month_table.previous_elements)
    year = int(year)
    month = MONTH_TO_NUMBER[month]

    for entry in month_table.find_all('tr'):
        summary = entry.contents[5].text
        (start, end, twodays) = parse_time(entry.td, month, year)

        ev = create_event(page, start, start if twodays else end, summary)
        out += ev

        if twodays:
            ev = create_event(page, end, end, summary)
            out += ev

out += 'END:VCALENDAR'

print out.replace('\n', '\r\n').encode('utf-8')

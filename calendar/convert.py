#!/usr/bin/python
# -*- coding: utf-8 -*-
from urllib2 import urlopen
from bs4 import BeautifulSoup, Tag
import re

month_names = [
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

month_nbr = dict([(month_names[i], i+1) for i in range(0, len(month_names))])

YEAR_MONTH_REGEX = re.compile(r"(?:(?P<month>[^\W\d_]+) ?/? ?)?(?P<year>\d{4})?", re.UNICODE)

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
                    year = matches.group("year")
                if month is None:
                    month = matches.group("month")
                if year is not None and month is not None:
                    return year, month
            except IndexError:
                pass

def find_events(month_table):
    return month_table.find_all('tr')

def parse_time(elem, month, year):
    timerange = re.compile("(\d{1,2}) *a *(\d{1,2})")
    isrange = re.match(timerange, elem.string)

    end = None
    datestr = "%d-%.2d-%%.2d" % (year, month)

    if isrange:
        start = int(isrange.group(1))
        end = int(isrange.group(2))
        return (datestr % start, datestr % end, False)

    twodays = re.compile("(\d{1,2}) *e *(\d{1,2})")
    istwodays = re.match(twodays, elem.string)

    if istwodays:
        day1 = int(istwodays.group(1))
        day2 = int(istwodays.group(2))
        return (datestr % day1, datestr % day2, True)

    day = int(elem.string)
    return (datestr % day, datestr % day, False)

def create_tag(soup, tag, attrs):
    t = soup.new_tag(tag)
    for attr in attrs:
        if attr == 'value':
            t.string = attrs[attr]
        else:
            t[attr] = attrs[attr]
    return t


def create_event(soup, start, end, summary):
    ev = create_tag(soup, 'div', {
        'class': 'vevent'
    })
    ev.append(create_tag(soup, 'span', {
        'class': 'summary',
        'value': summary
    }))
    ev.append(create_tag(soup, 'span', {
        'class': 'dtstart',
        'value': start
    }))
    ev.append(create_tag(soup, 'span', {
        'class': 'dtend',
        'value': end
    }))

    return ev

page = BeautifulSoup(urlopen('https://www.ufmg.br/conheca/calendario.shtml'), 'html.parser')
out = BeautifulSoup(u'''
<!DOCTYPE html>
<html lang="pt-BR">
<head>
    <meta charset="UTF-8"/> 
    <title></title>
</head>
<body>
</body>
''', 'html.parser')

out.title.string = page.title.string

for month_table in page.find_all('table'):
    (year, month) = parse_year_month(month_table.previous_elements)
    year = int(year)
    month = month_nbr[month]

    for entry in find_events(month_table):
        summary = entry.contents[5].text        
        (start, end, twodays) = parse_time(entry.td, month, year)

        ev = create_event(page, start, start if twodays else end, summary)
        out.body.append(ev)

        if twodays:
            ev = create_event(page, end, end, summary)
            out.body.append(ev)

print out.prettify().encode('utf-8')

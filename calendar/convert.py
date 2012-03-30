#!/usr/bin/python
# -*- coding: utf-8 -*-
from urllib2 import urlopen
from bs4 import BeautifulSoup
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

def find_events(month):
    events = []
    for ev in month.find_next_siblings():
        if ev.has_key('class') and 'ano' in ev['class']:
            break
        if ev.name == 'tr' and len(ev.contents) > 3:
            events.append(ev)
    return events

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


def create_event(soup, day, summary):
    ev = create_tag(soup, 'div', {
        'class': 'vevent'
    })
    ev.append(create_tag(soup, 'span', {
        'class': 'summary',
        'value': summary
    }))
    ev.append(create_tag(soup, 'span', {
        'class': 'dtstart',
        'value': day
    }))
    ev.append(create_tag(soup, 'span', {
        'class': 'dtend',
        'value': day
    }))

    return ev

page = BeautifulSoup(urlopen('http://www.ufmg.br/conheca/calendario.shtml'))
out = BeautifulSoup(u'''
<html lang="pt-BR">
<head>
    <meta http-equiv="Content-Type" content="text/html; charset=UTF-8"/> 
    <title></title>
</head>
''')

out.title.string = page.title.string

elems = page.table.find_all('tr', ['ano','mes'])
for (year_elem, month_elem) in zip(elems[::2], elems[1::2]):
    year = int(year_elem.td.string)
    month = month_nbr[month_elem.td.string]

    for event in find_events(month_elem):
        event.name = 'div'
        event['class'] = 'vevent'

        summary = event.contents[-2]
        summary.name = 'span'
        summary['class'] = 'summary'
        
        (start, end, twodays) = parse_time(event.td, month, year)

        for child in filter(lambda x: x != summary, event.contents):
            child.extract()
        
        event.append(create_tag(page, 'span', {
            'class': 'dtstart',
            'value': start
        }))

        event.append(create_tag(page, 'span', {
            'class': 'dtend',
            'value': start if twodays else end
        }))

        if twodays:
            # print 'two day event, %s & %s' % (start, end)
            ev = create_event(page, end, summary.string.encode('utf-8'))
            out.body.append(ev)

        out.body.append(event)

print out.prettify().encode('utf-8')

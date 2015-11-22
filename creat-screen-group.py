#!/usr/bin/env python
#coding=utf-8

import urllib2
import json
import argparse

def requestJson(url,values):
    data = json.dumps(values)
    req = urllib2.Request(url, data, {'Content-Type': 'application/json-rpc'})
    response = urllib2.urlopen(req, data)
    output = json.loads(response.read())
#    print output
    try:
        message = output['result']
    except:
        message = output['error']['data']
        print message
        quit()

    return output['result']

def authenticate(url, username, password):
    values = {'jsonrpc': '2.0',
              'method': 'user.login',
              'params': {
                  'user': username,
                  'password': password
              },
              'id': '0'
              }

    data = json.dumps(values)
    req = urllib2.Request(url, data, {'Content-Type': 'application/json-rpc'})
    response = urllib2.urlopen(req, data)
    output = json.loads(response.read())

    try:
        message = output['result']
    except:
        message = output['error']['data']
        print message
        quit()

    return output['result']

def getHosts(groupname,url,auth):
    host_list = []
    values = {'jsonrpc': '2.0',
              'method': 'hostgroup.get',
              'params': {
                  'output': 'extend',
                  'filter': {
                      'name': groupname
                  },

                  'selectHosts' : ['hostid','host'],
              },
              'auth': auth,
              'id': '2'
              }
    output = requestJson(url,values)
    for host in output[0]['hosts']:
        host_list.append(host['hostid'])
    return host_list

#循环所有host，把图添加到list
#当第一hostname的时候graph会添加到screen的第一列，然后x+1，y变回0，添加第二hostnam的graph到第二列，依次添加
def getGraph(hostlist, url, auth, graphtype, dynamic, columns):
    x = 0
    graph_list = []
    while x < len(hostlist):
        hostname = hostlist[x]
        if (graphtype == 0):
            selecttype = ['graphid']
            select = 'selectGraphs'
        if (graphtype == 1):
            selecttype = ['itemid', 'value_type']
            select = 'selectItems'

        values = {'jsonrpc': '2.0',
                  'method': 'host.get',
                  'params': {
                      select: selecttype,
                      'output': ['hostid', 'host'],
                      'searchByAny': 1,
                      'filter': {
                          'hostid': hostname
                      }
                  },
                  'auth': auth,
                  'id': '2'
                  }

        data = json.dumps(values)
        req = urllib2.Request(url, data, {'Content-Type': 'application/json-rpc'})
        response = urllib2.urlopen(req, data)
        host_get = response.read()

        output = json.loads(host_get)
        #print json.dumps(output)

        graphs = []
        if (graphtype == 0):
            for i in output['result'][0]['graphs']:
                graphs.append(i['graphid'])

        if (graphtype == 1):
            for i in output['result'][0]['items']:
                if int(i['value_type']) in (0, 3):
                    graphs.append(i['itemid'])
        y = 0
        for graph in graphs:
            graph_list.append({
                "resourcetype": graphtype,
                "resourceid": graph,
                "width": "500",
                "height": "100",
                "x": str(x),
                "y": str(y),
                "colspan": "1",
                "rowspan": "1",
                "elements": "0",
                "valign": "0",
                "halign": "0",
                "style": "0",
                "url": "",
                "dynamic": str(dynamic)
            })
            y += 1
        x += 1
    print 'graph_list:', graph_list
    return graph_list


def screenCreate(url, auth, screen_name, graphids, columns):
    # print graphids
    if len(graphids) % columns == 0:
        vsize = len(graphids) / columns
    else:
        vsize = (len(graphids) / columns) + 1

    values = {"jsonrpc": "2.0",
              "method": "screen.create",
              "params": [{
                  "name": screen_name,
                  "hsize": columns,
                  "vsize": vsize,
                  "screenitems": []
              }],
              "auth": auth,
              "id": 2
              }

    for i in graphids:
        values['params'][0]['screenitems'].append(i)

    data = json.dumps(values)
    req = urllib2.Request(url, data, {'Content-Type': 'application/json-rpc'})
    response = urllib2.urlopen(req, data)
    host_get = response.read()

    output = json.loads(host_get)

    try:
        message = output['result']
    except:
        message = output['error']['data']
    print json.dumps(message)


def main():
    url = 'http://10.10.100.233/api_jsonrpc.php'
    username = "admin"
    password = "xxxxx"

    parser = argparse.ArgumentParser(description='Create Zabbix screen from all of a host Items or Graphs.')
    parser.add_argument('groupname', metavar='H', type=str,
                        help='Zabbix Host to create screen from')
    parser.add_argument('screenname', metavar='N', type=str,
                        help='Screen name in Zabbix.  Put quotes around it if you want spaces in the name.')
    parser.add_argument('-c', dest='columns', type=int, default=3,
                        help='number of columns in the screen (default: 3)')
    parser.add_argument('-d', dest='dynamic', action='store_true',
                        help='enable for dynamic screen items (default: disabled)')
    parser.add_argument('-t', dest='screentype', action='store_true',
                        help='set to 1 if you want item simple graphs created (default: 0, regular graphs)')

    args = parser.parse_args()
    groupname = args.groupname
    screen_name = args.screenname
    columns = args.columns
    dynamic = (1 if args.dynamic else 0)
    screentype = (1 if args.screentype else 0)
    auth = authenticate(url, username, password)
    hostlist = getHosts(groupname,url,auth)
    graphids = getGraph(hostlist, url, auth, screentype, dynamic, columns)

    print "Screen Name: " + screen_name
    print "Total Number of Graphs: " + str(len(graphids))

    screenCreate(url, auth, screen_name, graphids, columns)

if __name__ == '__main__':
    main()

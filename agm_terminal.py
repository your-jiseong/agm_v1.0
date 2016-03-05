# -*- coding: utf-8 -*-

import sys, re
from bottle import route, run, template, request, response, post
import urllib, urllib2, json
from time import sleep

m_dir = 'm_data/'

# Global variables
default_conf = {}
conf = {}

input_string = None
input_json = None

answers = []
no_answers = []


def main():
  get_inputs()
  set_conf()
  get_answers()
  bye()


def get_inputs():
  global input_string
  global input_json

  input_str = sys.argv[1]
  input_json = json.loads(input_str)


def get_default_conf():
  global default_conf

  i_file = open(m_dir + 'conf.tsv', 'r')
  line = i_file.readline()
  while line:
    line = line[0:-1]

    s_line = re.split('\t', line)  
    if s_line[0] == 'kb_addresses':
      default_conf['kb_addresses'] = s_line[1:]
    elif s_line[0] == 'graph_uri':
      default_conf['graph_uri'] = s_line[1:]
    elif s_line[0] == 'answer_num':
      default_conf['answer_num'] = int(s_line[1])
    elif s_line[0] == 'query_interval':
      default_conf['query_interval'] = float(s_line[1])

    line = i_file.readline()
  i_file.close()


def set_conf():
  global default_conf
  global conf

  get_default_conf()

  try:
    conf['kb_addresses'] = input_json['conf']['kb']
  except KeyError:
    conf['kb_addresses'] = default_conf['kb_addresses']

  try:
    conf['graph_uri'] = input_json['conf']['graph_uri']
  except KeyError:
    conf['graph_uri'] = default_conf['graph_uri']

  try:
    conf['answer_num'] = input_json['conf']['answer_num']
  except KeyError:
    conf['answer_num'] = default_conf['answer_num']

  try:
    conf['query_interval'] = input_json['conf']['query_interval']
  except KeyError:
    conf['query_interval'] = default_conf['query_interval']

  input_json.pop('conf')


def get_answers(): 
  global answers

  agm_inputs = input_json['queries']
  for agm_input in agm_inputs:
    for graph_uri in conf['graph_uri']:
      arguments = {'default-graph-uri':graph_uri, 'format':'application/sparql-results+json', 'timeout':'0', 'debug':'on', 'query':''}
      query = agm_input['query'].encode('utf-8')
      arguments['query'] = query + '\n'
      
      sleep(conf['query_interval'])
      for kb_address in conf['kb_addresses']:
        full_url = kb_address + '?' + urllib.urlencode(arguments)  
        endpoint_output = urllib.urlopen(full_url).read()

        try:
          endpoint_output_json = json.loads(endpoint_output)
          var = endpoint_output_json['head']['vars'][0]
          for binding in endpoint_output_json['results']['bindings']:
            answer = binding[var]['value'].encode('utf-8')
            answers.append({'query': query, 'answer': answer})
        except Exception as e:
          no_answers.append({'query': query, 'endpoint_output': endpoint_output})

        if len(answers) >= conf['answer_num']:
          bye()


def send_getrequest(url):
  opener = urllib2.build_opener()
  request = urllib2.Request(url, headers={'Content-Type':'application/json'})
  return opener.open(request).read()
  

def send_postrequest(url, input_string):
  opener = urllib2.build_opener()
  request = urllib2.Request(url, data=input_string, headers={'Content-Type':'application/json'})
  return opener.open(request).read()


def bye():  
  output = json.dumps(answers, indent=5, separators=(',', ': '))

  sys.stdout.write(output)
  sys.stdout.flush()
  sys.exit(0)


main()
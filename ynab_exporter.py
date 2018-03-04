from prometheus_client import start_http_server, Gauge
import time
import json
import urllib.request
import os

def pull_raw_categories_object(budget_id, token):
  request = urllib.request.Request('https://api.youneedabudget.com/v1/budgets/%s/categories' % budget_id, headers={'Authorization': 'Bearer %s' % token})
  response_body = urllib.request.urlopen(request).read()
  raw_categories  = json.loads(response_body)
  return raw_categories


def get_category_metadata(raw_categories):
  category_map = {}
  for category_group in raw_categories['data']['category_groups']:
    category_group_metadata = {
      'name': category_group['name'],
      'hidden': category_group['hidden']
    }
    category_map[category_group['id']] = category_group_metadata
    
    for category in category_group['categories']:
      category_metadata = {
        'name': category['name'],
        'hidden': category['hidden'],
        'category_group_id': category_group['id']
      }
      category_map[category['id']] = category_metadata
  return category_map


def get_categories(raw_categories):
  categories = []
  for category_group in raw_categories['data']['category_groups']:
    for category in category_group['categories']:
      categories.append(category)
  return categories


def add_category_metadata_values_to_gauge(category_metadata, metadata_gauge, group_metadata_gauge):
  for cat_id, cat_metadata in category_metadata.items():
    if 'category_group_id' in cat_metadata:
      metadata_gauge.labels(
        cat_id, 
        cat_metadata['name'], 
        cat_metadata['hidden'],
        cat_metadata['category_group_id']
      ).set(1)
    else:
      group_metadata_gauge.labels(
        cat_id,
        cat_metadata['name'],
        cat_metadata['hidden'],
      ).set(1)


def clear_category_metadata_values_to_gauge(category_metadata, metadata_gauge, group_metadata_gauge):
  for cat_id, cat_metadata in category_metadata.items():
    if 'category_group_id' in cat_metadata:
      metadata_gauge.remove(
        cat_id, 
        cat_metadata['name'], 
        cat_metadata['hidden'],
        cat_metadata['category_group_id']
      )
    else:
      group_metadata_gauge.remove(
        cat_id,
        cat_metadata['name'],
        cat_metadata['hidden'],
      )




def add_category_values_to_gauge(categories, budgeted_gauge, activity_gauge, balance_gauge):
  for category in categories:
    budgeted_gauge.labels(category['id']).set(category['budgeted'] / 1000)
    activity_gauge.labels(category['id']).set(category['activity'] / 1000)
    balance_gauge.labels( category['id']).set(category['balance']  / 1000)


def clear_category_values_to_gauge(categories, budgeted_gauge, activity_gauge, balance_gauge):
  for category in categories:
    budgeted_gauge.remove(category['id'])
    activity_gauge.remove(category['id'])
    balance_gauge.remove(category['id'])


def process_raw_categories(raw_categories, budgeted_gauge, activity_gauge, balance_gauge, metadata_gauge, group_metadata_gauge):
  category_metadata = get_category_metadata(raw_categories)
  add_category_metadata_values_to_gauge(category_metadata, metadata_gauge, group_metadata_gauge)
  categories = get_categories(raw_categories)
  add_category_values_to_gauge(categories, budgeted_gauge, activity_gauge, balance_gauge)


def clear_gauges(raw_categories, budgeted_gauge, activity_gauge, balance_gauge, metadata_gauge, group_metadata_gauge):
  category_metadata = get_category_metadata(raw_categories)
  clear_category_metadata_values_to_gauge(category_metadata, metadata_gauge, group_metadata_gauge)
  categories = get_categories(raw_categories)
  clear_category_values_to_gauge(categories, budgeted_gauge, activity_gauge, balance_gauge)


NAMESPACE = 'ynab'
REFRESH_TIME_SECS = os.getenv('YNAB_REFRESH_TIME_SECS', 3600)
BUDGET_ID =         os.getenv('YNAB_BUDGET_ID')
API_TOKEN =         os.getenv('YNAB_API_TOKEN')

if __name__ == '__main__':
  start_http_server(8000)

  # Define needed gauges
  budgeted_gauge = Gauge('category_budgeted', 'Money budgeted per category', ['id'], namespace = NAMESPACE)
  activity_gauge = Gauge('category_activity', 'Money activity per category', ['id'], namespace = NAMESPACE)
  balance_gauge  = Gauge('category_balance',  'Money activity per category', ['id'], namespace = NAMESPACE)
  metadata_gauge = Gauge('category_metadata', 'Metadata about this category, including name', ['id', 'name', 'hidden', 'group_id'], namespace = NAMESPACE)
  group_metadata_gauge = Gauge('category_group_metadata', 'Metadata about this category, including name', ['id', 'name', 'hidden'], namespace = NAMESPACE)

  while True:
    print('Pulling data and populating gauges')
    raw_categories = pull_raw_categories_object(BUDGET_ID, API_TOKEN)
    process_raw_categories(raw_categories, budgeted_gauge, activity_gauge, balance_gauge, metadata_gauge, group_metadata_gauge)
    time.sleep(REFRESH_TIME_SECS)
    print('Clearing gauges')
    clear_gauges(raw_categories, budgeted_gauge, activity_gauge, balance_gauge, metadata_gauge, group_metadata_gauge)

"""
 ReportGeneratorConfig.py -- The configuration file for the Appfigures/Zendesk report generation script

 Copyright (C) 2017 Brandon Hurley

 This software may be modified and distributed under the terms
 of the MIT license.  See the LICENSE file for details.
 """

# Use these variables to toggle which report gets generated
generate_appfigures_report = False
generate_zendesk_report = False

# OAuth specific variables
base_url = "https://api.appfigures.com/v2"
client_key = ""
client_secret = ""

request_token_url = base_url + "/oauth/request_token"
authorize_url = base_url + "/oauth/authorize"
access_token_url = base_url + "/oauth/access_token"

oauth_access_token = ""
oauth_access_token_secret = ""
access_token_length = 16 # Do not change this value unless OAuth access token format is updated

# Variables required to connect to the MySQL database
database_ip = "localhost"
database_user = ""
database_password = ""

# Variables for naming the database and associated tables. All names must be MySQL compatible
database_name = "mobileappsreport"
database_table_appfigures = "appfiguresdata"
database_table_zendesk = "zendeskdata"

# Appfigures specific variables
starting_year = 2011

# Zendesk specific variables
zen_url = "https://your_domain_here.zendesk.com/api/v2/ticket_metrics.json?page=1"
zen_user = "email@example.com" + "/token"
zen_password = ""

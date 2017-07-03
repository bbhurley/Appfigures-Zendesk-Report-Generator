#!/usr/bin/env python3.6
"""
 ReportGeneratorMain.py -- The main logical component of the Appfigures/Zendesk report generation script

 Copyright (C) 2017 Brandon Hurley

 This software may be modified and distributed under the terms
 of the MIT license.  See the LICENSE file for details.
 """

import datetime
import os
import sys

import pymysql
import requests
from rauth import OAuth1Session, OAuth1Service

import ReportGeneratorConfig as config


# get_service function
# Pre-made OAuth function part of an AppFigures code sample
# http://docs.appfigures.com/code-samples
def get_service():
    """ Returns an OAuthService configured for us """
    return OAuth1Service(name="appfigures",
                         consumer_key=config.client_key,
                         consumer_secret=config.client_secret,
                         request_token_url=config.request_token_url,
                         access_token_url=config.access_token_url,
                         authorize_url=config.authorize_url,
                         base_url=config.base_url)


# get_session function
# Pre-made OAuth function part of an AppFigures code sample
# http://docs.appfigures.com/code-samples
def get_session(access_token=config.oauth_access_token, access_token_secret=config.oauth_access_token_secret):
    """If access_token and secret are given, create and return a session.

        If they are not given, go through the authorization process
        interactively and return the new session
    """
    oauth = get_service()

    if access_token and access_token_secret \
            and len(access_token) == config.access_token_length and len(
        access_token_secret) == config.access_token_length:
        session = OAuth1Session(config.client_key, config.client_secret,
                                access_token, access_token_secret,
                                service=oauth)
        return session

    params = {"oauth_callback": "oob"}
    headers = {'X-OAuth-Scope': 'private:read,products:read'}
    request_token, request_token_secret = oauth.get_request_token(
        params=params,
        headers=headers
    )

    authorization_url = oauth.get_authorize_url(request_token)
    print("Go here: %s to get your verification token."
          % authorization_url)
    verifier = input("Paste verifier here: ")
    session = oauth.get_auth_session(request_token,
                                     request_token_secret,
                                     "POST",
                                     data={"oauth_verifier": verifier})
    print("Access Token: %s\tAccess Secret:%s"
          % (session.access_token, session.access_token_secret))

    return session


class ReportGenerator:
    def __init__(self):
        # Connect to the database
        try:
            self.connection = pymysql.connect(host=config.database_ip,
                                              user=config.database_user,
                                              password=config.database_password)
            self.connection.set_charset('utf8')
            self.cursor = self.connection.cursor()
            self.cursor.execute("CREATE DATABASE IF NOT EXISTS " + config.database_name)
            self.cursor.execute("USE " + config.database_name)
            self.cursor.execute("DROP TABLE IF EXISTS " + config.database_table_appfigures)
            self.cursor.execute("DROP TABLE IF EXISTS " + config.database_table_zendesk)
            self.connection.commit()
        except:
            print("Something went wrong while trying to connect to the database!")
            print("Make sure the host, username, and password settings are correct.")
            exit(1)

    # get_product_details function
    # Populates 2 input lists with product names and store platform
    # Required as a separate API response is required by AppFigures to get detailed info
    @staticmethod
    def get_product_details(raw_data, product_names_list, product_platforms_list):
        for (id, product) in raw_data:
            product_details = product["product"]
            product_names_list[product_details["id"]] = product_details["name"]
            product_platforms_list[product_details["id"]] = product_details["store"]

    # add_appfigures_batch_to_database function
    # Adds the requested data from AppFigures and places them into the given database
    # Data is added to the database in weekly batches
    def add_appfigures_batch_to_database(self, raw_data, current_row,
                                         product_names, product_platforms, appfigures_header):
        for (week_of, product_list) in raw_data:
            for product in product_list:
                product_details = product_list[product]
                product_id = product_details["product_id"]
                raw_row_values = [current_row, product_id, str(product_names[product_id]),
                                  str(product_platforms[product_id]),
                                  int(product_details["downloads"]), int(product_details["net_downloads"]),
                                  int(product_details["updates"]), str(week_of), str(config.starting_year)]
                try:
                    sql = """INSERT INTO {table} ({columns}) VALUES ({values})""".format(
                        table=config.database_table_appfigures, columns=",".join(appfigures_header).lower(),
                        values=raw_row_values)
                    sql = sql.translate({ord(c): None for c in '[]'})
                    self.cursor.execute(sql)
                except:
                    print("There was an issue adding in data to the Appfigures table. Aborting...")
                    exit(1)
                current_row += 1
                # print(str(current_row))
            self.connection.commit()
        return current_row

    # generate_appfigures_report
    # Generates a MySQL table with information pulled from the Appfigures API
    def generate_appfigures_report(self):
        print("Generating Appfigures report...")
        # Sets up the OAuth session
        self.current_session = get_session()
        current_row = 1
        try:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS {table}(
                                        ID INT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                                        Product_ID BIGINT,
                                        Name TEXT,
                                        App_Platform TEXT,
                                        Weekly_Downloads INT,
                                        Net_Downloads INT,
                                        Updates INT,
                                        Week_Of DATE,
                                        Year_Of INT) 
                                        DEFAULT CHARSET=utf8 COLLATE=utf8_bin AUTO_INCREMENT=1""".format(
                table=config.database_table_appfigures))
            self.connection.commit()
        except:
            print("The Appfigures table could not be generated. Aborting...")
            return
        # Get the product details separately from the main API call
        product_detail_response = self.current_session.get(config.base_url + "/reports/sales/",
                                                           params=dict(group_by="product", format="json"))
        product_names = dict()
        product_platforms = dict()
        self.get_product_details(product_detail_response.json().items(), product_names, product_platforms)

        self.cursor.execute("SHOW columns FROM " + config.database_table_appfigures)
        appfigures_header = [column[0] for column in self.cursor.fetchall()]

        while 1:
            if config.starting_year != datetime.date.today().year:
                resp = self.current_session.get(config.base_url + "/reports/sales/",
                                                params=dict(group_by="date,product", granularity="weekly",
                                                            start_date=str(config.starting_year) + "-01-01",
                                                            end_date=str(config.starting_year) + "-12-31",
                                                            format="json"))
            else:
                resp = self.current_session.get(config.base_url + "/reports/sales/",
                                                params=dict(group_by="date,product", granularity="weekly",
                                                            start_date=str(config.starting_year) + "-01-01",
                                                            end_date=datetime.date.today(), format="json"))
            output = resp.json().items()
            current_row = self.add_appfigures_batch_to_database(output, current_row,
                                                                product_names, product_platforms,
                                                                appfigures_header)
            # print("The row is: " + str(self.current_row))
            if config.starting_year == datetime.date.today().year:
                break
            config.starting_year += 1

        print("Finished generating Appfigures report")

    # generate_zendesk_report
    # Generates a MySQL table with information pulled from the Zendesk API
    def generate_zendesk_report(self):
        print("Generating Zendesk report...")
        try:
            self.cursor.execute("""CREATE TABLE IF NOT EXISTS {table}(
                                                ID BIGINT NOT NULL AUTO_INCREMENT PRIMARY KEY,
                                                Ticket_ID BIGINT,
                                                Created_At TEXT,
                                                Updated_At TEXT,
                                                Url TEXT,
                                                Group_Stations INT,
                                                Reopens INT,
                                                Replies INT,
                                                Assignee_Updated_At TEXT,
                                                Requester_Updated_At TEXT,
                                                Status_Updated_At TEXT,
                                                Initially_Assigned_At TEXT,
                                                Assigned_At TEXT,
                                                Solved_At TEXT,
                                                Latest_Comment_Added_At TEXT,
                                                First_Resolution_Time_In_Minutes_Calendar INT,
                                                First_Resolution_Time_In_Minutes_Business INT,
                                                Reply_Time_In_Minutes_Calendar INT,
                                                Reply_Time_In_Minutes_Business INT,
                                                Full_Resolution_Time_In_Minutes_Calendar INT,
                                                Full_Resolution_Time_In_Minutes_Business INT,
                                                Agent_Wait_Time_In_Minutes_Calendar INT,
                                                Agent_Wait_Time_In_Minutes_Business INT,
                                                Requester_Wait_Time_In_Minutes_Calendar INT,
                                                Requester_Wait_Time_In_Minutes_Business INT) 
                                                DEFAULT CHARSET=utf8 COLLATE=utf8_bin AUTO_INCREMENT=1""".format(
                table=config.database_table_zendesk))
            self.connection.commit()
        except:
            print("The Zendesk table could not be generated. Aborting...")
            return

        # Set the request parameters
        data = self.get_zendesk_data()

        self.cursor.execute("SHOW columns FROM " + config.database_table_zendesk)
        zen_header = [column[0] for column in self.cursor.fetchall()]

        current_row = 1

        while 1:
            # Get page of tickets
            ticket_list = list(data)[0][1]
            for ticket in ticket_list:
                # Compare against total count variable in data dictionary
                if current_row == list(data)[3][1]:
                    break
                zen_values = [ticket["id"], ticket["ticket_id"], ticket["created_at"], ticket["updated_at"],
                              ticket["url"],
                              ticket["group_stations"], ticket["reopens"], ticket["replies"],
                              ticket["assignee_updated_at"],
                              ticket["requester_updated_at"], ticket["status_updated_at"],
                              ticket["initially_assigned_at"],
                              ticket["assigned_at"], ticket["solved_at"], ticket["latest_comment_added_at"],
                              ticket["first_resolution_time_in_minutes"]["calendar"],
                              ticket["first_resolution_time_in_minutes"]["business"],
                              ticket["reply_time_in_minutes"]["calendar"],
                              ticket["reply_time_in_minutes"]["business"],
                              ticket["full_resolution_time_in_minutes"]["calendar"],
                              ticket["full_resolution_time_in_minutes"]["business"],
                              ticket["agent_wait_time_in_minutes"]["calendar"],
                              ticket["agent_wait_time_in_minutes"]["business"],
                              ticket["requester_wait_time_in_minutes"]["calendar"],
                              ticket["requester_wait_time_in_minutes"]["business"]]

                # To prevent null values from entering the table
                for i in range(len(zen_values)):
                    if zen_values[i] is None:
                        zen_values[i] = 0
                try:
                    sql = """INSERT INTO {table} ({columns}) VALUES ({values})""".format(
                        table=config.database_table_zendesk, columns=",".join(zen_header).lower(), values=zen_values)
                    sql = sql.translate({ord(c): None for c in '[]'})
                    self.cursor.execute(sql)
                    self.connection.commit()
                except:
                    print("There was an issue adding in data to the Zendesk table. Aborting...")
                    exit(1)
                # print(current_row)
                current_row += 1
            # Compare against total count variable in data dictionary
            if current_row == list(data)[3][1]:
                break
            config.zen_url = list(data)[1][1]
            data = self.get_zendesk_data()
        print("Finished generating Zendesk report")

    # get_zendesk_data function
    # Pulls the raw data from the Zendesk API and returns a Python readable version of the items
    @staticmethod
    def get_zendesk_data():
        # Do the HTTP get request
        response = requests.get(config.zen_url, auth=(config.zen_user, config.zen_password))

        # Check for HTTP codes other than 200
        if response.status_code != 200:
            print("Status:", response.status_code, "Problem with the request. Exiting.")
            exit()

        # Decode the JSON response into a dictionary and use the data
        return response.json().items()


# Main program function
if __name__ == "__main__":
    os.chdir(os.path.dirname(sys.argv[0]))
    if not config.database_ip:
        print("The MySQL IP address is missing! Please make sure it has been added to the config file.")
        exit(0)
    if not config.database_user:
        print("The MySQL username is missing! Please make sure it has been added to the config file.")
        exit(0)
    if not config.database_password:
        print("The MySQL user password is missing! Please make sure it has been added to the config file.")
        exit(0)
    if not config.database_name:
        print("The MySQL database name is missing! Please make sure it has been added to the config file.")
        exit(0)
    if not config.database_table_appfigures:
        print("The Appfigures MySQL table name is missing! Please make sure it has been added to the config file.")
        exit(0)
    if not config.database_table_zendesk:
        print("The Zendesk MySQL table name is missing! Please make sure it has been added to the config file.")
        exit(0)
    app = ReportGenerator()
    if config.generate_appfigures_report:
        if not config.client_key:
            print("The Appfigures API client key is missing! Please make sure it has been added to the config file.")
            exit(0)
        if not config.client_secret:
            print("The Appfigures API secret key is missing! Please make sure it has been added to the config file.")
            exit(0)
        app.generate_appfigures_report()
    if config.generate_zendesk_report:
        if "your_domain_here" in config.zen_url:
            print(
                "The Zendesk API URL needs to be changed from the default! Please make sure that the URL domain has been changed in the config file.")
            exit(0)
        if "email@example.com" in config.zen_user:
            print(
                "The Zendesk username needs to be changed from the default! Please make sure that the email login has been changed in the config file.")
            exit(0)
        if not config.zen_password:
            print(
                "The Zendesk API password/access token is missing! Please make sure it has been added to the config file.")
            exit(0)
        app.generate_zendesk_report()
    app.connection.close()

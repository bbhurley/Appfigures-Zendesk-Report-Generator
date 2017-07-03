# Appfigures/Zendesk Report Generator
A Python 3 script that can generate MySQL tables that contain general app statictics ([Appfigures](https://appfigures.com/)) and support ticket metrics ([Zendesk](https://www.zendesk.com/))

## Getting Started

### Prerequisites
* Python 3.6.1 or newer, with pip
* MySQL 5.7.18

The following Python libraries need to be installed (minimum verson required):
* Rauth 0.7.3
* Requests 2.18.1
* PyMySQL 0.7.11

### Installing

#### Part 1:
1) Ensure that Python 3.6.1, MySQL 5.7.18, and pip for Python 3.6 are installed and set up on the machine.
2) Download the repository and extract the contents to the folder where the script will run (ex. **Report_Gen**).
3) In the command-line/terminal, go to the script folder and enter `python3.6 -m pip install -r requirements.txt`. This will automatically install the needed libraries.

#### Part 2:
1) Open the **ReportGeneratorConfig** file with a text editor of your choice.
2) A couple of variables and flags need to be configured in order for the script to work. At a minimum, the following variables need to be set:
    * **generate_appfigures_report**
    * **generate_zendesk_report**
    * **client_key** (Appfigures report only)
    * **client_secret** (Appfigures report only)
    * **database_ip**
    * **database_name**
    * **database_password**
    * **starting_year** (Appfigures report only)
    * **zen_url** (Zendesk report only)
    * **zen_user** (Zendesk report only)
    * **zen_password** (Zendesk report only)
* Full details about the configuration file variables can be found under **Configuration file options**.
3) Run the script with `python3.6 ./ReportGeneratorMain.py` (or `python ./ReportGeneratorMain.py` if Python 3.6 is set as the default version) and follow the on-screen instructions.
4) (Optional) Make the script executable with `chmod +x ReportGeneratorMain.py`.

### Part 3: (Optional, Appfigures report only)
At this point, the script can run on a manual basis just fine, but it's intended to run as an automated service. A little bit of extra work will make it possible to automate with scheduling tools like [Cron](https://help.ubuntu.com/community/CronHowto).

1) When the script runs, a verification token will be required. Go to the given URL and follow the instructions.
2) After giving the token, the script will print out the OAuth access token and secret access token. Copy and paste these values into the **oauth_access_token** and **oauth_access_token_secret** config variables respectively.
3) Save the changes made to the file. The script will now run without having to verify the session again.

#### Example use: Google Data Studio data source
1) Make sure the script is properly installed as per the above instructions and the computer has a network connection.
	* Pertaining to this, also make sure that MySQL can be accessed remotely over SSH and SSL.
2) (Optional) Automate the script to ensure up to date data for the data source.
3) Login to Google Data Studio and create a new data source.
4) Under **Connectors**, select **MySQL**.
5) Enter in the external IP address of the computer with the MySQL setup, along with the name of the database the tables are in, and a 
   MySQL username/password combo which is set up for remote connections (only read access to the script-generated database is required)
6) Enable SSL connectivity and upload the required certificate files (see the [official MySQL documentation](https://dev.mysql.com/doc/refman/5.7/en/creating-ssl-rsa-files.html) for details).
7) Once the connection has been confirmed, choose the table to be used in the data source.

## Configuration file options
The following options can be found in the **ReportGeneratorConfig** file:
* **generate_appfigures_report**: A boolean flag to tell the script to generate the Appfigures table. Set by default to *False*.
* **generate_zendesk_report**: A boolean flag to tell the script to generate the Zendesk table. Set by default to *False*.
* **base_url**: A string that holds the base URL for the Appfigures API. Should not be modified unless Appfigures changes their URL structure.
* **client_key**: A string that holds the Appfigures API client key for your app. Required to access the Appfigures API. 
			To get a key, create an API Client instance at https://appfigures.com/developers/keys and copy/paste the **Client Key** string from the client detail screen into this variable.
* **client_secret**: A string that holds the Appfigures API secret key for your app. Required to access the Appfigures API. 
			To get a key, create an API Client instance at https://appfigures.com/developers/keys (or use the client that was created for the previous variable) and copy/paste the **Secret Key** string from the client detail screen into this variable.
* **request_token_url**: A string that holds the Appfigures URL to request a token. Should not be modified unless Appfigures changes their URL structure.
* **authorize_url**: A string that holds the Appfigures URL for authorization. Should not be modified unless Appfigures changes their URL structure.
* **access_token_url**: A string that holds the Appfigures URL to recieve access tokens. Should not be modified unless Appfigures changes their URL structure.
* **oauth_access_token**: A string that hold the OAuth access token for Appfigures. See Part 3 of the installation guide on how to set this variable properly.
* **oauth_access_token_secret**: A string that hold the OAuth secret access token for Appfigures. See Part 3 of the installation guide on how to set this variable properly.
* **access_token_length**: An integer that holds the total number of characters expected in an OAuth access token. Used as part of error checking and should not be changed.
* **database_name**: A string that holds the name of the MySQL database the script will create. Set by default to *mobileappsreport*.
* **database_table_appfigures**: A string that holds the name of the MySQL Appfigures table. Set by default to *appfiguresdata*.
* **database_table_zendesk**: A string that holds the name of the MySQL Zendesk table. Set by default to *zendeskdata*.
* **database_ip**: A string that holds an IPv4 address for the database. Set by default to *localhost* (i.e. the computer currently running the script).
* **database_user**: A string that holds the MySQL username that the script will use to access the server. It is assumed that the user is properly set up in MySQL and has read/write access (in order to create the database and tables needed).
* **database_password**: A string that holds the password for the MySQL user being used by the script.
* **starting_year**: An integer that holds the year that the Appfigures report generator should start at. Set by default to *2011*
* **zen_url**: A string that holds the Zendesk ticket metrics URL. Only the domain component of the URL should be modified.
* **zen_user**: A string that holds the Zendesk username that the script will use to access the Zendesk API. Only the e-mail component of the variable should be modified.
* **zen_password**: A string that holds the Zendesk API token associated with the script. Required to access the Zendesk API. See the **API token** authentication method in the [official Zendesk API documentation](https://developer.zendesk.com/rest_api/docs/core/introduction#security-and-authentication) for details.

## Created By
* **Brandon Hurley** - [bbhurley](https://github.com/bbhurley)

## License
This project is licensed under the MIT License - see the [LICENSE.md](LICENSE.md) file for details

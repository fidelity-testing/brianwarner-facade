#!/usr/bin/python

# Copyright 2016-2017 Brian Warner
#
# This file is part of Facade, and is made available under the terms of the GNU
# General Public License version 2.
# SPDX-License-Identifier:        GPL-2.0
#
# Create all tables, and initialize the settings table with default values.

import sys
import os.path
import MySQLdb
import getpass
import imp
import bcrypt
from string import Template
import string
import random

#### Settings table ####

def create_settings(reset=0):

# Create and populate the default settings table.

	# default settings
	start_date = "2014-01-01";
	repo_directory = "/opt/facade/git-trees/";

	if reset:
		clear = "DROP TABLE IF EXISTS settings"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS settings ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"setting VARCHAR(32) NOT NULL,"
		"value VARCHAR(128) NOT NULL,"
		"last_modified TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6))")

	cursor.execute(create)
	db.commit()

	initialize = ("INSERT INTO settings (setting,value) VALUES"
		"('start_date','%s'),"
		"('repo_directory','%s'),"
		"('utility_status','Idle'),"
		"('log_level','Quiet'),"
		"('report_date','committer'),"
		"('report_attribution','author'),"
		"('working_author','done')"
		% (start_date,repo_directory))

	cursor.execute(initialize)
	db.commit()

	print "Settings table created."

#### Log tables ####

def create_repos_fetch_log(reset=0):

# A new entry is logged every time a repo update is attempted

	if reset:
		clear = "DROP TABLE IF EXISTS repos_fetch_log"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS repos_fetch_log ("
		"repos_id INT UNSIGNED NOT NULL,"
		"status VARCHAR(128) NOT NULL,"
		"date TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6))")

	cursor.execute(create)
	db.commit()

def create_analysis_log(reset=0):

# Log the analysis for each repo

	if reset:
		clear = "DROP TABLE IF EXISTS analysis_log"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS analysis_log ("
		"repos_id INT UNSIGNED NOT NULL,"
		"status VARCHAR(128) NOT NULL,"
		"date_attempted TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6))")

	cursor.execute(create)
	db.commit()

def create_utility_log(reset=0):

# Create the table that will track the state of the utility script that
# maintains repos and does the analysis.

	if reset:
		clear = "DROP TABLE IF EXISTS utility_log"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS utility_log ("
		"id BIGINT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"level VARCHAR(8) NOT NULL,"
		"status VARCHAR(128) NOT NULL,"
		"attempted TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6))")

	cursor.execute(create)
	db.commit()

#### Project and repo tables ####

def create_projects(reset=0):

# Create the table that tracks high level project descriptions

	if reset:
		clear = "DROP TABLE IF EXISTS projects"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS projects ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"name VARCHAR(128) NOT NULL,"
		"description VARCHAR(256),"
		"website VARCHAR(128),"
		"last_modified TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6))")

	cursor.execute(create)
	db.commit()

def create_repos(reset=0):

# Each project could have multiple repos. When a new repo is added, "status"
# will be set to "New" so that the first action is a git clone.  When it
# succeeds, "status" will be set to "Active" so that subsequent updates use git
# pull. When a repo is deleted, status will be set to "Delete" and it will be
# cleared the next time repo-management.py runs.

	if reset:
		clear = "DROP TABLE IF EXISTS repos"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS repos ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"projects_id INT UNSIGNED NOT NULL,"
		"git VARCHAR(256) NOT NULL,"
		"path VARCHAR(256),"
		"name VARCHAR(256),"
		"added TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6),"
		"status VARCHAR(32) NOT NULL,"
		"working_commit VARCHAR(40))")

	cursor.execute(create)
	db.commit()

#### Affiliation tables ####

def create_affiliations(reset=0):

# Track which domains/emails should be associated with what organizations. Also
# populate table with some sample entries.

	if reset:
		clear = "DROP TABLE IF EXISTS affiliations"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS affiliations ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"domain VARCHAR (64) NOT NULL,"
		"affiliation VARCHAR (64) NOT NULL,"
		"start_date DATE NOT NULL DEFAULT '1970-01-01',"
		"UNIQUE (domain,affiliation,start_date))")

	cursor.execute(create)
	db.commit()

	if reset:
		populate = ("INSERT INTO affiliations(domain,affiliation) VALUES "
			"('samsung.com','Samsung'),"
			"('linuxfoundation.org','Linux Foundation'),"
			"('ibm.com','IBM'),"
			"('brian@bdwarner.com','(Hobbyist)')")

		cursor.execute(populate)
		db.commit()

		populate = ("INSERT INTO affiliations(domain,affiliation,start_date) VALUES "
			"('brian@bdwarner.com','Samsung','2015-07-05'),"
			"('brian@bdwarner.com','The Linux Foundation','2011-01-06'),"
			"('brian@bdwarner.com','IBM','2006-05-20')")

		cursor.execute(populate)
		db.commit()

def create_aliases(reset=0):

# Store aliases to reduce individuals to one identity, and populate table with
# sample entries

	if reset:
		clear = "DROP TABLE IF EXISTS aliases"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS aliases ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"canonical VARCHAR(128) NOT NULL,"
		"alias VARCHAR(128) NOT NULL,"
		"UNIQUE (canonical,alias))")

	cursor.execute(create)
	db.commit()

	if reset:
		populate = ("INSERT INTO aliases (canonical,alias) VALUES "
			"('brian@bdwarner.com','brian.warner@samsung.com'),"
			"('brian@bdwarner.com','brian.warner@linuxfoundation.org'),"
			"('brian@bdwarner.com','bdwarner@us.ibm.com')")

		cursor.execute(populate)
		db.commit()

def create_excludes(reset=0):

# Create the table that will track what should be ignored.

	if reset:
		clear = "DROP TABLE IF EXISTS exclude"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS exclude ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"projects_id INT UNSIGNED NOT NULL,"
		"email VARCHAR(128),"
		"domain VARCHAR(128))")

	cursor.execute(create)
	db.commit()

def create_special_tags(reset=0):

# Entries in this table are matched against email addresses found during
# analysis categorize subsets of people.  For example, people who worked for a
# certain organization who should be categorized separately, to benchmark
# performance against the rest of a company.

	if reset:
		clear = "DROP TABLE IF EXISTS special_tags"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS special_tags ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"email VARCHAR(128) NOT NULL,"
		"start_date DATE NOT NULL,"
		"end_date DATE,"
		"tag VARCHAR(64) NOT NULL,"
		"UNIQUE (email,start_date,end_date,tag))")

	cursor.execute(create)
	db.commit()

#### Analysis tables ####

def create_analysis(reset=0):

# Analysis data

	if reset:
		clear = "DROP TABLE IF EXISTS analysis_data"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS analysis_data ("
		"repos_id INT UNSIGNED NOT NULL,"
		"commit VARCHAR(40) NOT NULL,"
		"author_name VARCHAR(128) NOT NULL,"
		"author_email VARCHAR(128) NOT NULL,"
		"author_date VARCHAR(10) NOT NULL,"
		"author_affiliation VARCHAR(128),"
		"committer_name VARCHAR(128) NOT NULL,"
		"committer_email VARCHAR(128) NOT NULL,"
		"committer_date VARCHAR(10) NOT NULL,"
		"committer_affiliation VARCHAR(128),"
		"added INT UNSIGNED NOT NULL,"
		"removed INT UNSIGNED NOT NULL,"
		"whitespace INT UNSIGNED NOT NULL,"
		"filename VARCHAR(4096) NOT NULL,"
		"date_attempted TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6))")

	cursor.execute(create)
	db.commit()

#### Cache tables ####

def create_unknown_caches(reset=0):

# After each facade-worker run, any unknown contributors and their email domain
# are cached in this table to make them easier to fetch later.

	if reset:
		clear = "DROP TABLE IF EXISTS unknown_cache"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS unknown_cache ("
		"type VARCHAR(10) NOT NULL,"
		"projects_id INT UNSIGNED NOT NULL,"
		"email VARCHAR(128) NOT NULL,"
		"domain VARCHAR(128),"
		"added BIGINT UNSIGNED NOT NULL)")

	cursor.execute(create)
	db.commit()

def create_web_caches(reset=0):

# After each facade-worker run, cache results used in summary tables to decrease
# load times when the database gets large. Also enables a read-only kiosk mode.
# Must store separate data for monthly and annual data because while you can
# easily add monthly LoC and patch data and get meaningful annual stats,
# contributors can't be added across months to get to total annual number.

	# Monthly caches by project

	if reset:
		clear = "DROP TABLE IF EXISTS project_monthly_cache"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS project_monthly_cache ("
		"projects_id INT UNSIGNED NOT NULL,"
		"email VARCHAR(128) NOT NULL,"
		"affiliation VARCHAR(128),"
		"month TINYINT UNSIGNED NOT NULL,"
		"year SMALLINT UNSIGNED NOT NULL,"
		"added BIGINT UNSIGNED NOT NULL,"
		"removed BIGINT UNSIGNED NOT NULL,"
		"whitespace BIGINT UNSIGNED NOT NULL,"
		"files BIGINT UNSIGNED NOT NULL,"
		"patches BIGINT UNSIGNED NOT NULL)")

	cursor.execute(create)
	db.commit()

	# Annual caches by project

	if reset:
		clear = "DROP TABLE IF EXISTS project_annual_cache"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS project_annual_cache ("
		"projects_id INT UNSIGNED NOT NULL,"
		"email VARCHAR(128) NOT NULL,"
		"affiliation VARCHAR(128),"
		"year SMALLINT UNSIGNED NOT NULL,"
		"added BIGINT UNSIGNED NOT NULL,"
		"removed BIGINT UNSIGNED NOT NULL,"
		"whitespace BIGINT UNSIGNED NOT NULL,"
		"files BIGINT UNSIGNED NOT NULL,"
		"patches BIGINT UNSIGNED NOT NULL)")

	cursor.execute(create)
	db.commit()

	# Monthly caches by repo

	if reset:
		clear = "DROP TABLE IF EXISTS repo_monthly_cache"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS repo_monthly_cache ("
		"repos_id INT UNSIGNED NOT NULL,"
		"email VARCHAR(128) NOT NULL,"
		"affiliation VARCHAR(128),"
		"month TINYINT UNSIGNED NOT NULL,"
		"year SMALLINT UNSIGNED NOT NULL,"
		"added BIGINT UNSIGNED NOT NULL,"
		"removed BIGINT UNSIGNED NOT NULL,"
		"whitespace BIGINT UNSIGNED NOT NULL,"
		"files BIGINT UNSIGNED NOT NULL,"
		"patches BIGINT UNSIGNED NOT NULL)")

	cursor.execute(create)
	db.commit()

	# Annual caches by repo

	if reset:
		clear = "DROP TABLE IF EXISTS repo_annual_cache"

		cursor.execute(clear)
		db.commit()

	create = ("CREATE TABLE IF NOT EXISTS repo_annual_cache ("
		"repos_id INT UNSIGNED NOT NULL,"
		"email VARCHAR(128) NOT NULL,"
		"affiliation VARCHAR(128),"
		"year SMALLINT UNSIGNED NOT NULL,"
		"added BIGINT UNSIGNED NOT NULL,"
		"removed BIGINT UNSIGNED NOT NULL,"
		"whitespace BIGINT UNSIGNED NOT NULL,"
		"files BIGINT UNSIGNED NOT NULL,"
		"patches BIGINT UNSIGNED NOT NULL)")

	cursor.execute(create)
	db.commit()

#### Authentication tables ####

def create_auth(reset=0):

# These are used for basic user authentication and account history.

	if reset:
		clear = "DROP TABLE IF EXISTS auth"

		cursor.execute(clear)
		db.commit()

		clear = "DROP TABLE IF EXISTS auth_history"

		cursor.execute(clear)
		db.commit()


	create = ("CREATE TABLE IF NOT EXISTS auth ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"user VARCHAR(64) UNIQUE NOT NULL,"
		"email VARCHAR(128) NOT NULL,"
		"password VARCHAR(64) NOT NULL,"
		"created TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6),"
		"last_modified TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6))")

	cursor.execute(create)
	db.commit()

	create = ("CREATE TABLE IF NOT EXISTS auth_history ("
		"id INT UNSIGNED AUTO_INCREMENT PRIMARY KEY,"
		"user VARCHAR(64) NOT NULL,"
		"status VARCHAR(96) NOT NULL,"
		"attempted TIMESTAMP(6) DEFAULT CURRENT_TIMESTAMP(6) ON UPDATE CURRENT_TIMESTAMP(6))")

	cursor.execute(create)
	db.commit()

	user = ''
	email = ''
	hashed = ''

	print "Setting administrator credentials.\n"

	while not user:
		user = raw_input(' User: ').strip()

	while not email:
		email = raw_input(' Email: ').strip()

	while not hashed:
		password = ''
		conf_password = ''

		while not password:
			password = getpass.getpass(' Password: ').strip()

		while not conf_password:
			conf_password = getpass.getpass(' Confirm password: ').strip()

		if password == conf_password:
			hashed = bcrypt.hashpw(password,bcrypt.gensalt())
		else:
			print "Passwords do not match.\n"

	query = ("INSERT INTO auth (user,email,password)"
		"VALUES ('%s','%s','%s')" % (user,email,hashed))

	cursor.execute(query)
	db.commit()

	query = ("INSERT INTO auth_history (user,status)"
		"VALUES ('%s','Created')" % user)

	cursor.execute(query)
	db.commit()

# ==== The real program starts here ==== #

# First make sure the database files have been setup

working_dir = os.path.dirname(os.path.abspath(__file__))

print ("========== Facade database setup  ==========\n\n"
	"What do you want to do?\n"
	" (C)reate database config files and initialize tables. Optionally create database and user.\n"
	" (I)nitialize tables only. This will clear any existing data.\n"
	" (U)pdate database while preserving settings, projects, and repos.\n")

action = raw_input('(c/i/u): ').strip()

if action.lower() == 'c':

	print ("========== Creating database credential files ==========\n\n"
		"This will overwrite your existing db.py and creds.php files.\n"
		"Are you sure?\n")

	confirm_creds = raw_input('(yes): ').strip()

	if confirm_creds.lower() == 'yes':

		print "\n===== Facade user information =====\n"

		db_user = raw_input('Facade username (leave blank for random): ').strip()
		db_pass = getpass.getpass('Facade password (leave blank for random): ').strip()

		if not db_user:
			db_user = ''.join((random.choice(string.letters+string.digits)) for x in range(16))

		if not db_pass:
			db_pass = ''.join((random.choice(string.letters+string.digits)) for x in range(16))

		print "\n===== Database information =====\n"

		db_host = raw_input('Database host (default: localhost): ').strip()

		if not db_host:
			db_host = 'localhost'

		db_name = raw_input('Database name (leave blank for random): ').strip()

		if not db_name:
			db_name = 'facade_'+''.join((random.choice(string.letters+string.digits)) for x in range(16))

		print ("\nShould Facade create the database? (requires root, "
			"not needed if the database already exists)\n")

		create_db = raw_input('(yes): ').strip()

		if create_db.lower() == 'yes':

			root_pw = getpass.getpass('mysql root password: ').strip()

			try:

				root_db = MySQLdb.connect( host=db_host,
					user = 'root',
					passwd = root_pw,
					charset='utf8mb4')
				root_cursor = root_db.cursor(MySQLdb.cursors.DictCursor)

			except:

				print 'Could not connect to database as root'
				sys.exit(1)

			try:

				create_database = ("CREATE DATABASE %s "
					"CHARACTER SET utf8mb4 COLLATE utf8mb4_unicode_ci"
					% db_name)

				root_cursor.execute(create_database)
				root_db.commit()

			except:

				print 'Could not create database: %s' % db_name
				sys.exit(1)

			try:

				create_user = ("CREATE USER '%s' IDENTIFIED BY '%s'"
					% (db_user,db_pass))

				root_cursor.execute(create_user)
				root_db.commit()

				grant_privileges = ("GRANT ALL PRIVILEGES ON %s.* to %s"
					% (db_name,db_user))

				root_cursor.execute(grant_privileges)
				root_db.commit()

				flush_privileges = ("FLUSH PRIVILEGES")

				root_cursor.execute(flush_privileges)
				root_db.commit()

			except:

				print 'Could not create user and grant privileges: %s' % db_user
				sys.exit(1)

			root_cursor.close()
			root_db.close()

		db_values = {'db_user': db_user,
			'db_pass': db_pass,
			'db_name': db_name,
			'db_host': db_host}

		db_py_template_loc = os.path.join(working_dir,'db.py.template')
		db_py_loc = os.path.join(working_dir,'db.py')
		creds_php_template_loc = os.path.join(working_dir,'../includes/creds.php.template')
		creds_php_loc = os.path.join(working_dir,'../includes/creds.php')

		db_py_template = string.Template(open(db_py_template_loc).read())

		db_py_file = open(db_py_loc,'w')
		db_py_file.write(db_py_template.substitute(db_values))
		db_py_file.close()

		creds_php_template = string.Template(open(creds_php_template_loc).read())

		creds_php_file = open(creds_php_loc,'w')
		creds_php_file.write(creds_php_template.substitute(db_values))
		creds_php_file.close()

		print '\nDatabase setup complete\n'

try:
    imp.find_module('db')
    from db import db,cursor
except:
    sys.exit("Can't find db.py.")

if action.lower() == 'i' or action.lower() == 'c':

	print ("========== Initializing database tables ==========\n\n"
		"This will set up your tables, and will clear any existing data.\n"
		"Are you sure?\n")

	confirm = raw_input('(yes): ')

	if confirm == "yes":
		print "Setting up database tables."

		create_settings('clear')

		create_repos_fetch_log('clear')
		create_analysis_log('clear')
		create_utility_log('clear')

		create_projects('clear')
		create_repos('clear')

		create_affiliations('clear')
		create_aliases('clear')
		create_excludes('clear')
		create_special_tags('clear')

		create_analysis('clear')

		create_unknown_caches('clear')
		create_web_caches('clear')

		create_auth('clear')

	else:
		print "Exiting without doing anything."

elif action.lower() == 'u':

	print ("========== Updating database tables ==========\n\n"
		"This will attempt to add database tables while preserving your major settings.\n"
		"It will reset your analysis data, which means it will be rebuilt the next time\n"
		"facade-worker.py runs. This minimizes the risk of stale data.\n\n"
		"This may or may not work. Are you sure you want to continue?\n")

	confirm = raw_input('(yes): ')

	if confirm.lower() == "yes":
		print "Attempting update."

		create_repos_fetch_log()
		create_analysis_log()
		create_utility_log()

		create_projects()
		create_repos()

		create_affiliations('clear')
		create_aliases('clear')
		create_excludes()
		create_special_tags()

		create_analysis('clear')

		create_unknown_caches('clear')
		create_web_caches('clear')

	else:
		print "Exiting without doing anything."

else:

	print "Exiting without doing anything."

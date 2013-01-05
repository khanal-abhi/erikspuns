import webapp2
import os
import cgi
import datetime
import urllib
import jinja2
import json

import email.utils as eu

jinja_environment = jinja2.Environment(
	loader=jinja2.FileSystemLoader(os.path.dirname(__file__)))

from google.appengine.api import users
from google.appengine.ext import db


class MainPage(webapp2.RequestHandler):
	def get(self):
		order = self.request.get('order')
		user = users.get_current_user()
		if user:
			nickname = user.nickname
			email = user.email
			url = users.create_logout_url(self.request.uri)
			url_link_text = 'Logout'

		else:
			nickname = 'Anonymous'
			email = None
			url = users.create_login_url(self.request.uri)
			url_link_text = 'Login'

		if order == "newest":
			puns = db.GqlQuery("SELECT * FROM Pun WHERE ANCESTOR IS :1 ORDER BY date DESC", pun_db_key())

		elif order == "oldest":
			puns = db.GqlQuery("SELECT * FROM Pun WHERE ANCESTOR IS :1 ORDER BY date ASC", pun_db_key())

		else:
			puns = db.GqlQuery("SELECT * FROM Pun WHERE ANCESTOR IS :1 ORDER BY date DESC", pun_db_key())

		template_values = {
							'puns': puns,
							'email': email,
							'nickname': nickname,
							'url': url,
							'url_link_text': url_link_text,
							'title': 'The beginning.'
		}

		template = jinja_environment.get_template('templates/index.html')
		self.response.headers['Content-Type'] = 'text/html'
		self.response.out.write(template.render(template_values))
	

class Search(webapp2.RequestHandler):
	def get(self):
		sort_order = self.request.get('sort_order')
		if sort_order == '':
			sort_order = 'date'
		if sort_order == 'upvotes':
			puns = db.GqlQuery("SELECT * FROM Pun WHERE ANCESTOR IS :1 ORDER BY upvotes DESC", pun_db_key())
		else:
			puns = db.GqlQuery("SELECT * FROM Pun WHERE ANCESTOR IS :1 ORDER BY date DESC", pun_db_key())


	def post(self):
		pun_db_name = 'authorized_user'

		user = users.get_current_user()
		if user:
			v_key = self.request.get('v_key')
			if v_key == 'Pass1234':
				auser = AUser(parent=auser_db_key(auser_db_name))
				auser.email = user.email
				auser.put()
				self.redirect('main')

class AddPun(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		user = users.get_current_user()
		admin = False
		if user:
			ausers = db.GqlQuery("SELECT * FROM AUser WHERE ANCESTOR IS :1 ORDER BY email", auser_db_key())

			for auser in ausers:
				if user.email() == auser.email:
					template_values = {
								'url': users.create_logout_url(self.request.uri),
								'url_link_text': 'Logout',
								'author': user.nickname(),
								'title': 'Adding a pun.'
					}
					template = jinja_environment.get_template('templates/add_pun.html')	
					admin = True
					pass			

			if not admin:
				template_values = {
									'url': users.create_logout_url(self.request.uri),
									'url_link_text': 'Logout',
									'author': user.nickname(),
									'alert_type': 'alert-danger',
									'alert_heading': 'Unauthorized Access!',
									'alert_description': 'Not so fast! You are not authorized to add puns!',
									'title': 'Unauthorized Access!'
				}
				template = jinja_environment.get_template('templates/alert_full.html')

			self.response.out.write(template.render(template_values))

		else:
			self.redirect(users.create_login_url(self.request.uri))

	def post(self):

		self.response.headers['Content-Type'] = 'text/html'

		pun = self.request.get('pun')
		description = self.request.get('description')
		author = self.request.get('author')

		if ((isNotEmpty(pun) and isNotEmpty(description)) and isNotEmpty(author)):
			if author == users.get_current_user().nickname():
				new_pun = Pun(parent=pun_db_key())
				new_pun.author = author
				new_pun.pun = pun
				new_pun.description = description
				new_pun.put()

				self.redirect('/')
				error_name = "None"
				error_description = "None"
				back = "/post"
				title = "Adding a pun."
			
			else:
				error_name = "User Mismatch!"
				error_description = "There was a mismatch between the author and the current user for the post!"
				back = "/post"
				title = "User Mismatch!"


		else:
			error_name = "Insufficient Data!"
			error_description = "One or more of the reqired fields were empty!"
			back = "/post"
			title = "Insufficient Data!"

		template_values = {
							'alert_type': 'alert-danger',
							'alert_heading': error_name,
							'alert_description': error_description,
							'url': users.create_login_url(self.request.uri),
							'url_link_text': 'Logout',
							'title': title
		}

		template = jinja_environment.get_template('templates/alert_full.html')
		self.response.out.write(template.render(template_values))

class AddUser(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = "text/html"

		user = users.get_current_user()
		if user:
			nickname = user.nickname()
			email = user.email()

			template_values = {
								'url': users.create_logout_url(self.request.uri),
								'url_link_text': 'Logout',
								'nickname': nickname,
								'email': email,
								'title': 'Erik\'s Puns: Authorized user validation!'
			}

			template = jinja_environment.get_template('templates/add_user.html')
			self.response.out.write(template.render(template_values))

		else:
			self.redirect(users.create_login_url(self.request.uri))


	def post(self):
		self.response.headers['Content-Type'] = 'text/html'

		email = self.request.get('email')
		v_key = self.request.get('v_key')
		user = users.get_current_user()

		if (isNotEmpty(email) and isNotEmpty(v_key)):
			ausers = db.GqlQuery("SELECT * FROM AUser WHERE ANCESTOR IS :1 ORDER BY email", auser_db_key())
			do_continue = True
			for a_user in ausers:
				if email == a_user.email:
					template_values = {
										'url': users.create_logout_url(self.request.uri),
										'url_link_text': 'Logout',
										'title': 'User Already Exists!',
										'alert_type': 'alert-danger',
										'alert_heading': 'User Already Exists!',
										'alert_description': 'The specified user has already been validated as an authorized user!',
					}

					template = jinja_environment.get_template('templates/alert_full.html')
					self.response.out.write(template.render(template_values))
					do_continue = False
					pass
				if not do_continue:
					pass


			if email == user.email() and v_key == "Pass1234" and do_continue:
				auser = AUser(parent=auser_db_key())
				auser.email = email
				auser.put()

				template = jinja_environment.get_template('templates/alert_full.html')
				template_values = {
									'url': users.create_logout_url(self.request.uri),
									'url_link_text': 'Logout',
									'title': 'Added the user!',
									'alert_type': 'alert-success',
									'alert_heading': 'Added the user!',
									'alert_description': 'The user has been successfully added!',
									'back': 'add_user'
				}
				self.response.out.write(template.render(template_values))
			
			elif do_continue:
				template_values = {
									'url': users.create_logout_url(self.request.uri),
									'url_link_text': 'Logout',
									'title': 'Invalid credentails!',
									'alert_type': 'alert-danger',
									'alert_heading': 'Invalid credentials!',
									'alert_description': 'Either the email, or the validation key is invalid. Please Try again!',
				}
				template = jinja_environment.get_template('templates/alert.html')
				self.response.out.write(template.render(template_values))

				user = users.get_current_user()
				if user:
					nickname = user.nickname()
					email = user.email()

					template_values = {
										'url': users.create_logout_url(self.request.uri),
										'url_link_text': 'Logout',
										'nickname': nickname,
										'email': email,
										'title': 'Erik\'s Puns: Authorized user validation!'
					}

					template = jinja_environment.get_template('templates/add_user.html')
					self.response.out.write(template.render(template_values))

				else:
					self.redirect(users.create_login_url(self.request.uri))



class AdminPageUsers(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		user = users.get_current_user()
		admin = False

		if user:
			ausers = db.GqlQuery("SELECT * FROM AUser WHERE ANCESTOR IS :1 ORDER BY email", auser_db_key())
			for auser in ausers:
				if user.email() == auser.email:
					admin = True
					pass

			if admin:
				template_values = {
									'url': users.create_logout_url(self.request.uri),
									'url_link_text': 'Logout',
									'title': 'Authorized Users!',
									'back': '/',
									'ausers': ausers
				}

				template = jinja_environment.get_template('templates/ausers.html')
				self.response.out.write(template.render(template_values))

			if not admin:
				template_values = {
									'url': users.create_logout_url(self.request.uri),
									'url_link_text': 'Logout',
									'title': 'Unauthorized Access!',
									'alert_type': 'alert-danger',
									'alert_heading': 'Unauthorized Access!',
									'alert_description': 'You are not authorized to edit remove authorized users!',
									'back': '/'
				}

				template = jinja_environment.get_template('templates/alert_full.html')
				self.response.out.write(template.render(template_values))



		else:
			self.redirect(users.create_login_url(self.request.uri))

	def post(self):
		self.response.headers['Content-Type'] = 'text/html'

		email = self.request.get('email')
		success = False

		ausers = db.GqlQuery("SELECT * FROM AUser WHERE ANCESTOR IS :1 ORDER BY email", auser_db_key())

		for auser in ausers:
			if email == auser.email:
				auser.delete()
				template_values = {
									'alert_type': 'alert-success',
									'alert_heading': 'Authorized user removed!',
									'alert_description': 'The selected authorized user had been removed from the list!'
				}

				template = jinja_environment.get_template('templates/alert.html')
				self.response.out.write(template.render(template_values))
				success = True
				pass


		if not success:
			template_values = {
								'alert_type': 'alert-danger',
								'alert_heading': 'Unable to remove user!',
								'alert_description': 'The selected authorized user could not be removed from the list!'
			}

			template = jinja_environment.get_template('templates/alert.html')
			self.response.out.write(template.render(template_values))

		user = users.get_current_user()
		admin = False

		if user:
			ausers = db.GqlQuery("SELECT * FROM AUser WHERE ANCESTOR IS :1 ORDER BY email", auser_db_key())
			for auser in ausers:
				if user.email() == auser.email:
					admin = True
					pass

			if admin:
				template_values = {
									'url': users.create_logout_url(self.request.uri),
									'url_link_text': 'Logout',
									'title': 'Authorized Users!',
									'ausers': ausers
				}

				template = jinja_environment.get_template('templates/ausers.html')
				self.response.out.write(template.render(template_values))

			if not admin:
				template_values = {
									'url': users.create_logout_url(self.request.uri),
									'url_link_text': 'Logout',
									'title': 'Unauthorized Access!',
									'alert_type': 'alert-danger',
									'alert_heading': 'Unauthorized Access!',
									'alert_description': 'You are not authorized to edit remove authorized users!',
				}

				template = jinja_environment.get_template('templates/alert_full.html')
				self.response.out.write(template.render(template_values))



		else:
			self.redirect(users.create_login_url(self.request.uri))


class AdminPagePuns(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/html'
		user = users.get_current_user()
		admin = False

		if user:
			ausers = db.GqlQuery("SELECT * FROM AUser WHERE ANCESTOR IS :1 ORDER BY email", auser_db_key())
			for auser in ausers:
				if user.email() == auser.email:
					admin = True
					pass

			if admin:

				puns = db.GqlQuery("SELECT * FROM Pun WHERE ANCESTOR IS :1 ORDER BY date DESC", pun_db_key())
				template_values = {
									'url': users.create_logout_url(self.request.uri),
									'url_link_text': 'Logout',
									'title': 'Puns.',
									'puns': puns
				}

				template = jinja_environment.get_template('templates/apuns.html')
				self.response.out.write(template.render(template_values))

			if not admin:
				template_values = {
									'url': users.create_logout_url(self.request.uri),
									'url_link_text': 'Logout',
									'title': 'Unauthorized Access!',
									'alert_type': 'alert-danger',
									'alert_heading': 'Unauthorized Access!',
									'alert_description': 'You are not authorized to remove puns!',
				}

				template = jinja_environment.get_template('templates/alert_full.html')
				self.response.out.write(template.render(template_values))



		else:
			self.redirect(users.create_login_url(self.request.uri))

	def post(self):
		self.response.headers['Content-Type'] = 'text/html'

		pun = self.request.get('pun')
		description = self.request.get('description')
		success = False

		apuns = db.GqlQuery("SELECT * FROM Pun WHERE ANCESTOR IS :1 ORDER BY date", pun_db_key())

		for apun in apuns:
			if pun == apun.pun and description == apun.description:
				apun.delete()
				template_values = {
									'alert_type': 'alert-success',
									'alert_heading': 'Pun removed!',
									'alert_description': 'The selected pun has been removed from the list!'
				}

				template = jinja_environment.get_template('templates/alert.html')
				self.response.out.write(template.render(template_values))
				success = True
				pass


		if not success:
			template_values = {
								'alert_type': 'alert-danger',
								'alert_heading': 'Unable to remove pun!',
								'alert_description': 'The selected authorized pun could not be removed from the list!'
			}

			template = jinja_environment.get_template('templates/alert.html')
			self.response.out.write(template.render(template_values))

		user = users.get_current_user()
		admin = False

		if user:
			ausers = db.GqlQuery("SELECT * FROM AUser WHERE ANCESTOR IS :1 ORDER BY email", auser_db_key())
			for auser in ausers:
				if user.email() == auser.email:
					admin = True
					pass

			if admin:
				template_values = {
									'url': users.create_logout_url(self.request.uri),
									'url_link_text': 'Logout',
									'title': 'Authorized Users!',
									'back': '/',
									'puns': apuns
				}

				template = jinja_environment.get_template('templates/apuns.html')
				self.response.out.write(template.render(template_values))

			if not admin:
				template_values = {
									'url': users.create_logout_url(self.request.uri),
									'url_link_text': 'Logout',
									'title': 'Unauthorized Access!',
									'error_name': 'Unauthorized Access!',
									'error_description': 'You are not authorized to remove puns!',
									'back': '/'
				}

				template = jinja_environment.get_template('templates/alert.html')
				self.response.out.write(template.render(template_values))



		else:
			self.redirect(users.create_login_url(self.request.uri))

class UpVote(webapp2.RequestHandler):
	def get(self):
		self.response.headers['Content-Type'] = 'text/html'

		if users.get_current_user():
			url = users.create_logout_url(self.request.uri)
			url_link_text = 'Logout'

		else:
			url = users.create_login_url(self.request.uri)
			url_link_text = 'Login'

		template_values = {
							'alert_type': 'alert-danger',
							'title': 'Page not accessible!',
							'alert_heading': 'Page not accessible!',
							'alert_description': 'This page is unavailable for viewing!',
							'url': url,
							'url_link_text': url_link_text
		}

		template = jinja_environment.get_template('templates/alert_full.html')
		self.response.out.write(template.render(template_values))

	def post(self):
		self.response.headers['Content-Type'] = 'application/json'

		date = self.request.get('date')
		email = self.request.get('email')

		match = False
		result = None

		punlikers = db.GqlQuery("SELECT * FROM PunLiker WHERE ANCESTOR IS :1", punliker_db_key(date))
		for each_punliker in punlikers:
			if email == each_punliker.email:
				match = True
				result = {
							'request': 'failed',
							'reason': 'duplicate_upvote'
				}
				pass

		if not match:
			puns = db.GqlQuery("SELECT * FROM Pun WHERE ANCESTOR IS :1", pun_db_key())
			success = False

			for pun in puns:
				p_date = pun.date.strftime('%Y-%m-%d %H:%M:%S.%f')
				if date == p_date:

					self.response.out.write('Success')

					if pun.upvotes:
						pun.upvotes = pun.upvotes+1
					else:
						pun.upvotes = 1

					pun.put()
					success = True
					pass

			if success:
				self.response.out.write('adding upvote')

				punliker = PunLiker(parent=punliker_db_key(date))
				punliker.email = email
				punliker.put()
				result = {
							'request': 'successful',
							'reason': 'upvote_commited'
				}

			else:
				result = {
							'request': 'failed',
							'reason': 'pun_unavailable'
				}

		self.response.out.write(json.dumps(result))



class AUser(db.Model):
	email = db.StringProperty()

class PunLiker(db.Model):
	email = db.StringProperty()

class Pun(db.Model):
	author = db.StringProperty()
	pun = db.StringProperty()
	description = db.StringProperty(multiline=True)
	upvotes = db.IntegerProperty()
	date = db.DateTimeProperty(auto_now_add=True)

def punliker_db_key(punliker_db_name):
	return db.Key.from_path('PunLiker', punliker_db_name or 'default_pun')

def pun_db_key(pun_db_name=None):
	return db.Key.from_path('Pun', pun_db_name or 'erikspun')

def auser_db_key(auser_db_name=None):
	return db.Key.from_path('AUser', auser_db_name or 'authorized_user')

def isNotEmpty(string_variable):
	if string_variable == "":
		return False
	else:
		return True

app = webapp2.WSGIApplication([('/', MainPage),
								('/search', Search),
								('/post', AddPun),
								('/add_user', AddUser),
								('/admin_page_users', AdminPageUsers),
								('/admin_page_puns', AdminPagePuns),
								('/upvote', UpVote)],
                              debug=True)
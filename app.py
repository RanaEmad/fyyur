#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from flask_migrate import Migrate
from datetime import datetime
from pprint import pprint
from sqlalchemy import text
import json
from models import db, Venue, Artist, Show
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

db.init_app(app)


migrate= Migrate(app,db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format)

app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#

@app.route('/')
def index():
  return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
def venues():
  venues=Venue.query.all()
  grouped={}
  for venue in venues:
    upcoming_shows= db.session.query(Show).filter_by(venue_id=venue.id).filter(Show.start_time > datetime.now()).all()
    venue.num_upcoming_shows=len(upcoming_shows)
    if not (venue.city in grouped.keys()):
      grouped[venue.city]={}
      grouped[venue.city][venue.state]=[]
    if venue.state in grouped[venue.city].keys():
      grouped[venue.city][venue.state].append(venue)
    else: 
      grouped[venue.city][venue.state]=[]  
      grouped[venue.city][venue.state].append(venue)  
  data=[]    
  for city in grouped:
    for state in grouped[city]:
      data.append({"city":city,"state":state, "venues": grouped[city][state]})
  return render_template('pages/venues.html', areas=data);

@app.route('/venues/search', methods=['POST'])
def search_venues():
  venues= Venue.query.filter(Venue.name.ilike('%'+request.form["search_term"]+'%')).all()
  for venue in venues:
    upcoming_shows= db.session.query(Show).filter_by(venue_id=venue.id).filter(Show.start_time > datetime.now()).all()
    venue.num_upcoming_shows=len(upcoming_shows)
  response={
    "count": len(venues),
    "data": venues
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  data= Venue.query.filter_by(id=venue_id).one()
  data.genres= json.loads(data.genres)

  upcoming_shows= db.session.query(Show,Artist).filter_by(venue_id=venue_id).join(Artist).filter(Show.start_time > datetime.now()).filter(Artist.id==Show.artist_id).all()
  upcoming_shows_arr=[]
  for show,artist in upcoming_shows:
    upcoming_shows_arr.append({
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    })
  data.upcoming_shows=upcoming_shows_arr
  data.upcoming_shows_count=len(upcoming_shows_arr)

  past_shows= db.session.query(Show,Artist).filter_by(venue_id=venue_id).join(Artist).filter(Show.start_time <= datetime.now()).filter(Artist.id==Show.artist_id).all()
  past_shows_arr=[]
  for show,artist in past_shows:
    past_shows_arr.append({
      "artist_id": artist.id,
      "artist_name": artist.name,
      "artist_image_link": artist.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    })
  data.past_shows=past_shows_arr
  data.past_shows_count=len(past_shows_arr)

  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  # : insert form data as a new Venue record in the db, instead
  error= False
  try:
    seeking_talent=True
    if request.form['seeking_talent']=='No':
      seeking_talent=False
    venue= Venue(name=request.form['name'],city=request.form['city'],state=request.form['state'],address=request.form['address'],phone=request.form['phone'],facebook_link=request.form['facebook_link'],image_link=request.form['image_link'],seeking_talent=seeking_talent,seeking_description=request.form['seeking_description'],website=request.form['website'],genres=json.dumps(request.form.getlist('genres')))
    db.session.add(venue)
    db.session.commit()
  except:
    error= True
    db.session.rollback()
  finally:
    db.session.close()    

  if error:
    flash('An error occurred. Venue ' + request.form["name"] + ' could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Venue ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
    Venue.query.filter_by(id=venue_id).delete()
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  return None

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artists=Artist.query.all()
  data=artists
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  artists= Artist.query.filter(Artist.name.ilike('%'+request.form["search_term"]+'%')).all()
  response={
    "count": len(artists),
    "data": artists
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  data= Artist.query.filter_by(id=artist_id).one()

  upcoming_shows= db.session.query(Show,Venue).filter_by(artist_id=artist_id).join(Venue).filter(Show.start_time > datetime.now()).filter(Venue.id==Show.venue_id).all()
  upcoming_shows_arr=[]
  for show,venue in upcoming_shows:
    upcoming_shows_arr.append({
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    })
  data.upcoming_shows=upcoming_shows_arr
  data.upcoming_shows_count=len(upcoming_shows_arr)

  past_shows= db.session.query(Show,Venue).filter_by(artist_id=artist_id).join(Venue).filter(Show.start_time <= datetime.now()).filter(Venue.id==Show.venue_id).all()
  past_shows_arr=[]
  for show,venue in past_shows:
    past_shows_arr.append({
      "venue_id": venue.id,
      "venue_name": venue.name,
      "venue_image_link": venue.image_link,
      "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
    })
  data.past_shows=past_shows_arr
  data.past_shows_count=len(past_shows_arr)

  data.genres=json.loads(data.genres)
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist= Artist.query.filter_by(id=artist_id).one()
  seeking_venue="No"
  if artist.seeking_venue:
    seeking_venue="Yes"
  form = ArtistForm(name=artist.name, city=artist.city, state=artist.state, phone = artist.phone, genres=json.loads(artist.genres),facebook_link=artist.facebook_link,image_link=artist.image_link, seeking_venue=seeking_venue,seeking_description=artist.seeking_description,website=artist.website)
  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  try:
    artist= Artist.query.filter_by(id=artist_id).one()
    artist.name=request.form["name"]
    artist.city=request.form["city"]
    artist.state=request.form["state"]
    artist.phone=request.form["phone"]
    artist.genres=json.dumps(request.form.getlist("genres"))
    artist.facebook_link=request.form["facebook_link"]
    artist.image_link=request.form["image_link"]
    seeking_venue=False
    if request.form["seeking_venue"]=="Yes":
      seeking_venue=True
    artist.seeking_venue=seeking_venue
    artist.seeking_description=request.form["seeking_description"]
    artist.website=request.form["website"]
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue= Venue.query.filter_by(id=venue_id).one()
  seeking_talent="No"
  if venue.seeking_talent:
    seeking_talent="Yes"
  form = VenueForm(name=venue.name,city=venue.city,state=venue.state,address=venue.address,phone=venue.phone,genres=json.loads(venue.genres),facebook_link=venue.facebook_link,image_link=venue.image_link,seeking_talent=seeking_talent,seeking_description=venue.seeking_description,website=venue.website)
  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  try:
    venue= Venue.query.filter_by(id=venue_id).one()
    venue.name=request.form["name"]
    venue.city=request.form["city"]
    venue.state=request.form["state"]
    venue.address=request.form["address"]
    venue.phone=request.form["phone"]
    venue.genres=json.dumps(request.form.getlist("genres"))
    venue.facebook_link=request.form["facebook_link"]
    venue.image_link=request.form["image_link"]
    seeking_talent=False
    if request.form["seeking_talent"]=="Yes":
      seeking_talent=True
    venue.seeking_talent=seeking_talent
    venue.seeking_description=request.form["seeking_description"]
    venue.website=request.form["website"]
    db.session.commit()
  except:
    db.session.rollback()
  finally:
    db.session.close()
  return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------

@app.route('/artists/create', methods=['GET'])
def create_artist_form():
  form = ArtistForm()
  return render_template('forms/new_artist.html', form=form)

@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
  error= False
  try:
    seeking_venue=True
    if request.form['seeking_venue']=='No':
      seeking_venue=False
    artist= Artist(name=request.form['name'],city=request.form['city'],state=request.form['state'],phone=request.form['phone'],facebook_link=request.form['facebook_link'],image_link=request.form['image_link'],seeking_venue=seeking_venue,seeking_description=request.form['seeking_description'],website=request.form['website'],genres=json.dumps(request.form.getlist('genres')))
    db.session.add(artist)
    db.session.commit()
  except:
    error= True
    db.session.rollback()
  finally:
    db.session.close()   

  if error:
    flash('An error occurred. Artist ' + request.form["name"] + ' could not be listed.')
  else:
    flash('Artist ' + request.form['name'] + ' was successfully listed!')
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  # displays list of shows at /shows
  all_shows=db.session.query(Show, Venue, Artist).join(Venue, Venue.id==Show.venue_id).join(Artist, Artist.id==Show.artist_id).all()
  data=[]
  for show,venue,artist in all_shows:
    data.append({
    "venue_id": venue.id,
    "venue_name": venue.name,
    "artist_id": artist.id,
    "artist_name": artist.name,
    "artist_image_link": artist.image_link,
    "start_time": show.start_time.strftime("%Y-%m-%d %H:%M:%S")
  })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  # called to create new shows in the db, upon submitting new show listing form
  error= False
  try:
    show= Show(venue_id=request.form['venue_id'],artist_id=request.form['artist_id'],start_time=request.form['start_time'])
    db.session.add(show)
    db.session.commit()
  except:
    error= True
    db.session.rollback()
  finally:
    db.session.close()  
  if error:
    flash('An error occurred. Show could not be listed.')
  else:
    # on successful db insert, flash success
    flash('Show was successfully listed!')
  return render_template('pages/home.html')

@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404

@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''

#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#
import collections
import collections.abc
import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for
from flask_migrate import Migrate
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
import logging
from logging import Formatter, FileHandler
from flask_wtf import Form
from forms import *
from models import db, Venue, Artist, Show

collections.Callable = collections.abc.Callable 
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)

migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#

def format_datetime(value, format='medium'):
  date = dateutil.parser.parse(value)
  if format == 'full':
      format="EEEE MMMM, d, y 'at' h:mma"
  elif format == 'medium':
      format="EE MM, dd, y h:mma"
  return babel.dates.format_datetime(date, format, locale='en')

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
  current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  data = []
  for Venues_one_city in Venue.query.distinct(Venue.state, Venue.city):
    state = Venues_one_city.state
    city = Venues_one_city.city
    one_city_data = {}
    venues = []
    venue_query = Venue.query.filter(Venue.state == state, Venue.city == city).all()
    for venue in venue_query:
      upcoming_shows = venue.shows.filter(Show.start_time > current_time).all()
      venues.append({
        "id": venue.id,
        "name": venue.name,
        "num_upcoming_shows": len(upcoming_shows)
      })
    data.append({
      "city": city,
      "state": state,
      "venues": venues
    })
  return render_template('pages/venues.html', areas=data)
  

@app.route('/venues/search', methods=['POST'])
def search_venues():
  search_term = request.form.get('search_term', '')
  matched_venues = Venue.query.filter(Venue.name.ilike(f'%{search_term}%')).all()
  data = []
  current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  for venue in matched_venues:
    upcoming_shows = venue.shows.filter(Show.start_time > current_time).all()
    data.append({
      "id": venue.id,
      "name": venue.name,
      "num_upcoming_shows": len(upcoming_shows)
    })
  response = {
    "count": len(matched_venues),
    "data": data
  }
  return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
  venue = db.session.query(Venue).filter(Venue.id == venue_id).one()
  past_shows_query = db.session.query(Show).join(Venue).filter(Venue.id==venue_id).filter(Show.start_time<datetime.now()).all()
  upcoming_shows_query = db.session.query(Show).join(Venue).filter(Venue.id==venue_id).filter(Show.start_time>datetime.now()).all()
  past_shows = []
  upcoming_shows = []
  for show in past_shows_query:
    past_shows.append({
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })
  for show in upcoming_shows_query:
    upcoming_shows.append({
        "artist_id": show.artist_id,
        "artist_name": show.artist.name,
        "artist_image_link": show.artist.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })
  data = {
      "id": venue.id,
      "name": venue.name,
      "genres": venue.genres,
      "address": venue.address,
      "city": venue.city,
      "state": venue.state,
      "phone": venue.phone,
      "website": venue.website,
      "facebook_link": venue.facebook_link,
      "seeking_talent": venue.seeking_talent,
      "seeking_description": venue.seeking_description,
      "image_link": venue.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
  }
  return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------

@app.route('/venues/create', methods=['GET'])
def create_venue_form():
  form = VenueForm()
  return render_template('forms/new_venue.html', form=form)

@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
  form = VenueForm(request.form, meta={"csrf": False})
  try:
    if form.validate_on_submit():
      venue = Venue(
          name=form.name.data,
          city=form.city.data,
          state=form.state.data,
          address=form.address.data,
          phone=form.phone.data,
          image_link=form.image_link.data,
          genres=form.genres.data,
          facebook_link=form.facebook_link.data,
          website=form.website_link.data,
          seeking_description=form.seeking_description.data,
          seeking_talent=form.seeking_talent.data
      )
      db.session.add(venue)
      db.session.commit()
      flash('Venue ' + request.form['name'] + ' was successfully listed!')
    else:
      for field, message in form.errors.items():
        flash(field + ' - ' + str(message), 'danger')
      raise ValueError
  except ValueError as e:
      db.session.rollback()
      flash('Error. Venue ' + request.form['name'] + ' listing Unsuccessful')
  finally:
      db.session.close()
  return render_template('pages/home.html')

@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
  try:
      venue = Venue.query.get_or_404(venue_id)
      db.session.delete(venue)
      db.session.commit()
      flash('The venue has been removed together with all of its shows.')
      return render_template('pages/home.html')
  except ValueError:
      db.session.rollback()
      flash('Deletion failed.')
  finally:
      db.session.close()
  return redirect(url_for('venues'))

  # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
  # clicking that button delete it from the db then redirect the user to the homepage
  

#  Artists
#  ----------------------------------------------------------------
@app.route('/artists')
def artists():
  artist_query = Artist.query.all()
  data = []
  for artist in artist_query:
    data.append({
      "id": artist.id,
      "name": artist.name,
    })
  return render_template('pages/artists.html', artists=data)

@app.route('/artists/search', methods=['POST'])
def search_artists():
  search_term = request.form.get('search_term', '')
  matched_artists = Artist.query.filter(Artist.name.ilike(f'%{search_term}%')).all()
  data = []
  current_time = datetime.now().strftime('%Y-%m-%d %H:%M:%S')
  for artist in matched_artists:
    upcoming_shows = artist.shows.filter(Show.start_time > current_time).all()
    data.append({
      "id": artist.id,
      "name": artist.name,
      "num_upcoming_shows": len(upcoming_shows)
    })
  response = {
    "count": len(matched_artists),
    "data": data
  }
  return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))

@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
  artist = db.session.query(Artist).filter(Artist.id == artist_id).one()
  past_shows_query = db.session.query(Show).join(Artist).filter(Show.artist_id == artist_id).filter(Show.start_time<datetime.now()).all()
  upcoming_shows_query = db.session.query(Show).join(Artist).filter(Show.artist_id == artist_id).filter(Show.start_time>datetime.now()).all()
  past_shows = []
  upcoming_shows = []
  for show in past_shows_query:
    past_shows.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })
  for show in upcoming_shows_query:
    upcoming_shows.append({
        "venue_id": show.venue_id,
        "venue_name": show.venue.name,
        "venue_image_link": show.venue.image_link,
        "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
        })
  data = {
      "id": artist.id,
      "name": artist.name,
      "genres": artist.genres,
      "city": artist.city,
      "state": artist.state,
      "phone": artist.phone,
      "website": artist.website,
      "facebook_link": artist.facebook_link,
      "seeking_venue": artist.seeking_venue,
      "seeking_description": artist.seeking_description,
      "image_link": artist.image_link,
      "past_shows": past_shows,
      "upcoming_shows": upcoming_shows,
      "past_shows_count": len(past_shows),
      "upcoming_shows_count": len(upcoming_shows),
  }
  return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------
@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
  artist = Artist.query.get_or_404(artist_id)
  form = ArtistForm(obj=artist)

  return render_template('forms/edit_artist.html', form=form, artist=artist)

@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
  form = ArtistForm(request.form, meta={"csrf": False})
  try:
    artist = Artist.query.get_or_404(artist_id)
    form.populate_obj(artist)
    db.session.commit()
    flash('Artist: ' + form.name.data + 'was successfully updated!')
  except:
    db.session.rollback()
    flash('Artist: ' + form.name.data + ' was unsuccessfully updated!')
  finally:
    db.session.close()

  return redirect(url_for('show_artist', artist_id=artist_id))

@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
  venue = Venue.query.get_or_404(venue_id)
  form = VenueForm(obj=venue)

  return render_template('forms/edit_venue.html', form=form, venue=venue)

@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
  form = VenueForm(request.form)
  try:
    venue = Venue.query.get_or_404(venue_id)
    form.populate_obj(venue)
    db.session.commit()
    flash('Venue: ' + form.name.data + ' was successfully updated!')
  except:
    db.session.rollback()
    flash('Venue: ' + form.name.data + ' was unsuccessfully updated!')
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
  form = ArtistForm(request.form, meta={"csrf": False})
  try:
    if form.validate_on_submit():
      artist = Artist(
          name=form.name.data,
          city=form.city.data,
          state=form.state.data,
          phone=form.phone.data,
          image_link=form.image_link.data,
          genres=form.genres.data,
          facebook_link=form.facebook_link.data,
          website=form.website_link.data,
          seeking_description=form.seeking_description.data,
          seeking_venue=form.seeking_venue.data
      )
      db.session.add(artist)
      db.session.commit()
      flash('Artist ' + request.form['name'] + ' was successfully listed!')
    else:
      for field, message in form.errors.items():
        flash(field + ' - ' + str(message), 'danger')
      raise ValueError
  except ValueError as e:
      db.session.rollback()
      flash('Error. Artist ' + request.form['name'] + ' listing Unsuccessful')
  finally:
      db.session.close()
  return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
  show_query = Show.query.all()
  data = []
  for show in show_query:
    data.append({
      "venue_id": show.venue.id,
      "venue_name": show.venue.name,
      "artist_id": show.artist.id,
      "artist_name": show.artist.name,
      "artist_image_link": show.artist.image_link,
      "start_time": show.start_time.strftime('%Y-%m-%d %H:%M:%S')
    })
  return render_template('pages/shows.html', shows=data)

@app.route('/shows/create')
def create_shows():
  # renders form. do not touch.
  form = ShowForm()
  return render_template('forms/new_show.html', form=form)

@app.route('/shows/create', methods=['POST'])
def create_show_submission():
  form = ShowForm(request.form)
  try:
      show = Show(
          artist_id=form.artist_id.data,
          venue_id=form.venue_id.data,
          start_time=form.start_time.data
      )
      db.session.add(show)
      db.session.commit()
      flash('Show  was successfully listed!')
  except ValueError as e:
      db.session.rollback()
      flash('An error occurred. Show could not be listed.')
  finally:
      db.session.close()
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

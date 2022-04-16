#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import sys
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
from models import db, Venue, Artist, Show
from sqlalchemy.exc import SQLAlchemyError

#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')
db.init_app(app)

# connect to a local postgresql database
DATABASE_PATH = app.config['SQLALCHEMY_DATABASE_URI']
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
migrate = Migrate(app, db)

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
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
    # num_upcoming_shows should be aggregated based on number of upcoming shows per venue.

    data = []
    all_areas = db.session.query(Venue.city, Venue.state).group_by(
        Venue.state,                                                              Venue.city).all()
    for area in all_areas:
        venues = db.session.query(Venue.id, Venue.name).filter(
            Venue.city == area[0], Venue.state == area[1]).all()
        data.append({
            "city": area[0],
            "state": area[1],
            "venues": []
        })
        for venue in venues:
            data[-1]["venues"].append({
                "id": venue[0],
                "name": venue[1],
            })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():
    search_term = request.form.get('search_term', '')
    found = Venue.query.filter(Venue.name.ilike(f'%{search_term}%'))
    response = {
        'count': found.count(),
        'data': found
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@ app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # shows the venue page with the given venue_id
    venue = Venue.query.get(venue_id)
    past_shows = []
    upcoming_shows = []
    shows = venue.shows
    for show in shows:
        show_info = {
            "artist_id": show.artist_id,
            "artist_name": show.artist_name,
            "artist_image_link": show.artist_image_link,
            "start_time": str(show.start_time)
        }
        if(show.upcoming):
            upcoming_shows.append(show_info)
        else:
            past_shows.append(show_info)

    data = {
        "id": venue.id,
        "name": venue.name,
        "genres": venue.genres.split(','),
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
        "upcoming_shows_count": len(upcoming_shows)
    }

    return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@ app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@ app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    venue = Venue()
    venue.name = request.form['name']
    venue.city = request.form['city']
    venue.state = request.form['state']
    venue.address = request.form['address']
    venue.phone = request.form['phone']
    venue.facebook_link = request.form['facebook_link']
    venue.genres = request.form['genres']
    venue.website = request.form['website_link']
    venue.image_link = request.form['image_link']
    try:
        db.session.add(venue)
        db.session.commit()
        # on successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')


@ app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # Complete this endpoint for taking a venue_id, and using
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    try:
        Venue.query.filter_by(id=venue_id).delete()
        db.session.commit()
        flash('The venue' + Venue.name + 'has been deleted succcessfully')
    except:
        db.session.rollback()
        print(sys.exc_info())
        flash('The venue' + Venue.name + 'could not be deleted')
    finally:
        db.session.close()

    return redirect(url_for('index'))

#  Artists
#  ----------------------------------------------------------------


@ app.route('/artists')
def artists():

    data = []
    artists_result = Artist.query.order_by(Artist.id).all()
    for artist in artists_result:
        data.extend([{
            "id": artist.id,
            "name": artist.name
        }])

    return render_template('pages/artists.html', artists=data)


@ app.route('/artists/search', methods=['POST'])
def search_artists():
    search_term = request.form.get('search_term', '')
    result = Artist.query.filter(Artist.name.ilike(f'%{search_term}%'))
    response = {
        'count': result.count(),
        'data': result
    }
    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    artist = Artist.query.get_or_404(artist_id)
    data = {
        'id': artist.id,
        'name': artist.name,
        'genres': artist.genres,
        'city': artist.city,
        'state': artist.state,
        'phone': artist.phone,
        'website': artist.website,
        'facebook_link': artist.facebook_link,
        'image_link': artist.image_link,
        'seeking_venue': artist.seeking_venue,
        'seeking_description': artist.seeking_description,
        'past_shows': [],
        'upcoming_shows': [],
        'past_shows_count': 0,
        'upcoming_shows_count': 0
    }
    shows = db.session.query(Show, Venue).join(
        Artist).filter_by(id=artist_id).all()

    upcoming_shows = []
    past_shows = []
    for show, venue in shows:
        a_show = {
            'venue_id': venue.id,
            'venue_name': venue.name,
            'venue_image_link': venue.image_link,
            'start_time': show.start_time.strftime("%d/%m/%Y, %H:%M")
        }

        if show.start_time <= datetime.now():
            past_shows.append(a_show)
        else:
            upcoming_shows.append(a_show)

    data['past_shows'] = past_shows
    data['upcoming_shows'] = upcoming_shows
    data['past_shows_count'] = len(past_shows)
    data['upcoming_shows_count'] = len(upcoming_shows)

    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@ app.route('/artists/<int:artist_id>/edit', methods=['GET'])
def edit_artist(artist_id):
    form = ArtistForm()
    #  populate form with fields from artist with ID <artist_id>
    artist = Artist.query.get(artist_id)
    form = ArtistForm(obj=artist)
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@ app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    # take values from the form submitted, and update existing
    # artist record with ID <artist_id> using the new attributes
    artist = Artist.query.get(artist_id)
    for field in request.form:
        if field == 'genres':
            setattr(artist, field, request.form.getlist(field))
        elif field == 'seeking_venue':
            setattr(artist, field, True if request.form.get(
                field) in ('y', True, 't', 'True') else False)
        else:
            setattr(artist, field, request.form.get(field))

    try:
        db.session.add(artist)
        db.session.commit()
        flash(f'Artist {request.form["name"]} was successfully listed!')

    except:
        flash(f'An error occurred. Artist {artist.name} could not be listed.')
        db.session.rollback()
        db.session.close()
    finally:
        db.session.close()

    return redirect(url_for('show_artist', artist_id=artist_id))


@ app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    # populate form with values from venue with ID <venue_id>
    venue = Venue.query.get(venue_id)
    form = VenueForm(obj=venue)
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@ app.route('/venues/<int:venue_id>/edit', methods=['POST'])
def edit_venue_submission(venue_id):
    # take values from the form submitted, and update existing
    # venue record with ID <venue_id> using the new attributes
    venue = Venue.query.get(venue_id)
    for field in request.form:
        if field == 'genres':
            setattr(venue, field, request.form.getlist(field))
        elif field == 'seeking_talent':
            setattr(venue, field, True if request.form.get(
                field) in ('y', True, 't', 'True') else False)
        else:
            setattr(venue, field, request.form.get(field))
    try:
        db.session.add(venue)
        db.session.commit()
        flash('Venue ' + request.form['name'] + ' was successfully listed!')

    except:
        db.session.rollback()
        flash(f'An error occurred. Venue {venue.name} could not be listed.')
        return render_template('pages/home.html')
        print(sys.exc_info())
    finally:
        db.session.close()

    return redirect(url_for('show_venue', venue_id=venue_id))

#  Create Artist
#  ----------------------------------------------------------------


@ app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@ app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    # insert form data as a new Venue record in the db, instead
    form = ArtistForm(request.form)
    new_artist = Artist(
        name=form.name.data,
        city=form.city.data,
        state=form.state.data,
        phone=form.phone.data,
        facebook_link=form.facebook_link.data,
        genres=','.join(form.genres.data),
        website=form.website_link.data,
        image_link=form.image_link.data,
        seeking_venue=form.seeking_venue.data,
        seeking_description=form.seeking_description.data,
    )
    try:
        db.session.add(new_artist)
        db.session.commit()
        flash('Artist ' + request.form['name'] +
              ' was successfully listed!')
    except:
        db.session.rollback()
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be listed.')
    finally:
        db.session.close()

    return render_template('pages/home.html')

#  Shows
#  ----------------------------------------------------------------


@ app.route('/shows')
def shows():
    # displays list of shows at /shows
    #  replace with real venues data.
    data = []
    show_item = {'venue_id': '', 'venue_name': '', 'artist_id': '',
                 'artist_name': '', 'artist_image_link': '', 'start_time': ''}
    for show in db.session.query(Venue.id, Venue.name, Artist.id, Artist.name, Artist.image_link, Show.start_time, Show.id).join(Venue).join(Artist).order_by(Show.id):
        show_item['venue_id'] = show[0]
        show_item['venue_name'] = show[1]
        show_item['artist_id'] = show[2]
        show_item['artist_name'] = show[3]
        show_item['artist_image_link'] = show[4]
        show_item['start_time'] = show[5].strftime("%Y-%m-%dT%H:%M:%S.%f%z")
        data.append(show_item)
    return render_template('pages/shows.html', shows=data)


@ app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@ app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    show = Show(
        artist_id=request.form['artist_id'],
        venue_id=request.form['venue_id'],
        start_time=request.form['start_time']
    )

    try:
        db.session.add(show)
        db.session.commit()
        # on successful db insert, flash success
        flash('Show was successfully listed!')
    except:
        flash('Error when inserting Show!')
        db.session.rollback()
        print(sys.exc_info())
    finally:
        db.session.close()
    return render_template('pages/home.html')


@ app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@ app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

if __name__ == '__main__':
    app.debug = True
    app.run(host="0.0.0.0", port=3000)

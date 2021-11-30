import datetime as dt
import numpy as np
import pandas as pd

import sqlalchemy
from sqlalchemy.ext.automap import automap_base
from sqlalchemy.orm import Session
from sqlalchemy import create_engine, func

from flask import Flask, jsonify

#################################################
# Database 
#################################################
engine = create_engine("sqlite:///Resources/hawaii.sqlite")
Base = automap_base()
Base.prepare(engine, reflect=True)

Measurement = Base.classes.measurement
Station = Base.classes.station

#################################################
# Flask Setup
#################################################
app = Flask(__name__)

#################################################
# Flask Routes
#################################################
@app.route("/")
def welcome():
     return (
         f"Home Page<br/>"
         f"-----------------<br/>"
         f"Available Routes:<br/>"
         f"/api/v1.0/precipitation<br/>"
         f"/api/v1.0/stations<br/>"
         f"/api/v1.0/tobs<br/>"
         f"/api/v1.0/startdate/<start><br/>"
         f"/api/v1.0/startend/<start>/<end><br/>"
         f"-----------------<br/>"
         f"NOTICE:<br/>"
         f"Please input the query date in ISO date format(YYYY-MM-DD), and the start date should not be later than 2017-08-23."
    )


@app.route("/api/v1.0/precipitation")
def precipitation():
    session = Session(engine)
    results = session.query(Measurement.date, Measurement.prcp).all()
    
    session.close()

    all_prcp = []
    for date, prcp in results:
        prcp_dict = {}
        prcp_dict[date] = prcp
        all_prcp.append(prcp_dict)

    return jsonify(all_prcp)


@app.route("/api/v1.0/stations")
def stations():
    session = Session(engine)
    results = session.query(Station.station).all()
    
    session.close()
    stations = list(np.ravel(results))

    return jsonify(stations)

@app.route("/api/v1.0/tobs")
def tobs():
    session = Session(engine)

    recent_date = session.query(Measurement).order_by(Measurement.date.desc()).first()
    last_date = dt.datetime.strptime(recent_date.date, '%Y-%m-%d').date()

    query_date = last_date - dt.timedelta(days=364)

    active_station_list = [Measurement.station, func.count(Measurement.station)]
    active_station = session.query(*active_station_list).group_by(Measurement.station).\
                    order_by(func.count(Measurement.station).desc()).first().station
 
    active_station_temp = session.query(Measurement.date, Measurement.tobs).\
                        filter(func.strftime('%Y-%m-%d', Measurement.date) > query_date).\
                        filter(Measurement.station == active_station).all()
    
    session.close()

    all_temp = []
    for date, temp in active_station_temp:
        temp_dict = {}
        temp_dict['Date'] = date
        temp_dict['Temperature'] = temp
        all_temp.append(temp_dict)

    return jsonify(all_temp)

@app.route('/api/v1.0/startdate/<start>')
def start_date(start=None):
    session = Session(engine)

    query_date = dt.datetime.strptime(start, '%Y-%m-%d').date()
    
    temp_list = [func.min(Measurement.tobs), 
             func.max(Measurement.tobs), 
             func.avg(Measurement.tobs)]

    date_temp = session.query(*temp_list).\
                filter(func.strftime('%Y-%m-%d', Measurement.date) >= query_date).all()
    
    session.close()

    return (
        f"Analysis of temperature from {start} to 2017-08-23 (the latest measurement in database):<br/>"
        f"Minimum temperature: {round(date_temp[0][0], 1)} °F<br/>"
        f"Maximum temperature: {round(date_temp[0][1], 1)} °F<br/>"
        f"Average temperature: {round(date_temp[0][2], 1)} °F"
    )

@app.route('/api/v1.0/startend/<start>/<end>')
def date_start_end(start, end):
    session = Session(engine)

    query_date_start = dt.datetime.strptime(start, '%Y-%m-%d').date()
    query_date_end = dt.datetime.strptime(end, '%Y-%m-%d').date()
    
    temp_list = [func.min(Measurement.tobs), 
             func.max(Measurement.tobs), 
             func.avg(Measurement.tobs)]

    date_temp = session.query(*temp_list).\
                filter(func.strftime('%Y-%m-%d', Measurement.date) >= query_date_start).\
                filter(func.strftime('%Y-%m-%d', Measurement.date) <= query_date_end).all()
    
    session.close()

    return (
        f"Analysis of temperature from {start} to {end}:<br/>"
        f"Minimum temperature: {round(date_temp[0][0], 1)} °F<br/>"
        f"Maximum temperature: {round(date_temp[0][1], 1)} °F<br/>"
        f"Average temperature: {round(date_temp[0][2], 1)} °F"
    )

if __name__ == "__main__":
    app.run(debug=True)
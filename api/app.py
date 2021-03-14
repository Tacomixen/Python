from flask import Flask, jsonify
from flask import abort
from flask import make_response
from flask import request

import os

import sqlite3
from sqlite3 import Error

app = Flask(__name__)

def create_db():
    database = os.getenv('DB_FILE')

    sql_create_sensors_table = """ CREATE TABLE IF NOT EXISTS sensors (
                                        id integer PRIMARY KEY AUTOINCREMENT,
                                        name text,
                                        description text,
                                        active integer
                                    ); """

    # create a database connection
    conn = create_connection(database)

    # create table
    if conn is not None:
        create_table(conn, sql_create_sensors_table)
        conn.commit()
        conn.close()
    else:
        print("Error! cannot create the database connection.")

def create_connection(db_file):
    conn = None
    try:
        conn = sqlite3.connect(db_file)
        print("Connection created...")
        return conn
    except Error as e:
        print(e)
    
    return conn

def create_table(conn, create_table_sql):
    try:
        c = conn.cursor()
        c.execute(create_table_sql)
        print("Table created...")
        populate_initial_sensors(conn, initial_sensors)
    except Error as e:
        print(e)

def populate_initial_sensors(conn, initial_sensors):
    cur = conn.cursor()
    try:

        for initial_sensor in initial_sensors:
            sql = ''' INSERT INTO sensors(id, name, description, active)
              VALUES(?,?,?,?) '''
            db_sensor = (initial_sensor.get('id'), initial_sensor.get('name'), initial_sensor.get('description'), initial_sensor.get('active'))
            cur.execute(sql, db_sensor)

        print("Table populated...")
    except Error as e:
        print(e)


# Initial sensors
initial_sensors = [
    {
        'id': 1,
        'name': u'Motion sensor 1',
        'description': u'IR motion sensor in location x.', 
        'active': 1
    },
    {
        'id': 2,
        'name': u'Accelerometer X',
        'description': u'X-axis accelerometer.', 
        'active': 0
    },
    {
        'id': 3,
        'name': u'Accelerometer Y',
        'description': u'Y-axis accelerometer.', 
        'active': 0
    }
]

# -- CRUD --
# Create
# Read
# Update
# Delete
# -- CRUD --

# Create a sensor
@app.route('/api/v1/sensors', methods=['POST'])
def create_sensor():
    if not request.json or not 'name' in request.json:
        abort(400)
    sensor = {
        'name': request.json['name'],
        'description': request.json.get('description', ""),
        'active': request.json['active']
    }

    # CREATE
    sql = ''' INSERT INTO sensors(name, description, active)
              VALUES(?,?,?) '''
    conn = create_connection(os.getenv('DB_FILE'))
    cur = conn.cursor()

    db_sensor = (sensor.get('name'), sensor.get('description'), sensor.get('active'))
    cur.execute(sql, db_sensor)
    conn.commit()
    
    sensor['id'] = cur.lastrowid
    print(f"Sensor: {sensor}")

    return jsonify({'sensor': sensor}), 201

# Read all sensors
@app.route('/api/v1/sensors', methods=['GET'])
def get_sensors():

    # GET ALL SENSORS
    conn = create_connection(os.getenv('DB_FILE'))
    cur = conn.cursor()
    cur.execute("SELECT * FROM sensors")

    db_sensors = cur.fetchall()
    json_sensors = []

    for sensor in db_sensors:
        json_sensor = {
            'id': sensor[0],
            'name': sensor[1],
            'description': sensor[2],
            'active': sensor[3]
        }
        json_sensors.append(json_sensor)
    return jsonify({'sensors': json_sensors})

# Read a sensor
@app.route('/api/v1/sensors/<int:sensor_id>', methods=['GET'])
def get_sensor(sensor_id):
    conn = create_connection(os.getenv('DB_FILE'))
    cur = conn.cursor()
    cur.execute(f"SELECT * FROM sensors WHERE id={sensor_id}")
    db_sensor = cur.fetchone()

    json_sensor = {
        'id': db_sensor[0],
        'name': db_sensor[1],
        'description': db_sensor[2],
        'active': db_sensor[3]
    }

    if len(db_sensor) == 0:
        abort(404)

    # GET A SENSOR
    return jsonify({'sensor': json_sensor})

# Update a sensor
@app.route('/api/v1/sensors/<int:sensor_id>', methods=['PUT'])
def update_sensor(sensor_id):
    conn = create_connection(os.getenv('DB_FILE'))
    cur = conn.cursor()

    cur.execute(f"SELECT * FROM sensors WHERE id={sensor_id}")
    db_sensor = cur.fetchone()

    print("DB SENSOR")
    print(db_sensor)

    new_sensor = {
        'id': db_sensor[0],
        'name': db_sensor[1],
        'description': db_sensor[2],
        'active': db_sensor[3]
    }

    if (db_sensor[1] != request.json.get('name') and request.json.get('name')):
        new_sensor['name'] = request.json.get('name')
    if (db_sensor[2] != request.json.get('description') and request.json.get('description')):
        new_sensor['description'] = request.json.get('description')
    if (db_sensor[3] != request.json.get('active') and (request.json.get('active') == 1 or request.json.get('active') == 0)):
        new_sensor['active'] = request.json.get('active')
    
    sql = ''' UPDATE sensors SET id = ?, name = ?, description = ?, active = ? WHERE id = ?'''

    data = (sensor_id, new_sensor['name'], new_sensor['description'], new_sensor['active'], sensor_id)
    
    cur.execute(sql, data)
    conn.commit()

    return jsonify({'sensor': new_sensor})

# Delete a sensor
@app.route('/api/v1/sensors/<int:sensor_id>', methods=['DELETE'])
def delete_sensor(sensor_id):
    # DELETE
    conn = create_connection(os.getenv('DB_FILE'))
    cur = conn.cursor()

    cur.execute(f"DELETE FROM sensors WHERE id={sensor_id}")
    conn.commit()

    return jsonify({'result': True})

# Error handling
@app.errorhandler(404)
def not_found(error):
    return make_response(jsonify({'error': 'Not found'}), 404)

if __name__ == '__main__':
    create_db()
    app.run(host='0.0.0.0', port=os.getenv('PORT'), debug=os.getenv('FLASK_DEBUG'))
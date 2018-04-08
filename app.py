import sys
import os
import yaml
import datetime
from flask import Flask, send_from_directory, request, jsonify, abort
from timelapsepi import sun
from timelapsepi import cam

config = yaml.safe_load(open(os.path.join(sys.path[0], "config.yml")))
local_timezone = sun.get_timezone(config['city'])
cam = cam.Cam(config)
app = Flask(__name__)


@app.route('/', methods=['GET'])
def hello_world():
    return send_from_directory('static', 'index.html')


# Static
@app.route('/static/<path:path>', methods=['GET'])
def send_static(path):
    return send_from_directory('static', path)


@app.route('/api/now', methods=['GET'])
def current_time():
    return jsonify(datetime.datetime.now(local_timezone).strftime('%Y %b %H:%M'))


@app.route('/api/camera/photo', methods=['GET'])
def take_photo():
    cam.take_preview_photo()
    return jsonify(datetime.datetime.now(local_timezone).strftime('%Y %b %H:%M'))


@app.route('/api/camera/config', methods=['GET'])
def get_camera_config():
    return jsonify(config['camera'])


@app.route('/api/camera/config', methods=['PUT'])
def set_camera_config():
    if not (request.json and 'title' in request.json):
        abort(400)
    config['camera'] = request.json
    return jsonify(config['camera'])


@app.route('/test')
def test():
    city_name = config['city']
    now = datetime.datetime.now(local_timezone)
    sunset_time = sun.get_today_sunset_time(city_name, now.date())
    result = [sunset_time, sun.get_today_sunrise_time(city_name, now.date())]
    return jsonify(result, config)


if __name__ == '__main__':
    app.run(host='0.0.0.0', port=5005)

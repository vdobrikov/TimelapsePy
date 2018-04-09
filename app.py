import sys
import os
import yaml
import datetime
import logging
from flask import Flask, send_from_directory, send_file, request, jsonify, abort
from timelapsepi import sun, cam


logger = logging.getLogger('root')
FORMAT = "[%(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
logger.setLevel(logging.DEBUG)

config = yaml.safe_load(open(os.path.join(sys.path[0], "config.yml")))
local_timezone = sun.get_timezone(config['city'])
cam = cam.Cam(config['camera'])
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


@app.route('/api/camera/preview', methods=['GET'])
def take_preview():
    path = config['path']['preview']
    cam.take_preview_photo(path)
    return send_file(path, mimetype='image/jpg')


@app.route('/api/camera/timelapse', methods=['GET'])
def make_timelapse():
    if (not cam.is_available()):
        abort(400, 'Camera is busy')
    duration = int(request.args.get('duration'))
    interval = int(request.args.get('interval'))

    path = config['path']['timelapse'] + '/' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    logger.debug("Making dir: %s", path)
    os.makedirs(path)
    cam.take_timelapse(path, duration, interval)
    return jsonify({"status": cam.get_status(), "path": path})


@app.route('/api/camera/sheduletimelapse', methods=['GET'])
def schedule_timelapse():
    if (not cam.is_available()):
        abort(400, 'Camera is busy')
    delay = int(request.args.get('delay'))
    duration = int(request.args.get('duration'))
    interval = int(request.args.get('interval'))

    path = config['path']['timelapse'] + '/' + datetime.datetime.now().strftime('%Y-%m-%d_%H-%M-%S')
    logger.debug("Making dir: %s", path)
    os.makedirs(path)
    cam.schedule_timelapse(delay, path, duration, interval)
    return jsonify({"status": cam.get_status(), "path": path})


@app.route('/api/camera/status', methods=['GET'])
def get_status():
    return jsonify(cam.get_status())


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

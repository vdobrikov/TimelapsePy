import logging
import time
import picamera
import threading
from collections import namedtuple
from enum import Enum

logger = logging.getLogger('root')
FORMAT = "[%(levelname)s %(filename)s:%(lineno)s - %(funcName)20s() ] %(message)s"
logging.basicConfig(level=logging.DEBUG, format=FORMAT)
logger.setLevel(logging.DEBUG)


class CamException(Exception):
    def __init__(self, message):
        super().__init__(message)


class IllegalStatusCamException(CamException):
    def __init__(self, message):
        super().__init__(message)


class State(object):
    IDLE = 'IDLE'
    SCHEDULED = 'SCHEDULED'
    RUNNING = 'RUNNING'
    CANCELLED = 'CANCELLED'
    FAILED = 'FAILED'


CamStatus = namedtuple('CamStatus', ['state', 'timelapse_delay', 'timelapse_duration', 'timelapse_interval'])


class Cam(object):
    _status = CamStatus(None, None, None, None)
    _timer = None
    _thread = None
    _config = None

    def __init__(self, config):
        self._set_status(CamStatus(State.IDLE, None, None, None))
        self._config = config

    def _set_status(self, status):
        logger.debug(status)
        self._status = status

    def get_status(self):
        return self._status

    def is_available(self):
        return self.get_status().state not in (State.SCHEDULED, State.RUNNING)


    def take_preview_photo(self, path):
        width = self._config['preview_resolution']['width']
        height = self._config['preview_resolution']['height'] 
        logger.debug("path=%s resolution=[%sx%s]", path, width, height)
        camera = picamera.PiCamera()
        self._apply_cam_config(camera, self._config)
        camera.resolution = (width, height)
        try:
            camera.capture(path)
        except Exception as e:
            logging.error("Failed to camera.capture(): %s", e)
        finally:
            camera.close()

    def schedule_timelapse(self, delay, path, duration, interval):
        logger.debug("delay=%s path=%s duration=%s interval=%s", delay, path, duration, interval)
        if self.get_status().state in (State.SCHEDULED, State.RUNNING):
            raise IllegalStatusCamException("Task is already scheduled")
        timer = threading.Timer(delay, self._take_timelapse, (path, duration, interval))
        timer.start()
        self._timer = timer
        self._set_status(CamStatus(State.SCHEDULED, delay, duration, interval))

    def take_timelapse(self, path, duration, interval):
        logger.debug("path=%s duration=%s interval=%s", path, duration, interval)
        thread = threading.Thread(target=self._take_timelapse, args=(path, duration, interval))
        thread.start()
        self._thread = thread

    def _take_timelapse(self, path, duration, interval):
        logger.debug("path=%s duration=%s interval=%s", path, duration, interval)
        if self.get_status().state == State.RUNNING:
            raise IllegalStatusCamException("Task is already running")
        self._set_status(CamStatus(State.RUNNING, 0, duration, interval))
        camera = picamera.PiCamera()
        self._apply_cam_config(camera, self._config)
        start = time.time()
        try:
            for i, filename in enumerate(
                    camera.capture_continuous(path + '/image{counter:06d}.jpg')):
                logger.debug("Timelapse: %s", filename)
                time.sleep(interval)
                elapsed = time.time() - start
                if self.get_status().state == State.CANCELLED:
                    logger.debug("Cancel timelapse")
                    self._set_status(CamStatus(State.IDLE, None, None, None))
                    break
                if elapsed > duration:
                    logger.debug("Finish timelapse")
                    self._set_status(CamStatus(State.IDLE, None, None, None))
                    break
        except Exception as e:
            logger.error("Failed to take timelapse %s", e)
            self._set_status(CamStatus(State.FAILED, None, None, None))
        finally:
            camera.close()

    def cancel(self):
        logger.debug("cancel")
        if self._status == State.RUNNING:
            self._set_status(CamStatus(State.CANCELLED, None, None, None))
        if self._status == State.SCHEDULED:
            self._timer.cancel()
            self._set_status(CamStatus(State.IDLE, None, None, None))

    def _apply_cam_config(self, camera, config):
        logger.debug("camera=%s config=%s", camera, config)
        if config['resolution']:
            camera.resolution = (
                config['resolution']['width'],
                config['resolution']['height']
            )

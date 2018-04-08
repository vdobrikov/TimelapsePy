import logging
import sched
import time
import picamera
from enum import Enum

logging.basicConfig(level=logging.DEBUG)


class CamException(object):
    pass


class IllegalStatusCamException(CamException):
    pass


class Status(Enum):
    IDLE = 0
    SCHEDULED = 1
    RUNNING = 2
    CANCELLED = 3
    FAILED = 4


class Cam(object):
    _status = Status.IDLE
    _scheduler = sched.scheduler(time.time, time.sleep)
    _scheduled_task = None
    _config = None

    def __init__(self, config):
        self._set_status(Status.IDLE)
        self._config = config

    def _set_status(self, status):
        logging.debug("Setting status: %s", status)
        self._status = status

    def get_status(self):
        return self._status

    def take_preview_photo(self):
        camera = picamera.PiCamera()
        camera.resolution = (
            self._config.resolution.preview.width,
            self._config.resolution.preview.height
        )
        try:
            camera.capture("static/img/preview.jpg")
        except:
            logging.error("Failed to take one shot")
        finally:
            camera.close()

    def schedule(self, delay, duration, interval):
        logging.debug("Scheduling with delay %s sec" % delay)
        if self.get_status() in (Status.SCHEDULED, Status.RUNNING):
            raise IllegalStatusCamException
        self._set_status(Status.SCHEDULED)
        self._scheduled_task = self._scheduler.enter(delay, 1, self.take_timelapse(), (duration, interval))
        self._scheduler.run()

    def take_timelapse(self, duration, interval):
        logging.debug("Start taking timelapse")
        if self.get_status() in (Status.SCHEDULED, Status.RUNNING):
            raise IllegalStatusCamException
        self._set_status(Status.RUNNING)
        camera = picamera.PiCamera()
        start = time.time()
        time.clock()
        try:
            for i, filename in enumerate(
                    camera.capture_continuous('image{counter:06d}.jpg')):
                logging.debug("Timelapse: %s" % filename)
                time.sleep(interval)
                elapsed = time.time() - start
                if self._status == Status.CANCELLED:
                    logging.debug("Cancel timelapse")
                    self._set_status(Status.IDLE)
                    break
                if elapsed > duration:
                    logging.debug("Finish timelapse")
                    self._set_status(Status.IDLE)
                    break
        except:
            logging.error("Failed to make timelapse")
            self._set_status(Status.FAILED)
        finally:
            camera.close()

    def cancel(self):
        logging.debug("Cancel")
        if self._status == Status.RUNNING:
            self._set_status(Status.CANCELLED)
        if self._status == Status.SCHEDULED:
            self._scheduler.cancel(self._scheduled_task)
            self._set_status(Status.IDLE)

    def apply_cam_config(self, config):
        logging.debug("Set config %s" % config)
        if config['resolution']:
            self.camera.resolution = (
                config['resolution']['width'],
                config['resolution']['height']
            )

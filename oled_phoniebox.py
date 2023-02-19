#!/usr/bin/python3
# -*- coding: utf-8 -*-

from PIL import ImageFont, Image, ImageDraw
from luma.core.render import canvas
from luma.core import cmdline, error
from luma.core.image_composition import ImageComposition, ComposableImage
from time import sleep
from datetime import timedelta
from mpd import MPDClient
import base64
import re
import os
import io
import sys
import signal
import configparser
import math
import RPi.GPIO as GPIO

# GPIO16 mutes the power stage.
# GPIO26 shuts down the power stage.
# $ raspi-gpio get | egrep '16|26'
# GPIO 16: level=1 fsel=0 func=INPUT
# GPIO 26: level=1 fsel=0 func=INPUT
# off
# raspi-gpio set 16 op # output
# raspi-gpio set 26 op
# on
# raspi-gpio set 26 ip
# raspi-gpio set 16 ip # input

GPIO.setmode(GPIO.BCM)

# if the pins are not configured, do nothing
def disable_hifiberry():
    if "mute" in config["HIFIBERRY"] and "power" in config["HIFIBERRY"]:
        GPIO.setup(config["HIFIBERRY"]["mute"], GPIO.OUT)
        sleep(0.5)
        GPIO.setup(config["HIFIBERRY"]["power"], GPIO.OUT)


def enable_hifiberry():
    if "mute" in config["HIFIBERRY"] and "power" in config["HIFIBERRY"]:
        GPIO.setup(config["HIFIBERRY"]["power"], GPIO.IN)
        sleep(0.5)
        GPIO.setup(config["HIFIBERRY"]["mute"], GPIO.IN)


# used googles material for the logos https://fonts.google.com/icons?preview.text=%E2%8F%BB&preview.text_type=custom&icon.set=Material+Icons&icon.query=power
# then IrfanView to convert them:
# image->show channel->alpha (or any)
# ctrl + r 	height 64
# shift v 128x64 center
# image->decrease color depth 2
# saved as png
# then did base64 -w 0 on the images
def get_logo():
    logo = {
        "card": "iVBORw0KGgoAAAANSUhEUgAAAIAAAABAAQMAAADoGO08AAAABlBMVEUAAAD///+l2Z/dAAAACXBIWXMAAB7CAAAewgFu0HU+AAAAUUlEQVQ4jWNgGMyA8T8YNMAFmCECB+AC7BCBB3ABfojAB0oE5CECP6isAkigqgALkKaCGu7Y//8vxe5gYGClQ4gNWRWEBTASLkbSxkj8gxEAAIJlKJ3Y53v8AAAAAElFTkSuQmCC",
        "music_note": "iVBORw0KGgoAAAANSUhEUgAAAIAAAABAAQMAAADoGO08AAAABlBMVEUAAAD///+l2Z/dAAAACXBIWXMAAB7CAAAewgFu0HU+AAAAYklEQVQ4jWNgoCdg/P+/AV3gAIoAMzEqDqCraCCognJbfjCgAmZ0gVEV+FUw/0YT4P+PJiCPLlBPUOA/mgAjLQSYidHygUQBoNMfoArUoyU5BntMgQZUAf5/qHwGpi8MdAUATb1mLPOSjm4AAAAASUVORK5CYII=",
        "pause": "iVBORw0KGgoAAAANSUhEUgAAAIAAAABAAQMAAADoGO08AAAABlBMVEUAAAD///+l2Z/dAAAACXBIWXMAAB7CAAAewgFu0HU+AAAAJklEQVQ4jWNgGFpA/v8P/v8/kATs//+Q//9nVGBUYFgIICftoQAAWYK9iYl2zxoAAAAASUVORK5CYII=",
        "pause_circle": "iVBORw0KGgoAAAANSUhEUgAAAIAAAABAAQMAAADoGO08AAAABlBMVEUAAAD///+l2Z/dAAAACXBIWXMAAB7CAAAewgFu0HU+AAAAr0lEQVQ4ja2TQQ7DIAwEQTlw5Al5Sp6WPC1P4Qkcc6i6hVAp3iVtqiq+eWTwYtbO/R1ewfzkPAArgQhsBCbgQQAlqEcFiwFDBYnvBLIC22Y6BVbrrAAQIQp8A4eyoYH1K4jZai/jCUlAVBCyfV1sFQTuqthuqLhXadCK9zwuJkbg+l+6r3QfwJH3htktZa08ngLrws64Qa3tWajr16P25aUb+c79vYmAkxMlFgW/xwuNGicFlFNGbAAAAABJRU5ErkJggg==",
        "play": "iVBORw0KGgoAAAANSUhEUgAAAIAAAABAAQMAAADoGO08AAAABlBMVEUAAAD///+l2Z/dAAAACXBIWXMAAB7CAAAewgFu0HU+AAAAgUlEQVQ4jdXSwQnAIAxA0QxQcIHSrOpojuIIHj2IqR7zU3rXm4/wUVTk9HUTUoBMqABtnBiESTBU1QonGmEQUFVDNRmqCxrBV1djcsJXNxSCq66GdU4EqL/R3eA5wsE6wV9OP64vgEnwzdUIz1AIGcDHVjQlhQ9TCGjKg71chBPXC+guVzpvSA/2AAAAAElFTkSuQmCC",
        "play_circle": "iVBORw0KGgoAAAANSUhEUgAAAIAAAABAAQMAAADoGO08AAAABlBMVEUAAAD///+l2Z/dAAAACXBIWXMAAB7CAAAewgFu0HU+AAAA9ElEQVQ4jbWTMQ7DIAxFbWVgzNgxvUF7gtIjdewQNRyNozB2zJAhQ1RqEkpsM3SKpUTi6dsY/AE4MLq3XOMQJTAxBpkR4yyAnS4fAeIdRRFcAAbHa1KBllc1tDAjA62nNA46yke+7y39egZe5ZejL7Ica3qnQcsaHeFMYG8VAzypMwF6AZoAloDfgU9nbSQISfcLEtsRUCoWoXBAY0CZEh0qhdcg/E3hu2zbqpRZK4I+i+cAq+PrC6I7fWhwFZcM65zZGOpBVaOshm2LLEdXCuVIlmq4pUzYvh1oWybjWtYoWdtJa9fmr55H9YAwqicGpwkOjC8IWW9N6FgJuAAAAABJRU5ErkJggg==",
        "power": "iVBORw0KGgoAAAANSUhEUgAAAIAAAABAAQMAAADoGO08AAAABlBMVEUAAAD///+l2Z/dAAAACXBIWXMAAB7CAAAewgFu0HU+AAAAsklEQVQ4jc3RQQrDIBAFUCWLWXoEb1IvFqxH8yhzBJcupFOni/CnEEug0EoQfCTfCd+5n66tvgHx96EQezz7SrwVnIKJCSehRhwwJSg0BM1AiAodQa9FSDrYWEFWyCvYFW4rGArpEnSFuILPn7x+I12CXTccPR/bGaQj6Aximf2aGursF0F7JWxOD6Zsmq9HhO3h3L0CeCnzAXDSguDZJZFhIIp0AyTCBrzYzBliI/5wPQFov1oTW3AKDgAAAABJRU5ErkJggg==",
        "volume": "iVBORw0KGgoAAAANSUhEUgAAAIAAAABAAQMAAADoGO08AAAABlBMVEUAAAD///+l2Z/dAAAACXBIWXMAAB7CAAAewgFu0HU+AAAAw0lEQVQ4jcWTvQ0DIQyFD1FQMgKjsFkwUiQ2Shk5FWswwpVXnOKQjmeXkS50fDLPf49t++8hdXeVFXjtCEI9NXgjSFVQNpOgauE0AAhFSOOE/LECL+Qgb5iSAOJMeoMyJshQhrQVuIdIp7TmEGkjEYI9GsAA+hFUxBkwoh0a6Ihunljgx88apg5detfNtaHbB/CcgJcRfofccepJ7rgXs6igd+uFERg7GMNshfIAkLkwAGPLWAXu1tpem99VlLAf6OLzAfmrobheyJl4AAAAAElFTkSuQmCC",
    }
    for img in logo:
        logo[img] = Image.open(io.BytesIO(base64.b64decode(logo[img]))).convert(device.mode)
    return logo


def get_config(file):
    base_path = os.path.abspath(os.path.dirname(__file__))
    font_path = os.path.join(base_path, "fonts", "Bitstream Vera Sans Mono Roman.ttf")  # Tried Inconsolata and VT323, but this one looked better
    config = configparser.ConfigParser()
    config.read(os.path.join(base_path, file))
    config_dict = {"PATH": {}, "FONT": {}}

    for section in config.sections():
        config_dict[section] = {}
        for key in config.options(section):
            config_dict[section][key] = config.get(section, key)

    config_dict["PATH"]["base_path"] = base_path
    config_dict["PATH"]["images"] = os.path.join(base_path, "images")
    config_dict["FONT"]["standard"] = ImageFont.truetype(font_path, 12)
    config_dict["FONT"]["small"] = ImageFont.truetype(font_path, 10)
    config_dict["DISPLAY"]["refresh"] = int(config_dict["DISPLAY"]["refresh"])

    if "mute" in config_dict["HIFIBERRY"]:
        config_dict["HIFIBERRY"]["mute"] = int(config_dict["HIFIBERRY"]["mute"])
    if "power" in config_dict["HIFIBERRY"]:
        config_dict["HIFIBERRY"]["power"] = int(config_dict["HIFIBERRY"]["power"])
    return config_dict


def get_device(deviceName):
    actual_args = ["-d", deviceName]
    parser = cmdline.create_parser(description="luma.examples arguments")
    args = parser.parse_args(actual_args)
    if args.config:
        config = cmdline.load_config(args.config)
        args = parser.parse_args(config + actual_args)
    try:
        device = cmdline.create_device(args)
    except error.Error as e:
        parser.error(e)
    return device


def get_wifi():
    wififile = "/proc/net/wireless"

    if not os.path.exists(wififile):
        return "--"

    wifirateFile = open(wififile)
    wifiline = wifirateFile.readlines()[2]  # last line
    wifirateFile.close()
    return int(math.ceil(float(re.split(r"\s+", wifiline)[3])))


def sigterm_handler(*_):
    draw_logo("power")
    sleep(config["DISPLAY"]["refresh"])
    sys.exit(0)


def draw_logo(image_name):
    device.display(logo[image_name])
    sleep(config["DISPLAY"]["refresh"])


def time_convert(s):
    result = re.search(r"^\d+:([^.]+)\.*", str(timedelta(seconds=float(s))))
    return result.groups()[0]


def mpc_state_convert(s):
    state = {
        "play": 2,
        "pause": 1,
        "stop": 0,
    }
    return state[s]


def mpc_file_convert(s):
    name = {
        #
        "artist": "",
        "title": "",
        "album": "",
    }

    result = re.search(r"^(.+)/([^/]+)\.[^.]+$", s)  # Kinderlieder/Kinderlieder Klassiker/1/Track.02.mp3
    if result.groups()[0].startswith("http"):
        return name
    name["artist"] = result.groups()[0]
    name["title"] = result.groups()[1]
    return name


def mpc_get_data(key, data, altdata):
    if key in data:
        return data[key]

    if key in altdata:
        return altdata[key]

    return ""


def mpc_get_alt_data(data):
    alt_data = {
        "song": -1,
        "playlistlength": -1,
        "elapsed": 0,
        "duration": 1,  # cant be zero (division). also 0 would mean 100%. with 1, its 0%
        "file": "/dev/null",
        "artist": "",
        "title": "",
        "album": "",
    }

    if "file" in data:
        alt_data["file"] = data["file"]
        alt_data.update(mpc_file_convert(data["file"]))

    return alt_data


def mpc_get_track_num(key, data, alt_data):
    return int(mpc_get_data(key, data, alt_data)) + 1


def mpc_get_track_time(key, data, alt_data):
    return time_convert(mpc_get_data(key, data, alt_data))


def mpc_get_track_time_percent(data, alt_data):
    current_seconds = float(mpc_get_data("elapsed", data, alt_data))
    total_seconds = float(mpc_get_data("duration", data, alt_data))
    percent = 100 / total_seconds * current_seconds
    return percent


def mpc_client():
    mpdc.connect(config["MPD"]["socket"])
    # {'volume': '30', 'repeat': '0', 'random': '0', 'single': '0', 'consume': '0', 'partition': 'default', 'playlist': '12', 'playlistlength': '5', 'mixrampdb': '0.000000', 'state': 'play', 'song': '0', 'songid': '56',
    # 'time': '26:79', 'elapsed': '26.377', 'bitrate': '320', 'duration': '78.968', 'audio': '44100:24:2', 'nextsong': '1', 'nextsongid': '57'}
    # of those, volume, playlistlength (starts with 0), state (play, pause, stop), song (currently playing song in list, starts with 0), elapsed and duration are of interest.
    status = mpdc.status()
    # {'file': 'Kinderlieder/Kinderlieder Klassiker/1/Track.05.mp3', 'last-modified': '2021-11-07T09:51:56Z', 'time': '87', 'duration': '87.222', 'pos': '4', 'id': '60'}
    # {'file': 'Musik/2008 For Emma, Forever Ago (L)/01. Flume.mp3', 'last-modified': '2013-07-02T12:56:55Z', 'time': '219', 'duration': '219.062', 'pos': '0', 'id': '61',
    # 'artist': 'Bon Iver', 'title': 'Flume', 'album': 'For Emma, Forever Ago', 'track': '1', 'date': '2008', 'genre': 'Folk-rock, Indie folk'}
    # first row is always present. all in all file, artist, title, album are of interest.
    song = mpdc.currentsong()
    mpdc.close()
    mpdc.disconnect()

    alt_data = mpc_get_alt_data(song)
    return {
        "status": mpc_state_convert(status["state"]),
        "volume": status["volume"],
        "track_num_current": mpc_get_track_num("song", status, alt_data),
        "track_num_total": mpc_get_track_num("playlistlength", status, alt_data),
        "track_time_elapsed": mpc_get_track_time("elapsed", status, alt_data),
        "track_time_total": mpc_get_track_time("duration", status, alt_data),
        "track_time_percent": mpc_get_track_time_percent(status, alt_data),
        "file_path": mpc_get_data("file", song, alt_data),
        "artist": mpc_get_data("artist", song, alt_data),
        "title": mpc_get_data("title", song, alt_data),
        "album": mpc_get_data("album", song, alt_data),
    }


class TextImage:
    def __init__(self, text, font):
        draw = ImageDraw.Draw(Image.new(device.mode, (device.width, device.height)))
        self.left, self.top, self.right, self.bottom = draw.textbbox((0, 0), text, font=font)
        self.image = Image.new(device.mode, (self.right, self.bottom))
        draw = ImageDraw.Draw(self.image)
        draw.text((0, 0), text, font=font, fill="white")
        self.width = self.right
        self.height = self.bottom
        del draw


def compose_text(text, cords):
    return ComposableImage(TextImage(text, cords[2]).image, position=(cords[0], cords[1]))


def get_coordinates():
    font_std = config["FONT"]["standard"]
    font_small = config["FONT"]["small"]
    cords = {
        # horizontal dividers. 64 pixels (0-63) divided in 4 sections a 16 pixels
        "section0_y": 0,  # start
        "section1_y": 15,  # TITLE
        "section2_y": 31,  # ARTIST
        "section3_y": 47,  # ALBUM
        "section4_y": 63,  # STATUS. no need to draw
        # vertical dividers for status section. 128 pixels (0-127) divided in 4 sections. The first two need 5 chars, the other two 4 chars.
        # this makes 36 pixels for the left and 28 for the right side
        "section4_x0": 0,  # TIME START
        "section4_x1": 35,  # TIME
        "section4_x2": 71,  # TRACK
        "section4_x3": 99,  # VOLUME
        "section4_x4": 127,  # WIFI. no need to draw
        "scroll": 10,  # pixel advancement per tick
    }

    cords["title"] = [0, cords["section0_y"] + 1, font_std]
    cords["artist"] = [0, cords["section1_y"] + 1, font_std]
    cords["album"] = [0, cords["section2_y"] + 1, font_std]
    cords["track_time_elapsed"] = [cords["section4_x0"], cords["section3_y"] + 2, font_small]
    cords["track"] = [cords["section4_x1"] + 2, cords["section3_y"] + 1, font_small]
    cords["volume"] = [cords["section4_x2"] + 2, cords["section3_y"] + 1, font_small]
    cords["wifi"] = [cords["section4_x3"] + 2, cords["section3_y"] + 1, font_small]
    cords["progress1_start"] = [cords["section4_x0"], cords["section4_y"]]
    cords["progress2_start"] = [cords["section4_x0"], cords["section4_y"] - 1]
    return cords


def get_outlines(cords):
    return [
        # horizontal dividers
        # [0, cords["section1_y"], device.width, cords["section1_y"]],  # x,y to x,y
        # [0, cords["section2_y"], device.width, cords["section2_y"]],
        [0, cords["section3_y"], device.width, cords["section3_y"]],
        # vertical dividers
        [cords["section4_x1"], cords["section3_y"], cords["section4_x1"], device.height],
        [cords["section4_x2"], cords["section3_y"], cords["section4_x2"], device.height],
        [cords["section4_x3"], cords["section3_y"], cords["section4_x3"], device.height],
    ]


def get_scroll_count(image_width, screen_width, scroll_tick):
    if image_width <= screen_width:
        return 0
    offscreen = image_width - screen_width
    return math.ceil(offscreen / scroll_tick)


def add_image(current, coordinates, image_composition, key, text):
    image = compose_text(text, coordinates[key])
    current[key] = {
        #
        "text": text,
        "image": image,
    }
    image_composition.add_image(image)
    current[key]["max_scroll"] = get_scroll_count(image.width, device.width, coordinates["scroll"])
    current[key]["cur_scroll"] = 0


def update_images(current, image_composition, coordinates, new):
    # if there is a content update, remove the old image, render and add the new content
    for key in new:
        if not key in coordinates:
            continue
        if not key in current:  # first iteration
            add_image(current, coordinates, image_composition, key, new[key])

        if current[key]["text"] != new[key]:  # updated content
            image_composition.remove_image(current[key]["image"])
            add_image(current, coordinates, image_composition, key, new[key])
            continue

        if current[key]["max_scroll"] != 0:  # scrolling
            if current[key]["cur_scroll"] == current[key]["max_scroll"]:
                # reset image
                current[key]["image"].offset = (0, 0)
                current[key]["cur_scroll"] = 0
                continue

            # scroll image
            current[key]["image"].offset = (current[key]["image"].offset[0] + coordinates["scroll"], 0)
            current[key]["cur_scroll"] += 1

    return current


# this skips every other mpc refresh to save power.
def update_refresh_counter(count):
    skip = 1
    if count == config["DISPLAY"]["refresh"] or count == 0:
        count = 0
        skip = 0
    count += 1
    return count, skip


def update_hifiberry_counter(count):
    off = 0
    if count == 5:
        count = 0
        off = 1
    count += 1
    return count, off


def update_state(state):
    state["count"], state["skip"] = update_refresh_counter(state["count"])
    if state["skip"] == 1:
        return state

    mpc = mpc_client()

    # the if statements here indicate distinct events, where actions could be added
    if mpc["status"] != state["status"]:
        state["wifi"] = get_wifi()  # a state change might be a good time to update wifi signal
        state["status"] = mpc["status"]

    if mpc["volume"] != state["volume"]:
        state["volume"] = mpc["volume"]

    current_id = mpc["artist"] + mpc["title"] + str(mpc["track_num_current"]) + mpc["track_time_total"]

    if current_id != state["id"]:  # track change
        state["id"] = current_id
        state["album"] = mpc["album"]
        state["title"] = mpc["title"]
        state["artist"] = mpc["artist"]

    # below are non-events
    if mpc["file_path"].startswith("http"):  # what is in track_time_percent or others when there is a stream running? i doubt this file check is good
        state["progress"] = device.width
    else:
        state["progress"] = int(math.ceil(device.width * mpc["track_time_percent"] / 100))

    state["track_time_elapsed"] = mpc["track_time_elapsed"]
    state["track_num_current"] = mpc["track_num_current"]
    state["track_num_total"] = mpc["track_num_total"]

    return state


def pad_state(state):
    if "volume" in state:
        padding = " "
        if state["volume"] == 100:
            padding = ""
        state["volume"] = "V" + padding + str(state["volume"])

    if state["status"] == 1:
        state["track_time_elapsed"] = "PAUSE"
    else:
        if len(state["track_time_elapsed"]) == 4:
            state["track_time_elapsed"] = " " + state["track_time_elapsed"]

    if "track_num_current" in state and "track_num_total" in state:
        track_cur = str(state["track_num_current"])
        track_total = str(state["track_num_total"])
        if len(track_cur) == 1:
            track_cur = "0" + track_cur
        if len(track_total) == 1:
            track_total = "0" + track_total
        state["track"] = track_cur + "/" + track_total

    if "wifi" in state:
        wifi = str(state["wifi"])
        padding = " "
        if len(wifi) == 3:
            padding = ""
        state["wifi"] = "W" + padding + wifi

    return state


def save_power(state):
    if state["status"] == 0 and state["save_power"] == 1:  # no need to render old state if nothing happens to save power
        return 1

    if state["status"] == 0 and state["save_power"] == 0:
        state["hifiberry_shutdown_wait"], off = update_hifiberry_counter(state["hifiberry_shutdown_wait"])
        if off == 1:
            state["save_power"] = 1
            disable_hifiberry()
            draw_logo("card")  # instead of redrawing every cycle, draw once
            return 1

    if state["status"] != 0 and state["save_power"] == 1:  # reenable sound
        enable_hifiberry()
        state["save_power"] = 0
        state["hifiberry_shutdown_wait"] = 0

    return 0


def main():
    image_composition = ImageComposition(device)
    coordinates = get_coordinates()
    current_display = {}
    current_state = {
        #
        "status": 0,
        "volume": 0,
        "id": ".",
        "count": 0,
        "hifiberry_shutdown_wait": 0,
        "save_power": 0,
    }

    try:
        while True:
            current_state = update_state(current_state)
            if save_power(current_state):
                continue

            current_display = update_images(current_display, image_composition, coordinates, pad_state(current_state.copy()))

            with canvas(device, background=image_composition()) as draw:
                image_composition.refresh()
                for line in get_outlines(coordinates):
                    draw.line(line[0:4], fill="white")
                # progress bar
                draw.line(
                    (coordinates["progress1_start"][0], coordinates["progress1_start"][1], current_state["progress"], coordinates["progress1_start"][1]),
                    fill="white",
                )
                draw.line(
                    (coordinates["progress2_start"][0], coordinates["progress2_start"][1], current_state["progress"], coordinates["progress2_start"][1]),
                    fill="white",
                )
            sleep(1)
    except KeyboardInterrupt:
        pass

    return


if __name__ == "__main__":
    config = get_config("oled_phoniebox.conf")
    device = get_device(config["DISPLAY"]["controller"])
    device.contrast(int(config["DISPLAY"]["contrast"]))
    logo = get_logo()
    mpdc = MPDClient()
    signal.signal(signal.SIGTERM, sigterm_handler)
    draw_logo("music_note")
    main()

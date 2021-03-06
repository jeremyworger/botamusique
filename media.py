import re
import urllib
import logging
import json
import http.client
import struct
import os


def get_radio_server_description(url):
    p = re.compile('(https?\:\/\/[^\/]*)', re.IGNORECASE)
    res = re.search(p, url)
    base_url = res.group(1)
    url_icecast = base_url + '/status-json.xsl'
    url_shoutcast = base_url + '/stats?json=1'
    title_server = None
    try:
        request = urllib.request.Request(url_shoutcast)
        response = urllib.request.urlopen(request)
        data = json.loads(response.read().decode("utf-8"))
        title_server = data['servertitle']
        logging.info("TITLE FOUND SHOUTCAST: " + title_server)
    except urllib.error.HTTPError:
        pass
    except http.client.BadStatusLine:
        pass
    except ValueError:
        return False

    if not title_server:
        try:
            request = urllib.request.Request(url_icecast)
            response = urllib.request.urlopen(request)
            data = json.loads(response.read().decode('utf-8', errors='ignore'), strict=False)
            title_server = data['icestats']['source'][0]['server_name'] + ' - ' + data['icestats']['source'][0]['server_description']
            logging.info("TITLE FOUND ICECAST: " + title_server)
            if not title_server:
                title_server = url
        except urllib.error.URLError:
            title_server = url
        except urllib.error.HTTPError:
            return False
        except http.client.BadStatusLine:
            pass
    return title_server


def get_radio_title(url):
    request = urllib.request.Request(url, headers={'Icy-MetaData': 1})
    try:

        response = urllib.request.urlopen(request)
        icy_metaint_header = int(response.headers['icy-metaint'])
        if icy_metaint_header is not None:
            response.read(icy_metaint_header)

            metadata_length = struct.unpack('B', response.read(1))[0] * 16  # length byte
            metadata = response.read(metadata_length).rstrip(b'\0')
            logging.info(metadata)
            # extract title from the metadata
            m = re.search(br"StreamTitle='([^']*)';", metadata)
            if m:
                title = m.group(1)
                if title:
                    return title.decode()
    except (urllib.error.URLError, urllib.error.HTTPError):
        pass
    return 'Unable to get the music title'


def get_url(string):
    if string.startswith('http'):
        return string
    p = re.compile('href="(.+)"', re.IGNORECASE)
    res = re.search(p, string)
    if res:
        return res.group(1)
    else:
        return False


def get_size_folder(path):
    folder_size = 0
    for (path, dirs, files) in os.walk(path):
        for file in files:
            filename = os.path.join(path, file)
            folder_size += os.path.getsize(filename)
    return int(folder_size / (1024 * 1024))


def clear_tmp_folder(path, size):
    if size == -1:
        return
    elif size == 0:
        for (path, dirs, files) in os.walk(path):
            for file in files:
                filename = os.path.join(path, file)
                os.remove(filename)
    else:
        if get_size_folder(path=path) > size:
            all_files = ""
            for (path, dirs, files) in os.walk(path):
                all_files = [os.path.join(path, file) for file in files]
                all_files.sort(key=lambda x: os.path.getmtime(x))
            size_tp = 0
            print(all_files)
            for idx, file in enumerate(all_files):
                size_tp += os.path.getsize(file)
                if int(size_tp/(1024*1024)) > size:
                    logging.info("Cleaning tmp folder")
                    to_remove = all_files[idx:]
                    print(to_remove)
                    for f in to_remove:
                        logging.debug("Removing " + f)
                        os.remove(os.path.join(path, f))
                    return

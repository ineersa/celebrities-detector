import io
import json
import logging
import os
import re
import time
import urllib.request
import uuid

import requests
from bs4 import BeautifulSoup
from werkzeug.utils import secure_filename
from PIL import Image
from models.celebrity_image import CelebrityImage
logger = logging.getLogger(name="Download Images")

class CelebrityImagesDownload(object):
    def __init__(self, db):
        self.keywords = ['', ' face', ' side face', ' looking up', ' looking down', ' wearing glasses', ' happy face', ' nose', ' close up', ' young', ' angry']
        self.db = db
        self.headers = {"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/103.0.5060.114 Safari/537.36"}
        logger.info("Init")


    def _download_image_and_save(self, url, celebrity):
        try:
            logger.info(f"Downloading image for {url['original']}")
            req = urllib.request.Request(url['original'], headers={"User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/101.0.4951.54 Safari/537.36"})
            raw_img = urllib.request.urlopen(req, timeout=5).read()
            filename = secure_filename(f"{uuid.uuid4().hex}.jpg")
            file_path = os.path.join(f"./images/celebrity/{celebrity.id}/", filename)
            uri_path = os.path.join(f"/images/celebrity/{celebrity.id}/", filename)
            os.makedirs(os.path.dirname(file_path), exist_ok=True)
            image = Image.open(io.BytesIO(raw_img))
            image.convert("RGB").save(file_path, "JPEG")
            new_image = CelebrityImage(
                celebrity_id=celebrity.id,
                image_path=uri_path
            )
            self.db.session.add(new_image)
            self.db.session.commit()
            logger.info(f"Downloaded image for {url['original']} DONE")
        except Exception as e:
            logger.error(f"Downloaded image for {url['original']} FAILED")
            logger.error(e)

    def get_original_images(self, soup):

        """
        https://kodlogs.com/34776/json-decoder-jsondecodeerror-expecting-property-name-enclosed-in-double-quotes
        if you try to json.loads() without json.dumps() it will throw an error:
        "Expecting property name enclosed in double quotes"
        """

        google_images = []

        all_script_tags = soup.select("script")

        # # https://regex101.com/r/48UZhY/4
        matched_images_data = "".join(re.findall(r"AF_initDataCallback\(([^<]+)\);", str(all_script_tags)))

        matched_images_data_fix = json.dumps(matched_images_data)
        matched_images_data_json = json.loads(matched_images_data_fix)

        # https://regex101.com/r/VPz7f2/1
        matched_google_image_data = re.findall(r'\"b-GRID_STATE0\"(.*)sideChannel:\s?{}}', matched_images_data_json)

        # https://regex101.com/r/NnRg27/1
        matched_google_images_thumbnails = ", ".join(
            re.findall(r'\[\"(https\:\/\/encrypted-tbn0\.gstatic\.com\/images\?.*?)\",\d+,\d+\]',
                       str(matched_google_image_data))).split(", ")

        thumbnails = [
            bytes(bytes(thumbnail, "ascii").decode("unicode-escape"), "ascii").decode("unicode-escape") for thumbnail in
            matched_google_images_thumbnails
        ]

        # removing previously matched thumbnails for easier full resolution image matches.
        removed_matched_google_images_thumbnails = re.sub(
            r'\[\"(https\:\/\/encrypted-tbn0\.gstatic\.com\/images\?.*?)\",\d+,\d+\]', "",
            str(matched_google_image_data))

        # https://regex101.com/r/fXjfb1/4
        # https://stackoverflow.com/a/19821774/15164646
        matched_google_full_resolution_images = re.findall(r"(?:'|,),\[\"(https:|http.*?)\",\d+,\d+\]",
                                                           removed_matched_google_images_thumbnails)

        full_res_images = [
            bytes(bytes(img, "ascii").decode("unicode-escape"), "ascii").decode("unicode-escape") for img in
            matched_google_full_resolution_images
        ]

        for index, (thumbnail, original) in enumerate(
                zip(thumbnails, full_res_images), start=1):
            google_images.append({
                "thumbnail": thumbnail,
                "original": original
            })
            if index == 10:
                break
        logger.info(f"Collected {len(google_images)} images to download")
        return google_images

    def _get_items(self, search):
        # search query parameters
        params = {
            "q": search,  # search query
            "tbm": "isch",  # image results
            "hl": "en",                   # language of the search
            "gl": "us",                   # country where search comes from
            "ijn": "0",                    # page number
        }
        html = requests.get("https://www.google.com/search", params=params, headers=self.headers, timeout=30)
        logger.info("Received html")
        soup = BeautifulSoup(html.text, "lxml")
        logger.info("soup done")
        original_images = self.get_original_images(soup)

        return original_images

    def search_images(self, celebrity):

        images = []
        for keyword in self.keywords:
            search = celebrity.name + keyword
            logger.info(f"Searching for {search}")
            images = images + (self._get_items(search))
        logger.info(f"Collected {len(images)} images to download")
        for image in images:
            self._download_image_and_save(image, celebrity)
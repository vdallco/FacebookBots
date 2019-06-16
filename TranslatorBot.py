#!/usr/bin/python
# -*- coding: utf-8 -*-

# Google Translate Bot
# Cody DallaValle's code
# Modified by Edwin 'Solly'
# Do not change the source encoding.

# !!! Auth token from Maximum Bots - Paintmin !!!
# http://maxbots.ddns.net/token/

# Make sure you have installed all the README.md requirements

from PIL import ImageFont, Image, ImageDraw
import urllib.request as myurllib
from datetime import datetime
import googletrans
import facebook
import platform
import random
import time
import json
import html
import sys
import re

categories = ['students', 'art', 'love', 'funny', 'life', 'sports', 'management', 'inspire']


# https://stackoverflow.com/questions/9662346/python-code-to-remove-html-tags-from-a-string
def clean_html(raw_html):
    cleanr = re.compile('<.*?>')
    return re.sub(cleanr, '', raw_html)


def fb_post(fb, p_id, img_sauce, post_txt):

    post_img = open(img_sauce, 'rb')
    resp = fb.put_photo(parent_object=p_id, connection_name='feed', message=post_txt, image=post_img)
    post_id = resp['id']
    return post_id


def txt_to_png(txt):

    img = Image.new('RGB', (1000, 900), color=(20, 20, 20))
    d = ImageDraw.Draw(img)

    font_path = "arial.ttf"
    if platform.system() == 'Linux':
        font_path = "/usr/share/fonts/truetype/noto/NotoSansMono-Regular.ttf"

    font = ImageFont.truetype(font=font_path, size=20)
    d.text((15, 15), txt, font=font, fill=(255, 255, 255))
    file_name = datetime.now().strftime('%Y.%m.%d.%H.%M.%S.%f') + ".png"
    img.save(file_name)
    return file_name


def pick_quote(quotes_api):

    src = myurllib.urlopen(quotes_api).read()
    src_obj = json.loads(src[1:-1])
    print(src_obj)
    return clean_html(src_obj['content'])


def rand_transl(str_sauce, trans_cli, dest_lang, langs):

    translated = trans_cli.translate(str_sauce, dest_lang)
    if not type(translated) is list:
        trans_txt = translated.text
    else:
        trans_txt = translated[0].text
    destlang_txt = list(langs.keys())[(list(langs.values())).index(dest_lang)]
    print("Translated into " + destlang_txt + ": " + trans_txt)
    return [dest_lang, trans_txt, destlang_txt]


def break_point(list_src, orig_src, breaks):

    for x in range(1, breaks):
        for y in range(int(len(orig_src) * (x/breaks)), int(len(orig_src) * ((x+1)/breaks))):
            if list_src[y] == ' ' and not '/"' == list_src[y - 1]:
                list_src[y] = '\n'
                break

    return str("".join(list_src))


def transl_request(seed_txt, trans_cli):

    # In later versions, seed_min and max will be evaluated according to the defined image size
    if len(seed_txt) > 100:
        seed_min, seed_max = 8, 10
    else:
        seed_min, seed_max = 10, 14

    rand_rounds = random.randint(seed_min, seed_max)

    current_txt = ['', html.unescape(seed_txt)]
    previous = current_txt[1]

    if len(current_txt[1]) > 50:
        swap = list(current_txt[1])
        current_txt[1] = break_point(swap, current_txt[1], int(len(current_txt[1]) / 25))

    translator_txt = u'Starting text: ' + current_txt[1]
    print("Starting text: " + current_txt[1])
    glangs = googletrans.LANGCODES
    avail_langs = list(glangs.keys())
    avail_langs.pop(avail_langs.index('Filipino'))  # Remove redundant entry in GoogleTranslate language codes list
    avail_langs.pop(avail_langs.index('english'))

    for x in range(0, rand_rounds):
        rand_lang = random.choice(avail_langs)
        dest_lang = glangs[rand_lang]
        current_txt = rand_transl(previous, trans_cli, dest_lang, glangs)
        # previous is used to put romanized text in img while showing bot_admin original output from rand_transl
        previous = current_txt[1]
        # Planning to introduce nltk to romanize previously broken characters from unsupported languages
        # http://www.lrec-conf.org/proceedings/lrec2010/pdf/30_Paper.pdf

        if len(current_txt[1]) > 50:
            swap = list(current_txt[1])
            current_txt[1] = break_point(swap, current_txt[1], int(len(current_txt[1])/25))

        translator_txt += current_txt[2] + ": " + current_txt[1] + '\n'
        avail_langs.pop(avail_langs.index(current_txt[2]))

    to_english = trans_cli.translate(current_txt[1], "en")

    if not type(to_english) is list:
        current_txt = to_english.text
    else:  # if there are multiple translations, just use the first
        current_txt = to_english[0].text
    print("Back to English: " + current_txt)

    return [html.unescape(seed_txt), translator_txt, current_txt]


def post_randtransl(fb, quoapi, trns, p_id):

    transl_target = pick_quote(quoapi)
    while len(transl_target) > 120:  # Limit quote len to avoid output view issues
        transl_target = pick_quote(quoapi)
    translate = transl_request(transl_target, trns)
    img_file = txt_to_png(translate[1] + '\n' + translate[2])

    if len(translate[0]) > 50:
        swap = list(translate[0])
        translate[0] = break_point(swap, translate[0], int(len(translate[0])/25))

    txt_to_post = str(u'𝐒𝐭𝐚𝐫𝐭𝐢𝐧𝐠 𝐭𝐞𝐱𝐭: ' + translate[0] + u'\n𝐓𝐫𝐚𝐧𝐬𝐥𝐚𝐭𝐞𝐝 𝐢𝐧𝐭𝐨: ' + translate[2])
    fb_post(fb, p_id, img_file, txt_to_post)


def main():

    # Will later introduce a standard file to load tokens directly (very simple task but oh well...)
    my_token = 'YOUR-PAINTMIN-TOKEN-HERE'
    page_id = 'YOUR-OWN-PAGE-ID-HERE'

    fb = facebook.GraphAPI(access_token=my_token, version="3.1")
    trans = googletrans.Translator()
    quotes_api = 'http://quotesondesign.com/wp-json/posts?filter[orderby]=rand&filter[posts_per_page]=1'

    while True:
        try:
            post_randtransl(fb, quotes_api, trans, page_id)
            time_to_wait = random.randint(0, 1800)
            print("Waiting " + str((1800 + time_to_wait) / 60) + " minutes until the next post")
            time.sleep(time_to_wait + 1800)
        except KeyboardInterrupt:
            sys.exit(0)
        except Exception as e:
            print(str(e))


if __name__ == "__main__":
    main()

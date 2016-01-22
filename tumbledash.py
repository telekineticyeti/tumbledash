#!/usr/bin/env python
# -*- coding: utf-8 -*-

"""
    Tumbledash.py   : Generate a Tumblr Dashboard RSS feed by querying the 
                      Tumblr API. To view a list of command line arguements
                      execute this program with -h flag.
    Author          : Paul Castle
    Python Version  : 3.4.2
"""

import os
import datetime
import requests
import json
import argparse
import codecs
from xml.dom.minidom import Document
from requests_oauthlib import OAuth1


def retrieve_dash(amount=20, dump=True, starting_offset=0):
    """
        Establish API connection to Tumblr and retrieve dashboard JSON
        Args:
            amount: Number of posts to retrieve (Maximum 300)
            dump (Boolean): Will dump JSON data to file if true.
            starting_offset: Post number to start grabbing from
    """


    def query_split(amount):
        """
            Determine number of queries to be made to the API based on specified
            amount of posts. Only 20 posts may be retrieved in a single query. 
            Example: >20 must be split over a number of queries with a defined 
            offset.
        """
        calls = int(amount) / 20
        integer, fraction = divmod(calls, 1)

        calls = int(integer)
        if fraction > 0:
            calls += 1
            remainder = int(fraction * 20)
        else:
            remainder = 0

        # return [amount, calls, remainder]
        return { "amount" : amount, "calls" : calls, "remainder" : remainder }

    def get_oauth():
        oauth = OAuth1(config['consumer_key'],
            client_secret = config['consumer_secret'],
            resource_owner_key = config['token'],
            resource_owner_secret = config['token_secret'])
        return oauth

    data = [] # Holds post json objects resulting from query
    query = query_split(amount) 
    oauth = get_oauth()
    remainder = False

    if verbose:
        print("Retrieving %s posts (%s API queries)" % (amount, query["calls"]))

    for i in range(query["calls"]):
        offset = i * 20 + starting_offset

        # If current call is the last call, set remainder variable
        if i == query["calls"] - 1:
            remainder = True

        dash_url = (
            "http://api.tumblr.com/v2/user/dashboard?offset="
            + str(offset)
        )

        if remainder:
            dash_url = dash_url + "&limit=" + str(query["remainder"])

        if verbose:
            print("Iteration %s/%s: %s" % (i + 1, (query["calls"]), dash_url))

        response = requests.post(dash_url, auth=oauth)
        data = data + response.json()["response"]["posts"]


    if dump is True:
        with open("dash_output.json", 'w') as data_file:
            json.dump(data, data_file, indent=4)

    return data


def create_rss():
    """
        Returns XML Data to be outputted
    """
    date_now = str(datetime.datetime.now().strftime('%a, %d %b %Y %H:%M:%S GMT'))


    def rss_channel_tag(tag, content=None):
        """
            Create a tag and append it to the current RSS document channel
            Args:
                tag: The name of the tag being created
                content: The text content of the tag
        """
        tag = doc.createElement(tag)

        if content:
            tag_content = doc.createTextNode(content)
            tag.appendChild(tag_content)

        channel.appendChild(tag)


    def rss_create_item(post):
        """
            Create <item> and append it to the RSS document's <channel>
            Args:
                post: Single post from Tumblr dashboard JSON
        """
        item = doc.createElement('item')


        def rss_create_item_node(tag, content=None, cdata=False, attr=None):
            """
                Create a tag inside current <item>
                Args:
                    tag: The name of the tag
                    content: The text content of the tag
                    cdata (Boolean): If true, wrap the text content in cdata
                    attr: Add an attribute to the tag. Expects a list of two 
                          items; the attribute key and it's value.
            """
            tag = doc.createElement(tag)
            
            # Apply content, if specified
            if content:
                if cdata:
                    tag_content = doc.createCDATASection(content)
                else:
                    tag_content = doc.createTextNode(content)
                
                tag.appendChild(tag_content)

            # Apply attribute, if specified
            if attr:
                tag.setAttribute(attr[0], attr[1])

            item.appendChild(tag)


        # The following conditionals determine how and which item tags will be 
        # generated, determined by Tumblr post type.
        reblogged = True if "source_url" in post else False

        # Set title tag of post
        title_string = post["blog_name"] + ": "

        if "title" in post:
            if post["title"] is not None:
                title_string = title_string + post["title"]
                # Description is appended to as conditions below are met
                description = '<h1>' + post["title"] + '</h1>'
            else:
                title_string = title_string + post["summary"]
                description = ''
        else:
            title_string = title_string + post["summary"]
            description = ''

        if reblogged:
            title_string = (
                title_string
                + " (reblogged via "
                + post["source_title"]
                + ")")

        # Link will populate with Tumblr post permalink
        link = post["post_url"]

        # Set category tags based on post tags
        for category in post["tags"]:
            tag = category
            rss_create_item_node("category", tag)

        post_date = datetime.datetime.fromtimestamp(
            int(post["timestamp"])
        ).strftime('%a, %d %b %Y %H:%M:%S GMT')

        rss_create_item_node("title", title_string)
        rss_create_item_node("link", link)
        rss_create_item_node("guid", link, attr=['isPermaLink', 'false'])
        rss_create_item_node("pubDate", post_date)


        """
            Post Type: Question
        """
        if post["type"] == "question":

            if post["asking_url"] == None:  # Asker was anonymous
                asker = post["asking_name"]
            else:
                asker = ('<a href="'
                        + post["asking_url"]
                        + '" target="_blank">'
                        + post["asking_name"] 
                        + '</a>')

            asked = post["question"]
            answer = post["answer"]
            description = (
                description
                + '<blockquote><i>'
                + asker
                + ' asked</i><p>'
                + asked
                + '</p></blockquote>'
                + answer)

        """
            Post Type: Photo(s)
        """
        if post["type"] == "photo":
            photos = []

            for photo in post["photos"]:
                photo_string = (
                    '<img src="'
                    + photo["original_size"]["url"]
                    + '"')

                if photo["caption"] is not None:
                    photo_string = (
                        photo_string
                        + ' alt="'
                        + photo["caption"]
                        + '"')

                photo_string = photo_string + '>'

                photos.append(photo_string)

            if post["caption"] != None:
                description = description + post["caption"]
            else:
                description = description + post["summary"]

            description = description + '<br>'.join(photos)

        """
            Post Type: Text
        """
        if post["type"] == "text":
            description = description + post["body"]

        """
            Post Type: Link
        """
        if post["type"] == "link":
            if post["excerpt"] == None:
                excerpt_string = post["summary"]
            else:
                excerpt_string = post["excerpt"]

            description = (
                description
                + '<h1> <a href="'
                + post["url"]
                + '" alt="'
                + excerpt_string
                + '" target="_blank">'
                + post["summary"]
                + '</a></h1>')

        """
            Post Type: Audio
        """
        if post["type"] == "audio":
            description = (
                description
                + post["embed"]
                + '<p>'
                + post["caption"]
                + '</p')

        """
            Post Type: Video
        """
        if post["type"] == "video":
            description = (
                description
                + post["player"][-1]["embed_code"]
                + '<p>'
                + post["caption"]
                + '</p>')

        """
            Post Type: Quote
        """
        if post["type"] == "quote":
            description = (
                description 
                + '<blockquote><h2>'
                + post["text"]
                + '</h2>'
                + '<cite style="display: block; text-align: right;"> - '
                + post["source"]
                + '</cite></blockquote>')

        """
            Post Type: Chat
        """
        if post["type"] == "chat":
            description = (
                description
                + '<table width="80%" cellspacing="0" cellpadding="2">')

            # Alternate background colour of <tr>
            x = 0
            for row in post["dialogue"]:
                tr = '<tr'
                if x % 2 != 0:
                    tr = tr + ' style="background: #eaeaea;"'
                tr = tr + '>'
                x += 1

                exchange = (
                    tr
                    + '<th width="10%" align="left" valign="top">'
                    + row["label"]
                    + '</th><td align="left" valign="top">'
                    + row["phrase"]
                    + '</td></tr>')

                description = description + exchange

            description = description + '</table>'

        # If post is reblogged, append a not to the end of the description
        # indicating so.
        if reblogged:
            reblog_string = ('<p><small>Reblogged via <a href="'
                             + post["source_url"] 
                             + '">' + post["source_title"] 
                             + '</a><small></p>')
            description = description + reblog_string

        # Append note count
        notes_string = ("<br><p>" + str(post["note_count"]) + " notes</p>")
        description = description + notes_string

        rss_create_item_node("description", description, True)
        channel.appendChild(item)


    # Create The Base RSS Document Using minidom
    doc = Document()
    rss = doc.createElement('rss')
    rss.setAttribute('version', '2.0')
    rss.setAttribute('xmlns:atom', 'http://www.w3.org/2005/Atom')
    doc.appendChild(rss)

    # Create RSS Channel
    channel = doc.createElement('channel')
    rss.appendChild(channel)

    # Populate Channel With Standard Tags
    rss_channel_tag("title", content="My Tumblr Dashboard")
    rss_channel_tag("description", content="Tumblr Dashboard")
    rss_channel_tag("link", content="https://www.tumblr.com/dashboard")
    rss_channel_tag("language", content="en-us")
    rss_channel_tag("lastBuildDate", content=date_now)
    rss_channel_tag("ttl", content="5")

    # Appened ATOM Content to Channel
    atom = doc.createElement("atom:link")
    atom.setAttribute("href", "http://rss.poot.pw/dashboard.xml")
    atom.setAttribute("rel", "self")
    atom.setAttribute("type", "application/rss+xml")
    channel.appendChild(atom)

    # Create RSS Items by Iterating Over Each "posts" Item In The JSON Data
    for posts in data:
        rss_create_item(posts)

    return doc


"""
    Parse command line arguements
"""
scriptdir = os.path.dirname(os.path.abspath(__file__))
default_config = scriptdir + '/config.json'
parser = argparse.ArgumentParser()

parser.add_argument("-c", "--config",
    help="Specify path to configuration file. If not specified, this program "
    "will use the default file: %s" % default_config)

parser.add_argument("-d", "--dropbox",
    help="Launch with Dropbox support.",
    action='store_true')

parser.add_argument("-v", "--verbose",
    help="Enable verbose mode",
    action='store_true')

parser.add_argument("--dump",
    help="Dump the raw JSON recieved from Tumblr's API to a file for debugging",
    action="store_true")

parser.add_argument("-o", "--output",
    help="Where to output the RSS feed. By default this will be the directory "
    "where this program resides",
    action="store_true")

args = parser.parse_args()

if args.config:
    if os.path.isfile(args.config):
        config_path = args.config
    else:
        quit("Specified configuration file not found: %s" % args.config)
else:
    if os.path.isfile(default_config):
        config_path = default_config
    else:
        quit("Default configuration file not found: %s" % default_config)

    with open(config_path, 'r') as f:
        config = json.load(f)

verbose = False

if args.verbose:
    verbose = True


# Retreive dash contents
data = retrieve_dash()

# Generate XML
getrss = create_rss()

# Output XML to file
xml_file = scriptdir + "/dashboard.xml"
with codecs.open(xml_file, 'w', encoding="utf-8") as f:
    getrss.writexml(f, indent='\t', newl='\n')


# pip install requests requests_oauthlib
# tumbledash.py
Generate an RSS feed of your Tumblr dashboard using Tumblr's API.

## Usage
This program is designed to run in a CLI. When executed, it will produce an RSS valid XML file containing the latest posts from your Tumblr Dashboard. It is recommended to set up the program to run automatically, using cron or scheduled tasks.

## Tumblr OAUTH
Using the config.json file, you must provide your OAUTH consumer / token information in order to interact with Tumblr's API. As the program develops, this process will be more streamlined. For now, this requires [registering an application](https://www.tumblr.com/oauth/register) to obtain a consumer key/consumer secret codes.

Once you have registered an application and have a Consumer Key / Consumer Secret, [use Tumblr's API console](https://api.tumblr.com/console/calls/user/info) to generate a token / token secret. You will now have four codes to populate the config file.

## Optional Arguments
Arguments may be passed to the script at the command line

* _-c, --config_ : Specify a custom configuration file to use. Useful for retrieving multiple dashboards. If not specified, the program will attempt to use 'config.json' in the same directory.
* _-v, --verbose_ : Verbosity mode. Output behaviour for the purpose of debugging.
* _--dump_ : If specified, the retrieved JSON data will be outputted to a file called output.json

Arguments for features that will be implemented soon
* _-o, --output_ : Specify where to write the XML file
* _-d, --dropbox_ : If specified, this will include the Dropbox module when executed.

## TODO
* Add optional argument to define the output destination of the XML file.
* Add a process to retrieve the OATH token, and write this token to the config file.
* Add an optional module to push the XML file to a dropbox account, so that Dropbox may host the file via a publicly accessible URL.

## About the Author
I am relatively new to Python programming, and this is my first involved Python project. I welcome any comments and criticisms regarding improvement of the code. I hope that you find it useful.
#!/usr/bin/python3

import argparse
from html.parser import HTMLParser
import logging
import os

from discussion import TopicDiscussionParser
from example import ExampleParser
from problem import ProblemParser


class FirstPassParser(HTMLParser):
    '''
    Does a quick pass of the file and determines the sections of the file which
    define the discussion, examples, and problems. The division of the sections
    are contained in the positions property
    '''

    def __init__(self):
        super(FirstPassParser, self).__init__()
        self._level = 0
        self._page = self._currentlevel = -1
        self.positions = [[-1,-1], [-1,-1], [-1,-1]]
        logging.debug('Created First Pass Parser')

    def handle_starttag(self, tag, attrs):
        if tag == 'div':
            for i in range(3):
                idstr = 'p{}'.format(i+1)
                if ('id', idstr) in attrs:
                    logging.debug('Page {} started at {}'.format(
                        i+1,
                        self.getpos()))
                    self.positions[i][0] = self.getpos()[0] - 1
                    self._page = i

                    self._currentlevel = self._level

            self._level += 1

    def handle_endtag(self, tag):
        if tag == 'div':
            self._level -= 1

            if self._level == self._currentlevel:
                i = self._page
                logging.debug('Ended Page {} at {}'.format(
                    i+1,
                    self.getpos()))
                
                self.positions[i][1] = self.getpos()[0] - 1
                self._currentlevel = self._page = -1

def execute():
    logging.getLogger().setLevel(logging.DEBUG)

    parser = argparse.ArgumentParser(
        description='Custom script to parse old Math Emporium files',
        epilog='With no target specified, then all sections are parsed')

    parser.add_argument('filename', type=str,
        help='The file name located in the "raw" directory')

    parser.add_argument('-discussion', dest='targets', action='append_const',
        const='discussion', help='Flag to specifically parse the topic discussion')
    parser.add_argument('-examples', dest='targets', action='append_const',
        const='examples', help='Flag to specifically parse the examples')
    parser.add_argument('-problem', dest='targets', action='append_const',
        const='problem', help='Flag to specifically parse the section problem')

    parser.add_argument('-ignore_images', action='store_true', 
            help='Force the program to ignore all images and insert placeholders.')

    args = parser.parse_args()

    logging.info('Scrubbing file "raw/{}.html"'.format(args.filename))

    scrub_file(args)

def scrub_file(args):
    '''
    Goes through the process of setting up the files to write to then converting
    the original file.
    '''

    # Get absolute paths for the files
    filenames = prepare_folder(args.filename)
    filename, outputfilenames = filenames[0], filenames[1:]
    
    # First pass: get the sections dedicated to discussion, examples, and
    # problems
    logging.info('Determining section locations for {}'.format(filename))
    parser = FirstPassParser()

    with open(filename) as f:
        parser.feed(f.read())

    positions = parser.positions
    logging.info('File Sections Discovered in line sections {}'.format(positions))

    # Second pass: for each position set, iterate through the original file and
    # write the appropriate contents using the second pass parser to the new
    # file
    targets = ['discussion', 'examples', 'problem']
    parser_classes = [TopicDiscussionParser, ExampleParser, ProblemParser]

    if args.targets is None:
        args.targets = targets
        
    for target, parser_class, line_range, ofilename in zip(targets, parser_classes, positions, outputfilenames):
        if target in args.targets:
            logging.info('Parsing {}...'.format(target))
            parse_section(parser_class, line_range, filename, ofilename, args.ignore_images)

def parse_section(parser_class, line_range, filename, outputfilename, ignore_images):
    start_line, end_line = line_range
    with open(filename) as infile, open(outputfilename, 'w') as outfile:
        parser = parser_class(outfile, ignore_images)
        for line_number, line in enumerate(infile):
            if start_line <= line_number <= end_line:
                parser.feed(line)

def prepare_folder(foldername):
    '''
    Just makes sure a folder with given name exists in the output directory.
    Furthermore, even if the folder exists, returns a tuple containing the
    filenames to write to: discussion, examples, problems.
    '''

    basepath = os.path.realpath(os.path.dirname(__file__))
    dirpath = os.path.join(basepath, 'output', foldername)
    filename = os.path.join(basepath, 'raw', foldername) + '.html'

    if not os.path.exists(dirpath):
        logging.info('Creating directory {}'.format(dirpath))
        os.mkdir(dirpath)
    else:
        logging.warn('Directory already exists. May overwrite files')

    filenamebuilder = lambda x: os.path.join(dirpath, x) + '.html'
    outputs = tuple(map(filenamebuilder, ['discussion', 'examples', 'problem']))

    return (filename,) + outputs


if __name__ == '__main__':
    execute()

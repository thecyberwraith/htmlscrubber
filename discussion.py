'''
module discussion

Contains the classes required to parse the old Math Emporium discussion format
interactively into the newer, simpler format.
'''

from functools import partial
from htmlparse import *
import logging
import os

class TopicDiscussionParser(CustomHTMLParser):
    '''
    Rip the contents of the file into a plainer format and present the user with
    the option to typeset image files if possible.
    '''

    def __init__(self, file_handler, ignore_images, config):
        super(TopicDiscussionParser, self).__init__(file_handler, ignore_images, config)

    def handle_starttag(self, tag, attrs):
        print('{} + {}'.format(self._tag_converters, tag))
        level = len(self._tag_converters)

        tag_map = {
            'strong': partial(InlineTagConverter, 'strong', attrs),
            'b': partial(InlineTagConverter, 'strong', attrs),
            'i': partial(InlineTagConverter, 'i', attrs),
            'a': partial(HyperlinkTagConverter, attrs),
            'table' : partial(TagConverter, include=True),
            'tbody' : partial(TagConverter, include=True),
            'tr' : partial(TagConverter, include=True),
            'td' : partial(TagConverter, include=True)
        }

        new_converter = None

        if tag == 'div':
            if ('class', 'contentbox') in attrs:
                new_converter = NewlineTagConverter('p', level, [])
            elif ('class', 'beigebox') in attrs:
                new_converter = NewlineTagConverter('div', level, [('class',
                'defbox')])
            elif ('class', 'popuphelpp1') in attrs:
                new_converter = NewlineTagConverter('div', level, [('class', 'hintbox'), ('id', 'hintContainer?')])
            else:
                new_converter = TagConverter(include=True)
        elif tag == 'img':
            self.handle_image(attrs)
        elif tag == 'span':
            if ('class', 'title') in attrs:
                new_converter = TitleConverter(attrs)
            elif ('class', 'flyouthelp') in attrs:
                new_converter = InlineTagConverter('a', [('id', 'hintLink?')])
            else:
                new_converter = DefaultSpanConverter(attrs, self._config)
        else:
            if tag in tag_map:
                new_converter = tag_map[tag]()
            else:
                logging.warning('Tag "{}" not supported'.format(tag))

        if not new_converter is None:
            self._tag_converters.append(new_converter)
            new_converter.on_tag_start(self._handler)


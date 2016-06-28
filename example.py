from functools import partial
from html.parser import HTMLParser
import logging
import re

from htmlparse import *


class ExampleParser(CustomHTMLParser):
    def __init__(self, outputfile, interactive, config):
        super(ExampleParser, self).__init__(outputfile, interactive, config)
        self._current_example = 0
        self._example_table_tag = None
        self._last_popped = None

    def handle_starttag(self, tag, attrs):
        new_tag = None
        level = len(self._tag_converters)

        tag_map = {
            'strong': partial(InlineTagConverter, 'strong', []),
            'b': partial(InlineTagConverter, 'strong', []),
            'i': partial(InlineTagConverter, 'i', []),
            'a': partial(HyperlinkTagConverter, attrs),
            'tbody': partial(TagConverter, include=True)
        }

        if tag == 'span':
            if ('class', 'questionstatement') in attrs:
                # Example instructions
                new_tag = InlineTagConverter('p', [('class', 'examplestatement')]) 
            elif ('class', 'hint') in attrs:
                example, hint = self.grab_numbers_from_id(attrs)
                if hint == 1:
                    new_tag = NewlineTagConverter('div', level,
                        [('class', 'hintbox')])
                else:
                    new_tag = NewlineTagConverter('div', level,
                        [('class', 'hintbox'), ('id', 'exampleHint{}-{}'.format(example, hint))])
            else:
                new_tag = DefaultSpanConverter(attrs, self._config)
        elif tag == 'table':
                # Table to store the examples
            if ('class', 'example') in attrs:
                new_tag = NewlineTagConverter('ol', level, [('class', 'questionlist')])
                self._example_table_tag = new_tag
            else:
                new_tag = TagConverter(include=True)
        elif tag == 'td':
            if ('class', 'leftcell') in attrs:
                # Example question text (start new example)
                self._current_example += 1
                logging.debug(self._tag_converters)
                new_tag = NewlineTagConverter('p', level, [])
            elif ('class', 'exanswerbox') in attrs:
                # Example solution
                logging.debug(self._tag_converters)
                new_tag = ExampleSolution(level, self._current_example)
            else:
                new_tag = TagConverter(include=True)
        elif tag == 'tr':
            # Questions are divided into rows of a table, assuming the table is
            # the above ('class', 'example') table. If two parents ago (tbody is
            # a boring parent) is this table, then we start a new question.
            if self._example_table_tag is self._tag_converters[-2]:
                new_tag = NewlineTagConverter('li', level, [])
            else:
                new_tag = TagConverter(include=True)
        elif tag == 'img':
            if ('class', 'exarrow') in attrs:
                # This signifies a link to continue in the problem. We need its
                # id to uncover the correct hint and solution section.
                # Furthermore, if the last popped element was a
                # ExamplePartContainer, we need to close it (assuming this isn't
                # the first part)
                example, hint = self.grab_numbers_from_id(attrs)
                link = '<a id="exampleLink{}-{}">Continue</a>'.format(example, hint)
                if isinstance(self._last_popped, ExamplePartConverter) and not hint == 1:
                    self._last_popped.close_tag_with_link(self._handler, link)
                    self._last_popped = None
                else:
                    logging.debug('what is this? {} <-------------'.format(attrs))
            else:
                self.handle_image(attrs)
        elif tag == 'div':
            if ('class', 'exanswer') in attrs:
                example, part = self.grab_numbers_from_id(attrs)
                new_tag = ExamplePartConverter(example, part, level)
            else:
                new_tag = TagConverter(True)
        else:
            if tag in tag_map:
                new_tag = tag_map[tag]()
            else:
                logging.debug('Tag "{}" not supported'.format(tag))

        if not new_tag is None:
            new_tag.on_tag_start(self._handler)
            self._tag_converters.append(new_tag)

    def handle_endtag(self, tag):
        if not isinstance(self._last_popped, ExamplePartConverter):
            self._last_popped = self._tag_converters[-1]
        super(ExampleParser, self).handle_endtag(tag)

    def grab_numbers_from_id(self, attrs):
        for attr, value in attrs:
            if attr == 'id':
                example, hint = map(int, re.findall(r'\d+', value))
                return example, hint
        else:
            raise AttributeError('"id" attribute not present in {}'.format(attrs))


class ExamplePartConverter(NewlineTagConverter):
    '''
    In the old version, the continue link is outside of the div it appears with.
    In the new version, the continue link must be located inside the division.
    Thus, this container does not close itself! When the image that will be
    replaced with a continue link is read, we must go back to this popped
    converter (they should be sequential) and call its close method after we
    convert the link. However, the last one does not have a continue link, so it
    must be closed by the containing example solution class (anyway, the "Close
    Example" link is contained int he last ExamplePartContainer
    '''
    def __init__(self, example, part, level):
        id_str = 'exampleContainer{}-{}'.format(example, part)
        if part == 1:
            super(ExamplePartConverter, self).__init__('p', level, [])
        else: 
            super(ExamplePartConverter, self).__init__('div', level, [('id', id_str)])
        
    def on_tag_end(self, tag):
        pass

    def close_tag_with_link(self, writer, link):
        logging.debug('Closing tag with link {}'.format(link))
        super(ExamplePartConverter, self).on_tag_data(writer, link)
        super(ExamplePartConverter, self).on_tag_end(writer)


class ExampleSolution(NewlineTagConverter):
    def __init__(self, level, example):
        id_string = 'exampleContainer{}'.format(example)
        attrs = [('class', 'examplebox'), ('id', id_string)]
        super(ExampleSolution, self).__init__('div', level, attrs)
        self.example = example

    def on_tag_start(self, writer):
        writer.write('\n' + self.tabs() + '<p><a id="exampleLink{}">Begin</a></p>'.format(self.example))
        super(ExampleSolution, self).on_tag_start(writer)

    def on_tag_end(self, writer):
        writer.write('<p><a id="closeExample{}">Close Example</a></p>'.format(self.example))
        super(ExampleSolution, self).on_tag_end(writer)

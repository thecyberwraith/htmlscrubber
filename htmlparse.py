from html.parser import HTMLParser
import logging
import os

class CustomHTMLParser(HTMLParser):
    '''
    Rip the contents of the file into a plainer format and present the user with
    the option to typeset image files if possible.
    '''

    def __init__(self, file_handler, ignore_images, config):
        super(CustomHTMLParser, self).__init__()
        self._handler = file_handler
        self._ignore_images = ignore_images
        self._image_command = config['DEFAULT']['image_command']
        self._default_img_text = config['DEFAULT']['default_image_text']
        # Keep a list of tag converters. Every time a new tag is encountered, we
        # push the appropriate converter on the stack. The top converter handles
        # the data, and we pop it when the end tag is encountered.
        self._tag_converters = []

    def handle_endtag(self, tag):
        self._tag_converters[-1].on_tag_end(self._handler)
        self._tag_converters.pop(-1)

    def handle_data(self, data):
        data = data.replace('\n', '').replace('\r', '').replace('\t', '')
        if all(self._tag_converters) and data:
            self._tag_converters[-1].on_tag_data(self._handler, data)

    def handle_image(self, image_attrs):
        content = self.get_image_text(image_attrs)
        self._handler.write(' {} '.format(content))
        
    def get_image_text(self, image_attrs):
        for attr, value in image_attrs:
            if attr == 'src':
                logging.info('Handling image {}'.format(value))
                content = ''
                if not self._ignore_images:
                    imgpath = os.path.join('raw', value)
                    os.system(self._image_command.format(imgpath))
                    content = input('? ')

                if not content:
                    content = self._default_img_text
                
                return content
                

class TagConverter():
    '''
    Generic class for converting tags from the old format to the new.
    '''
    def __init__(self, include=False):
        self._include = include

    def on_tag_start(self, writer):
        pass

    def on_tag_data(self, writer, data):
        pass

    def on_tag_end(self, writer):
        pass

    def __repr__(self):
        return 'TagConverter({})'.format(self._include)

    def __bool__(self):
        '''
        Used to flag whether or not to care about the data contained in this tag
        or its nested tags. By default, this returns false and thus can be used
        (and should be used) as a null object.
        '''
        return self._include


class WrappedTagConverter(TagConverter):
    '''
    Used when the old tag data just needs to be put (inline) as a new tag.
    '''

    def __init__(self, tag_name, attrs):
        super(WrappedTagConverter, self).__init__(include=True)
        self.tag = tag_name 
        attr_str = ', '.join(['{}="{}"'.format(*attr) for attr in attrs])

        if attr_str:
            attr_str = ' ' + attr_str

        self.start_tag = '<{}{}>'.format(tag_name, attr_str)
        self.end_tag = '</{}>'.format(tag_name)

    def on_tag_start(self, writer):
        writer.write(self.start_tag)

    def on_tag_data(self, writer, data):
        writer.write(data)

    def on_tag_end(self, writer):
        writer.write(self.end_tag)

    def __repr__(self):
        return 'WrappedTagConverter({})'.format(self.tag)


class InlineTagConverter(WrappedTagConverter):
    '''
    Same as parent, but add spaces around the tag
    '''
    
    def __init__(self, tag_name, attrs):
        super(InlineTagConverter, self).__init__(tag_name, attrs)
        self.start_tag = ' ' + self.start_tag
        self.end_tag = self.end_tag + ' '


class NewlineTagConverter(WrappedTagConverter):
    '''
    Same as a wrapped, but we add a newline after the tags and appropriate
    spacing.
    '''

    def __init__(self, tag_name, level, attrs):
        super(NewlineTagConverter, self).__init__(tag_name, attrs)
        self._level = level
        self.start_tag = '\n{0}{1}\n{0}'.format(self.tabs(), self.start_tag)
        self.end_tag = '\n{0}{1}'.format(self.tabs(), self.end_tag)

    def tabs(self):
        return '\t'*self._level

    def on_tag_data(self, writer, data):
        writer.write(data)


class TitleConverter(WrappedTagConverter):
    def __init__(self, attrs):
        super(TitleConverter, self).__init__('p', attrs)
        self.start_tag = self.start_tag + '<strong>'
        self.end_tag = '</strong>' + self.end_tag + '\n'


class HyperlinkTagConverter(InlineTagConverter):
    def __init__(self, attrs):
        new_attrs = [('target', '_blank'), ('href', '!!URL!!')]
        super(HyperlinkTagConverter, self).__init__('a', new_attrs)


class DefaultSpanConverter(InlineTagConverter):
    def __init__(self, attrs):
        new_color_attrs = self.get_color(attrs)
        super(DefaultSpanConverter, self).__init__('span', new_color_attrs)

    def get_color(self, attrs):
        for attr in attrs:
            if attr[0] == 'style':
                old_color = attr[1][7:]

                color_dict = { # What new color hex values are
                    'cyan': '009E73',
                    'purple': 'CC79A7',
                    'yellow': 'E65F00',
                    'navy': '0072B2',
                    'orange': 'D55E00',
                    'skyblue': '56B4E9',
                    'brightyellow': 'F0E442'
                }

                old_color_rev_dict = { # What old hex looked like
                    'FF00FF': 'magenta',
                    'FF0000': 'red',
                    '996633': 'orange',
                    'FF9900': 'orange',
                    'FF8000': 'orange',
                    '00FF00': 'green',
                    '7F4040': 'maroon',
                    '0000FF': 'blue',
                    '800080': 'purple',
                }

                conversion_dict = { # What the color was to what it should be
                    'magenta': 'navy',
                    'red': 'yellow',
                    'brown': 'purple',
                    'green': 'orange',
                    'maroon': 'cyan',
                    'blue': 'navy',
                    'purple': 'purple',
                    'orange': 'orange'
                }

                return [('style', 'color:#{};'.format(
                    color_dict[conversion_dict[old_color_rev_dict[old_color]]]
                    ))]
        else:
            return []

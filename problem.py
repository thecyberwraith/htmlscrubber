import logging

from htmlparse import CustomHTMLParser

class ProblemParser(CustomHTMLParser):
    def __init__(self, outputfile, ignore_images, config):
        super(ProblemParser, self).__init__(outputfile, ignore_images, config)
        self._data = {}
        self._target = None
        self._level = 0

    def handle_starttag(self, tag, attrs):
        if tag == 'span':
            self._level += 1
            if ('class', 'title') in attrs:
                self._target = 'title'
            else:
                try:
                    self._target = self.get_id(attrs)
                except AttributeError:
                    pass
        elif tag == 'div':
            self._level += 1
            if ('class', 'lessonprob') in attrs:
                self._level = 0
            elif ('class', 'choiceanswer') in attrs:
                self._target = self.get_id(attrs)
            elif ('class', 'answer') in attrs:
                self._target = 'answer' + self.get_id(attrs)[2]
            elif ('class', 'response') in attrs:
                self._target = 'answer' + self.get_id(attrs)[2]

        elif tag in ['td', 'i', 'strong', 'b', 'tr', 'tbody', 'table']:
            self._level += 1
        elif tag == 'img':
            content = self.get_image_text(attrs)
            self.handle_data(content)
        else:
            pass
            #logging.warn(tag)
        #logging.warn('+{} -> {}'.format(tag, self._level))

    def handle_data(self, data):
        data = data.replace('\n', '')

        if data and not self._target is None:
            if not self._target in self._data:
                self._data[self._target] = ''

            # Check if we are doing the response, which would indicate if
            # we are correct or not. This requires its own formatting
            if self._target.startswith('answer'):
                target = 'is{}correct'.format(self._target[-1])
                if 'This answer is incorrect.' in data:
                    self._data[target] = False
                    data = data[25:]
                elif 'This answer is correct.' in data:
                    logging.debug('Correct [{}]: {}'.format(self._target, data))
                    self._data[target] = True
                    data = data[25:]
            logging.debug('{} -> {}'.format(self._target, data))
            self._data[self._target] += data

    def handle_endtag(self, tag):
        self._level -= 1
        #logging.info('-{} -> {}'.format(tag, self._level))
        if self._level < 0:
            self.finalize()

    def finalize(self):
        logging.info(self._data)
        logging.info(self._data.keys())
        
        # For each item, we must wrap the correct solution/answer in an
        # appropriately formatted div.
        
        for i in range(1,4): #1,2,3
            if self._data['is{}correct'.format(i)]:
                format_string = '<div><a id="solutionlink">Solution</a></div>'
                format_string +='\n\n<div class="solution" id="solution">{}</div>'
                self._data['response{}'.format(i)] = 'Correct'
            else:
                format_string = '<div class="answer" id="choiceanswer{}">{{}}</div>'.format(i)
                self._data['response{}'.format(i)] = 'Incorrect'
            attr_str = 'answer{}'.format(i)
            self._data[attr_str] = format_string.format(self._data[attr_str])

        # Write it to the template
        with open('problem_template.txt') as template_file:
            template = template_file.read()
            self._handler.write(template.format(**self._data))

    def get_id(self, attrs):
        for attr, value in attrs:
            if attr == 'id':
                return value
        else:
            raise AttributeError('Attributes {} does not have an "id" attribute'.format(attrs))

# HTML Scrubber

A tool to help convert old Math Emporium lesson files to the new, simplified format. The program extracts the necessary components, and gives the user minor control on how to handle images. This readme file should help a novice start using this program.

* Installation
* Standard Usage
* Arguments
* Configuration
* Standard Errors
* Interactive Mode
* Conversion Tips

## Installation
The program is the `htmlscrubber.py` script. To use the script, you must have Python3 or later installed. To test whether you do, enter the command

```python -V```

Sometimes, python3 is a separate command, so if the first command yields an insufficient version, try

```python3 -V```

After validating that Python3 or later is installed on your system, copy the '.py', '.txt', and '.ini' files to a folder of your choice. Navigate in your console to the directory containing these files. If necessary (and you know what you are doing) you may modify the bash command at the beginning of the `htmlscrubber.py` script to point to your version of Python3. Otherwise, run the command

```python htmlscrubber.py -h```

You should see a simple help output to your console on the proper syntax for executing the program. If this works, congratulations!

## Standard Usage
The previous format of the Emporium Courses was to put the Topic Discussion, Examples, and Lesson Problem all in the same html document. To use the Scrubber, use your internet browser (I used Firefox) to save a Math Emporium page in the old format into a folder called `raw`. This folder should be inside the same folder as the `htmlscrubber.py` script. It is important to use your internet browser's save feature so that the images associated to the page will also be loaded (in case you want to perform the Console Power User method). Furthermore, ensure the file you saved has the appropriate .html extension.

For example, if you download Unit 6 Module 5 Lesson 1 to your `raw` folder using Firefox, a `raw/lesson1.html` file should appear. Then to convert the file, simply execute

```python htmlscrubber.py lesson1```

You should see some output, but no errors. If you then examine the newly created output folder, there should be three files now present: `output/lesson1/discussion.html`, `output/lesson1/examples.html`, `output/lesson1/problem.html`.

If you open these files in any text editor, it should display the basic contents of the appropriate section of the lesson. You will not may instances of `<p>IP</p>` pop up in the file. This is the default image text and will be discussed in the Configuration section. Note that the conversion is not precise at this point, so you will still need to manually read through the file to make sure everything is as it should be.

## Arguments
As displayed in the program's help string, there are commands you can provide to the htmlscrubber that can help you specify what you need done:

* interactive (-i) : Tell the program to switch to interactive mode, thus allowing the user to be displayed each picture referenced in the file and insert appropriate text. See the Interactive Mode section is you wish to use this.
* verbose (-v) : Changes the log level from info to debug.
* discussion (-d) : Specify that the discussion section should be parsed from the file.
* problem (-p) : Specify that the lesson problem section should be parsed from the file.
* examples (-e) : Specify that the examples section should be parsed from the file.

The last three arguments, when explicitly specified, toggle off the default behavior or parsing all sections. For example,

```python htmlscrubber.py -p -e lessonx```

would parse both the lesson problem and the examples from the specified lessonx, but not the topic discussion. By default,

```python htmlscrubber.py lessonx```

parses all section.

##Configuration
The program can be greatly configured by modifying the `config.ini` file.

###Program Configuration
The following configuration settings alter the workflow of the program.

* `default_image_text`: Specify the string that will be placed in default mode when an image is encountered. In interactive mode, specifies the default string when an image is handled with an empty string.
* `abort_text`: When this string is encountered while handling an image, an exception is thrown in order to exit the program. Note: Do not set the `abort_text` to the same string as the `default_image_text` string.
* `text_edit_command`: In interactive mode, specify the console command to edit the desired contents of the image. Place "{}" where the filename should be inserted.
* `image_command`: In interactive mode, specify the console command to view the image to handle. Place "{}" where the filename should be inserted.

###Color Configuration
As anyone familiar with the old Emporium courses can attest, the previous format was extremely colorful. The program handles most text coloring by configuration. When the program encounters a color, it first looks up a human readable name for the color in the `OLD_COLOR_NAME` in the `config.ini` file. Next, it looks up the human readable conversion of what the old color should become in the `COLOR_MAPPING` section of the `config.ini` file. Finally, the program grabs the proper hex value for the new color from the `NEW_COLOR_HEX_VALUES` section of the `config.ini` file. If the program encounters a color that is not handled in the `config.ini` file, it throws a helpful exception specifying where the color should be added.

##Standard Errors
You should always run the program once without interactive mode in case there is a color which is not handled by the program. This is the only standard error. Note that the program does not handle errors gracefully. Furthermore, if an error is thrown before a file is finished being handled, then the entire process must restart in order to parse the file. Therefore, if you use interactive mode, it is imperative to run the program once in default mode to detect any possible errors.

##Interactive Mode
Interactive mode is the most efficient method for using the program, especially if you are a console power user (text editor is a console program). In order to use Interactive Mode, ensure the `abort_text`, `text_edit_command`, and `image_command` all are properly set.

When in interactive mode, the following will occur:

* When an image is encountered in the file.
* The image is shown to the user using the `image_command`.
* The `text_edit_command` will be executed with the filepath to a temporary file where the contents relating to the image should go.
* The user should edit and SAVE the desired contents to the file.
* The user quits the editor.
* The program then reads in the saved text.
* If the saved text is empty, the `default_image_text` is inserted into the file.
* If the saved text is the `abort_text` string, then an exception is raised to allow the program to exit.
* Otherwise, the program inserts the saved string into the file where the image was encountered.

##Conversion Tips
Here are some things I have noticed my program do, which I typically have to clean up.

* Lots of double spaces are inserted into the file. I do a couple of find an replaces to swap them to single spaces.
* In the Examples section, the program cannot tell ahead of time how many sections there are to an example. Thus, if there is more than one section, it will close the first div tag without enclosing the subsequent div tags relating to that example in it. Therefore, if an example has multiple reveals, be sure to move the </div> tag to the end of the example.
* In the Example section, a lot of empty hint sections are inserted. This is because the old format always had a hint section for every reveal, even if the contents are empty. This is most notable on the first reveal (the Begin link) will show a hint box immediately.
* The program ignores table tags, but will convert the contents. This tends to make the table creation process easier to do in a text editor than in the Drupal editor.

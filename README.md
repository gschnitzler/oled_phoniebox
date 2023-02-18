Just wanted to fix some issues. Had a quick look over the code. Ended up rewriting the whole thing from scratch, even though I never wrote a single line of Python before. 
Here are some changes from the top of my head:

- Use of MPD API via socket
- Graphics are composed
- Rendering is sane
- Images are embedded and based on Material
- Legacy scripts, fonts and functionality (GPIO controls) got removed
- Retained the look of the 'FULL' interface
- UTF8

There is one more feature I wanted to add, namely GPIO controls to turn off the hifiberry when nothing is playing to save battery.

This should be a simple drop-in replacement. Disable the GPIO service and use the one from the Jukebox. Update the configfile, replace the script, install missing dependencies. That should do it.
Look at the original repo for anything else.


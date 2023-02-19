Just wanted to fix some issues. Had a quick look over the code. Ended up rewriting the whole thing from scratch, even though I never wrote a single line of Python before. 
Code quality is sufficient to maintain it I believe, even though a few sprinkles of OO and a refactor wouldn't hurt.
It should be a simple drop-in replacement. Disable the old GPIO service and use the one from RPI Jukebox. Update the configfile, replace the script with this one, install missing dependencies and that should do it.
Look at the original repo for anything else.

Here are some changes from the top of my head:

- Use of MPD API via socket
- Graphics are composed
- Rendering is sane
- Images are embedded and based on Material
- Legacy scripts, fonts and functionality (GPIO controls) got removed
- Retained the look of the 'FULL' interface
- UTF8
- GPIO control to turn off hifiberry when nothing is playing

One mayor goal was to save power. In addition to the internal changes to achieve this, the display has a certain delay. Sufficient as a status monitor for parents, but I might make this adjustible in the future.


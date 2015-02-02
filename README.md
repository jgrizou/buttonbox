Button box tools
==============

Code to create a simple button box using an arduino board and handling events in python.

The documentation is minimal, code should speak for itself.

Load the arduino/pooling/pooling.ino in the arduino board of your choice. This code stream data to the serail port.
 Button should be from pin 3 to 12. Adapt the code for more or less button.

Plug the board to your computer via USB. And use the code in python/button.py to listen to the serial port.
There is several class for:

- Button() is the class that listen to the serail port
- ButtonEvent() call a callback each time a button is button is pressed or released
- ButtonEventRecorder() and ButtonReplay() respectively record and replay button event, so you can debug your code without the box
- ButtonClient() and ButtonServer() can be used to stream button values over TCP, useful to setup interactive experiments with non co-located users
- ButtonPersistOn() is meant to replace a Button() class by simulating a longer pressed time of the button. This is useful when displaying events, sometimes they are too fast for the eyes

TODO: add picture

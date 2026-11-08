# MacaqueSTEP 0.23.1 installer repair

Fixes the Calamares fatal startup error: key not found: slideshow.
The installer now references its bundled monkey.svg as an image slideshow.
Adds a branding preflight check before the ISO build. Desktop remains version 0.23.

On your normal build machine, extract this kit and run:

    sudo bash build-iso.sh

Use a fresh empty output directory; previous build output is preserved.
Flash output/build/live-image-amd64.hybrid.iso to the USB using your image writer.
No repair commands are needed in the live session.

Validation: branding YAML and referenced image verified; build script syntax checked.
A full ISO build and disk installation could not be tested in the preparation environment.

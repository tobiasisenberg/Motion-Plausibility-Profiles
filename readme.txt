General
=======
This demo accompanies the following journal article. If you use the results in new projects, create images with it for some future work, or use it in a different way we would appreciate a citation:

Tobias Isenberg, Zujany Salazar, Rafael Blanco, and Catherine Plaisant (2022). Do You Believe Your (Social Media) Data? A Personal Story on Location Data Biases, Errors, and Plausibility as well as their Visualization. IEEE Transactions on Visualization and Computer Graphics, 2022. To appear. https://doi.org/10.1109/10.1109/TVCG.2022.3141605

Bibtex:
=======
@ARTICLE{Isenberg:2022:DYB,
  author      = {Tobias Isenberg and Zujany Salazar and  Rafael Blanco and  Catherine Plaisant},
  title       = {Do You Believe Your (Social Media) Data? A Personal Story on Location Data Biases, Errors, and Plausibility as well as their Visualization},
  journal     = {IEEE Transactions on Visualization and Computer Graphics},
  year        = {2022},
  doi         = {10.1109/10.1109/TVCG.2022.3141605},
  doi_url     = {https://doi.org/10.1109/10.1109/TVCG.2022.3141605},
  oa_hal_url  = {https://hal.inria.fr/hal-03516682},
  osf_url     = {https://osf.io/u8ejr/},
  url         = {https://tobias.isenberg.cc/VideosAndDemos/Isenberg2022DYB},
  pdf         = {https://tobias.isenberg.cc/personal/papers/Isenberg_2022_DYB.pdf},
  note        = {To appear},
}

Project website:
================
https://tobias.isenberg.cc/VideosAndDemos/Isenberg2022DYB

Note:
=====
Please note the software is provided "as is".  Use it at your own risk, although data loss is unlikely. Do take the standard precautions like saving your work in other programs.

License:
========
Attribution-ShareAlike 4.0 International (CC BY-SA 4.0) https://creativecommons.org/licenses/by-sa/4.0/
(see license.txt).

Requirements:
=============
The Python3 script requires, in addition to a normal Python3 installation, several packages including (potentially more):
* geopy
* plotly
* matplotlib
* numpy
* powerlaw
Install them using "pip3 install [package]" or the respective alternative for your version of Python.

For some functions, the script also needs to be able to call some external programs to do some of the data conversions. In particular:
* gpsbabel: https://www.gpsbabel.org/
* zip: e.g., http://infozip.sourceforge.net/

Configuration:
==============
To configure the script, enable the flags create* at the top of the script as needed. Also needs CSV data files (names as specified in the familyFiles list in the script) downloaded from https://www.inaturalist.org/observations/export (if using different files adjust the familyFiles list).

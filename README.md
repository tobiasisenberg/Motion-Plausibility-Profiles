# Motion Plausibility Profiles

## General
This demo accompanies the following journal article. If you use the results in new projects, create images with it for some future work, or use it in a different way we would appreciate a citation:

Tobias Isenberg, Zujany Salazar, Rafael Blanco, and Catherine Plaisant (2022). Do You Believe Your (Social Media) Data? A Personal Story on Location Data Biases, Errors, and Plausibility as well as their Visualization. IEEE Transactions on Visualization and Computer Graphics, 2022. To appear. doi: [10.1109/TVCG.2022.3141605](https://doi.org/10.1109/TVCG.2022.3141605); open-access version available at https://hal.inria.fr/hal-03516682

## Bibtex
```
@ARTICLE{Isenberg:2022:DYB,
  author      = {Tobias Isenberg and Zujany Salazar and Rafael Blanco and Catherine Plaisant},
  title       = {Do You Believe Your (Social Media) Data? A Personal Story on Location Data Biases, Errors, and Plausibility as well as their Visualization},
  journal     = {IEEE Transactions on Visualization and Computer Graphics},
  year        = {2022},
  doi         = {10.1109/TVCG.2022.3141605},
  doi_url     = {https://doi.org/10.1109/TVCG.2022.3141605},
  oa_hal_url  = {https://hal.inria.fr/hal-03516682},
  osf_url     = {https://osf.io/u8ejr/},
  url         = {https://tobias.isenberg.cc/VideosAndDemos/Isenberg2022DYB},
  pdf         = {https://tobias.isenberg.cc/personal/papers/Isenberg_2022_DYB.pdf},
  note        = {To appear},
}
```

## Project website
https://tobias.isenberg.cc/VideosAndDemos/Isenberg2022DYB

## Note
Please note the software is provided "as is".  Use it at your own risk, although data loss is unlikely. Do take the standard precautions like saving your work in other programs.

## License
![CC BY-SA](https://i.creativecommons.org/l/by-sa/3.0/88x31.png) [Creative Commons Attribution-ShareAlike 4.0 International (CC BY-SA 4.0)](https://creativecommons.org/licenses/by-sa/4.0/)
(see [license.txt](license.txt)).

## Requirements

### Software Requirements
The Python3 script requires, in addition to a normal Python3 installation, several packages including (potentially more):
* ```geopy```
* ```plotly```
* ```matplotlib```
* ```numpy```
* ```powerlaw```

Install them using ```pip3 install [package]``` or the respective alternative for your installation of Python 3.

For some functions (but not in the default configuration), the script also needs to be able to call some external programs to do some of the data conversions. In particular:
* ```gpsbabel```: https://www.gpsbabel.org/
* ```zip```: e.g., http://infozip.sourceforge.net/

### Data requirements
The script requires additional CSV data files (named as specified in the ```familyFiles``` list in the script) downloaded from https://www.inaturalist.org/observations/export (if using different files you need to adjust the ```familyFiles``` list).

For the default configuration, please go to [the iNaturalist export page (may require an iNaturalist login)](https://www.inaturalist.org/observations/export) and download the data files for the taxa ```droseraceae```, ```nepenthaceae```, ```sarraceniaceae```, ```roridulaceae```, ```byblidaceae```, ```lentibulariaceae```, ```cephalotaceae```, and ```drosophyllaceae```. To do so, for each taxon, enter the taxon name into the ```taxon``` field on the form, select the suggested family in the pop-up that appears, select ```All``` for ```Geo``` and for ```Taxon``` under Point 3  (```Choose columns```), and then click the ```Create export``` button at the bottom of the page. Each export can take a while to generate based on the size of the family (e.g., families ```droseraceae```, ```nepenthaceae```, ```sarraceniaceae```, and ```lentibulariaceae``` are large and can take several hours each) and you can see the status at the bottom of the export page if you reload it (ask iNaturalist to send you an e-mail with the data once the export is complete). Also note that you can only create one export at a time. Once downloaded, unzip the data and rename the exported ```observations-123456.csv``` (or similar) files from iNaturalist to ```family.csv``` for easier association and to match the name in the script (e.g., ```droseraceae.csv```). Note that only with data files present for all families mentioned above the produced results will be appropriate and similar to those in the paper.

## Configuration
To configure the script, adjust the flags ```create*``` at the top of the script as needed (but the script runs with the default configuration out of the box). 

## Running the script
```
python3 _inaturalist.py
```

## Files produced
The script produces the visual representations of Fig. 17, 20, 34–36, and 68–72 of the paper (adjusted to the newly downloaded data). The Motion Plausibility Profiles are separated into the main representation and the respective histogram in two files.

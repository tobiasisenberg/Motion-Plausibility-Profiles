#!/usr/bin/python3

import os,sys
from subprocess import call,check_output
print("running Python " + sys.version)
# change to directory of the script
pathOfTheScript = os.path.dirname(sys.argv[0])
if (len(pathOfTheScript) > 0): os.chdir(pathOfTheScript)

import csv
import powerlaw
import math
import datetime
from geopy.distance import great_circle

# for visualizations
from plotly.offline import iplot, init_notebook_mode
import matplotlib.pyplot as plt
import numpy as np
import plotly.offline as py
import plotly.graph_objs as go
import plotly.io as pio

if (sys.version_info.major < 3):
    print("This script is called with Python " + str(sys.version_info.major) + ". But it needs at least Python 3, please call it with \"python3\" instead.")
    sys.exit()

############################################################################
# enable the different export functions by setting the flags to True below #
############################################################################
createDataExportForHeatmap = False # generate CSV data for separate heatmap visualization
createDataExportForVisTool = False # generate a clean CSV of the data
createDataExportForGPSTools = False # generate data for GPS tools (GPX, KML, KMZ)
createGeneralVisualizations = True # produce general/summary visualizations of the data
generateColorBlindCompatible = False # if false, then use the regular color mappings; otherwise use the adjusted color mappings for people with color impairments
createPersonVisualizationExcerpts = True # if true, then the Motion Plausibility Profile visualizations are generated for the ppl. mentioned below
createPersonVisualizationExcerptsWide = True # if true, then the MPPs are more wide than square
createPersonVisualizationExcerptsHistograms = True # if true, then also export the histogram for each person
createPersonVisualizationExcerptsWithPredefinedList = False # if true, then use the predefined list below for export, otherwise export people with >= 80 posts

# specify for which poster to export the Motion Plausibility Profiles (using createPersonVisualizationExcerpts)
peopleExcerptPlots = []
if createPersonVisualizationExcerptsWithPredefinedList:
    peopleExcerptPlots = [
        "987073",  # strgzzr: 545
        "997336",  # cobaltducks: 405
        "18823",  # ahospers: 344
        "383144",  # tonyrebelo: 316
        "388888",  # rfoster: 300
        "59391",  # a_calidris: 196
        "222137",  # reiner: 192
        "31792",  # aaroncarlson: 192
        "119644",  # rroutledge: 188
        "970009",  # brandoncorder: 168
        "578924",  # teresa45: 165
        "254480",  # bogwalker: 153
        "64568",  # ericpo1: 127
        "1829749",  # cclborneo: 126
        "1195500",  # kg-: 124
        "705762",  # misspt: 123
        "14208",  # philiptdotcom: 121
        "527990",  # vynbos: 120
        "17401",  # najera_tutor: 117
        "472267",  # j_appleget: 117
        "56162",  # janetwright: 112
        "533871",  # burke_korol: 107
        "365249",  # petekleinhenz: 103
        "1371028",  # tropicbreeze: 97
        "2991",  # sea-kangaroo: 97
        "875456",  # mcferny: 96
        "416993",  # umpquamatt: 96
        "777160",  # stevendaniel: 92
        "290071",  # nefariousdrru: 89
        "56498",  # anewman: 88
        "267179",  # jokurtz: 87
        "196849",  # questagame: 83
        "66205",  # neotiki: 80
        ]

# needs data downloaded from https://www.inaturalist.org/observations/export (one for each entry below in the familyFiles list)
familyFiles = [ "droseraceae", "nepenthaceae", "sarraceniaceae", "roridulaceae", "byblidaceae", "lentibulariaceae", "cephalotaceae", "drosophyllaceae" ]

############################################################################

# color maps for normal and color-blind Motion Trust Profiles
myColorMap = []
if (generateColorBlindCompatible): # ussing "7-class YlOrRd" from ColorBrewer
    myColorMap.append("rgb(55,126,184)")  # 0 not moving, blue
    myColorMap.append("rgb(254,217,118)") # 1 walking, yellow
    myColorMap.append("rgb(254,178,76)")  # 2 fast walking
    myColorMap.append("rgb(253,141,60)")  # 3 no more nunning, must be driving
    myColorMap.append("rgb(252,78,42)")   # 4 fast driving, unbelievable
    myColorMap.append("rgb(227,26,28)")   # 5 fastest driving, totally wrong
    myColorMap.append("rgb(177,0,38)")    # 6 flying, totally wrong, red
    myColorMap.append("rgb(0,0,0)")       # 7 no time has passed, black
else:
    myColorMap.append("rgb(55,126,184)")  # 0 not moving, blue
    myColorMap.append("rgb(26,150,65)")   # 1 walking, green
    myColorMap.append("rgb(166,217,106)") # 2 fast walking, light green
    myColorMap.append("rgb(203,203,15)")  # 3 no more nunning, must be driving, yellow
    myColorMap.append("rgb(253,174,97)")  # 4 fast driving, unbelievable, orange
    myColorMap.append("rgb(215,25,28)")   # 5 fastest driving, totally wrong, red
    myColorMap.append("rgb(129,15,124)")  # 6 flying, totally wrong, purple
    myColorMap.append("rgb(0,0,0)")       # 7 no time has passed, black

iNaturalistData = []
iNaturalistDataIDs = []
numberOfPrivateObservations = 0
numberOfPrivateObservationsWoGeo = 0

for dataFile in familyFiles:
    dataFileName = dataFile + ".csv"
    if os.path.isfile(dataFileName):
        with open(dataFileName, 'r', encoding='utf-8') as csvfile:
            # id, -> Unique identifier for the observation
            # observed_on_string, -> Date/time as entered by the observer
            # observed_on, -> Normalized date of observation
            # time_observed_at, -> Normalized datetime of observation
            # time_zone, -> Time zone of observation ################### could be a measure of accuracy, local time ###################
            # out_of_range, -> Whether or not this observation lies outside the taxon's known range
            # user_id, -> Unique identifier for the observer
            # user_login, -> Username of the observer
            # created_at, -> Datetime observation was created
            # updated_at, -> Datetime observation was last updated

            # quality_grade, -> Quality grade of this observation. See Help section for details on what this means:
            # "research", "needs_id", "casual"

            # license, -> License the observer has chosen for this observation
            # url, -> URL for the observation
            # image_url, -> URL for the default image
            # sound_url, -> URL for the default sound. Note this will only work for direct uploads, not sounds hosted on 3rd-party services
            # tag_list, -> Comma-separated list of tags
            # description,
            # id_please, -> Whether or not the observer requested ID help
            # num_identification_agreements, -> Number of identifications in concurrence with the observer's identification
            # num_identification_disagreements, -> Number of identifications conflicting with the observer's identification
            # captive_cultivated,
            # oauth_application_id,
            # place_guess, -> Locality description as entered by the observer
            # latitude, -> Publicly visible latitude
            # longitude, -> Publicly visible longitude
            # positional_accuracy, -> Coordinate precision (yeah, yeah, accuracy != precision, poor choice of names)
            # private_place_guess,
            # private_latitude, -> Private latitude, set if observation private or obscured
            # private_longitude, -> Private longitude, set if observation private or obscured
            # private_positional_accuracy,

            # geoprivacy, -> Whether or not the observer has chosen to obscure or hide the coordinates:
            #  "" (=="open"), "private", "obscured"

            # open
            # Everyone can see the coordinates, unless the taxon geoprivacy is "obscured" or "private". Appears as a
            #  teardrop-shaped marker.

            # obscured
            # Public coordinates are shown as a random point within a 0.2 by 0.2 degree area that contains the true coordinates.
            # This area works out to about a 22 by 22 kilometer area at the equator, decreasing in size and narrowing as you
            # approach the poles. The randomized public coordinates appear within the rectangle as a circular marker without
            # a stem. True coordinates are only visible to you, trusted users, and trusted project curators. iNaturalist Network
            # organizations, in their respective countries, can view true coordinates for taxa set to automatically obscure,
            # but they can only view your manually obscured coordinates if you choose to affiliate with the network in your
            # account settings.

            # private
            # Coordinates are completely hidden from public maps. True coordinates are only visible to you, trusted users, and
            # trusted project curators. iNaturalist Network organizations, in their respective countries, can view true
            # coordinates for taxa set to automatically display as private, but they can only view the coordinates of
            # observations you have manually set to private if you choose to affiliate with the network in your account settings.

            # taxon_geoprivacy, -> Most conservative geoprivacy applied due to the conservation statuses of taxa in current identification:
            # "", "obscured", "open"

            # coordinates_obscured, -> Whether or not the coordinates have been obscured, either because of geoprivacy or because of a threatened taxon:
            # "true", "false"

            # positioning_method, -> How the coordinates were determined
            # positioning_device, -> Device used to determine coordinates
            # place_town_name,
            # place_county_name,
            # place_state_name,
            # place_country_name,
            # place_admin1_name,
            # place_admin2_name,
            # species_guess, -> Name the observer entered for the observed taxon
            # scientific_name, -> Scientific name of the observed taxon according to this site
            # common_name, -> Common or vernacular name of the observed taxon according to this site
            # iconic_taxon_name, -> Higher-level taxonomic category for the observed taxon
            # taxon_id, -> Unique identifier for the observed taxon
            # taxon_kingdom_name,
            # taxon_phylum_name,
            # taxon_subphylum_name,
            # taxon_superclass_name,
            # taxon_class_name,
            # taxon_subclass_name,
            # taxon_superorder_name,
            # taxon_order_name,
            # taxon_suborder_name,
            # taxon_superfamily_name,
            # taxon_subfamily_name,
            # taxon_supertribe_name,
            # taxon_tribe_name,
            # taxon_subtribe_name,
            # taxon_family_name,
            # taxon_genus_name,
            # taxon_genushybrid_name,
            # taxon_species_name,
            # taxon_hybrid_name,
            # taxon_subspecies_name,
            # taxon_variety_name,
            # taxon_form_name

            dataReader = csv.reader(csvfile, delimiter=',', quotechar='"')
            headers = next(dataReader)[0:]
            for row in dataReader:
                newEntry = {key: str(value) for key, value in zip(headers, row[0:])}
                # filter out non-habitats
                if (newEntry["captive_cultivated"] == "true"): continue
                # make sure to record each observation only once (just as a safe-guard)
                if newEntry["id"] in iNaturalistDataIDs: continue
                # count the number of private entries
                if (newEntry['geoprivacy'] == "private"):
                    numberOfPrivateObservations += 1
                    if (newEntry["latitude"] == "") or (newEntry["longitude"] == ""):
                        numberOfPrivateObservationsWoGeo += 1
                # make sure we only record data with actual coordinates
                if newEntry["latitude"] == "": continue
                if newEntry["longitude"] == "": continue
                # ignore data without genus names (sometimes only the family is recorded)
                if newEntry["taxon_genus_name"] == "":
                    # we only map the monotypic families (only one so far) to their respective genuses
                    if newEntry["scientific_name"] in ["Nepenthaceae"]: # add more here if needed, so far only seems to be necessary for Nepenthaceae
                        if newEntry["scientific_name"] == "Nepenthaceae": newEntry["taxon_genus_name"] = "Nepenthes"
                    else:
                        # and ignore the rest
                        print("No genus name for id: " + str(newEntry["id"]), end='')
                        print(" ; scientific name: " + newEntry["scientific_name"], end='')
                        print(" (due to incomplete data; this is not an error but just FYI)")
                        continue

                # # make noise if we have obscured data and private location
                # # this was for debugging only; this happens if we have special access to the data for some people
                # # then we may have access to the private data despite the data being publically obscured
                # if createDataExportForVisTool:
                #     if ('private_latitude' in newEntry.keys()) and (len(str(newEntry['private_latitude'])) > 0) and (newEntry["coordinates_obscured"] == "true"):
                #         print("++++ PRIVATE DATA BUT COORD. STILL MARKED AS OBSCURED, fix FIXME in clean data export ++++ -> priv lat: " + str(newEntry['private_latitude']) + " priv lon: " + str(newEntry['private_longitude']))
                #         print("  -> " + newEntry["id"] + ";" + newEntry["scientific_name"])

                # add the new observation to our local list
                iNaturalistData.append(newEntry)
                iNaturalistDataIDs.append(newEntry["id"])

            csvfile.close()

totalEntryCount = len(iNaturalistData)
print("Read " + str(totalEntryCount) + " iNaturalist entries that include location data and are not captive plants.")

############################################
# some data analysis
############################################
obscuredCoordinatesCounter = 0

setOfQualityGrades = []
setOfGeoprivacy = []
setOfTaxonGeoprivacy = []
setOfObscuredTaxa = []
setOfUnobscuredTaxa = []
setOfCaptiveCultivated = []
numberOfGenusOnlyObservations = 0
numberOfResearchGradeObservations = 0

for location in iNaturalistData:
    if (location['coordinates_obscured'] == "true"): obscuredCoordinatesCounter += 1
    if not (location['quality_grade'] in setOfQualityGrades): setOfQualityGrades.append(location['quality_grade'])
    if not (location['geoprivacy'] in setOfGeoprivacy): setOfGeoprivacy.append(location['geoprivacy'])
    if not (location['taxon_geoprivacy'] in setOfTaxonGeoprivacy): setOfTaxonGeoprivacy.append(location['taxon_geoprivacy'])
    if not (location['captive_cultivated'] in setOfCaptiveCultivated): setOfCaptiveCultivated.append(location['captive_cultivated'])
    if (location['taxon_geoprivacy'] == "obscured"):
        if not (location['scientific_name'] in setOfObscuredTaxa):
            setOfObscuredTaxa.append(location['scientific_name'])
    else:
        if not (location['scientific_name'] in setOfUnobscuredTaxa):
            setOfUnobscuredTaxa.append(location['scientific_name'])

    if (location['taxon_species_name'] == ""):
        numberOfGenusOnlyObservations += 1

    if (location['quality_grade'] == "research"):
        numberOfResearchGradeObservations += 1

#     print(location['scientific_name'] + ": "
#         + location['latitude'] + " -:- " + location['longitude'] + " "
#         + " >" + location['quality_grade'] + "< "
#         + " >" + location['positional_accuracy'] + "< "
#         + " >" + location['geoprivacy'] + "< "
#         + " >" + location['taxon_geoprivacy'] + "< "
#         + " >" + location['coordinates_obscured'] + "< "
# #         + location['image_url']
#         )

print("Out of these, " + str(obscuredCoordinatesCounter) + " entries obscured.")
print("And " + str(totalEntryCount - obscuredCoordinatesCounter) + " entries unobscured.")

print("With " + str(numberOfGenusOnlyObservations) + " entries with genus information only, this is " + str(round(100.0*float(numberOfGenusOnlyObservations)/float(totalEntryCount),1)) + "%.")
print("With " + str(numberOfResearchGradeObservations) + " entries with research grade data, this is " + str(round(100.0*float(numberOfResearchGradeObservations)/float(totalEntryCount),1)) + "%.")
print("With " + str(numberOfPrivateObservations) + " out of " + str(totalEntryCount+numberOfPrivateObservationsWoGeo) + " entries with private data (incl. private entries w/o location data), this is " + str(round(100.0*float(numberOfPrivateObservations)/float(totalEntryCount+numberOfPrivateObservationsWoGeo),1)) + "%.")

# print("\nObserved quality_grade types:")
# for item in setOfQualityGrades:
#     print(item)

# print("\nObserved geoprivacy types:")
# for item in setOfGeoprivacy:
#     print(item)

# print("\nObserved taxon_geoprivacy types:")
# for item in setOfTaxonGeoprivacy:
#     print(item)

# print("\nObserved obscured taxa:")
# for item in setOfObscuredTaxa:
#     print(item)

# print("\nObserved unobscured taxa:")
# for item in setOfUnobscuredTaxa:
#     print(item)

print("\nIn total, " + str(len(setOfObscuredTaxa)) + " out of " + str(len(setOfObscuredTaxa) + len(setOfUnobscuredTaxa)) + " taxa are (partially!) obscured.")

# print("\nObserved captive_cultivated types:")
# for item in setOfCaptiveCultivated:
#     print(item)

############################################
# data export for EOL heat map analysis
############################################
if createDataExportForHeatmap:
    with open('inaturalist_data_heatmap.csv', 'w', encoding='utf-8') as outfile:
        for location in iNaturalistData:
            outfile.write(str(location['id']))
            outfile.write("\t"+location['user_id'])
            outfile.write("\t"+location['user_login'])
            # we use the private data if we have it (empty if we have no access)
            if 'private_latitude' in location.keys():
                outfile.write("\t"+str(location['private_latitude']))
            else:
                outfile.write("\t"+str(location['latitude']))
            if 'private_longitude' in location.keys():
                outfile.write("\t"+str(location['private_longitude']))
            else:
                outfile.write("\t"+str(location['longitude']))
            outfile.write("\n")
        outfile.close()

    with open('inaturalist_data_precise_heatmap.csv', 'w', encoding='utf-8') as outfile:
        for location in iNaturalistData:
            if (location['coordinates_obscured'] == "false"):
                outfile.write(str(location['id']))
                outfile.write("\t"+location['user_id'])
                outfile.write("\t"+location['user_login'])
                # we use the private data if we have it (empty if we have no access)
                if 'private_latitude' in location.keys():
                    outfile.write("\t"+str(location['private_latitude']))
                else:
                    outfile.write("\t"+str(location['latitude']))
                if 'private_longitude' in location.keys():
                    outfile.write("\t"+str(location['private_longitude']))
                else:
                    outfile.write("\t"+str(location['longitude']))
                outfile.write("\n")
        outfile.close()

    with open('inaturalist_data_obscured_heatmap.csv', 'w', encoding='utf-8') as outfile:
        for location in iNaturalistData:
            if (location['coordinates_obscured'] == "true"):
                outfile.write(str(location['id']))
                outfile.write("\t"+location['user_id'])
                outfile.write("\t"+location['user_login'])
                # we use the private data if we have it (empty if we have no access)
                if 'private_latitude' in location.keys():
                    outfile.write("\t"+str(location['private_latitude']))
                else:
                    outfile.write("\t"+str(location['latitude']))
                if 'private_longitude' in location.keys():
                    outfile.write("\t"+str(location['private_longitude']))
                else:
                    outfile.write("\t"+str(location['longitude']))
                outfile.write("\n")
        outfile.close()

    with open('inaturalist_data_taxon_empty_heatmap.csv', 'w', encoding='utf-8') as outfile:
        for location in iNaturalistData:
            if (location['taxon_geoprivacy'] == ""):
                outfile.write(str(location['id']))
                outfile.write("\t"+location['user_id'])
                outfile.write("\t"+location['user_login'])
                # we use the private data if we have it (empty if we have no access)
                if 'private_latitude' in location.keys():
                    outfile.write("\t"+str(location['private_latitude']))
                else:
                    outfile.write("\t"+str(location['latitude']))
                if 'private_longitude' in location.keys():
                    outfile.write("\t"+str(location['private_longitude']))
                else:
                    outfile.write("\t"+str(location['longitude']))
                outfile.write("\n")
        outfile.close()

    with open('inaturalist_data_taxon_open_heatmap.csv', 'w', encoding='utf-8') as outfile:
        for location in iNaturalistData:
            if (location['taxon_geoprivacy'] == "open"):
                outfile.write(str(location['id']))
                outfile.write("\t"+location['user_id'])
                outfile.write("\t"+location['user_login'])
                # we use the private data if we have it (empty if we have no access)
                if 'private_latitude' in location.keys():
                    outfile.write("\t"+str(location['private_latitude']))
                else:
                    outfile.write("\t"+str(location['latitude']))
                if 'private_longitude' in location.keys():
                    outfile.write("\t"+str(location['private_longitude']))
                else:
                    outfile.write("\t"+str(location['longitude']))
                outfile.write("\n")
        outfile.close()

    with open('inaturalist_data_taxon_obscured_heatmap.csv', 'w', encoding='utf-8') as outfile:
        for location in iNaturalistData:
            if (location['taxon_geoprivacy'] == "obscured"):
                outfile.write(str(location['id']))
                outfile.write("\t"+location['user_id'])
                outfile.write("\t"+location['user_login'])
                # we use the private data if we have it (empty if we have no access)
                if 'private_latitude' in location.keys():
                    outfile.write("\t"+str(location['private_latitude']))
                else:
                    outfile.write("\t"+str(location['latitude']))
                if 'private_longitude' in location.keys():
                    outfile.write("\t"+str(location['private_longitude']))
                else:
                    outfile.write("\t"+str(location['longitude']))
                outfile.write("\n")
        outfile.close()

    with open('inaturalist_data_d-rot_taxon_empty_heatmap.csv', 'w', encoding='utf-8') as outfile:
        for location in iNaturalistData:
            if (location['taxon_geoprivacy'] == "") and (location['scientific_name'] == "Drosera rotundifolia"):
                outfile.write(str(location['id']))
                outfile.write("\t"+location['user_id'])
                outfile.write("\t"+location['user_login'])
                # we use the private data if we have it (empty if we have no access)
                if 'private_latitude' in location.keys():
                    outfile.write("\t"+str(location['private_latitude']))
                else:
                    outfile.write("\t"+str(location['latitude']))
                if 'private_longitude' in location.keys():
                    outfile.write("\t"+str(location['private_longitude']))
                else:
                    outfile.write("\t"+str(location['longitude']))
                outfile.write("\n")
        outfile.close()

    with open('inaturalist_data_d-rot_taxon_open_heatmap.csv', 'w', encoding='utf-8') as outfile:
        for location in iNaturalistData:
            if (location['taxon_geoprivacy'] == "open") and (location['scientific_name'] == "Drosera rotundifolia"):
                outfile.write(str(location['id']))
                outfile.write("\t"+location['user_id'])
                outfile.write("\t"+location['user_login'])
                # we use the private data if we have it (empty if we have no access)
                if 'private_latitude' in location.keys():
                    outfile.write("\t"+str(location['private_latitude']))
                else:
                    outfile.write("\t"+str(location['latitude']))
                if 'private_longitude' in location.keys():
                    outfile.write("\t"+str(location['private_longitude']))
                else:
                    outfile.write("\t"+str(location['longitude']))
                outfile.write("\n")
        outfile.close()

    with open('inaturalist_data_d-rot_taxon_empty-open_heatmap.csv', 'w', encoding='utf-8') as outfile:
        for location in iNaturalistData:
            if ( (location['taxon_geoprivacy'] == "") or (location['taxon_geoprivacy'] == "open") ) and (location['scientific_name'] == "Drosera rotundifolia"):
                outfile.write(str(location['id']))
                outfile.write("\t"+location['user_id'])
                outfile.write("\t"+location['user_login'])
                # we use the private data if we have it (empty if we have no access)
                if 'private_latitude' in location.keys():
                    outfile.write("\t"+str(location['private_latitude']))
                else:
                    outfile.write("\t"+str(location['latitude']))
                if 'private_longitude' in location.keys():
                    outfile.write("\t"+str(location['private_longitude']))
                else:
                    outfile.write("\t"+str(location['longitude']))
                outfile.write("\n")
        outfile.close()

    with open('inaturalist_data_d-rot_taxon_obscured_heatmap.csv', 'w', encoding='utf-8') as outfile:
        for location in iNaturalistData:
            if (location['taxon_geoprivacy'] == "obscured") and (location['scientific_name'] == "Drosera rotundifolia"):
                outfile.write(str(location['id']))
                outfile.write("\t"+location['user_id'])
                outfile.write("\t"+location['user_login'])
                # we use the private data if we have it (empty if we have no access)
                if 'private_latitude' in location.keys():
                    outfile.write("\t"+str(location['private_latitude']))
                else:
                    outfile.write("\t"+str(location['latitude']))
                if 'private_longitude' in location.keys():
                    outfile.write("\t"+str(location['private_longitude']))
                else:
                    outfile.write("\t"+str(location['longitude']))
                outfile.write("\n")
        outfile.close()

    with open('inaturalist_data_geoprivacy_empty_heatmap.csv', 'w', encoding='utf-8') as outfile:
        for location in iNaturalistData:
            if (location['geoprivacy'] == ""):
                outfile.write(str(location['id']))
                outfile.write("\t"+location['user_id'])
                outfile.write("\t"+location['user_login'])
                # we use the private data if we have it (empty if we have no access)
                if 'private_latitude' in location.keys():
                    outfile.write("\t"+str(location['private_latitude']))
                else:
                    outfile.write("\t"+str(location['latitude']))
                if 'private_longitude' in location.keys():
                    outfile.write("\t"+str(location['private_longitude']))
                else:
                    outfile.write("\t"+str(location['longitude']))
                outfile.write("\n")
        outfile.close()

    with open('inaturalist_data_geoprivacy_obscured_heatmap.csv', 'w', encoding='utf-8') as outfile:
        for location in iNaturalistData:
            if (location['geoprivacy'] == "obscured"):
                outfile.write(str(location['id']))
                outfile.write("\t"+location['user_id'])
                outfile.write("\t"+location['user_login'])
                # we use the private data if we have it (empty if we have no access)
                if 'private_latitude' in location.keys():
                    outfile.write("\t"+str(location['private_latitude']))
                else:
                    outfile.write("\t"+str(location['latitude']))
                if 'private_longitude' in location.keys():
                    outfile.write("\t"+str(location['private_longitude']))
                else:
                    outfile.write("\t"+str(location['longitude']))
                outfile.write("\n")
        outfile.close()

    with open('inaturalist_data_geoprivacy_private_heatmap.csv', 'w', encoding='utf-8') as outfile:
        for location in iNaturalistData:
            if (location['geoprivacy'] == "private"):
                outfile.write(str(location['id']))
                outfile.write("\t"+location['user_id'])
                outfile.write("\t"+location['user_login'])
                # we use the private data if we have it (empty if we have no access)
                if 'private_latitude' in location.keys():
                    outfile.write("\t"+str(location['private_latitude']))
                else:
                    outfile.write("\t"+str(location['latitude']))
                if 'private_longitude' in location.keys():
                    outfile.write("\t"+str(location['private_longitude']))
                else:
                    outfile.write("\t"+str(location['longitude']))
                outfile.write("\n")
        outfile.close()

############################################
# data export for GPS tools
############################################
if createDataExportForGPSTools:
    with open('inaturalist_data_clean_precise.gpx', 'w') as outfile:
        outfile.write('<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<gpx version=\"1.1\" creator=\"Manual\" xmlns=\"http://www.topografix.com/GPX/1/1\" xmlns:gpxx=\"http://www.garmin.com/xmlschemas/GpxExtensions/v3\" xmlns:gpxtpx=\"http://www.garmin.com/xmlschemas/TrackPointExtension/v1\">\n')
        for location in iNaturalistData:
            if (location['coordinates_obscured'] == "false") or (len(str(location['private_latitude'])) > 0):
                # we use the private data if we have it (they are empty if we have no access)
                outfile.write("  <wpt lat=\"")
                if ('private_latitude' in location.keys()) and (len(str(location['private_latitude'])) > 0):
                    outfile.write(str(location['private_latitude']))
                else:
                    outfile.write(str(location['latitude']))
                outfile.write("\" lon=\"")
                if ('private_longitude' in location.keys()) and (len(str(location['private_longitude'])) > 0):
                    outfile.write(str(location['private_longitude']))
                else:
                    outfile.write(str(location['longitude']))
                outfile.write("\">\n")
                outfile.write("    <ele>0.000000</ele>\n") # FIXME: maybe add elevation data from public data later

                speciesName = ""
                hybrid = 0
                if location['taxon_hybrid_name'] != "":
                    speciesName = "x " + location['taxon_hybrid_name'].split(' ')[-1]
                    hybrid = 1
                else:
                    if ' ' in location['taxon_species_name']:
                        speciesName = location['taxon_species_name'].split(' ')[1]

                outfile.write("    <name>"+location['taxon_genus_name']+" "+speciesName+"</name>\n")
                outfile.write("    <cmt>"+location['taxon_genus_name']+" "+speciesName+"</cmt>\n") # "+location.encode('utf-8','replace').decode('utf-8')+" 
                outfile.write("    <desc>"+location['taxon_genus_name']+" "+speciesName+"</desc>\n") #"+location+" 
                outfile.write("    <cmt></cmt>\n") # "+location.encode('utf-8','replace').decode('utf-8')+" 
                outfile.write("    <desc></desc>\n") #"+location+" 
                outfile.write("  </wpt>\n")
        outfile.write('</gpx>\n')
        outfile.close()			
    call(["gpsbabel", "-i", "gpx,gpxver=1.1,garminextensions", "-f", "inaturalist_data_clean_precise.gpx", "-o", "kml", "-F", "inaturalist_data_clean_precise.kml"])
    call(["zip", "inaturalist_data_clean_precise.kmz", "inaturalist_data_clean_precise.kml"])

    with open('inaturalist_data_clean_obscured.gpx', 'w') as outfile:
        outfile.write('<?xml version=\"1.0\" encoding=\"UTF-8\"?>\n<gpx version=\"1.1\" creator=\"Manual\" xmlns=\"http://www.topografix.com/GPX/1/1\" xmlns:gpxx=\"http://www.garmin.com/xmlschemas/GpxExtensions/v3\" xmlns:gpxtpx=\"http://www.garmin.com/xmlschemas/TrackPointExtension/v1\">\n')
        for location in iNaturalistData:
            if (location['coordinates_obscured'] == "true") and (len(str(location['private_latitude'])) == 0):
                # we use the private data if we have it (empty if we have no access)
                outfile.write("  <wpt lat=\"")
                outfile.write(str(location['latitude']))
                outfile.write("\" lon=\"")
                outfile.write(str(location['longitude']))
                outfile.write("\">\n")
                outfile.write("    <ele>0.000000</ele>\n")

                speciesName = ""
                hybrid = 0
                if location['taxon_hybrid_name'] != "":
                    speciesName = "x " + location['taxon_hybrid_name'].split(' ')[-1]
                    hybrid = 1
                else:
                    if ' ' in location['taxon_species_name']:
                        speciesName = location['taxon_species_name'].split(' ')[1]

                outfile.write("    <name>"+location['taxon_genus_name']+" "+speciesName+"</name>\n")
                outfile.write("    <cmt>"+location['taxon_genus_name']+" "+speciesName+"</cmt>\n") # "+location.encode('utf-8','replace').decode('utf-8')+" 
                outfile.write("    <desc>"+location['taxon_genus_name']+" "+speciesName+"</desc>\n") #"+location+" 
                outfile.write("    <cmt></cmt>\n") # "+location.encode('utf-8','replace').decode('utf-8')+" 
                outfile.write("    <desc></desc>\n") #"+location+" 
                outfile.write("  </wpt>\n")
        outfile.write('</gpx>\n')
        outfile.close()			
    call(["gpsbabel", "-i", "gpx,gpxver=1.1,garminextensions", "-f", "inaturalist_data_clean_obscured.gpx", "-o", "kml", "-F", "inaturalist_data_clean_obscured.kml"])
    call(["zip", "inaturalist_data_clean_obscured.kmz", "inaturalist_data_clean_obscured.kml"])

############################################
# data export for web tool
############################################
if createDataExportForVisTool:
    with open('inaturalist_data_clean.csv', 'w', encoding='utf-8') as outfile:
        outfile.write('#observationID,serviceName,lat,long,elevation,genus,species,subspecies,variety,hybrid,country,date,location_information,picture_author,picture_author_id,status_of_verification_by_TI,image_URL\n')
        for location in iNaturalistData:
            outfile.write(str(location['id']))

            # we use the private data if we have it (it is empty if we have no access)
            if ('private_latitude' in location.keys()) and (len(str(location['private_latitude'])) > 0):
                outfile.write(",in-precise")
                outfile.write(","+str(location['private_latitude']))
            else:
                if (location['coordinates_obscured'] == "true"):
                    outfile.write(",in-obscured")
                else:
                    outfile.write(",in-precise")
                outfile.write(","+str(location['latitude']))

            if ('private_longitude' in location.keys()) and (len(str(location['private_longitude'])) > 0):
                outfile.write(",in-precise")
                outfile.write(","+str(location['private_longitude']))
            else:
                if (location['coordinates_obscured'] == "true"):
                    outfile.write(",in-obscured")
                else:
                    outfile.write(",in-precise")
                outfile.write(","+str(location['longitude']))

            outfile.write(",") # no elevation data yet, will maybe add later (FIXME)
            
            outfile.write(","+location['taxon_genus_name'])

            speciesName = ""
            hybrid = 0
            if location['taxon_hybrid_name'] != "":
                speciesName = "x " + location['taxon_hybrid_name'].split(' ')[-1]
                hybrid = 1
            else:
                if ' ' in location['taxon_species_name']:
                    speciesName = location['taxon_species_name'].split(' ')[1]
            outfile.write(","+speciesName)

            if ' ' in location['taxon_subspecies_name']:
                outfile.write(","+location['taxon_subspecies_name'].split(' ')[-1])
            else:
                outfile.write(","+location['taxon_subspecies_name'])
            
            if ' ' in location['taxon_variety_name']:
                outfile.write(","+location['taxon_variety_name'].split(' ')[-1])
            else:
                outfile.write(","+location['taxon_variety_name'])
            
            outfile.write(","+str(hybrid))
            outfile.write(",\""+location['place_country_name']+"\"")
            outfile.write(","+location['observed_on'].replace('-','/'))
            # outfile.write(","+location['time_observed_at'])
            # outfile.write(",\""+location['observed_on_string']+"\"")
            outfile.write(",\""+location['place_guess'].replace('"','')+"\"")
            outfile.write(",\""+location['user_login']+"\"")
            outfile.write(",\""+location['user_id']+"\"")
            outfile.write(",unverified") # no personal verification data yet, will add later
            if "https://static.inaturalist.org/" in location['image_url']:
                outfile.write(","+location['image_url'])
            else: # some image URLs from outside iNaturalist exist, but they are typically invalid, so ignore them
                outfile.write(",")
            outfile.write("\n")
        outfile.close()

############################################
# visualizations
############################################
if createGeneralVisualizations:
    print ("\nGenerating visualization")
    os.makedirs(pathOfTheScript + os.sep + "vis", exist_ok=True)

    # find information about people and their postings
    print ("Collecting information about people's posts counts (incl. sorting, may take a bit)")
    peopleAndPictureDict = {}
    peopleDict = {}
    for location in iNaturalistData:
        # record all people who posted
        if not location['user_id'] in peopleDict.keys():
            peopleDict[location['user_id']] = location['user_login']
        
        # for each person, record the list of posted observations
        ownerIdForLookup = location['user_id'] + "-" + location['user_login']
        if not ownerIdForLookup in peopleAndPictureDict.keys():
            peopleAndPictureDict[ownerIdForLookup] = ["i" + str(location['id'])]
        else:
            peopleAndPictureDict[ownerIdForLookup].append("i" + str(location['id']))
    
    # store the collected list of people's ids, their logins, and their post counts
    with open('iNaturalist_posters.csv', 'w', encoding='utf-8') as outfile:
        for personId in peopleDict.keys():
            outfile.write(personId + "," + peopleDict[personId] + "," + str(len(peopleAndPictureDict[personId + "-" + peopleDict[personId]])) + "\n")

        outfile.close()

    ##################################
    # get a list of all recorded species
    ##################################
    speciesList = []
    speciesListCount = {}
    for location in iNaturalistData:
        species = location['scientific_name']
        if not (species in speciesList):
            speciesList.append(species)
            speciesListCount[species] = 1
        else:
            speciesListCount[species] = speciesListCount[species] + 1
    speciesList.sort()

    ##################################
    # create visualization of species counts (alphabetical)
    ##################################
    print ("Species visualizations")
    speciesListSortedByCount = []
    speciesCountSortedByCount = []
    for species in sorted(speciesListCount.keys(), reverse=True):
        speciesKey = species
        if (len(species.split(' ')) == 1): speciesKey = species + " (unclassified)"
        speciesListSortedByCount.append(speciesKey)
        speciesCountSortedByCount.append(speciesListCount[species])
    data = [
        go.Bar(
            x = speciesCountSortedByCount,
            y = speciesListSortedByCount,
            orientation = 'h',
            # text = speciesCountSortedByCount,
            # textposition = 'auto',
            # textfont = dict( size=9 ),
            marker = dict( color='rgb(55,126,184)', line=dict(width=0) )
        )
    ]
    layout = go.Layout(
        margin=dict(l = 150, r = 10, b = 10, t = 10, pad = 4),
        font=dict(size = 4)
    )
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='vis' + os.sep + '0_iNaturalist-species-count-alphabetical.html', auto_open=False, show_link=False)
    layout = go.Layout(
        width = 1200,
        height = 1600,
        margin = dict(l = 55, r = 5, b = 25, t = 5, pad = 4),
        #xaxis = dict(tickangle=180),
        font = dict(size = 2.2),
        # xaxis = dict(tickfont = dict(size = 20)),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            tickfont = dict(size = 20),
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor='#2a3f5f',
            gridwidth=0.5,
            gridcolor='rgb(230,230,230)',
        ),
        # yaxis=dict(
        # 	zeroline=True,
        # 	zerolinewidth=1,
        # 	zerolinecolor='#2a3f5f',
        # 	gridwidth=0.5,
        # 	gridcolor='rgb(230,230,230)',
        # ),
    )
    annotations = []
    for i in range(0, len(speciesCountSortedByCount)):
        annotations.append(dict(
            xref = 'x', yref  ='y', y = i, x = speciesCountSortedByCount[i] + 2, xanchor = 'left', yanchor = 'middle',
            text = str(speciesCountSortedByCount[i]),
            font = dict(color = '#2a3f5f',size = 2),
            showarrow=False
        ))
    layout['annotations'] = annotations
    fig = go.Figure(data=data, layout=layout)
    pio.write_image(fig, 'vis' + os.sep + '0_iNaturalist-species-count-alphabetical.pdf')

    ##################################
    # create visualization of species counts (rank)
    ##################################
    speciesListSortedByCount = []
    speciesCountSortedByCount = []
    unclassifiedGenusCounter = 0 # this value is used later for genrating the logarithmic distribution graph

    for species, speciesCount in sorted(speciesListCount.items(), key=lambda item: item[1]):
    # for species in sorted(speciesListCount.values(), reverse=True):
        speciesKey = species
        if (len(species.split(' ')) == 1): 
            speciesKey = species + " (unclassified)"
            unclassifiedGenusCounter += 1
        speciesListSortedByCount.append(speciesKey)
        speciesCountSortedByCount.append(speciesCount)

    data = [
        go.Bar(
            x = speciesCountSortedByCount,
            y = speciesListSortedByCount,
            orientation = 'h',
            # text = speciesCountSortedByCount,
            # textposition = 'auto',
            # textfont = dict( size=9 ),
            marker = dict( color='rgb(55,126,184)', line=dict(width=0) )
        )
    ]
    layout = go.Layout(
        margin = dict(l=150, r=10, b=10, t=10, pad=4),
        font = dict(size=4)
    )
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='vis' + os.sep + '0_iNaturalist-species-count-rank.html', auto_open=False, show_link=False)
    layout = go.Layout(
        width = 1200,
        height = 1600,
        margin = dict(l = 55, r = 5, b = 25, t = 5, pad = 4),
        #xaxis=dict(tickangle=180),
        font = dict(size = 2.2),
        # xaxis = dict(tickfont = dict(size = 20)),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            tickfont = dict(size = 20),
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor='#2a3f5f',
            gridwidth=0.5,
            gridcolor='rgb(230,230,230)',
        ),
        # yaxis=dict(
        # 	zeroline=True,
        # 	zerolinewidth=1,
        # 	zerolinecolor='#2a3f5f',
        # 	gridwidth=0.5,
        # 	gridcolor='rgb(230,230,230)',
        # ),
    )
    annotations = []
    for i in range(0, len(speciesCountSortedByCount)):
        annotations.append(dict(
            xref='x', yref='y', y = i, x = speciesCountSortedByCount[i] + 2, xanchor = 'left', yanchor = 'middle',
            text = str(speciesCountSortedByCount[i]),
            font = dict(color='#2a3f5f',size=2),
            showarrow=False
        ))
    layout['annotations'] = annotations
    fig = go.Figure(data=data, layout=layout)
    pio.write_image(fig, 'vis' + os.sep + '0_iNaturalist-species-count-rank.pdf')

    ##################################
    # the power-law plot for the species
    ##################################
    # dedicated assembly of the data again as there are genus entries without species, which we do not want to count
    speciesRankSortedByCount = []
    speciesCountForRankSortedByCount = []
    speciesCounter = len(speciesListCount) - unclassifiedGenusCounter
    for species, speciesCount in sorted(speciesListCount.items(), key=lambda item: item[1]):
        if (len(species.split(' ')) != 1): 
            speciesCountForRankSortedByCount.append(speciesCount)
            speciesRankSortedByCount.append(speciesCounter)
            speciesCounter -= 1

    print("Computing powerlaw for observations per species counts")
    fit = powerlaw.Fit(speciesCountForRankSortedByCount[::-1], verbose=False, discrete=True) #, xmin=1)
    print("powerlaw alpha: " + str(fit.power_law.alpha) + " " + str(fit.power_law.parameter1_name))
    print("powerlaw sigma: " + str(fit.power_law.sigma) + " " + str(fit.power_law.parameter2_name))
    print("powerlaw x_min: " + str(fit.power_law.xmin))
    fit = powerlaw.Fit(speciesCountForRankSortedByCount[::-1], verbose=False, discrete=True, xmin=2)
    print("powerlaw alpha: " + str(fit.power_law.alpha) + " " + str(fit.power_law.parameter1_name))
    print("powerlaw sigma: " + str(fit.power_law.sigma) + " " + str(fit.power_law.parameter2_name))
    print("powerlaw x_min: " + str(fit.power_law.xmin))
    fit = powerlaw.Fit(speciesCountForRankSortedByCount[::-1], verbose=False, discrete=True, xmin=1)
    print("powerlaw alpha: " + str(fit.power_law.alpha) + " " + str(fit.power_law.parameter1_name))
    print("powerlaw sigma: " + str(fit.power_law.sigma) + " " + str(fit.power_law.parameter2_name))
    print("powerlaw x_min: " + str(fit.power_law.xmin))

    data = [
        go.Scatter(
            y = speciesCountForRankSortedByCount,
            x = speciesRankSortedByCount,
            orientation = 'v',
            line = dict( color='rgb(55,126,184)', width=4)
        )
    ]
    layout = go.Layout(
        margin = dict(l=55, r=10, b=10, t=10, pad=4),
        font = dict(size=4)
    )
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='vis' + os.sep + '0_iNaturalist-species-count-distribution.html', auto_open=False, show_link=False)
    layout = go.Layout(
        width = 1300,
        height = 1200,
        margin = dict(l=115, r=10, b=75, t=10, pad=4),
        font = dict(size=40),
        xaxis_type="log", yaxis_type="log",
        # yaxis = dict(range=(0, math.log10(speciesCountForRankSortedByCount[-1]) + 0.1), constrain='domain')
    	paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showline=True,
            linewidth=2,
            linecolor='#2a3f5f',
            # zeroline=True,
            # zerolinewidth=1,
            # zerolinecolor='#2a3f5f',
            gridwidth=1,
            gridcolor='rgb(230,230,230)',
        ),
        yaxis=dict(
            showline=True,
            linewidth=2,
            linecolor='#2a3f5f',
            # zeroline=True,
            # zerolinewidth=1,
            # zerolinecolor='#2a3f5f',
            gridwidth=1,
            gridcolor='rgb(230,230,230)',
            range=(0, math.log10(speciesCountForRankSortedByCount[-1]) + 0.1), constrain='domain',
        ),
)
    fig = go.Figure(data=data, layout=layout)
    # fig.update_xaxes(showline=True, linewidth=2, linecolor='black')
    # fig.update_yaxes(showline=True, linewidth=2, linecolor='black')
    pio.write_image(fig, 'vis' + os.sep + '0_iNaturalist-species-count-distribution.pdf')

    ##################################
    # create visualization of people's post counts (rank)
    ##################################
    # count the entries per person and sort the dictionary accordingly
    peopleAndPictureCount = {}
    for personId in peopleAndPictureDict.keys():
        peopleAndPictureCount[personId] = len(peopleAndPictureDict[personId])
    # peopleAndPictureCountSorted = sorted(peopleAndPictureCount.items(), key = lambda kv: kv[1], reverse=True)
    # print(peopleAndPictureCountSorted)

    peopleAndPictureCountSortedKeys = []
    peopleAndPictureCountSortedRank = []
    peopleAndPictureCountSortedValues = []
    peopleAndPictureCountSortedTopKeys = []
    peopleAndPictureCountSortedTopRank = []
    peopleAndPictureCountSortedTopValues = []
    totalKnownPicturesWithDuplicates = len(iNaturalistData)
    halfKnownPicturesWithDuplicates = int(totalKnownPicturesWithDuplicates * 0.5)
    pictureCounter = len(iNaturalistData)
    medianPersonFromTop = len(peopleAndPictureCount)
    personCounter = len(peopleAndPictureCount)
    personWith1ImageCounter = 0
    personWith2OrLessImagesCounter = 0
    personWith3OrLessImagesCounter = 0
    personWith5OrLessImagesCounter = 0
    sortedPeopleAndPictureCount = sorted(peopleAndPictureCount.items(), key=lambda item: item[1])
    for peoplePosting, postCountCount in sortedPeopleAndPictureCount:
        peopleAndPictureCountSortedKeys.append(peoplePosting)
        peopleAndPictureCountSortedValues.append(postCountCount)
        peopleAndPictureCountSortedRank.append(personCounter)

        # find the rank of the person after which we have half our pictures
        if (pictureCounter > halfKnownPicturesWithDuplicates):
            pictureCounter -= postCountCount
            medianPersonFromTop -= 1

        # data for the top posters with at least 5 pictures each
        if postCountCount > 10:
            peopleAndPictureCountSortedTopKeys.append(peoplePosting)
            peopleAndPictureCountSortedTopValues.append(postCountCount)
            peopleAndPictureCountSortedTopRank.append(personCounter)
    
        # count the low contributers
        if postCountCount <= 5: personWith5OrLessImagesCounter += 1
        if postCountCount <= 3: personWith3OrLessImagesCounter += 1
        if postCountCount <= 2: personWith2OrLessImagesCounter += 1
        if postCountCount == 1: personWith1ImageCounter += 1

        # decrease the rank counter
        personCounter -= 1

    print("The most frequent posters are (at least 80 posts):")
    for peoplePosting, postCountCount in sortedPeopleAndPictureCount[::-1]:
        if postCountCount >= 80:
            print("     " + peoplePosting + ": " + str(postCountCount))
            if createPersonVisualizationExcerptsWithPredefinedList == False:
                peopleExcerptPlots.append(peoplePosting.split("-")[0])

    print("Only " + str(round(float(medianPersonFromTop)*100.0/float(len(peopleAndPictureCount)),1)) + "%% of the people (i.e., " + str(medianPersonFromTop) + ", out of " + str(len(peopleAndPictureCount)) + " total people posting images) are responsible for half (" + str(halfKnownPicturesWithDuplicates) + ") of the images (" + str(pictureCounter) + " images to be precise).")
    print("Posters with N or less images:")
    print("<= 5: " + str(personWith5OrLessImagesCounter) + " (i.e., " + str(round(float(personWith5OrLessImagesCounter)*100.0/float(len(peopleAndPictureCount)),1)) + "%%)")
    print("<= 3: " + str(personWith3OrLessImagesCounter) + " (i.e., " + str(round(float(personWith3OrLessImagesCounter)*100.0/float(len(peopleAndPictureCount)),1)) + "%%)")
    print("<= 2: " + str(personWith2OrLessImagesCounter) + " (i.e., " + str(round(float(personWith2OrLessImagesCounter)*100.0/float(len(peopleAndPictureCount)),1)) + "%%)")
    print("== 1: " + str(personWith1ImageCounter) + " (i.e., " + str(round(float(personWith1ImageCounter)*100.0/float(len(peopleAndPictureCount)),1)) + "%%)")

    # print("Observation count array:")
    # print(peopleAndPictureCountSortedValues)
    print("Computing powerlaw")
    fit = powerlaw.Fit(peopleAndPictureCountSortedValues[::-1], discrete=True, verbose=False) #, xmin=1)
    print("powerlaw alpha: " + str(fit.power_law.alpha) + " " + str(fit.power_law.parameter1_name))
    print("powerlaw sigma: " + str(fit.power_law.sigma) + " " + str(fit.power_law.parameter2_name))
    print("powerlaw x_min: " + str(fit.power_law.xmin))
    # print("lognormal " + str(fit.lognormal.parameter1_name) + ": " + str(fit.lognormal.parameter1))
    # print("lognormal " + str(fit.lognormal.parameter2_name) + ": " + str(fit.lognormal.parameter2))
    # print("lognormal x_min: " + str(fit.lognormal.xmin))
    # print("distribution_compare powerlaw - longnormal: " + str(fit.distribution_compare('power_law', 'lognormal')))
    # print("exponential " + str(fit.exponential.parameter1_name) + ": " + str(fit.exponential.parameter1))
    # print("exponential " + str(fit.exponential.parameter2_name) + ": " + str(fit.exponential.parameter2))
    # print("exponential x_min: " + str(fit.exponential.xmin))
    # print("distribution_compare powerlaw - exponential: " + str(fit.distribution_compare('power_law', 'exponential')))

    ##################################
    # the bar graph of the top people
    ##################################
    data = [
        go.Bar(
            x = peopleAndPictureCountSortedTopValues,
            y = peopleAndPictureCountSortedTopKeys,
            orientation = 'h',
            marker = dict( color='rgb(55,126,184)', line=dict(width=0) )
        )
    ]
    layout = go.Layout(
        margin = dict(l=150, r=10, b=10, t=10, pad=4),
        font = dict(size=3)
    )
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='vis' + os.sep + '0_iNaturalist-people-post-count-rank-top.html', auto_open=False, show_link=False)
    layout = go.Layout(
        width = 1200,
        height = 1600,
        margin = dict(l=150, r=10, b=30, t=10, pad=4),
        #xaxis=dict(tickangle=180),
        font = dict(size=2),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            tickfont = dict(size = 20),
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor='#2a3f5f',
            gridwidth=0.5,
            gridcolor='rgb(230,230,230)',
        ),
        # yaxis=dict(
        # 	zeroline=True,
        # 	zerolinewidth=1,
        # 	zerolinecolor='#2a3f5f',
        # 	gridwidth=0.5,
        # 	gridcolor='rgb(230,230,230)',
        # ),
    )
    annotations = []
    for i in range(0, len(peopleAndPictureCountSortedTopValues)):
        annotations.append(dict(
            xref='x', yref='y', y = i, x = peopleAndPictureCountSortedTopValues[i] + 2, xanchor = 'left', yanchor = 'middle',
            text = str(peopleAndPictureCountSortedTopValues[i]),
            font = dict(color='#2a3f5f'),
            showarrow=False
        ))
    layout['annotations'] = annotations
    fig = go.Figure(data=data, layout=layout)
    pio.write_image(fig, 'vis' + os.sep + '0_iNaturalist-people-post-count-rank-top.pdf')

    ##################################
    # the power-law plot for all people
    ##################################
    data = [
        go.Scatter(
            y = peopleAndPictureCountSortedValues,
            x = peopleAndPictureCountSortedRank,
            orientation = 'v',
            line = dict( color='rgb(55,126,184)', width=4)
        )
    ]
    layout = go.Layout(
        margin = dict(l=150, r=10, b=10, t=10, pad=4),
        font = dict(size=4)
    )
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='vis' + os.sep + '0_iNaturalist-people-post-count-distribution.html', auto_open=False, show_link=False)
    layout = go.Layout(
        width = 1300,
        height = 1200,
        margin = dict(l=100, r=10, b=55, t=10, pad=4),
        #xaxis=dict(tickangle=180),
        font = dict(size=40),
        xaxis_type="log", yaxis_type="log",
        # yaxis = dict(range=(0, math.log10(peopleAndPictureCountSortedValues[-1]) + 0.1), constrain='domain')
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            showline=True,
            linewidth=2,
            linecolor='#2a3f5f',
            gridwidth=1,
            gridcolor='rgb(230,230,230)',
        ),
        yaxis=dict(
            showline=True,
            linewidth=2,
            linecolor='#2a3f5f',
            gridwidth=1,
            gridcolor='rgb(230,230,230)',
            range=(0, math.log10(peopleAndPictureCountSortedValues[-1]) + 0.1), constrain='domain',
        ),
    )
    fig = go.Figure(data=data, layout=layout)
    # fig.update_xaxes(showline=True, linewidth=2, linecolor='black')
    # fig.update_yaxes(showline=True, linewidth=2, linecolor='black')
    pio.write_image(fig, 'vis' + os.sep + '0_iNaturalist-people-post-count-distribution.pdf')

    ##################################
    # the bar graph of the all people
    ##################################
    data = [
        go.Bar(
            x = peopleAndPictureCountSortedValues,
            y = peopleAndPictureCountSortedKeys,
            orientation = 'h',
            marker = dict( color='rgb(55,126,184)', line=dict(width=0) )
        )
    ]
    layout = go.Layout(
        margin = dict(l=150, r=10, b=10, t=10, pad=4),
        font = dict(size=4)
    )
    fig = go.Figure(data=data, layout=layout)
    py.plot(fig, filename='vis' + os.sep + '0_iNaturalist-people-post-count-rank.html', auto_open=False, show_link=False)
    layout = go.Layout(
        width = 1200,
        height = 1600,
        margin = dict(l=5, r=5, b=25, t=5, pad=4),
        #xaxis=dict(tickangle=180),
        yaxis = dict(showticklabels = False),
        font = dict(size=20.0),
        paper_bgcolor='rgba(0,0,0,0)',
        plot_bgcolor='rgba(0,0,0,0)',
        xaxis=dict(
            tickfont = dict(size = 20),
            zeroline=True,
            zerolinewidth=1,
            zerolinecolor='#2a3f5f',
            gridwidth=0.5,
            gridcolor='rgb(230,230,230)',
        ),
        # yaxis=dict(
        # 	zeroline=True,
        # 	zerolinewidth=1,
        # 	zerolinecolor='#2a3f5f',
        # 	gridwidth=0.5,
        # 	gridcolor='rgb(230,230,230)',
        # ),
    )
    # this part failed with a 522 timeout in orca, but works with the new python/plotly
    annotations = []
    for i in range(0, len(peopleAndPictureCountSortedValues)):
        annotations.append(dict(
            xref='x', yref='y', y = i, x = peopleAndPictureCountSortedValues[i] + 2, xanchor = 'left', yanchor = 'middle',
            text = str(peopleAndPictureCountSortedValues[i]),
            font = dict(color='#2a3f5f', size=1.0),
            showarrow=False
        ))
    layout['annotations'] = annotations
    fig = go.Figure(data=data, layout=layout)
    pio.write_image(fig, 'vis' + os.sep + '0_iNaturalist-people-post-count-rank.pdf')

##################################
# create person excerpts
##################################
if createPersonVisualizationExcerpts:
    rankCounter = 0
    with open('frequent-poster.log', 'w') as outfile:
        print("Creating person excerpts:")
        for person in peopleExcerptPlots:
            rankCounter += 1
            personLabel = person
            personMissedImages = 0
            outfile.write('============================\n')
            outfile.write(person)
            pictureListOfPersonWithDetails = []
            counterObservationsPrecise = 0
            counterObservationsObscured = 0
            counterObservationsWithTime = 0
            counterObservationsWithoutTime = 0
            counterObservationsClassFirst = 0
            counterObservationsClassInstantaneous = 0
            counterObservationsClass0kmh = 0
            counterObservationsClass0to5kmh = 0
            counterObservationsClass5to10kmh = 0
            counterObservationsClass10to25kmh = 0
            counterObservationsClass25to80kmh = 0
            counterObservationsClass80to200kmh = 0
            counterObservationsClassMoreThan200kmh = 0
            
            for cpLocation in iNaturalistData:
                if cpLocation["user_id"] == person:
                    personLabel = cpLocation["user_id"] + '-' + cpLocation["user_login"]
                    # filter out empty dates
                    # also filter out dates from before 1950 (found some on 1900/01/01 and, e.g., 1939/06/04)
                    if (cpLocation['observed_on'] != "") and (int(cpLocation['observed_on'].split('-')[0]) > 1950):
                        locationTag = ""
                        if (cpLocation['coordinates_obscured'] == "true"):
                            locationTag = "iN-o" + str(cpLocation['id'])
                            counterObservationsObscured += 1
                        else:
                            locationTag = "iN-p" + str(cpLocation['id'])
                            counterObservationsPrecise += 1
                        entry = []
                        entry.append(locationTag)
                        entry.append(cpLocation['latitude'])
                        entry.append(cpLocation['longitude'])
                        entry.append(cpLocation['observed_on'].replace('-','/'))
                        if (cpLocation['time_observed_at'] != ""):
                            entry.append(cpLocation['time_observed_at'].split(' ')[1])
                            counterObservationsWithTime += 1
                        else:
                            entry.append("00:00:00") # use midnight if we have no time
                            counterObservationsWithoutTime += 1
                        entry.append(cpLocation['coordinates_obscured'])
                        pictureListOfPersonWithDetails.append(entry)
                    else:
                        personMissedImages += 1

            pictureListOfPersonWithDetails.sort(key=lambda x: x[4])
            pictureListOfPersonWithDetails.sort(key=lambda x: x[3])
            prevDateTimeObj = datetime.datetime.strptime("1001-01-01 00:00:00", '%Y-%m-%d %H:%M:%S') # remember, year 0 did not exist
            prevDate = ""
            prevLatitude = 0.0
            prevLongitude = 0.0
            finalLatitude = 0.0
            finalLongitude = 0.0
            data = []
            dataTrace = {}
            dataEntryCounter = 0
            horizontalOffset = 0.0
            additionalHorizontalOffset = 0.0
            shapeList = []
            firstNonObscuredAlreadyPlaced = False
            numberOfObscuredObservations = 0
            obscuredObservationsTimeUnavailable = []
            markerSize = 8.0
            print(personLabel + ", active from " + pictureListOfPersonWithDetails[0][3] + " to " + pictureListOfPersonWithDetails[-1][3], end='')
            outfile.write(", active from " + pictureListOfPersonWithDetails[0][3] + " to " + pictureListOfPersonWithDetails[-1][3] + "\n")
            outfile.write('============================\n')
            for locationTag, latitude, longitude, date, time, coordinates_obscured in pictureListOfPersonWithDetails:
                dateTimeStr = date.replace("/", "-") + " " + time
                dateTimeObj = datetime.datetime.strptime(dateTimeStr, '%Y-%m-%d %H:%M:%S')
                elapsedSeconds = -1.0
                distance = -1.0
                speed = -1.0
                if (prevDate != date): # we start a new day
                    # before starting the new line for the new day, place all potentially unplaced markers
                    if (numberOfObscuredObservations > 0):
                        distance = great_circle((finalLatitude, finalLongitude), (prevLatitude, prevLongitude)).meters
                        additionalHorizontalOffset = math.log(distance+1.0, 2) / float(numberOfObscuredObservations)
                        for i in range(0, numberOfObscuredObservations):
                            horizontalOffset += additionalHorizontalOffset
                            # place the obscured marker
                            mySymbol="rect"
                            if obscuredObservationsTimeUnavailable[i]: mySymbol="circle"
                            shapeList.append(
                                go.layout.Shape(
                                    type=mySymbol,
                                    xsizemode='pixel',
                                    ysizemode='pixel',
                                    xanchor=prevDate.replace('/', '-'), # need prevDate here!!!
                                    yanchor=dataEntryCounter,
                                    x0=markerSize*0.5+horizontalOffset,
                                    y0=markerSize*(-0.5),
                                    x1=markerSize*1.5+horizontalOffset,
                                    y1=markerSize*0.5,
                                    line=dict(
                                        color='DarkGrey',
                                        width=1.0,
                                    ),
                                    fillcolor='rgb(255,255,255)',
                                )
                            )
                            horizontalOffset += markerSize

                    # we start a new line, the first element is the first image posted for a day
                    # placed traditionally in data space and using a normal data trace
                    dataEntryCounter += 1
                    horizontalOffset = 0.0
                    data.append(dataTrace)
                    dataTrace = {}
                    firstNonObscuredAlreadyPlaced = False
                    numberOfObscuredObservations = 0
                    obscuredObservationsTimeUnavailable = []
                    dataTrace['type'] = 'scatter'
                    dataTrace['x'] = [date.replace('/', '-')]
                    dataTrace['y'] = [dataEntryCounter]
                    dataTrace['mode'] = 'markers'
                    mySymbol="square"
                    if time == "00:00:00": mySymbol="circle"
                    if coordinates_obscured == "true":
                        dataTrace['marker'] = dict( color='rgb(255,255,255)', symbol=mySymbol, size=markerSize, line=dict(width=1, color='rgb(0,0,0)') ) # the first obscured is white with outline
                    else:
                        dataTrace['marker'] = dict( color='rgb(128,128,128)', symbol=mySymbol, size=markerSize ) # the first non-obscured is gray
                        firstNonObscuredAlreadyPlaced = True
                        counterObservationsClassFirst += 1
                    data.append(dataTrace)

                    # save y previous data to be able to compute speeds
                    # (we do this also for the imprecise points since we need a starting point)
                    prevLatitude = latitude
                    prevLongitude = longitude
                    outfile.write(locationTag + ", " + str(latitude) + ", " + str(longitude) + ", " + date + ", " + time + ", first entry of the day\n")
                    prevDateTimeObj = dateTimeObj
                else: # this is still the old day
                    if (coordinates_obscured == "false"): # we have a true data point
                        # we append an element to an existing line by placing shapes that we anchor in data space
                        # but that we layout in pixel space; each box is 5 by 5 pixels large
                        elapsedSeconds = (dateTimeObj - prevDateTimeObj).total_seconds()
                        distance = great_circle((latitude, longitude), (prevLatitude, prevLongitude)).meters
                        if (elapsedSeconds > 0.0): speed = distance * 3.6 / float(elapsedSeconds)
                        additionalHorizontalOffset = math.log(distance+1.0, 2)

                        if (not firstNonObscuredAlreadyPlaced): # if we are the first unobscured marker in a day, use gray
                            firstNonObscuredAlreadyPlaced = True
                            fillcolorBySpeed = 'rgb(128,128,128)'
                            counterObservationsClassFirst += 1
                        else:
                            if (speed > 200.0):
                                fillcolorBySpeed = myColorMap[6] # flying, totally wrong, purple
                                counterObservationsClassMoreThan200kmh += 1
                            else:
                                if (speed > 80.0):
                                    fillcolorBySpeed = myColorMap[5] # fastest driving, totally wrong, red
                                    counterObservationsClass80to200kmh += 1
                                else:
                                    if (speed > 25.0):
                                        fillcolorBySpeed = myColorMap[4] # fast driving, unbelievable, orange
                                        counterObservationsClass25to80kmh += 1
                                    else:
                                        if (speed > 10.0):
                                            fillcolorBySpeed = myColorMap[3] # no more nunning, must be driving, yellow
                                            counterObservationsClass10to25kmh += 1
                                        else:
                                            if (speed > 5.0):
                                                fillcolorBySpeed = myColorMap[2] # fast walking, light green
                                                counterObservationsClass5to10kmh += 1
                                            else:
                                                if (speed > 0.0):
                                                    fillcolorBySpeed = myColorMap[1] # walking, green
                                                    counterObservationsClass0to5kmh += 1
                                                else:
                                                    if elapsedSeconds == 0.0:
                                                        fillcolorBySpeed = myColorMap[7] # no time has passed, black
                                                        counterObservationsClassInstantaneous += 1
                                                    else:
                                                        fillcolorBySpeed = myColorMap[0] # not moving, blue
                                                        counterObservationsClass0kmh += 1

                        # we divide the calculated additionalHorizontalOffset by the number of markers we have to place
                        additionalHorizontalOffset = additionalHorizontalOffset / (float(numberOfObscuredObservations) + 1.0)

                        for i in range(0, numberOfObscuredObservations):
                            horizontalOffset += additionalHorizontalOffset
                            # place the obscured marker
                            mySymbol="rect"
                            if obscuredObservationsTimeUnavailable[i]: mySymbol="circle"
                            shapeList.append(
                                go.layout.Shape(
                                    type=mySymbol,
                                    xsizemode='pixel',
                                    ysizemode='pixel',
                                    xanchor=date.replace('/', '-'),
                                    yanchor=dataEntryCounter,
                                    x0=markerSize*0.5+horizontalOffset,
                                    y0=markerSize*(-0.5),
                                    x1=markerSize*1.5+horizontalOffset,
                                    y1=markerSize*0.5,
                                    line=dict(
                                        color='DarkGrey',
                                        width=1.0,
                                    ),
                                    fillcolor='rgb(255,255,255)',
                                )
                            )
                            horizontalOffset += markerSize
                        
                        # the final step for the actual marker                    
                        mySymbol="rect"
                        if time == "00:00:00": mySymbol="circle"
                        horizontalOffset += additionalHorizontalOffset
                        # place the true marker
                        shapeList.append(
                            go.layout.Shape(
                                type=mySymbol,
                                xsizemode='pixel',
                                ysizemode='pixel',
                                xanchor=date.replace('/', '-'),
                                yanchor=dataEntryCounter,
                                x0=markerSize*0.5+horizontalOffset,
                                y0=markerSize*(-0.5),
                                x1=markerSize*1.5+horizontalOffset,
                                y1=markerSize*0.5,
                                line=dict(
                                    color=fillcolorBySpeed,
                                    width=0.0,
                                ),
                                fillcolor=fillcolorBySpeed,
                            )
                        )
                        horizontalOffset += markerSize

                        # save y previous data to be able to compute speeds (later only for non-obscured observations)
                        prevLatitude = latitude
                        prevLongitude = longitude
                        prevDateTimeObj = dateTimeObj
                        outfile.write(locationTag + ", " + str(latitude) + ", " + str(longitude) + ", " + date + ", " + time + ", " + str(elapsedSeconds) + "s, " + str(round(distance, 1)) + "m, " + str(round(speed, 1)) + "km/h\n")
                        # we placed a real marker, so the obscured marker count is again 0
                        numberOfObscuredObservations = 0
                        obscuredObservationsTimeUnavailable = []

                    else: # the data point is obscured, so just store the number of obscured points
                        numberOfObscuredObservations += 1
                        if time == "00:00:00": obscuredObservationsTimeUnavailable.append(True)
                        else: obscuredObservationsTimeUnavailable.append(False)
                        outfile.write(locationTag + ", " + str(latitude) + ", " + str(longitude) + ", " + date + ", " + time + ", obscured\n")
                        # store the data of the observation (to be used when finishing a day lines)
                        finalLatitude = latitude
                        finalLongitude = longitude
    
                prevDate = date

            # place all remaining potentially unplaced markers from the last day
            if (numberOfObscuredObservations > 0):
                distance = great_circle((finalLatitude, finalLongitude), (prevLatitude, prevLongitude)).meters
                additionalHorizontalOffset = math.log(distance+1.0, 2) / float(numberOfObscuredObservations)
                for i in range(0, numberOfObscuredObservations):
                    horizontalOffset += additionalHorizontalOffset
                    # place the obscured marker
                    mySymbol="rect"
                    if obscuredObservationsTimeUnavailable[i]: mySymbol="circle"
                    shapeList.append(
                        go.layout.Shape(
                            type=mySymbol,
                            xsizemode='pixel',
                            ysizemode='pixel',
                            xanchor=prevDate.replace('/', '-'), # need prevDate here!!!
                            yanchor=dataEntryCounter,
                            x0=markerSize*0.5+horizontalOffset,
                            y0=markerSize*(-0.5),
                            x1=markerSize*1.5+horizontalOffset,
                            y1=markerSize*0.5,
                            line=dict(
                                color='DarkGrey',
                                width=1.0,
                            ),
                            fillcolor='rgb(255,255,255)',
                        )
                    )
                    horizontalOffset += markerSize

            print(", on " + str(dataEntryCounter) + " days, with " + str(len(pictureListOfPersonWithDetails)) + " observ., " + str(personMissedImages) + " observ. rejected (no date).")
            outfile.write("\n")
            data.append(dataTrace) # add the last trace

            yearOfFirstPicture = int(pictureListOfPersonWithDetails[0][3].split('/')[0])
            yearOfLastPicture = int(pictureListOfPersonWithDetails[-1][3].split('/')[0])
            numberOfYears = yearOfLastPicture - yearOfFirstPicture + 1
            myNumberOfTicks = 7
            myTickFormat = '%Y'
            if (numberOfYears <= 7): numberOfTicks = numberOfYears
            if (numberOfYears == 1): 
                numberOfTicks = 6
                myTickFormat = '%m/%Y'
            
            # adjust left border based on # of days
            leftMarginOffset = 0
            if dataEntryCounter > 95: leftMarginOffset = 20

            # regular layout for the visualization, more square
            layout = go.Layout( # main layout
                width = 1200,
                height = 1200,
                margin = dict(l=50 + leftMarginOffset, r=10, b=40, t=10, pad=4),
                font = dict(size=35),
                # yaxis = dict(range=(0, dataEntryCounter + 1.5), constrain='domain'),
                # xaxis = dict(tickangle=0, tickformat = myTickFormat, nticks=myNumberOfTicks),
                showlegend=False,
				paper_bgcolor='rgba(0,0,0,0)',
				plot_bgcolor='rgba(0,0,0,0)',
				xaxis=dict(
					tickangle=0, tickformat = myTickFormat, nticks=myNumberOfTicks,
					# zeroline=True,
					# zerolinewidth=1,
					# zerolinecolor='#2a3f5f',
					gridwidth=0.5,
					gridcolor='rgb(230,230,230)',
				),
				yaxis=dict(
					range=(0, dataEntryCounter + 1.5), constrain='domain',
					zeroline=True,
					zerolinewidth=1,
					zerolinecolor='#2a3f5f',
					gridwidth=0.5,
					gridcolor='rgb(230,230,230)',
				),
            )
            layout['shapes'] = shapeList

            fig = go.Figure(data=data, layout=layout)
            pio.write_image(fig, 'vis' + os.sep + '0_people-moves-iNaturalist_' + str(rankCounter).zfill(2) + "_" + personLabel.replace('@', '_') + '.pdf')

            if createPersonVisualizationExcerptsWide:
                # wide layout for the visualization, make it take less vertical space
                layout = go.Layout( # main layout
                    width = 1600,
                    height = 1200,
                    margin = dict(l=58 + leftMarginOffset, r=10, b=45, t=10, pad=4),
                    font = dict(size=40),
                    # yaxis = dict(range=(0, dataEntryCounter + 1.5), constrain='domain'),
                    # xaxis = dict(tickangle=0, tickformat = myTickFormat, nticks=myNumberOfTicks),
                    showlegend=False,
                    paper_bgcolor='rgba(0,0,0,0)',
                    plot_bgcolor='rgba(0,0,0,0)',
                    xaxis=dict(
                        tickangle=0, tickformat = myTickFormat, nticks=myNumberOfTicks,
                        # zeroline=True,
                        # zerolinewidth=1,
                        # zerolinecolor='#2a3f5f',
                        gridwidth=0.5,
                        gridcolor='rgb(230,230,230)',
                    ),
                    yaxis=dict(
                        range=(0, dataEntryCounter + 1.5), constrain='domain',
                        zeroline=True,
                        zerolinewidth=1,
                        zerolinecolor='#2a3f5f',
                        gridwidth=0.5,
                        gridcolor='rgb(230,230,230)',
                    ),
                )
                layout['shapes'] = shapeList

                fig = go.Figure(data=data, layout=layout)
                pio.write_image(fig, 'vis' + os.sep + '0_people-moves-iNaturalist_' + str(rankCounter).zfill(2) + "_" + personLabel.replace('@', '_') + '-wide.pdf')

            if createPersonVisualizationExcerptsHistograms:
                sumOfEntries = counterObservationsPrecise + counterObservationsObscured

                # histogram of reported data points
                print("Histogram:")
                print("sum:", str(counterObservationsPrecise + counterObservationsObscured), end = '')
                print(" precise:", str(counterObservationsPrecise), end = '')
                print(" obscured:", str(counterObservationsObscured))
                print("sum:", str(counterObservationsWithTime + counterObservationsWithoutTime), end = '')
                print(" w/ time:", str(counterObservationsWithTime), end = '')
                print(" w/o time:", str(counterObservationsWithoutTime))
                print("sum:", str(counterObservationsClassFirst + counterObservationsClassInstantaneous + counterObservationsClass0kmh + counterObservationsClass0to5kmh + counterObservationsClass5to10kmh + counterObservationsClass10to25kmh + counterObservationsClass25to80kmh + counterObservationsClass80to200kmh + counterObservationsClassMoreThan200kmh), end = '')
                print(" first:", str(counterObservationsClassFirst), end = '')
                print(" blue:", str(counterObservationsClassInstantaneous), end = '')
                print(" 0:", str(counterObservationsClass0kmh), end = '')
                print(" 0--5:", str(counterObservationsClass0to5kmh), end = '')
                print(" 5--10:", str(counterObservationsClass5to10kmh), end = '')
                print(" 10--25:", str(counterObservationsClass10to25kmh), end = '')
                print(" 25--80:", str(counterObservationsClass25to80kmh), end = '')
                print(" 80--200:", str(counterObservationsClass80to200kmh), end = '')
                print(" >200:", str(counterObservationsClassMoreThan200kmh))

                dataValues = [counterObservationsPrecise, counterObservationsObscured, 0,
                    counterObservationsWithTime, counterObservationsWithoutTime, 0,
                    counterObservationsClassFirst, counterObservationsClassInstantaneous, counterObservationsClass0kmh,
                    counterObservationsClass0to5kmh, counterObservationsClass5to10kmh, counterObservationsClass10to25kmh, counterObservationsClass25to80kmh, counterObservationsClass80to200kmh, counterObservationsClassMoreThan200kmh]
                barColors = ['rgb(100,100,100)',] * 15
                barColors[6] = 'rgb(128,128,128)' # gray
                barColors[7] =  myColorMap[7]     # black
                barColors[8] =  myColorMap[0]     # blue
                barColors[9] =  myColorMap[1]     # green
                barColors[10] = myColorMap[2]     # light green
                barColors[11] = myColorMap[3]     # yellow
                barColors[12] = myColorMap[4]     # orange
                barColors[13] = myColorMap[5]     # red
                barColors[14] = myColorMap[6]     # purple
                data=[
                    go.Bar(
                        y = dataValues,
                        orientation = 'v',
                        marker_color=barColors,
						marker = dict( line=dict(width=0) )
                    ),
                ]
                # find good y-labels, depending on the number of entries, and start with 0
                myTickvals = []
                myTickUnit = 10.0
                if sumOfEntries > 80: myTickUnit = 20.0
                if sumOfEntries > 100: myTickUnit = 25.0
                if sumOfEntries > 200: myTickUnit = 50.0
                if sumOfEntries > 400: myTickUnit = 100.0
                for i in range(0, math.ceil((sumOfEntries)/myTickUnit)):
                    myTickvals.append(i * myTickUnit)
                histogramWidth = 1000
                histogramHeight = 700
                layout = go.Layout(
                    width = histogramWidth,
                    height = histogramHeight,
                    xaxis=dict(showticklabels=False),
                    margin = dict(l=50, r=10, b=80, t=0, pad=4),
                    font = dict(size=20.0),
                    # yaxis = dict(tickvals = myTickvals),
					paper_bgcolor='rgba(0,0,0,0)',
					plot_bgcolor='rgba(0,0,0,0)',
					# xaxis=dict(
					# 	zeroline=True,
					# 	zerolinewidth=1,
					# 	zerolinecolor='#2a3f5f',
					# 	gridwidth=0.5,
					# 	gridcolor='rgb(230,230,230)',
					# ),
					yaxis=dict(
						zeroline=True,
						zerolinewidth=1,
						zerolinecolor='#2a3f5f',
						gridwidth=0.5,
						gridcolor='rgb(230,230,230)',
						tickvals = myTickvals,
					),
                )
                # overall marker size
                markerRadius = 10
                # apply the marker size via array, exclude the emty bars
                shapeSizes = [markerRadius,] * 15
                shapeSizes[0] = 0
                shapeSizes[1] = 0
                shapeSizes[2] = 0
                shapeSizes[3] = 0
                shapeSizes[4] = 0
                shapeSizes[5] = 0
                shapeSizes[6] = 0
                # apply the marker size via array, exclude the emty bars
                shapeTypes = ["rect",] * 15
                shapeTypes[4] = "circle"
                # fill color via array from above, with exceptions
                fillColors = barColors.copy()
                fillColors[0] = 'rgb(0,0,0)'
                fillColors[1] = 'rgb(255,255,255)'
                fillColors[3] = 'rgb(0,0,0)'
                fillColors[4] = 'rgb(0,0,0)'
                # line color via array from above, with exceptions
                lineColors = fillColors.copy()
                lineColors[1] = 'rgb(0,0,0)'
                # line widths via array
                lineWidths = [0,] * 15
                lineWidths[1] = 1

                shapes = []
                # for 0--1, 6: precise, we need both the circle and the square versions, filled for 0 and outlined for 1
                for i in [0, 1, 6]:
                    shapes.append(dict(
                        xref='x', yref='y', x0 = -markerRadius * 2.3, y0 = -3 * markerRadius, x1 = -markerRadius * 0.3, y1 = -1 * markerRadius, xanchor = i, yanchor = 0, xsizemode = "pixel", ysizemode = "pixel",
                        type = shapeTypes[i], line = dict(color = lineColors[i], width=lineWidths[i]), fillcolor = fillColors[i],
                    ))
                    shapes.append(dict(
                        xref='x', yref='y', x0 = markerRadius * 0.3, y0 = -3 * markerRadius, x1 = markerRadius * 2.3, y1 = -1 * markerRadius, xanchor = i, yanchor = 0, xsizemode = "pixel", ysizemode = "pixel",
                        type = "circle", line = dict(color = lineColors[i], width=lineWidths[i]), fillcolor = fillColors[i],
                    ))
                # for 3--4: precise, we need both the circle and the square versions, filled for 0 and outlined for 1
                for i in [3, 4]:
                    shapes.append(dict(
                        xref='x', yref='y', x0 = -markerRadius * 2.3, y0 = -3 * markerRadius, x1 = -markerRadius * 0.3, y1 = -1 * markerRadius, xanchor = i, yanchor = 0, xsizemode = "pixel", ysizemode = "pixel",
                        type = shapeTypes[i], line = dict(color = lineColors[i], width=lineWidths[i]), fillcolor = fillColors[i],
                    ))
                    shapes.append(dict(
                        xref='x', yref='y', x0 = markerRadius * 0.3, y0 = -3 * markerRadius, x1 = markerRadius * 2.3, y1 = -1 * markerRadius, xanchor = i, yanchor = 0, xsizemode = "pixel", ysizemode = "pixel",
                        type = shapeTypes[i], line = dict(color = lineColors[1], width=lineWidths[1]), fillcolor = fillColors[1],
                    ))
                for i in range(0, 15):
                    if shapeSizes[i] > 0:
                        shapes.append(dict(
                            xref='x', yref='y', x0 = -shapeSizes[i], y0 = -3 * shapeSizes[i], x1 = shapeSizes[i], y1 = -1 * shapeSizes[i], xanchor = i, yanchor = 0, xsizemode = "pixel", ysizemode = "pixel",
                            type = shapeTypes[i], line = dict(color = lineColors[i], width=lineWidths[i]), fillcolor = fillColors[i],
                        ))
                layout['shapes'] = shapes

                annotations = []
                annotations.append(dict(
                    xref='x', yref='paper', y = 1.0 / float(histogramHeight) * -8.0 * markerRadius, x = 0.5, xanchor = 'center', yanchor = 'bottom',
                    text = "precise/<br>obscured",
                    font = dict(color='#2a3f5f', size=20.0),
                    showarrow=False,
                    # orientation = 'v',
                ))
                annotations.append(dict(
                    xref='x', yref='paper', y = 1.0 / float(histogramHeight) * -8.0 * markerRadius, x = 3.5, xanchor = 'center', yanchor = 'bottom',
                    text = "with/without<br>time stamp",
                    font = dict(color='#2a3f5f', size=20.0),
                    showarrow=False,
                ))
                annotations.append(dict(
                    xref='x', yref='paper', y = 1.0 / float(histogramHeight) * -8.0 * markerRadius, x = 10, xanchor = 'center', yanchor = 'bottom',
                    text = "apparent speed classes or first observation of<br>the day (gray) or identical time stamp (black)",
                    font = dict(color='#2a3f5f', size=20.0),
                    showarrow=False,
                ))
                layout['annotations'] = annotations

                fig = go.Figure(data=data, layout=layout)
                # fig.update_xaxes(showticklabels=False)
                pio.write_image(fig, 'vis' + os.sep + '0_people-moves-iNaturalist_' + str(rankCounter).zfill(2) + "_" + personLabel.replace('@', '_') + '-histogram.pdf')

    outfile.close()

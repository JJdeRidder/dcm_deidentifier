import os
import pydicom
import uuid
import csv
import re
import shutil



def hexifier(tag_str):
    '''function to convert "(0001,0002)" to (0x1,0x2)'''
    no_braces = tag_str[1:-1]
    hex_str1, hex_str2 = tuple(no_braces.split(","))
    hex1 = hex(int(hex_str1, 16))
    hex2 = hex(int(hex_str2, 16))
    return hex1, hex2

 # Setup a dictionary where D needs to get a nonzero dummie value, Z needs to get a zero value, X can be deleted and U needs a new Unique Identifier
Tag_dict = {
    'D_list': [],
    'Z_list': [],
    'X_list': [],
    'U_list': [],
}

# Creating a dict with all tags according to the NEMA Standard (http://dicom.nema.org/dicom/2013/output/chtml/part15/chapter_E.html
# DICOMstandard.csv is the same as Appendix 2. 

with open("DICOMstandard.csv", "r") as csvf:
    reader = csv.reader(csvf)
    for row in reader:
        if row[2][-1] == "D":
            TagHex = hexifier(row[1])
            Tag_dict["D_list"].append(TagHex)
        elif row[2][-1] == "Z":
            TagHex = hexifier(row[1])
            Tag_dict["Z_list"].append(TagHex)
        elif row[2][-1] == "X":
            TagHex = hexifier(row[1])
            Tag_dict["X_list"].append(TagHex)
        elif row[2][-1] == "U":
            TagHex = hexifier(row[1])
            Tag_dict["U_list"].append(TagHex)


# deidentification:

# create a set of dummies for each value representation
VR_dummies = {
    "AS": "150Y",
    "DA": "19010101",
    "DS": "999",
    "DT": "19990101010101.111111",
    "LO": "Long string dummy",
    "LT": "Long text dummy",
    "PN": "Anonymous",
    "SH": "Short string dummy",
    "ST": "Short text dummy",
    "TM": "010101.111111"
}

# initialize a list to keep track of used UID to keep internal consistency
known_UIDS = {}


def deidentifier(src_path, newptID):
    ds = pydicom.dcmread(src_path) ## defer_size could improve performance
    ds.remove_private_tags()  # this will get rid of all private tags, this will cause some loss of information (aka, mevisLab comments orso) but this is inevitable for good de-identification
    
    if (0x40, 0x275) in ds:
        del ds[(0x40, 0x275)]  # ugly way to get arround key error of (0x40,0x275)

    for row in ds.iterall():
    	# if tag of data_element is in X_list it will be deleted
        if row.tag in Tag_dict["X_list"]:
            delattr(ds, row.keyword)
            
        # if tag of data_elem is in Z_list it shall be set to an empty string
        elif row.tag in Tag_dict["Z_list"]:
            row.value = ""

        # if tag in in D_list it shall be set to a dummy value
        elif row.tag in Tag_dict["D_list"]:
        	# sequences needed some extra touch, since they need to be changed to an empty sequence
            if row.VR == "SQ":
                row.value = pydicom.Sequence([pydicom.Dataset()])  # Might cause issues at some point

            # gets the dummie values from VR_dummies by VR
            else:
                row.value = VR_dummies[row.VR]  # oneline wonders

        # if tag of data_elem is in U_list a new UID needs to be created, keeping the internal consistency
        elif row.tag in Tag_dict["U_list"]:
            if row.value not in known_UIDS.keys():
                new_UID = "2.25." + str(uuid.uuid4().int).lstrip("0")  # or use pydicom.uid.generate(prefix = None)
                '''
				In accordance with the NEMA standard of creating UID by using Universeally Unique Identifier (UUID)
				http://dicom.nema.org/medical/dicom/current/output/chtml/part05/sect_B.2.html
				'''
                known_UIDS[row.value] = new_UID
                row.value = new_UID

            else:
                new_UID = known_UIDS[row.value]
                row.value = new_UID
                
    # two hardcoded group removals for the 50xx (Curve Data) and (60xx,3000)[Overlay Data] and (60xx,4000)[Overlay Comments] groups of the nema standards:
            group = row.tag.group
            if group >= 0x5000 and group < 0x5100:
                delattr(ds, row.keyword)
            if group >= 0x6000 and group < 0x6100 and (row.tag.element == 0x3000 or row.tag.element == 0x4000):
                delattr(ds, row.keyword)
    # sets PatientID and PatientName to a newptID given when calling this function
    ds.PatientID = newptID
    ds.PatientName = newptID
    # removes all dates mentioned in the seriesDescription in the fromat of "digitdigit nonwhitespacecharacter digitdigit nonwhitespacecharacter digitdigitdigitdigit"
    if  (0x008,0x103E) in ds:
        ds.SeriesDescription = re.sub(r"\d{2}\S\d{2}\S\d{4}", "", ds.SeriesDescription)
    
    
    return ds
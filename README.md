# dcm_deidentifier
Basic concept for deidentifying DICOM files using Python and pydicom.


I am not a seasoned python expert, but I figured that my work could come in useful for someone else.

I made the python script originally to anonymize a lot of CT DICOM scans automatically, but what's on this github is only the piece of code that deidentifies 1 pydicom dataset (one DICOM instance). Handling the files themselves depends a lot on the directory structure of your data, so I decided not to upload that part here.

The NEMA DICOM Standard chapter E (http://dicom.nema.org/dicom/2013/output/chtml/part15/chapter_E.html) provides a a thorough guide on de-identification of DICOM files. Care is taken to comply with this standard as much as possible. The only two tags from the list of NEMA that are not editted are SeriesDescription and ImageComments. 

Please let me know if you have any feedback so I could improve the script. 


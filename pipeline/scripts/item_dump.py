"""

This script is used to dump the scrapped data into the database and the object storage.
We take in the data from the scraper as a single jsonl file and then process each line
of the  (JSON) and dump it into the object storage and the database.

The sync between the database and the object storage is done via an UUID that is
assigned to each song (JSON) during the dumping process. This UUID is common to
both the database and the object storage and used to link the two.

Input:
    - A JSONL file containing all the songs (JSON)

Output:
    - A series of JSON files containing the songs (JSON) with the original fields
      uploaded to the object storage and a copy of the same inserted into the database

"""

"""

This script is used to vectorize the song (JSON) title, lyrics, metadata citations.
This is done for each of the songs (JSON) for each of the original, transliterated,
and translated copies. The vectorized data is uploaded to the object storage.


We scan across all the songs in the database and then for each song we get the
original, transliterated, and translated copies from the object storage.

We then vectorize the title, lyrics, and metadata citations of the songs from the
original, transliterated, and translated copies and upload the vectorized data in
the object storage.


Input:
    - A series of JSON files containing the songs (JSON) with the fields

Output:
    - A series of JSON files containing the songs (JSON) with the vectorized fields
      uploaded to the object storage

"""
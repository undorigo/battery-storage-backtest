"""Transport only: parameters in, tidy frame out.

Nothing outside this package may import a source module.  The rest of the project
goes through `src.data`, which owns caching and the Contract 5 normalisation, and
therefore never knows whether the bytes came from ENTSO-E or from SMARD.  That is
what makes swapping a source a one-line change instead of an edit to every caller.
"""

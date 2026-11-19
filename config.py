# Every room matching ALL of these is watched. Set one to None to ignore it.

# Building address. Matches whole words from the start, so "Moholt allmenning"
# covers 2, 5, 7, 8 and 11, while "Moholt allmenning 5" is only that building.
BUILDING_ADDRESS = "Moholt allmenning"

# SiT housing type code:
#   "HybelKB" = dorm with own bathroom in a collective
#   "HybelK"  = dorm with shared bathroom in a collective
#   "2rompar" = 1-bedroom apartment in a collective
#   "1-roms", "2-roms", "3-roms", ... = apartments
HOUSING_TYPE = "HybelKB"

# Number of people sharing the kitchen (including you).
SHARING_KITCHEN = 15

# Exact rooms to watch on top of the search above, e.g. ["MAL5-501"].
EXTRA_UNIT_IDS = []

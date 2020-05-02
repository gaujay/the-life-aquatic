import sys
import pstats
import os.path

# Constants
profileResFile = 'profile_res.txt'
profileScriptFile = 'profile_main.bat'


# Check profile result file exists
if not os.path.exists(profileResFile):
    print('Unable to find profile result file:', profileResFile)
    print('Please run profiling script first:', profileScriptFile)
    sys.exit(1)

# Parse results
p = pstats.Stats(profileResFile)

# Print 20 most time-consuming functions
p.sort_stats(pstats.SortKey.TIME).print_stats(20)

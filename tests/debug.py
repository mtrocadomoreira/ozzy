import ozzy as oz

path = "/Volumes/Mariana/Simulations/LCODE/gap_position_scan"
runs = "from_*/10m_noramp"
# path = "~/cernbox/Simulations/LCODE/gap_position_scan/from_002400/10m_noramp"

table = oz.open_compare("lcode", path=path, runs=runs, quants="xi_")

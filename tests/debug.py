import ozzy_refactor as oz

data = oz.open_compare(
    "lcode", path="/Volumes/Mariana/Simulations/LCODE", runs="*gap*", quants="tb"
)

print(data)

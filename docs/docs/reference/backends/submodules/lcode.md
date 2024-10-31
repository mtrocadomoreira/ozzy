# LCODE backend

## Available file types

At the moment, the following LCODE 2D file types can be read by ozzy:

- [x] plasma density profile along propagation (`plzshape.dat`)
- [x] particle information at a single timestep (`tb?????.swp`,`beamfile.bin`)
- [x] local/absolute extrema of on-axis longitudinal field or on-axis potential (`emaxf.dat`, `gmaxf.dat`, `elocf.dat`, `glocf.dat`)
- [x] grid density data
- [x] lineouts along longitudinal coordinate (`xi_*.swp`)
- [ ] particle data for selected particles (`partic.swp`) 
- [ ] lost particle data (`beamlost.dat`)
- [ ] key between exact times of diagnostic outputs and their 5-digit representations (`times.dat`)
- [ ] trapped particle data (`captured.pls`)
- [ ] plasma particle data (`pl?????.swp`, `plasma.bin`)
- [ ] full grid information for fields and currents (`fl?????.swp`, `fields.bin`)

- [ ] histogram of particle data
- [ ] plasma particle data (`?????.pls`, `s?????.pls`)
- [ ] substepped lineouts along longitudinal coordinate (`u?????.det`, `v?????.det`)
- [ ] real and imaginary components of laser envelope (`ls??????.???.swp`)

## Default metadata

The variable metadata, such as the mathematical symbol and units, is inferred from the file name and file type. Since this translation is mostly hard-coded, some quantities have not yet been included and will therefore not be displayed as properly formatted metadata.

The default metadata for each foreseen quantity can be inspected with:
```python
import ozzy as oz
for k, v in oz.backends.lcode_backend.quant_info.items():
    print(k)
    for k1, v1 in v.items():
        print(f' {k1}:')
        print(f'    label: {v1[0]}')
        print(f'    units: {v1[1]}')
```



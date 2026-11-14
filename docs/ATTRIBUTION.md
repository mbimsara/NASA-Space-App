# Data attribution and references

Checked against official NASA POWER documentation on 2026-11-14. This file records data credit; it does not assign a software license to the repository or assert NASA endorsement.

## NASA POWER

The [official referencing guide](https://power.larc.nasa.gov/docs/referencing/) asks users to include project credit and a data reference with the service name, version and date accessed. Use the actual response metadata, not a hardcoded access date.

Suggested project credit, paraphrased: AgroSphere uses data from NASA Langley Research Center's Prediction Of Worldwide Energy Resources (POWER) project, supported by NASA's Earth Science Division.

Data-reference template: NASA POWER Daily API, version `{api.version}`, accessed `{retrieved_at UTC date}`; variables T2M and PRECTOTCORR; UTC daily interval; requested coordinates and dates; source `{sources}`; request `{source_url}`. Imported responses without a known access date should say that the original access date is unknown rather than invent one.

The [acknowledgement page](https://power.larc.nasa.gov/docs/acknowledgements/) credits the POWER collaborators and NASA Langley ASDC. For MERRA-2 context and spatial resolution, link the [meteorological source documentation](https://power.larc.nasa.gov/docs/methodology/data/sources_meteorology/). Retain these references in dashboard source details, exports, and the final presentation.

The [POWER website](https://power.larc.nasa.gov/) describes its datasets as free. This does not replace product-specific review when adding other competition resources, imagery, map tiles or models. The referencing guide also requests publication/redistribution notification; no email or external notification has been sent by this project task. The team can decide how to handle that request when publishing.

## Competition selection and synthetic data

NASA POWER is listed on the [challenge resources page](https://www.spaceappschallenge.org/2026/challenges/adapting-farms-with-nasa-data/?tab=resources). Current live examples request Sri Lankan points only. Keep the project owner's source/location restrictions in [the source register](DATA_SOURCES.md).

Synthetic fixtures are invented engineering examples, not NASA data. They require visible synthetic labels and must not be cited as environmental findings.

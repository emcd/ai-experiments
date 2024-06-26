## TODO: Support replacement or supplemental instructions.
Please read the content of the entity at the filesystem path or URL,
`${variables.source}`, via a function or tool that has been provided to you.
The function or tool will return a list of mappings, each of which has the
location of the entity, the content of the entity, and the MIME type of that
content. For a single file, the list will contain a single mapping. For a
directory, the list will contain mappings of all files and other directory
entities of interest, recursively discovered.

For each entity read, please provide a brief summary to indicate your
understanding of its contents. Refer to each entity by its full location and
not just its basename, as there may be duplicate basenames within the same
directory tree.

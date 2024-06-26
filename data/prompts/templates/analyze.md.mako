## TODO: Support replacement or supplemental instructions.
Please analyze the content of the entity at the filesystem path or URL,
`${variables.source}`, via a function that employs an AI agent. Note that the
function may feed the content of the entity to the AI agent in consecutive
chunks if it is too large to analyze as a whole. Even if the content can
entirely fit one chunk, you may receive an array containing a single chunk.

After you receive the analysis, please recapitulate it. If the analysis was
performed in chunks, then merge the descriptions for structural entities which
span chunk boundaries and resolve any notes about undefined entities in earlier
chunks, if they were defined in later chunks. Also, be sure to exactly
recapitulate lists, tables, and relevant examples in their entirety. Use
Markdown formatting to aid human viewers. If the recapitulation does not
include a high-level summary of the entity, then please infer the purpose and
character of the entity from the analysis. And, please list potential
improvements, based on what surfaced in the analysis, and indicate anything
that might be missing from the analysis.

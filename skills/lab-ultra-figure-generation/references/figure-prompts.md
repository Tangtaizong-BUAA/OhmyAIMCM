# Local figure repair checklist

Before execution, state the actual data source, the meaning of each field, panel type, units, explicit transformations, uncertainty definition, layout owner and final dimensions.

For a traceback, identify the failing operation and repair the smallest relevant code section. Missing data or an undefined statistical method is not a request to invent a substitute.

For visual review, compare the rendered result with the request and the source mapping. Check label text, scale endpoints, missing values, clipping, overlapping annotations, color semantics and legibility. A reference figure supplies visual ideas; it is not ground-truth experimental data.

Keep aesthetic comments separate from scientific failures. A model score may help compare valid variants but cannot establish correctness. Preserve the selected source revision and all input arrays while iterating.

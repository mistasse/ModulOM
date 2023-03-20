# ModulOM

Code around the supervision and decoding of networks in Deep Learning can quickly become a nightmare. The main cause is that interdependent maths are achieved through cascades of functions. As functions route data through their parameters, it is not rare for a modification in the flow of data to require refactoring through a whole cascade of functions. The final system is not only rigid, but only barely observable:

- Are there terms that were computed but not needed?
- Are there terms that were computed twice?
- What are the exact dependencies of each term?

In the [ModulOM paper](https://openreview.net/pdf?id=264iXDLnD59), we suggested that those issues could be solved by:

1. Regrouping parameters in favor of a single object containing the data
2. Regrouping those functions in classes, as methods
3. Composing classes through inheritance

The resulting class instance can become the systematic function parameter, and cache the results so as to avoid recomputations.

ModulOM therefore achieves the following properties:
- A term is only computed if it is needed, and only once: when it is needed,
- Easy access to any of the terms from within, but also outside of the ModulOM,
- Multiple inheritance allows for easy combination to explore of the possible systems.

**This repository just got started, please be patient if you are looking for something stable.**

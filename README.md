# python
a collection of helpful tools for python

## gplot.py - A python gnuplot interface

You can plot data from python via gnuplot with commands as simple as

```python
gplot([1, 4, 2, 3, 3.5], "w lp")
```

See [wiki/gplot.py](https://github.com/mzechmeister/python/wiki/gplot.py) for more details.

It works also with Jupyter ([gplot_demo.ipynb](https://github.com/mzechmeister/python/blob/master/gplot_demo.ipynb)).

### Installation of gplot.py

Create a folder and run there

```bash
wget https://raw.githubusercontent.com/mzechmeister/python/master/gplot.py
python -c "import setuptools; setuptools.setup(name='gplot')" develop --user
```

Additionally, you might be interested in the file [zoom.gnu](https://github.com/mzechmeister/python/blob/master/zoom.gnu), which offers additional shortcuts for zooming and panning.
If so, download, e.g. to the same directory
```bash
wget https://raw.githubusercontent.com/mzechmeister/python/master/zoom.gnu
```
and include the following line in your `~/.gnuplot`:
```
load "<path>/zoom.gnu"
```

## ds9.py - A python ds9 interface

Here is an example, how to use `ds9` from python
```python
from ds9 import *
ds9([[1,2],[3,4]])
ds9.cmap('bb')
ds9.zoom_to(16)
```

### Installation of ds9.py

```bash
wget https://raw.githubusercontent.com/mzechmeister/python/master/ds9.py
```

Moreover, `numpy` and `astropy` are required and `xpa` must be available for the corresponding architecture (can be downloaded from https://sites.google.com/cfa.harvard.edu/saoimageds9/download).


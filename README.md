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

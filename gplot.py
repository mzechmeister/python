# A python-gnuplot interface

from __future__ import print_function
import subprocess
from numpy import savetxt
import tempfile
import os

__author__ = 'Mathias Zechmeister'
__version__ = 'v09'
__date__ = '2018-05-08'
__all__ = ['gplot', 'Gplot', 'ogplot', 'Iplot']

#path = os.path.dirname(__file__)

class Gplot(object):
   """An interface between Python and gnuplot.
   
   Parameters
   ----------
   args : array or str for function, file, or other plot commands like style
   tmp : str, optional
       None - create a non-persistent temporary file (default)
       '' - create a local persistent file
       '-' - use gnuplot special filename (no interactive zoom available,
             replot does not work)
       '$' - use inline datablock (not faster than temporary data,
             does not work with flush='' an ogplot)
       'filename' - create manually a temporary file
   flush : str, optional
       set to '' to suppress flush until next the ogplot (for large data sets)
   stdout : boolean, optional
       if true plot commands are send to stdout instead to gnuplot pipe

   pl : str, optional
       leading command (default: 'plot', can be changed to replot or splot)
   calling with a gnuplot set attribute return the same instance. This allows to chain calls.

   Examples
   --------
   >>> gplot('sin(x) w lp lt 3')
   >>> ogplot(numpy.arange(10)**2.,'w lp lt 3')
   >>> ogplot('"filename" w lp lt 3')
   >>> gplot('x/5, 1, x**2/50 w l lt 3,', numpy.sqrt(numpy.arange(10)),' us 0:1 ps 2 pt 7 ,sin(x)')
   >>> gplot.mxtics().mytics(2).repl
   >>> gplot([1,2,3,4])
   >>> gplot([1,2,3,4], [2,2,1,1.5])
   >>> gplot([1,2,3,4], [[2,2,1,1.5], [3,1,4,5.5]])
   >>> gplot([[2,2,1,1.5]])
   >>> gplot([1],[2],[3],[4])
   >>> gplot(1,2,3,4)
   >>> gplot([1,2,1,0.5])
   >>> gplot([[2,2,1,1.5]])
   
   """
   version = subprocess.check_output(['gnuplot', '-V'])
   version = float(version.split()[1]) 
   
   def __init__(self, stdout=False, tmp=None, mode='plot'):
      self.stdout = stdout
      self.tmp = tmp
      self.mode = getattr(self, mode) # set the default mode (plot, splot)
      self.gnuplot = subprocess.Popen(['gnuplot','-p'], shell=True, stdin=subprocess.PIPE,
                   universal_newlines=True, bufsize=0)  # This line is needed for python3! Unbuffered and to pass str instead of bytes
      self.pid = self.gnuplot.pid
      #if version in [4.6]: gp('set term wxt;') # Prefer wxt over qt. Still possible in 4.6
      #gp('load "%s"\n'%os.path.join(path,"zoom.gnu")) # preload
      self.og = 0  # overplot number
      self.buf = ''
      self.tmp2 = []
      self.flush = None
   
   def _plot(self, *args, **kwargs):
      # collect all argument
      tmp = kwargs.pop('tmp', self.tmp)
      flush = kwargs.pop('flush', '\n')
      if self.version in [4.6] and flush=="\n": flush = "\n\n" # append a newline to workaround a gnuplot pipe bug
      # with mouse zooming (see http://sourceforge.net/p/gnuplot/bugs/1203/)
      self.flush = flush
      pl = ''
      data = ()
      for arg in args+(flush,):
         if isinstance(arg, str):   # append argument, but flush the data before
            if data:
               # transpose data when writing
               data = zip(*data)
               self.og += 1
               tmpname = tmp
               if tmp in ('-',):
                  # use gnuplot's special filename '-'
                  self.buf += "\n".join(" ".join(map(str,tup)) for tup in data)+"\ne\n"
               elif tmp in ('$',):
                  # gnuplot's inline datablock
                  tmpname = "$data%s" % self.og
                  # prepend the datablock
                  pl = tmpname+" <<EOD\n"+("\n".join(" ".join(map(str,tup)) for tup in data))+"\nEOD\n" + pl
               elif tmp is None:
                  # create temporary file; default
                  self.tmp2.append(tempfile.NamedTemporaryFile())
                  tmpname = self.tmp2[-1].name
                  #savetxt(tmp2[-1], data) #zipped data not supported by python3
                  savetxt(self.tmp2[-1], list(data), fmt="%s") # zipped data not supported by python3, fmt="%s" to allow for strings
                  self.tmp2[-1].seek(0)
               else:
                  # create local temporary file
                  if tmp=='':
                     tmpname = 'gptmp_'+str(self.pid)+str(self.og)
                  savetxt(tmpname, data)
               pl += '"'+tmpname+'"'
            pl += ' ' + arg
            data = ()
         else:   
            # collect data; append columns and matricies
            _2D = hasattr(arg, '__iter__') and hasattr(arg[0], '__iter__')
            data += tuple(arg) if _2D else (arg,)
      self.put(pl if flush=='' else pl+self.buf, end='')
   
   def put(self, *args, **kwargs):
      # send the commands to gnuplot
      print(file=None if self.stdout else self.gnuplot.stdin, *args, **kwargs)
      return self
   # some plot commands (kwargs possible)
   def plot(self, *args, **kwargs):
      self.og = 0; self.buf = ''; self.put('\n')        # reset
      return self._plot('plot', *args, **kwargs)
   def splot(self, *args, **kwargs):
      self.og = 0; self.buf = ''; self.put('\n')        # reset
      return self._plot('splot', *args, **kwargs)
   def replot(self, *args, **kwargs):
      return self._plot('replot', *args, **kwargs)
   def test(self, *args, **kwargs):
      return self._plot('test', *args, **kwargs)
   def oplot(self, *args, **kwargs):
      pl = ',' if self.flush=='' else 'replot '
      return self._plot(pl, *args, **kwargs)
   
   def __call__(self, *args, **kwargs):
      # by default plot mode is executed, but the user can change that
      return self.mode(*args, **kwargs)
   
   def __getattr__(self, name):
      # generic translatation, e.g. gplot.title sends "set title"
      if name in ('__repr__', '__str__'):
         raise AttributeError 
      elif name=='repl':
         return self.replot()
      elif name in ['set', 'unset', 'reset', 'print', 'bind']:
         # some fixed keywords
         # print as attribute does not work in python 2
         def func(*args):
            return self.put(name, *args)
         return func
      else:   
         def func(*args):
            return self.set(name, *args)
         return func


class Iplot(Gplot):
   '''
   Jupyter
   Similar as Gplot, but plot returns an object that can be displayed rather than self
   '''
   def __init__(self, *args, **kwargs):
      '''
      Iplot(*arg, suffix='png', uri=True, cleanup=True, *kwargs)
      
      Parameters:
      -----------
      suffix : str, optional
          Support for svg, html, and png.
      uri : boolean, optional
          If true, the figure will inline.
      cleanup : boolean, optional
          If true, the temporary image file will be deleted.
          
      '''
      #, cleanup=True, uri=False
      self.suffix = kwargs.pop('imgfile', 'png')
      self.opt = kwargs.pop('opt', '')
      self.uri = kwargs.pop('uri', True)
      self.jsdir = kwargs.pop('jsdir', 'jsdir "gp/"') # 'jsdir "https://gnuplot.sourceforge.net/demo_svg_5.0/"'
      self.cleanup = kwargs.pop('cleanup', True)
      self.canvasnum = 0
      return super().__init__(*args, **kwargs)

   def _plot(self, *args, **kwargs):
      canvasname = "fishplot_%s" % self.canvasnum
      self.canvasnum += 1
      term = {'svg': 'svg mouse %s' % self.jsdir, # toggle does not work
              'svg5': 'svg mouse standalone', 
              'html': 'canvas name "%s" mousing %s' % (canvasname, self.jsdir)
             }.get(self.suffix, 'pngcairo') + ' ' + self.opt
      # png + no_uri, Image still converts into uri -> works
      # png + uri, Image still converts into uri ->  works
      # svg + local_svg, mousing work
      # svg + no_uri, as inline
      # svg + uri, as inline
      # html + no_uri
      imgfile = tempfile.NamedTemporaryFile(suffix='.'+self.suffix).name
      if not self.uri and self.suffix=='svg':
         imgfile='simple.1.svg' # c
      if self.suffix=='html':
         imgfile = canvasname + '.js' #gnuplot_canvas.js"
#         if self.uri:
            # cleanup is already exists
      os.system("rm -f "+imgfile)                                                                                                               
            
      if self.uri:
         os.mkfifo(imgfile)

      self.term(term).out('"%s"' % imgfile)
      super()._plot(*args, **kwargs)
      self.out()

      if not self.uri:
         import time
         counter = 0
         while counter<100 and not (os.path.exists(imgfile) and os.system("lsof "+imgfile)):
            time.sleep(0.003)
            counter += 1
            if not self.cleanup: print(counter, end='\r')   
         if not self.cleanup:                                                                                                                  
            print(counter, imgfile, os.path.exists(imgfile), os.system("lsof "+imgfile))
                                                                                                                                              
      from IPython.display import Image, SVG, HTML, Javascript, display_javascript
      showfunc = {'svg':SVG, 'html':HTML}.get(self.suffix, Image)
      imgdata = imgfile
      if self.suffix=='svg' and not self.uri:
         showfunc = HTML
         imgdata = '<embed src="%s" type="image/svg+xml">' % imgfile
      if self.uri:
         1
         #imgfile = 'data:image/png;base64,'+
         #imgdata = open(imgfile, "rb").read() # png needs rb, but imgfile can be also passed directly 
         #return imgdata   
         #imgdata.replace('<svg ','<script type="text/javascript" xmlns:xlink="http://www.w3.org/1999/xlink" xlink:href="./gp/gnuplot_svg.js"></script>\n<svg ')
         #import base64                                                                                                                             
         #print (base64.b64encode(imgdata).decode('ascii')[-10:])

      if self.suffix=='html':
         if self.uri and 0:
            imgdata = 555 #'<script>%s</script>' % open(imgfile).read()
            return display_javascript(imgfile)
         else:
            imgdata = '''<script src="%s"></script>''' % imgfile
            # set overflow in site from auto to none to enable mouse tracking
            imgdata = '''
         <link rel="stylesheet" href="%sgp/gnuplot_mouse.css" type="text/css">
         <script src="%scanvastext.js"></script>
         <script src="%sgnuplot_common.js"></script>
         <script src="%sgnuplot_mouse.js"></script>
<script type="text/javascript">
   document.getElementById("site").style.overflow = "visible";
   console.log(document.getElementById("site"))
</script>

<script type="text/javascript">
var canvas, ctx;
gnuplot.grid_lines = true;
gnuplot.zoomed = false;
gnuplot.active_plot_name = "gnuplot_canvas";
gnuplot.active_plot = gnuplot.dummyplot;
gnuplot.help_URL = "http://gnuplot.sourceforge.net/demo_canvas_5.0/canvas_help.html";
gnuplot.dummyplot = function() {};
function gnuplot_canvas( plot ) { gnuplot.active_plot(); };
</script>
         %s
<table class="noborder" style="margin-top:0; border:0;">
  <tr style="border:0;">
    <td style="border:0;">
    <table class="mbright" tabindex=0>
    <tr style="max-width:None">
      <td class="icon" onclick="gnuplot.toggle_grid();"><img src="grid.png" id="gnuplot_grid_icon" class="icon-image" alt="#" title="toggle grid"></td>
      <td class="icon" onclick="gnuplot.unzoom();"><img src="previouszoom.png" id="gnuplot_unzoom_icon" class="icon-image" alt="unzoom" title="unzoom"></td>
      <td class="icon" onclick="gnuplot.rezoom();"><img src="nextzoom.png" id="gnuplot_rezoom_icon" class="icon-image" alt="rezoom" title="rezoom"></td>
      <td class="icon" onclick="gnuplot.toggle_zoom_text();"><img src="textzoom.png" id="gnuplot_textzoom_icon" class="icon-image" alt="zoom text" title="zoom text with plot"></td>
      <td class="icon" onclick="gnuplot.popup_help();"><img src="help.png" id="gnuplot_help_icon" class="icon-image" alt="?" title="help"></td>
  <td class="icon"></td>
       <td class="mb0">x&nbsp;</td> <td class="mb1"><span id="%s_x">&nbsp;NaN&nbsp;</span></td>
      <td class="mb0">y&nbsp;</td> <td class="mb1"><span id="%s_y">&nbsp;NaN&nbsp;</span></td>
  <td class="icon">&nbsp;</td>
      <td class="icon" onclick='gnuplot.toggle_plot("%s_plot_1")'>&#9312;</td>
      <td class="icon" onclick='gnuplot.toggle_plot("%s_plot_2")'>&#9313;</td>
      <td class="icon" onclick='gnuplot.toggle_plot("%s_plot_3")'>&#9314;</td>
      <td class="icon" onclick='gnuplot.toggle_plot("%s_plot_4")'>&#9315;</td>
      <td class="icon" onclick='gnuplot.toggle_plot("%s_plot_5")'>&#9316;</td>
      <td class="icon" onclick='gnuplot.toggle_plot("%s_plot_6")'>&#9317;</td>
      <td class="icon" onclick='gnuplot.toggle_plot("%s_plot_7")'>&#9318;</td>
    </tr>
    </table>
    </td>
  </tr>
  <tr style="border:0;">
    <td style="border:0;">
<canvas id="%s" width=600 height=400 tabindex="0">
    <div class='box'><h2>Your browser does not support the HTML 5 canvas element</h2></div>
</canvas>
    </td>
  </tr>
</table>

      <script>
            %s();
              $('body').on('contextmenu', '#%s', function(e){ return false; });
       </script>
            ''' % (("","","","", imgdata) + (canvasname,)*12)

      im = showfunc(imgdata)
      #print (showfunc, imgdata)
      if self.cleanup:                                                       
         os.system("rm -f "+imgfile)                                                                                                               
      #   print(counter, end='\r')
      #print(counter, imgfile, os.path.exists(imgfile), os.system("lsof "+imgfile))
      return im

# a default instance
gplot = Gplot()
ogplot = gplot.oplot



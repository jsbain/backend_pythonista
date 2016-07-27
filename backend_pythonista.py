"""
Pythonista Backend for matplotlib
	https://github.com/jsbain/backend_pythonista.git
	 	
  import matplotlib
  matplotlib.use('module://my_backend')

TODO: 
	draw_image support
	fix text (small figures lose title and xlabel)
	add mathtext support
	add proper figure manager
	improve speed with more native calls, use native transforms, etc
	
	
Naming Conventions

  * classes Upper or MixedUpperCase

  * varables lower or lowerUpper

  * functions lower or underscore_separated

"""

from __future__ import (absolute_import, division, print_function,
                        unicode_literals)

import six

import matplotlib
from matplotlib import rcParams
from matplotlib._pylab_helpers import Gcf
from matplotlib.backend_bases import RendererBase, GraphicsContextBase,\
     FigureManagerBase, FigureCanvasBase
from matplotlib.figure import Figure
from matplotlib.path import Path
from matplotlib.transforms import Affine2D
from matplotlib.transforms import Bbox
from objc_util import *
from overlay import create 
import ui
print('imported backend')
rcParams['figure.figsize']=(576./160.,290./160.)

import logging,pprint
logger = logging.getLogger('backend_pythonista')
hdlr = logging.FileHandler('backend_pythonista.txt')
formatter = logging.Formatter('%(asctime)s %(levelname)s %(message)s')
hdlr.setFormatter(formatter)
logger.addHandler(hdlr) 
logger.setLevel(logging.WARNING)
GraphicsContextPythonista=GraphicsContextBase
UIFont=ObjCClass('UIFont')
class RendererPythonista(RendererBase):
	"""
	The renderer handles drawing/rendering operations.
	
	This is a minimal do-nothing class that can be used to get started when
	writing a new backend. Refer to backend_bases.RendererBase for
	documentation of the classes methods.
	"""
	def __init__(self, ctx,dpi):
		self.ctx = ctx
		self.width,self.height = self.get_canvas_width_height()
		self.dpi=dpi

	@staticmethod
	def convert_path(p, path, transform):
		# TODO  USE ctm rather than cpu transforms
		for points, code in path.iter_segments(transform):
			#print(code,points)
			if code == Path.MOVETO:
				p.move_to(*points)
			elif code == Path.CLOSEPOLY:
				p.close()
			elif code == Path.LINETO:
				p.line_to(*points)
			elif code == Path.CURVE3:
				p.add_curve(points[0], points[1],
				points[0], points[1],
				points[2], points[3])
			elif code == Path.CURVE4:
				p.add_curve(*points)
				
	def _fill_and_stroke (self, p, c, fill_c, alpha, alpha_overrides):
		if fill_c is not None:
			with ui.GState():
				if len(fill_c) == 3 or alpha_overrides:
					ui.set_color ((fill_c[0], fill_c[1], fill_c[2], alpha))
				else:
					ui.set_color((fill_c[0], fill_c[1], fill_c[2], fill_c[3]))
					#ctx.fill_preserve()
				p.fill()
		with ui.GState():
			ui.set_color(c)
			p.stroke()		
	def draw_path(self, gc, path, transform, rgbFace=None):
		if len(path.vertices) > 18980:
			raise ValueError("The Cairo backend can not draw paths longer than 18980 points.")

		#print ('called',path,transform)
		p=ui.Path()#ctx = gc.ctx
		dashes=gc.get_dashes()
		if dashes[1]:
			p.set_line_dash(dashes[1],dashes[0])
		transform = transform + \
		Affine2D().scale(1.0, -1.0).translate(0, self.height)
		self.convert_path(p, path, transform)
		logger.debug('draw:{} {} {} {}'.format(gc.get_rgb(),rgbFace,dashes,path))
		self._fill_and_stroke(p, gc.get_rgb(), rgbFace, gc.get_alpha(),gc.get_forced_alpha())
		
	# draw_markers is optional, and we get more correct relative
	# timings by leaving it out.  backend implementers concerned with
	# performance will probably want to implement it
#     def draw_markers(self, gc, marker_path, marker_trans, path, trans, rgbFace=None):
#         pass

	# draw_path_collection is optional, and we get more correct
	# relative timings by leaving it out. backend implementers concerned with
	# performance will probably want to implement it
#     def draw_path_collection(self, gc, master_transform, paths,
#                              all_transforms, offsets, offsetTrans, facecolors,
#                              edgecolors, linewidths, linestyles,
#                              antialiaseds):
#         pass

	# draw_quad_mesh is optional, and we get more correct
	# relative timings by leaving it out.  backend implementers concerned with
	# performance will probably want to implement it
#     def draw_quad_mesh(self, gc, master_transform, meshWidth, meshHeight,
#                        coordinates, offsets, offsetTrans, facecolors,
#                        antialiased, edgecolors):
#         pass

	def draw_image(self, gc, x, y, im):
		pass
		
	def draw_text(self, gc, x, y, s, prop, angle, ismath=False, mtext=None):
		font='Menlo',prop.get_size_in_points()*1.1

		w,h=ui.measure_string(s, font=font, alignment=ui.ALIGN_RIGHT, line_break_mode=ui.LB_WORD_WRAP)
		y-=h
		if True or angle:
			with ui.GState():
				ui.concat_ctm(ui.Transform.translation(x,y))
				ui.concat_ctm(ui.Transform.rotation(-angle*matplotlib.numpy.pi/180.))
				ui.draw_string(s, rect=(0, 0, 0, 0), font=font, color='black', alignment=ui.ALIGN_RIGHT, line_break_mode=ui.LB_WORD_WRAP)
		else:
			ui.draw_string(s, rect=(x, y, 0, 0), font=font, color='black', alignment=ui.ALIGN_RIGHT, line_break_mode=ui.LB_WORD_WRAP)
		#pass
		
	def flipy(self):
		return True
		
	def get_canvas_width_height(self):
		
		width=c.CGBitmapContextGetWidth(self.ctx)/2.
		height=c.CGBitmapContextGetHeight(self.ctx)/2.
		return width,height
		
	def get_text_width_height_descent(self, s, prop, ismath):
		'''in pixels?'''
		w,h=ui.measure_string(s,		font=('Menlo',prop.get_size_in_points()))
		d=-UIFont.fontWithName_size_('Menlo',prop.get_size_in_points()).descender()
		return w, (h-d), d
		
	def new_gc(self):
		return GraphicsContextPythonista()
		
	def points_to_pixels(self, points):
		# if backend doesn't have dpi, eg, postscript or svg
		#return points
		# elif backend assumes a value for pixels_per_inch
		#return points/72.0 * self.dpi.get() * pixels_per_inch/72.0
		# else
		return points*self.dpi/72.
	
	"""
	The graphics context provides the color, line styles, etc...  See the gtk
	and postscript backends for examples of mapping the graphics context
	attributes (cap styles, join styles, line widths, colors) to a particular
	backend.  In GTK this is done by wrapping a gtk.gdk.GC object and
	forwarding the appropriate calls to it using a dictionary mapping styles
	to gdk constants.  In Postscript, all the work is done by the renderer,
	mapping line styles to postscript calls.
	
	If it's more appropriate to do the mapping at the renderer level (as in
	the postscript backend), you don't need to override any of the GC methods.
	If it's more appropriate to wrap an instance (as in the GTK backend) and
	do the mapping here, you'll need to override several of the setter
	methods.
	
	The base GraphicsContext stores colors as a RGB tuple on the unit
	interval, eg, (0.5, 0.0, 1.0). You may need to map this to colors
	appropriate for your backend.
	"""
	pass
	
	
	
########################################################################
#
# The following functions and classes are for pylab and implement
# window/figure managers, etc...
#
########################################################################

def draw_if_interactive():
	"""
	For image backends - is not required
	For GUI backends - this should be overriden if drawing should be done in
	interactive python mode
	"""
	manager= Gcf.get_active()
	try:
		manager.canvas.draw()
		if not ObjCInstance(manager.view).superview():
			manager.view.attach()
	except AttributeError:
		show()
	
def show():
	"""
	For image backends - is not required
	For GUI backends - show() is usually the last line of a pylab script and
	tells the backend that it is time to draw.  In interactive mode, this may
	be a do nothing func.  See the GTK backend for an example of how to handle
	interactive versus batch mode
	"""
	for manager in Gcf.get_all_fig_managers():
		if not manager.view:
			manager = new_figure_manager(manager.num)
		# do something to display the GUI
		if not ObjCInstance(manager.view).superview():
			manager.view.attach()
		#manager.view.present('sheet')
		#v=create(manager.view)
		#manager._view=v
		manager.canvas.draw()
		pass
		
		
def new_figure_manager(num, *args, **kwargs):
	"""
	Create a new figure manager instance
	"""
	# if a main-level app must be created, this (and
	# new_figure_manager_given_figure) is the usual place to
	# do it -- see backend_wx, backend_wxagg and backend_tkagg for
	# examples.  Not all GUIs require explicit instantiation of a
	# main-level app (egg backend_gtk, backend_gtkagg) for pylab
	FigureClass = kwargs.pop('FigureClass', Figure)
	thisFig = FigureClass(*args, **kwargs)
	return new_figure_manager_given_figure(num, thisFig)
	
	
def new_figure_manager_given_figure(num, figure):
	"""
	Create a new figure manager instance for the given figure.
	"""
	canvas = FigureCanvasPythonista(figure)
	manager = FigureManagerPythonista(canvas, num)
	canvas.imgview.name='Figure %d'%num
	
	def event_resize(overlay):
		winch,hinch=overlay.content_view.width/160., overlay.content_view.height/160.
		figure.set_size_inches(winch, hinch)
		FigureCanvasBase.resize_event(canvas)
		canvas.draw()
	def event_close(overlay):
		matplotlib.pyplot.close(figure)
		FigureCanvasBase.close_event(canvas)
	v=create(canvas.imgview)
	if v:
		v.connect(v.EVENT_RESIZE,event_resize)
		v.connect(v.EVENT_CLOSE,event_close)
		manager.view=v
	else:
		manager.view= None
	return manager 
	

class FigureCanvasPythonista(FigureCanvasBase):
	"""
	The canvas the figure renders into.  Calls the draw and print fig
	methods, creates the renderers, etc...
	
	Public attribute
	
	figure - A Figure instance
	
	Note GUI templates will want to connect events for button presses,
	mouse movements and key presses to functions that call the base
	class methods button_press_event, button_release_event,
	motion_notify_event, key_press_event, and key_release_event.  See,
	eg backend_gtk.py, backend_wx.py and backend_tkagg.py
	"""
	def __init__(self,figure):
		FigureCanvasBase.__init__(self, figure)
		l,b,w,h = figure.bbox.bounds
		self.imgview=ui.ImageView(frame=(0,0,w,h))

		
	def draw(self):
		"""
		Draw the figure using the renderer
		"""
		#print('draw called')
		dpi=self.figure.dpi
		c.UIGraphicsBeginImageContextWithOptions(
			CGSize(self.imgview.width,self.imgview.height), False, 0);
		ctx = c.UIGraphicsGetCurrentContext ( )
		renderer = RendererPythonista(ctx,dpi)
		self.figure.draw(renderer)
		self.imgview.image=ui.Image.from_image_context()
		self.imgview.set_needs_display()
		c.UIGraphicsEndImageContext()

		
	# You should provide a print_xxx function for every file format
	# you can write.
	
	# If the file type is not in the base set of filetypes,
	# you should add it to the class-scope filetypes dictionary as follows:
	filetypes = FigureCanvasBase.filetypes.copy()
	filetypes['foo'] = 'My magic Foo format'
	
	def print_foo(self, filename, *args, **kwargs):
		"""
		Write out format foo.  The dpi, facecolor and edgecolor are restored
		to their original values after this call, so you don't need to
		save and restore them.
		"""
		pass
		
	def get_default_filetype(self):
		return 'foo'
		
class FigureManagerPythonista(FigureManagerBase):
	"""
	Wrap everything up into a window for the pylab interface
	
	For non interactive backends, the base class does all the work
	"""
	figManager = Gcf.get_active()
	if figManager is not None:
		figManager.canvas.draw()
		if not figManager.view.on_screen:
			figManager.view.present('sheet')
	
########################################################################
#
# Now just provide the standard names that backend.__init__ is expecting
#
########################################################################

FigureCanvas = FigureCanvasPythonista
FigureManager = FigureManagerPythonista


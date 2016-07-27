''' overlay:
	A new presentation mode for views, which act like a regular os window:
		1) float over existing content without stealing focus or having to switch tabs
		2) can be resized by user
		3) Include a title bar with a title label, close button, a minimize button (to hide view content), an expand/contract button.  
		4) Events connectable to user methods: resize, close implemented
		
		TODO: 1)Add gesturerecognizer to allow display inside editor or console windows
		 2) maybe, support theming
		 3) Docking (to top/sides of window in a minimized way)
'''
		
import ui
from objc_util import *
from math import pi


class AppWindows(object):
	app=UIApplication.sharedApplication()
	@classmethod
	def root(cls):
		'''pythonista's root window.  add here to be always present'''
		return cls.app.keyWindow()
	@classmethod	
	def accessory(cls):
		'''accessory, a.k.a. console/panel.  dragging does not work yet until gesture recognizer is added'''
		return cls.app.keyWindow().rootViewController().accessoryContainerView()
	@classmethod	
	def detail(cls):
		'''detail, a.k.a. editor panel.  dragging does not work yet until gesture recognizer is added'''
		return cls.app.keyWindow().rootViewController().detailContainerView()
	
class OverlayEvent(object):
	'''Simple enumeration of available events'''
	EVENT_CLOSE  =0
	EVENT_RESIZE =1
	EVENT_TAP    =2
	EVENT_LONGTAP=3
	

class Overlay(ui.View,OverlayEvent):
	'''Overlay class. User adds content to content_view, or as argument'''
	TOOLBAR_HEIGHT=36
	last_offset=[60,20]
	def __new__(cls,content=None,parent=AppWindows.root(),*args,**kwargs):
		if not content or not parent:
			return None
		else:
			return ui.View.__new__(cls, content=content,parent=parent, *args, **kwargs)
	def __init__(self,content=None,parent=AppWindows.root(),*args,**kwargs):
		import ui
		if content:
			kwargs['frame']=content.bounds.inset(-self.TOOLBAR_HEIGHT,0,0,0)
		ui.View.__init__(self,*args,**kwargs)
		self._pt=None
		self.actions={}
		self.w0=self.width
		self.h0=self.height
		# setup toolbar
		H=self.TOOLBAR_HEIGHT
		toolbar=ui.View(frame=(0,0,self.width,self.TOOLBAR_HEIGHT),
							 bg_color=(.8,.8,.8,.8))
		toolbar.flex='w'
		self.add_subview(toolbar)
		close=ui.Button(frame=(0,0,H,H))
		close.image=ui.Image.named('iob:close_32')
		close.action=self.remove
		toolbar.add_subview(close)
		minimize=ui.Button(frame=(self.width,0,-H,H))
		minimize.image=ui.Image.named('iob:chevron_down_32')
		toolbar.add_subview(minimize)
		minimize.flex='L'
		minimize.action=self.toggle
		zoom=ui.Button(frame=(minimize.x-8,0,-H,H))
		zoom.image=ui.Image.named('iob:arrow_expand_32')
		zoom.flex='L'
		zoom.action=self.zoom
		toolbar.add_subview(zoom)
		self.lbl=ui.Label(frame=(H+8,0,zoom.x-2*8-2*H,H),flex='wr')
		toolbar.add_subview(self.lbl)
		#content
		self.content_view = 		\
				ui.View(frame=(0,H,self.width,self.height-H),
					flex='wh',
					bg_color=(.9,.99,.99,.8))
		self.content_view.touch_enabled=False
		self.content_view.content_mode = ui.CONTENT_BOTTOM
		self.add_subview(self.content_view)
		self.resize=ui.ImageView(frame=(self.width-H,self.height-H,H,H))
		self.resize.image=ui.Image.named('iob:arrow_resize_32')
		self.resize.transform=ui.Transform.rotation(pi/2.)
		self.resize.flex='tl'
		self.add_subview(self.resize)
		self.resize.send_to_back()
		self.content_view.send_to_back()
		self.resizing=False
		self.x=self.last_offset[0]
		self.y=self.last_offset[0]
		self.last_offset[0]+=H
		self.last_offset[1]+=H
		
		if content:
			self.content_view.add_subview(content)
			content.flex='wh'
			self.lbl.text=content.name
		#add to top window
		# TODO: add to main console window instead... don't place over editor
		self.parent = parent
		self.attach()
	def connect(self,event,callback):
		try:
			self.actions[event].append(callback)
		except (KeyError, AttributeError):
			self.actions[event]=[callback]
	def draw(self):
		if self._pt:
			ui.fill_rect(self._pt[0]-10,self._pt[1]-10,20,20)
	def zoom(self,sender):
		if self.width<self.w0: #minimized
			if self.height==self.TOOLBAR_HEIGHT:
				self.toggle(self)
			self.width=self.w0
			self.height=self.h0
			self.content_view.frame=(0,self.TOOLBAR_HEIGHT,self.width,self.height-self.TOOLBAR_HEIGHT)
		else:
			self.width=200
			self.height=75+self.TOOLBAR_HEIGHT
			self.content_view.frame=(0,self.TOOLBAR_HEIGHT,self.width,self.height-self.TOOLBAR_HEIGHT)
		if not self.content_view.superview and self.height>self.TOOLBAR_HEIGHT:
			self.add_subview(self.content_view)
			self.content_view.send_to_back()
	def toggle(self,sender):
		if self.height==self.TOOLBAR_HEIGHT: #reveal
			self.height=self.h0
			sender.image=ui.Image.named('iob:chevron_down_32')
			self.content_view.frame=(0,self.TOOLBAR_HEIGHT,self.width,self.height-self.TOOLBAR_HEIGHT)
			if not self.content_view.superview:
				self.add_subview(self.content_view)
			self.content_view.send_to_back()
			self.process_events(self.EVENT_RESIZE)
		else: #hide
			sender.image=ui.Image.named('iob:chevron_up_32')
			self.remove_subview(self.content_view)
			self.height=self.TOOLBAR_HEIGHT

	def touch_began(self,touch):
		l=list(touch.location)
		self._pt=l
		self.set_needs_display()
		if ui.Point(*l) in self.resize.frame:
			self.resizing=True
		else:
			self.resizing=False
		self.parent.bringSubviewToFront_(self)
	def touch_moved(self,touch):
		l=touch.location
		p=touch.prev_location		

		t=l-p

		if self.resizing: 
			#i.e touching bottom corner. update size, limiting width and height 
			#to reasonable values
			self.width+=max(-self.width+3.5*self.TOOLBAR_HEIGHT,t.x)
			self.height+=max(-self.height+2*self.TOOLBAR_HEIGHT,t.y)
			self.w0=self.width
			self.h0=self.height
		else:
			self.x+=t.x
			self.y+=max(-self.y+20,t.y) #do not push above status bar
			self.alpha=.5
		self.set_needs_display()
	def process_events(self,evt):
		try:
			callbacks= self.actions.get(evt,[])
		except AttributeError:
			callbacks=[]
		for c in callbacks:
			c(self)
	def touch_ended(self,touch):
		self._pt=None
		if self.resizing:
			self.process_events(self.EVENT_RESIZE)
		self.alpha=1.
		self.set_needs_display()
	def remove(self,sender):
		import objc_util
		objc_util.ObjCInstance(self).removeFromSuperview()
		self.process_events(self.EVENT_CLOSE)
	def attach(self):
		self.parent.addSubview_(self)
	def __del__(self):
		#print('deleted overlay')
		#for s in self.subviews:
			#self.remove_subview(s)
		self.remove(self)
def create(content):
	if not ui:
		return
	else:
		return Overlay(content)
	
if __name__=='__main__':
	i=ui.ImageView(frame=(0,0,490,490))
	i.image=ui.Image.named('test:Mandrill')
	i.name='Family resemblance'
	i.alpha=1
	o=Overlay(content=i)
	o.content_view.border_width=2
	i.border_width=1
	i.content_mode=ui.CONTENT_SCALE_ASPECT_FIT

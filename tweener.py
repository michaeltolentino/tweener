import pymel.core as pm
from PySide.QtGui import *
from PySide.QtCore import *
import maya.mel as mel
from functools import partial
import maya.OpenMayaUI as omui
from shiboken import wrapInstance

# Get the maya main window as a QMainWindow instance
def getMayaWindow():
	mayaMainWindowPtr = omui.MQtUtil.mainWindow()
	mayaMainWindow = wrapInstance(long(mayaMainWindowPtr), QWidget)
	return mayaMainWindow

class tweener(QDialog):
	
	def __init__(self, parent=getMayaWindow()):
		super(tweener, self).__init__(parent)
		
		# Set main window title and size
		self.setWindowTitle('Tweener')
		self.setMinimumWidth(400)
		self.setMinimumHeight(65)
		self.setMaximumWidth(300)
		self.setMaximumHeight(65)
		self.setWindowFlags(Qt.Window)
		
		# Create main layout
		self.mainLayout = QVBoxLayout()
		self.setLayout(self.mainLayout)
		self.layout().setContentsMargins(10, 10, 10, 10)		
		
		# Add horizontal layout for the preset bias buttons
		self.biasButtonsLayout = QHBoxLayout()
		self.prevBiasMaxBtn = QPushButton("<<75%")
		self.prevBiasMaxBtn.setStyleSheet("background-color:#00b32d;")
		self.prevBiasMidBtn = QPushButton("<<60%")
		self.prevBiasMidBtn.setStyleSheet("background-color:#248f3e;")
		self.prevBiasLowBtn = QPushButton("<<33%")
		self.prevBiasLowBtn.setStyleSheet("background-color:#3e744c;")
		self.neutralBiasBtn = QPushButton("0%")
		self.nextBiasLowBtn = QPushButton("33%>>")
		self.nextBiasLowBtn.setStyleSheet("background-color:#5970a6;")
		self.nextBiasMidBtn = QPushButton("60%>>")
		self.nextBiasMidBtn.setStyleSheet("background-color:#3361cc;")
		self.nextBiasMaxBtn = QPushButton("75%>>")
		self.nextBiasMaxBtn.setStyleSheet("background-color:#004cff;")
		
		# Call the tweenPose function with the proper bias value based on which button was clicked
		self.prevBiasMaxBtn.clicked.connect(partial(self.triggerBiasValueUpdate, biasValue=-75))
		self.prevBiasMidBtn.clicked.connect(partial(self.triggerBiasValueUpdate, biasValue=-60))
		self.prevBiasLowBtn.clicked.connect(partial(self.triggerBiasValueUpdate, biasValue=-33))
		self.neutralBiasBtn.clicked.connect(partial(self.triggerBiasValueUpdate, biasValue=0))
		self.nextBiasLowBtn.clicked.connect(partial(self.triggerBiasValueUpdate, biasValue=33))
		self.nextBiasMidBtn.clicked.connect(partial(self.triggerBiasValueUpdate, biasValue=60))
		self.nextBiasMaxBtn.clicked.connect(partial(self.triggerBiasValueUpdate, biasValue=75))
		
		# Add horizontal layout for the slider and labels
		self.biasSliderLayout = QHBoxLayout()
		self.biasValue = QLineEdit()
		self.biasValue.setMaximumSize(70,20)
		self.biasValue.setText("0")
		self.intValidator = QIntValidator(-100, 100)
		self.biasValue.setValidator(self.intValidator)
				
		self.prevLabel = QLabel("Prev")
		self.nextLabel = QLabel("Next")
		
		self.biasSlider = QSlider(Qt.Horizontal)
		self.biasSlider.setMaximumSize(270, 50)
		self.biasSlider.setMinimum(-100)
		self.biasSlider.setMaximum(100)
		self.biasSlider.setValue(0)
		self.biasSlider.setTickPosition = (QSlider.TicksBothSides)
		self.biasSlider.setTickInterval(5)
		
		# Let the value of the line edit change the value of the slider
		self.biasValue.returnPressed.connect(self.biasValueChange)
		# Let the value of the slider change the value of the line edit
		self.biasSlider.valueChanged.connect(self.biasSliderChange)	
		self.biasSlider.sliderReleased.connect(self.biasSliderRelease)		
		
		# Add the widgets to the layout
		self.biasButtonsLayout.addWidget(self.prevBiasMaxBtn)
		self.biasButtonsLayout.addWidget(self.prevBiasMidBtn)
		self.biasButtonsLayout.addWidget(self.prevBiasLowBtn)
		self.biasButtonsLayout.addWidget(self.neutralBiasBtn)
		self.biasButtonsLayout.addWidget(self.nextBiasLowBtn)
		self.biasButtonsLayout.addWidget(self.nextBiasMidBtn)
		self.biasButtonsLayout.addWidget(self.nextBiasMaxBtn)
		self.biasSliderLayout.addWidget(self.biasValue)
		self.biasSliderLayout.addWidget(self.prevLabel)
		self.biasSliderLayout.addWidget(self.biasSlider)
		self.biasSliderLayout.addWidget(self.nextLabel)
		
		self.mainLayout.addLayout(self.biasButtonsLayout)
		self.mainLayout.addLayout(self.biasSliderLayout)
		
		self.show()
		
	# Updates the bias value line edit when the slider value is changed and create a keyframe based on the bias value
	def biasSliderChange(self):
		self.biasValue.setText(str(self.biasSlider.value()))
		
	# Updates the bias value line edit when the slider value is changed and create a keyframe based on the bias value
	def biasSliderRelease(self):
		self.biasValue.setText(str(self.biasSlider.value()))
		self.tweenPose(self.biasSlider.value())		
		
	# Updates the slider when the bias value line edit is updated
	def biasValueChange(self):
		self.biasSlider.setValue(int(self.biasValue.text()))
		self.tweenPose(int(self.biasValue.text()))
		
	def triggerBiasValueUpdate(self, biasValue):
		self.biasSlider.setValue(biasValue)
		self.tweenPose(biasValue)
		
	def tweenPose(self, biasValue):
		self.selectedObjects = pm.ls(sl=True)
		currentFrame = pm.currentTime(query=True)
		
		for item in self.selectedObjects:
			curves = pm.keyframe(item, query=True, name=True)
			
			for curve in curves:
				# Find where the prev and next keyframes were set
				framePrev = pm.findKeyframe(timeSlider=True, which="previous")
				frameNext = pm.findKeyframe(timeSlider=True, which="next")
				
				# Find which tangent type was used by the prev and next keyframes
				tanOutPrevKey = mel.eval('keyTangent -time ' + str(framePrev) + ' -q -ott ' +  curve)[0]
				tanInNextKey = mel.eval('keyTangent -time ' + str(frameNext) + ' -q -itt ' +  curve)[0]
				
				tanInNewKey = tanOutPrevKey
				tanOutNewKey = tanInNextKey
				
				# Set the new keyframe's tangent to 'auto' if the next or prev keyframes uses 'fixed'
				if tanOutPrevKey == 'fixed' or tanInNextKey == 'fixed':
					tanInNewKey = 'auto'
					tanOutNewKey = 'auto'
				elif tanOutPrevKey == 'step':
					tanInNewKey = 'linear'
					tanOutNewKey = 'step'
					
				# Retrieve the values of the next and previous keyframes
				prevCurveVal = pm.keyframe(curve, time=framePrev, query=True, valueChange=True)[0]
				nextCurveVal = pm.keyframe(curve, time=frameNext, query=True, valueChange=True)[0]
				
				# Compute the value of the new keyframe based on the bias value
				percentBias = (biasValue + 100) / float(200)
				newCurveVal = ((nextCurveVal - prevCurveVal) * percentBias) + prevCurveVal
				
				# Set a new keyframe using the new value
				pm.setKeyframe(curve, time=currentFrame, value=newCurveVal, itt=tanInNewKey, ott=tanOutNewKey)
	
		# Reset the current time to refresh the values shown in the channel box
		pm.currentTime(currentFrame, edit=True)
		
test = tweener()		
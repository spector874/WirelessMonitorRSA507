import matplotlib
matplotlib.use("Agg")  # or whichever backend you wish to use
import wx
import wx.xrc
import wx.grid
import wx.html
import wx.lib.buttons as buttons
from wx import adv
import os
import numpy.core._methods
import numpy.lib.format
from numpy import arange
from numpy import pi
from numpy import array
from numpy import ones
from numpy import linspace
from numpy import cos
from numpy import sin
from numpy import linspace
from numpy import argmax
from numpy import float64
from numpy import max
import json
from matplotlib.backends.backend_wxagg import FigureCanvasWxAgg as FigureCanvas
from matplotlib.figure import Figure
import matplotlib.pyplot as plt
import matplotlib.dates as mdates
import matplotlib.ticker as ticker
from scipy.interpolate import spline
import method
###################
from ctypes import *
import pandas
from pandas import DataFrame,concat
import datetime
import time
import pymysql as mdb
import cx_Oracle   #导入oracle
import threading
import wx.html2
import webbrowser as web
from queue import Queue
import subprocess				 
###################
import serial
import serial.tools.list_ports  #读取串口数据
TIMER_ID = wx.NewId()
#修改注册表
import winreg

#读取文件初始设置参数
# with open(os.getcwd()+'\\wxpython.json','r') as data:
    # config_data = json.load(data)

method = method.method1()
config_data=method.config_data
direction_cache=method.direction_cache
mysql_config=method.mysql_config
reflect_inf=method.reflect_inf
span=config_data['start_freq']-config_data['end_freq']
rsa_true=0
deviceSerial_true=0
continue_time=0
work_state=1   #工作方式是数据导入还是实时监测 0-数据导入， 1-监测
mon_or_real=0  #是月报模式还是实时监测模式 0——月报模式  1——实时监测模式
database_state=1  #数据库初始阶段默认为连接
detection_state=0 #初始时处于未检测状态，如果1处于检测状态（再次点击检测按钮无效）
longitude=-1  #经度
latitude=-1  #纬度
#longitude=116.3656073320  #经度
#latitude=39.9698474287  #纬度,
height=-1  #高度
GPS_end=False
has_rect = False #坐标轴中是否有标注框
has_txt = False  #坐标轴中是否有标注字
connect_state = 0 #仪器连接状态
connect_machine = '' #仪器型号
connect_change = 0 #仪器连接状态需要调整与否
start_spectrum_state = True
simple_start_freq = 930e6
simple_stop_freq = 950e6
simple_rbw=1e3  # 频谱查看中的 rbw设置，
uav_rbw=1e3   # uav 无人机监测中的 rbw 设置
# 测向模块需要用到的全局变量
Dir_cf = 8e8	#测向中心频率
Dir_BW = 2e4	#测向带宽
Dir_rbw = 1e3	#测向rbw
Dir_rl = 0	#测向参考电平

#current_loca=[-1,-1,-1]


#oracle链接
conn_str1 = method.conn_str1
conn_str2 = method.conn_str2
print (conn_str1)

lines=[]  #记录检测信号提示框
txts=[]

lines_waterfall=[]  #记录瀑布图

#设置初始默认参数
#频率都是以MHz为单位
# start_freq=200
# end_freq=3000
# RBW=0.1
# VBW=100
# step_freq=10
# trigger_level=6  #dB为单位
# Spec_dir=os.getcwd()+'\\spectrum_data'
# IQ_dir=os.getcwd()+'\\IQ_data'
# Antenna_number=''
# Antenna_level=''

#多线程
class WorkerThread(threading.Thread):     #画实时监测信号动态图  用于月报监测和自定义监测功能模块中
	"""
	This just simulates some long-running task that periodically sends
	a message to the GUI thread.
	"""
	def __init__(self,threadNum,window,rsa_true,deviceSerial_true,span,t,anteid,start_freq,end_freq,rbw,vbw):
	#def __init__(self,threadNum,window):
		threading.Thread.__init__(self)
		self.threadNum = threadNum
		self.window = window
		self.rsa_true=rsa_true
		self.deviceSerial_true=deviceSerial_true
		self.span=span
		self.t=t
		self.anteid=anteid
		self.start_freq=start_freq
		self.end_freq=end_freq
		self.rbw=rbw
		self.vbw=vbw
		#print (type(rbw),rbw)
		#print (type(vbw),vbw)
		#self.q=q
		self.timeToQuit = threading.Event()
		self.timeToQuit.clear()
		self._running = True

	def stop(self):
		global detection_state
		print ('Thread WorkerThread will be stopped')
		#self.timeToQuit.set()
		detection_state=0
		self._running = False


	def run(self):#运行一个线程
		# count=1
		# while count<5 and self._running:
			# wx.CallAfter(self.add2,'dsf')
			# self.timeToQuit.wait(5)
			# print ('run stop')
		##wx.CallAfter(self.window.spectrum2,self.rsa_true,self.deviceSerial_true, self.span , self.t ,self.anteid, self.start_freq, self.end_freq,self.rbw,self.q)
		
		global lines
		global txts
		global detection_state
		global has_rect
		global has_txt
		global longitude
		global latitude
		global height
		global start_spectrum_state
		global connect_change
		global mon_or_real
		# 进行连接获得检测设备信息
		# print (average)
		# 参数设置
		# 获取并设置设置起始频率和终止频率
		startFreq = c_double(float(self.start_freq))
		stopFreq = c_double(float(self.end_freq))
		# set span
		span = c_double(float(self.span))
		# # 设置rbw
		# rbw = c_double(float(self.rbw))
		# # 设置vbw
		# vbw = c_double(float(self.vbw))
		# 从别的数据库读取出所选用的天线类型
		# 设置step_size
		# step_size = c_double(float(input()))
		t = float(self.t)  # 持续时间
		time_ref = time.time()
		# 本次扫描的全部数据存储
		deviceSerial=self.deviceSerial_true
		anteid=self.anteid
		trace1= [] #保存采集的信号
		trace2= [] #保存一段时间的月报存储信号
		count = 0
		signal_count = 0 #检测出现子信号的段数
		
		'''
		参数配置完之后就可以开始进行数据库的创建，之后具体信号的检测得到的数据在
		之后的程序中写入表中即可
		'''
		# 先建立主表即测试任务，起始时间，持续时间
		str_time = str(datetime.datetime.now().strftime('%F-%H-%M-%S'))  # 整个测试的起始的准确时间用于存储原始文件路径的因为路径中不能有：
		start_time = str(datetime.datetime.now().strftime('%F %H:%M:%S')) # 总表的起始时间
		end_time=(datetime.datetime.now() + datetime.timedelta(seconds=t)).strftime('%F %H:%M:%S')
		
		if longitude==-1:
			longitude_set = float(116.41)
			latitude_set = float(39.85)
			height_set = float(1)
		else:
			longitude_set= longitude
			latitude_set= latitude
			height_set = height
		Sub_cf_all=[]
		Sub_band_all=[]
		Sub_peak_all=[]
		Sub_Spectrum_freq=[]
		Sub_Spectrum_trace=[]
		Sub_Spectrum_time=[]
		Sub_Spectrum_cf = []
		Sub_Spectrum_peak = []
		Sub_Spectrum_band = []
		load_time=time_ref
		load_data_time = time_ref
		load_time_pre=start_time
		num_signal=0     #种类信号标号
		num_signals=[]   #存入每次扫描的不同种类的标号
		# work_state=self.window.notebook.GetSelection() #0-月报检测  1-随机任务
		self.window.list_ctrl.DeleteAllItems()   #清空之前信号列表的数据
		max_axis_value = -20  #设置坐标轴最大小值
		min_axis_value = -20
		#print ('work_state:',work_state)
		#测试数据库的使用
		try:
			method.test_oracle_connection()
			print ('oracle_sucess')
		except:
			wx.MessageBox(u' 数据库连接不成功', "Message" ,wx.OK | wx.ICON_INFORMATION)
		while time.time() - time_ref < t and self._running:
			average = method.detectNoise(self.rsa_true,self.start_freq,self.end_freq,self.rbw,self.vbw)
			#print ('#'*20)
			#print ('average:',average)
			count += 1
			str_tt1 = str(datetime.datetime.now().strftime('%F %H:%M:%S'))  # 内部扫频的时刻
			str_tt2 = str(datetime.datetime.now().strftime('%F-%H-%M-%S'))  # 作为内部细扫的文件名
			spectrum1 = method.spectrum1(self.rsa_true,average, startFreq, stopFreq, span, self.rbw, self.vbw, str_time, count, str_tt1, str_tt2,longitude_set,latitude_set,num_signal,Sub_cf_all)
			if spectrum1 != 0:
				head,data1,Sub_cf_channel,Sub_span,Sub_cf,Sub_band,Sub_peak,Sub_Spectrum1,Sub_Spectrum2,freq1,traceData1,point,point_xy,num_signal_new,Sub_illegal,Sub_type= spectrum1
				num_signal=num_signal_new
				#把不重复信号给滤除掉
				Sub_cf_length = len(Sub_cf_all) #已经有多少种不重复信号
				if Sub_cf:
					if not Sub_cf_all:
						Sub_cf_all=Sub_cf[:]
						
						#输入初始框的内容
						#在右边的列表里显示信号段信息
						for i in range(len(Sub_cf)):
							#保存列表里每一行数据的来源数据段
							Sub_Spectrum_freq.append(Sub_Spectrum1)
							Sub_Spectrum_trace.append(Sub_Spectrum2)
							Sub_Spectrum_time.append(str_tt1)
							Sub_Spectrum_cf.append(Sub_cf[i])
							Sub_Spectrum_peak.append(Sub_peak[i])
							Sub_Spectrum_band.append(Sub_band[i])
							#将数据信息插入列表
							self.window.list_ctrl.InsertItem(i,str(i+1))
							self.window.list_ctrl.SetItem(i,1,str(Sub_cf[i]/1e6))
							self.window.list_ctrl.SetItem(i,2,str(Sub_band[i]/1e6))
							self.window.list_ctrl.SetItem(i,3,str(Sub_peak[i]))
							self.window.list_ctrl.SetItem(i,4,str(Sub_type[i]))   #业务类型暂时不知道
							#如果判定为不合格则标注为红色
							if Sub_illegal[i]==0:
								self.window.list_ctrl.SetItemBackgroundColour(i, "red")
						
					else:
						for cf_i in range(len(Sub_cf)):
							divide_cf = array(Sub_cf_all)-Sub_cf[cf_i]
							#判断是否有重复信号（cf在一定范围内则算作重复），如果有重复，则给出是与第几个列表信号重复
							divide_no = 0 
							while divide_no<Sub_cf_length:
								if abs(divide_cf[divide_no])<=0.2*1e6:
									break;
								divide_no += 1
							if divide_no == Sub_cf_length:
								#与之前的信号都不重复,记录频段信号来源
								Sub_Spectrum_freq.append(Sub_Spectrum1)
								Sub_Spectrum_trace.append(Sub_Spectrum2)
								Sub_Spectrum_time.append(str_tt1)
								Sub_Spectrum_cf.append(Sub_cf[cf_i])
								Sub_Spectrum_peak.append(Sub_peak[cf_i])
								Sub_Spectrum_band.append(Sub_band[cf_i])
								#直接在列表中加入该信号
								Sub_cf_all.append(Sub_cf[cf_i])
								Sub_cf_length += 1
								self.window.list_ctrl.InsertItem(divide_no,str(divide_no+1))
								self.window.list_ctrl.SetItem(divide_no,1,str(Sub_cf[cf_i]/1e6))
								self.window.list_ctrl.SetItem(divide_no,2,str(Sub_band[cf_i]/1e6))
								self.window.list_ctrl.SetItem(divide_no,3,str(Sub_peak[cf_i]))
								self.window.list_ctrl.SetItem(divide_no,4,str(Sub_type[cf_i]))   #业务类型暂时不知道
								#如果判定为不合格则标注为红色
								if Sub_illegal[cf_i]==0:
									self.window.list_ctrl.SetItemBackgroundColour(divide_no, "red")
							else:
								#如果重复了，则与那个重复信号幅度做比较，如果比之大，则替换掉它的幅度
								list_peak= self.window.list_ctrl.GetItem(divide_no, 3)
								list_peak= float(list_peak.GetText())
								list_cf =self.window.list_ctrl.GetItem(divide_no, 1).GetText()
								if Sub_peak[cf_i]> list_peak:
									self.window.list_ctrl.SetItem(divide_no,1,str(Sub_cf[cf_i]/1e6))
									self.window.list_ctrl.SetItem(divide_no,2,str(Sub_band[cf_i]/1e6))
									self.window.list_ctrl.SetItem(divide_no,3,str(Sub_peak[cf_i]))
									Sub_Spectrum_freq[divide_no]=Sub_Spectrum1
									Sub_Spectrum_trace[divide_no]=Sub_Spectrum2
									Sub_Spectrum_time[divide_no]=str_tt1
									Sub_Spectrum_cf[divide_no] = Sub_cf[cf_i]
									Sub_Spectrum_peak[divide_no] = Sub_peak[cf_i]
									Sub_Spectrum_band[divide_no] = Sub_band[cf_i]
				
				#输出到底有多少信号
#				if count % 100==0:
#					print (count)
				#################信号段颜色设置，0-非法，红色，1-合法，绿色
				color_list=['r','g']
				
				self.window.freq=freq1
				self.window.traceData=traceData1
				# print(self.window.traceData[0:10])
				# self.window.l_user.set_xdata(self.window.freq)
				# self.window.l_user.set_ydata(self.window.traceData)
				if max(traceData1) > max_axis_value:
					max_axis_value = max(traceData1) + 5
				if average < min_axis_value:
					min_axis_value = average - 10
				self.window.axes_score.set_ylim(min_axis_value,max_axis_value)
				self.window.axes_score.set_xlim(self.window.freq[0],self.window.freq[-1])
				self.window.l_user.set_data(self.window.freq,self.window.traceData)
				
				if lines and has_rect:
					for i in range(len(lines)):
						lines[i][0].remove()
					has_rect = False
				if txts and has_txt:
					for j in range(len(txts)):
						txts[j].remove()
					has_txt = False
				lines=[]
				txts=[]
				
				#print ('dsfdsfsdfsdfsdf:',point_xy)
				for i in range(len(point_xy)):
					#print(point_xy[i])
					j1=i+1
					#print (j1)
					#print ('koasdfdsfdsfds')
					line=self.window.axes_score.plot([point_xy[i][0], point_xy[i][0]], [point_xy[i][2], point_xy[i][3]],color_list[Sub_illegal[i]])
					lines.append(line)
					line=self.window.axes_score.plot([point_xy[i][0], point_xy[i][1]], [point_xy[i][3], point_xy[i][3]],color_list[Sub_illegal[i]])
					lines.append(line)
					line=self.window.axes_score.plot([point_xy[i][1], point_xy[i][1]], [point_xy[i][3], point_xy[i][2]],color_list[Sub_illegal[i]])
					lines.append(line)
					line=self.window.axes_score.plot([point_xy[i][0], point_xy[i][1]], [point_xy[i][2], point_xy[i][2]],color_list[Sub_illegal[i]])
					lines.append(line)
					has_rect = True
					txt=self.window.axes_score.text((point_xy[i][0]+point_xy[i][1])/2,point_xy[i][3],'%s'%j1,color='w')
					txts.append(txt)
					has_txt = True
				self.window.axes_score.draw_artist(self.window.l_user)
				self.window.canvas.draw()
				
				#在右边的列表里显示信号段信息
				'''
				for i in range(len(Sub_cf)):
					#print (i)
					self.window.list_ctrl.InsertItem(i+signal_count,str(i+1))
					self.window.list_ctrl.SetItem(i+signal_count,1,str(Sub_cf[i]/1e6))
					self.window.list_ctrl.SetItem(i+signal_count,2,str(Sub_band[i]/1e6))
					self.window.list_ctrl.SetItem(i+signal_count,3,str(Sub_type[i]))   #业务类型暂时不知道
					#如果判定为不合格则标注为红色
					if Sub_illegal[i]==0:
						self.window.list_ctrl.SetItemBackgroundColour(i+signal_count, "red")
				'''
				signal_count += len(Sub_cf)
				
				trace1.append(data1)
				trace2.append(data1[3:])
				
				if time.time()-load_time>35 :
					trace2 = array(trace2)
					time_now=str(datetime.datetime.now().strftime('%F %H:%M:%S')) # 总表的起始时间
					print (1)
					method.rmbt_facility_freqband_emenv(str_time,self.span,load_time_pre,time_now,longitude_set,latitude_set)
					print (2)
					method.rmbt_facility_freq_emenv3(str_time,load_time_pre,time_now,'01') #ssid默认为ssid
					print (3)
					method.rmbt_freq_occupancy(self.span,load_time_pre,time_now,self.start_freq,self.end_freq,longitude_set,latitude_set,height_set,trace2,head[3:],average)
					#pass;    ##一个小时存一次
					load_time=time.time()
					load_time_pre = time_now
					trace2=[]
				
				#分时间存储原始数据
				'''
				if time.time() - load_data_time > 600 :
					new_time = str(datetime.datetime.now().strftime('%F-%H-%M-%S'))
					path = method.config_data['Spec_dir']+"\\%s\\"%(str_time+'--'+str_time1 + ("spectrum%d" % t)) + (str_time+'--'+new_time) + "spectrum%ds.csv" % t  # 频谱数据粗扫描数据存储路径
					trace = DataFrame(trace1,index=range(len(trace1)),columns=head)
					trace.to_csv(
						path,
						index=False
					)

					start_time = str(datetime.datetime.now().strftime('%F-%H-%M-%S'))
					load_data_time = time.time()
				'''
			else:
				self._running = False
				connect_change = 1
				wx.MessageBox(u"仪器连接不正常", "Message" ,wx.OK | wx.ICON_INFORMATION)
				self.stop()   # add by vinson to stop the thread
				
		wx.MessageBox('监测任务完成！','Information',wx.OK|wx.ICON_INFORMATION)
		self.window.m_button10.SetLabel("开始监测")
		self.window.m_button10.SetValue(False)
        
        #  something wrong   
		if mon_or_real:   # true 时是自定义监测
			self.window.m_textCtrl1.Enable(True)
			self.window.m_textCtrl2.Enable(True)
			self.window.m_textCtrl3.Enable(True)
			self.window.m_tc_MonitorTime.Enable(True)
		else:
			self.window.textCtrl3.Enable(True)
			self.window.textCtrl5.Enable(True)
			self.window.textCtrl10.Enable(True)
        
		detection_state=0 #任务结束，监测状态归为0
		#保存最大的数据段到csv文件里
		Max_spectrum = [str_tt1]
		Max_Spectrum_trace = [[Sub_Spectrum_time[i],Sub_Spectrum_cf[i],Sub_Spectrum_peak[i],Sub_Spectrum_band[i]]+[longitude_set,latitude_set]+list(Sub_Spectrum_trace[i]) for i in range(len(Sub_Spectrum_trace))]
		array_spectrum = array(Max_Spectrum_trace)
		if Max_Spectrum_trace:
			for i in range(1,len(Max_Spectrum_trace[0])):
				spectrum_i = array(array_spectrum[:,i],float64)
				Max_spectrum.append(max(spectrum_i))
			Max_Spectrum_trace.append(Max_spectrum)
		
		#保存数据段
		self.window.Sub_freq=Sub_Spectrum_freq
		self.window.Sub_Spectrum=Sub_Spectrum_trace
		# self.window.lines=lines
		# self.window.txts=txts
		print (len(self.window.Sub_Spectrum))
		# 获取测试时间,保存原始频谱数据
		str_time1 = str(datetime.datetime.now().strftime('%F-%H-%M-%S'))  # 结束的准确时间，直接传到数据库中自动转化成datetime格式
		#file_path=os.getcwd()+"\\data1\\%s\\"%(str_time+'--'+str_time1 + ("spectrum%d" % t))
		file_path=method.config_data['Spec_dir']+"\\%s\\"%(str_time+'--'+str_time1 + ("spectrum%d" % t))
		if not os.path.exists(file_path):
			os.mkdir(file_path)
		#存入原始扫描数据，文件名设置
		#path = os.getcwd()+"\\data1\\%s\\"%(str_time+'--'+str_time1 + ("spectrum%d" % t)) + (str_time+'--'+str_time1) + "spectrum%ds.csv" % t  # 频谱数据粗扫描数据存储路径
		path = method.config_data['Spec_dir']+"\\%s\\"%(str_time+'--'+str_time1 + ("spectrum%d" % t)) + (str_time+'--'+str_time1) + "spectrum%ds.csv" % t  # 频谱数据粗扫描数据存储路径
		trace = DataFrame(trace1,index=range(len(trace1)),columns=head)
		trace.to_csv(
			path,
			index=False
		)
		#存入最大信号扫描信号，文件名设置
		#path2 = os.getcwd()+"\\data1\\%s\\"%(str_time+'--'+str_time1 + ("spectrum%d" % t)) + (str_time+'--'+str_time1) + "Max_spectrum%ds.csv" % t  # 频谱数据粗扫描数据存储路径
		path2 = method.config_data['Spec_dir']+"\\%s\\"%(str_time+'--'+str_time1 + ("spectrum%d" % t)) + (str_time+'--'+str_time1) + "Max_spectrum%ds.csv" % t  # 频谱数据粗扫描数据存储路径
		head_new = [head[0]] + ['cf','peak','band']+head[1:]
		traceMax = DataFrame(Max_Spectrum_trace,index=range(len(Max_Spectrum_trace)),columns=head_new)
		traceMax.to_csv(
			path2,
			index=False
		)
		
		s_c = method.spectrum_occ(start_time, str_time1, str_time, startFreq.value, stopFreq.value)
		# 数据库构建
		#con=mdb.connect(mysql_config['host'],mysql_config['user'],mysql_config['password'],mysql_config['database'])
		con = cx_Oracle.Connection(conn_str1)  
		#con = mdb.connect('localhost', 'root', 'cdk120803', 'ceshi1')
		with con:
			# 获取连接的cursor，只有获取了cursor，我们才能进行各种操作
			cur = con.cursor()  # 一条游标操作就是一条数据插入，第二条游标操作就是第二条记录，所以最好一次性插入或者日后更新也行
			#print ([str_time, start_time, str_time1, float(t), float(s_c), path, deviceSerial, anteid, count])
			cur.execute("INSERT INTO Minitor_Task VALUES('%s',to_date('%s','yyyy-MM-dd hh24:mi:ss'),to_date('%s','yyyy-MM-dd hh24:mi:ss'),%s,%s,'%s','%s','%s',%s,%s,%s,%s,%s)"%(str_time, start_time, str_time1, float(t), float(s_c), path, deviceSerial, anteid, count,float(startFreq.value), float(stopFreq.value),float(longitude_set),float(latitude_set)))
			cur.close()
		con.commit()
		con.close()
		print ('insert Minitor_Task success')
		
		#######################################

class WorkerThread2(threading.Thread):    #画 UAB 无人机动态图线程
	"""
	This just simulates some long-running task that periodically sends
	a message to the GUI thread.
	"""
	def __init__(self,threadNum,window,rsa_true,deviceSerial_true,t,test_No,anteid,rbw,vbw,freq_interval):
	#def __init__(self,threadNum,window):
		threading.Thread.__init__(self)
		#multiprocessing.Process.__init__(self)
		self.threadNum = threadNum
		self.window = window
		self.rsa_true=rsa_true
		self.deviceSerial_true=deviceSerial_true
		self.t=t
		self.rbw=rbw
		self.vbw=vbw
		#print (type(rbw),rbw)
		#print (type(vbw),vbw)
		self.freq_interval=freq_interval
		self.test_No=test_No
		self.anteid=anteid
		self.timeToQuit = threading.Event()
		self.timeToQuit.clear()
		self._running = True

	def stop(self):
		global detection_state
		#print ('will be stopped')
		#self.timeToQuit.set()
		detection_state = 0
		self._running = False

	def run(self):#运行一个线程
		global lines_pubu
		global longitude
		global latitude
		global connect_change
		global uav_rbw
		self.test_No=79
		test_No=self.test_No
		trace_IQ = DataFrame({})
		count = 0
		startFreq=self.freq_interval[0]*1e6
		endFreq=self.freq_interval[1]*1e6
		self.rbw=uav_rbw
		#print("uav_rbw in detection thread:" + str(uav_rbw))
		average = method.detectNoise(self.rsa_true,startFreq,endFreq,self.rbw,self.vbw)
		a = []  # 存储无人机出现的时间段
		b = []  # 存储无人机信号出现的带宽
		c = []  # 存储无人机信号出现的中心频点
		I_data=[]
		Q_data=[]
		
		
		str_time = str(datetime.datetime.now().strftime('%F-%H-%M-%S'))  # 无人机检测起始时间
		t_ref = time.time()
		time_list=[]
		x_y = 0
		time1=0
		if longitude==-1:
			longitude_set = float(116.41)
			latitude_set = float(39.85)
			height_set = float(1)
		else:
			longitude_set= longitude
			latitude_set= latitude
			height_set = height
		max_axis_value = -20
		min_axis_value = -100
		while time.time() - t_ref < self.t and self._running:
			self.rbw=uav_rbw
			time1 = time1-1
			if time1==0:
				self.window.axes_score_new.cla()
			x_y = 0-time1
			time_list.append(time1)
			uav0_spectrum = method.uav0(self.rsa_true,startFreq,endFreq,average,self.rbw,self.vbw)
			if uav0_spectrum != 0:
				freq_cf, band, peak,freq,traceData= uav0_spectrum
				################################
				###动态画UAV频谱图
				#self.window.canvas.restore_region(self.window.bg)
				self.window.traceData=traceData
				self.window.freq=freq
				if max(traceData) > max_axis_value:
					max_axis_value = max(traceData) + 5
				min_trace = min(traceData)
				if  min_trace > min_axis_value + 10 :
					min_axis_value = min_trace-10
				elif min_trace<min_axis_value:
					min_axis_value=min_trace-10
				self.window.axes_score.set_ylim(min_axis_value,max_axis_value)
				self.window.axes_score.set_xlim(freq[0],freq[-1])
				self.traceData_new=-1 * array(self.window.traceData[0:-1]+[-10])  #要让噪声近乎无色
				self.window.axes_score_new.scatter(self.window.freq,[time1]*len(self.window.freq),c=self.traceData_new,cmap=plt.cm.Blues,s=0.5)
				self.window.l_user.set_ydata(self.window.traceData)
				self.window.l_user.set_xdata(self.window.freq)
				self.window.axes_score.draw_artist(self.window.l_user)
				#self.window.canvas.blit(self.window.axes_score.bbox)
				###动态画瀑布图
				# for i in range(len(lines_waterfall)):
					# lines_waterfall[i][0].remove()
				# lines_waterfall=[]
				
				self.window.axes_score_new.set_xlim(freq[0],freq[-1])
				#print (time1)
				if x_y > 100:
					#del x_y[time1+200]
					x_y = 0
					time1 = 1
					print ('delete')
					self.l_user,=self.window.axes_score.plot([],[],'b')
					self.window.axes_score_new.cla()
					self.r_user,=self.window.axes_score_new.plot([],[],'b')
					
					

				x_y_keys=x_y
				if x_y_keys:
					self.window.axes_score_new.set_ylim(time1,time1+100)
				else:
					self.window.axes_score_new.cla()
					self.window.axes_score_new.set_ylim(0,100)

				# for x_i in x_y:
					# if x_y[x_i] == 0:
						# pass
					# else:
						# line=self.window.axes_score_new.plot(x_y[x_i],[x_i,x_i],'r')
						# lines_waterfall.append(line)
				self.window.axes_score.draw_artist(self.window.r_user)
				self.window.canvas.draw()
			else:
				self._running = False
				connect_change = 1
				wx.MessageBox(u"仪器连接不正常", "Message" ,wx.OK | wx.ICON_INFORMATION)
				self.stop()   # add by vinson to stop the thread
			
			# for i in range(len(freq_cf)):
				# df1,I,Q = method.uav1(self.rsa_true,band[i],freq_cf[i])
				# I_data.append(I)
				# Q_data.append(Q)
				# trace_IQ = pandas.concat([trace_IQ, df1])
		'''
		#画IQ图
		# print (I,Q)
		# print (len(I))
		os.mkdir(os.getcwd()+"\\IQ\\%s\\" % str_time)
		path = os.getcwd()+"\\IQ\\%s\\" % str_time + str_time + "IQ%s.csv" % self.t  # IQ数据存储路径
		trace_IQ.to_csv(
			path,
			index=False
		)
		con=mdb.connect(mysql_config['host'],mysql_config['user'],mysql_config['password'],mysql_config['database'])
		#con = mdb.connect('localhost', 'root', 'cdk120803', 'ceshi1')
		with con:
			# 操作数据库需要一次性的进行，一条代码就是写入一行所以一次就把表的一行全部写入
			cur = con.cursor()
			#cur.execute("INSERT INTO uav VALUES(%s, %s, %s, %s, %s, %s, %s, %s, %s,%s,%s)", [int(test_No), str_time, str_time, float(c[0]-b[0]/2), float(c[0] + b[0] / 2), float(b[0]), path, self.deviceSerial_true, self.anteid,float(longitude_set),float(latitude_set)])
			cur.close()
		con.commit()
		con.close()
		
		
		if a==[]:
			a.append(self.t)
		peak_freq_str=[str(float(i/1e6))+'MHz' for i in c]
		band_str=[str(float(i/1e6))+'MHz' for i in b]
		self.window.peak_freq_list=peak_freq_str
		self.window.band_list=band_str
		self.window.I=I_data
		print ('length:',len(I_data))
		self.window.Q=Q_data
		self.window.m_listBox8.Clear()
		self.window.m_listBox8.SetItems(peak_freq_str)  #必须导入字符串
		#print (self.window.band.get())
		#print(a,b,c)
		'''


class WorkerThread3(threading.Thread):     #频谱回放功能，画导入信号动态图
	"""
	This just simulates some long-running task that periodically sends
	a message to the GUI thread.
	"""
	def __init__(self,window,start_freq,end_freq,x_data,y_data,continue_time,detail_information):
	#def __init__(self,threadNum,window):
		threading.Thread.__init__(self)
		self.window = window
		self.start_freq=start_freq
		self.end_freq=end_freq
		self.x_data=x_data
		self.y_data=y_data
		self.continue_time=continue_time
		self.detail_information = detail_information
		self.timeToQuit = threading.Event()
		self.timeToQuit.clear()
		self._running = True

	def stop(self):
		global work_state
		print ('690 data_import_show will be stopped')
		#self.timeToQuit.set()
		work_state=1
		self.window.point = []
		self._running = False

	def run(self):#运行一个线程
		print (type(self.x_data))
		global has_rect
		global has_txt
		global work_state
		global lines
		global txts
		[m,n]=self.y_data.shape
		num=0
		if lines and has_rect:
			for i in range(len(lines)):
				lines[i][0].remove()
			has_rect = False
		if txts and has_txt:
			for j in range(len(txts)):
				txts[j].remove()
			has_txt = False
		lines=[]
		txts=[]
		#测试数据库的使用
		try:
			method.test_oracle_connection()
			print ('oracle_sucess in WorkThread3')
		except:
			wx.MessageBox(u' 数据库连接不成功', "Message" ,wx.OK | wx.ICON_INFORMATION)
		# -----------add by vinson 
		max_axis_value=max(self.y_data[0])+5
		min_axis_value=min(self.y_data[0])-10
		# -------------
		while self._running and num<m:
			# 自动调整频谱图上下阈值，使频谱图完整显示
			if max(self.y_data[num,:])>=max_axis_value:
				max_axis_value=max(self.y_data[num,:])+5
			if min(self.y_data[num,:])<=min_axis_value:
				min_axis_value=min(self.y_data[num,:])-10
				
			self.window.traceData=self.y_data[num,:]
			self.window.axes_score.set_xlim(self.start_freq,self.end_freq)
			self.window.axes_score.set_ylim(min_axis_value,max_axis_value)
			self.window.l_user.set_data(self.x_data,self.y_data[num,:])
			self.window.axes_score.draw_artist(self.window.l_user)
			self.window.canvas.draw()
			time.sleep(0.2)
			num+=1
			# self.window.canvas.draw()
			# self.window.m_panel2.Refresh()
			#最后一帧的时候显示所有信息
			if num == m:
				work_state = 1
		
class WorkerThread4(threading.Thread):     #获取GPS的时间进度条

	def __init__(self,window,count,gause_range):
	#def __init__(self,threadNum,window):
		threading.Thread.__init__(self)
		self.window = window
		self.count=count
		self.gause_range=gause_range
		self.timeToQuit = threading.Event()
		self.timeToQuit.clear()
		self._running = True

	def stop(self):
		print ('will be stopped')
		#self.timeToQuit.set()
		self._running = False

	def run(self):#运行一个线程
		global longitude
		global latitude
		global height
		count=self.count
		self.window.count1=count  #记录进度条是否正常结束
		while self._running and count < self.gause_range:
			count=count+1
			self.window.count1=self.window.count1+1
			#longitude,latitude,height=method.get_GPS()
			#longitude,latitude,height=method.get_GPS2(rsa_true)
			#print (longitude,latitude,height)
			if sum(array(self.window.location)==-1)==0:
				count=self.gause_range
				self.window.button1.Enable(True)
				self.window.button2.Enable(False)
				self.window.GPS_state=True
				wx.MessageBox(u"经度，纬度，高度信息为："+str(self.window.location), "Message" ,wx.OK | wx.ICON_INFORMATION)
			self.window.gauge.SetValue(count)
			if count ==self.gause_range and self.window.GPS_state==False:
				count=0
		if count !=self.gause_range:
			self.window.gauge.SetValue(self.gause_range)  #如果gause每到最右端而强制删除，程序会卡住
		self.window.GPS_end=True
		# if self.window.count1==self.gause_range:    #运行时间到，还没获取到位置信息
			# self.window.GPS_wait=True
			# wx.MessageBox("Can't get location,please try it again", "Message" ,wx.OK | wx.ICON_INFORMATION)
			# self.window.button1.Enable(True)
			# self.window.button2.Enable(False)

class WorkerThread5(threading.Thread):     #测向模块：自动读取信号方向，幅度

	def __init__(self,t,window,input_detail):
		threading.Thread.__init__(self)
		self.input_detail = input_detail  # [freq,span,rfLevel,rbw,vbw]
		self.t = t
		self.window = window
		self.timeToQuit = threading.Event()
		self.timeToQuit.clear()
		self._running = True

	def stop(self):
		print (u'测向模块功能中获取信号强度和方向现成将终止！')
		#self.timeToQuit.set()
		self._running = False

	def run(self):#运行一个线程
		global detection_state
		global connect_change
		global Dir_BW
		global Dir_cf
		global Dir_rbw
		global Dir_rl
		
		time_ref = time.time()
		cache_num = 1
		first_step = 0
		self.t = 10
		self.freq = 0
		self.traceData = 0
		# self.rbw = self.input_detail[3]
		self.vbw = self.input_detail[4]
		self.rbw = Dir_rbw

		while self._running :
			angel=self.window.get_direction()
			# angel = 20 # commented by vinson
			#print (angel)
			if angel==-2:
				detection_state = 0
				return   # 连接错误直接终止
			elif angel==-1:
				wx.MessageBox('获取方向失败  .', "Error" ,wx.OK | wx.ICON_ERROR)
				detection_state = 0
				return   # 连接错误直接终止
			elif angel>360 or angel<0:
				continue
			else:
				if self.window.input_state == 1:
					print (u'829 WorkerThread5 测向线程中读取频谱参数数据！')
					
					angel=360-angel    # add by vinson  2018-8-19
					
					centerFreq = Dir_cf     # 参数受界面上的输入框改变而控制
					Span = Dir_BW
					RefLevel = Dir_rl
					self.rbw = Dir_rbw
					
					Span = self.input_detail[1]
					k = 5 #连续扫描多少帧，取最大值
					self.traceAll = []
					for i in range(k):
						direction_spectrum = method.find_direction(rsa_true,centerFreq,Span,RefLevel,self.rbw)
						if direction_spectrum != 0:
							peakPower,self.freq,self.traceData = direction_spectrum
							self.traceAll.append(self.traceData)
						else:
							self._running = False
							connect_change = 1
							wx.MessageBox(u"仪器连接不正常", "Message" ,wx.OK | wx.ICON_INFORMATION)
							self.stop()
							break
						time.sleep(0.05)
					
					if direction_spectrum != 0 and first_step != 0:
						self.traceData = max(array(self.traceAll),0).tolist()
						if sum(self.traceData) == 0:
							continue
						#print (self.traceData)
						peakPower = max(self.traceData)
						#####################将信号峰值显示到表格中
						i=self.window.list_ctrl.GetItemCount()
						self.window.list_ctrl.InsertItem(i,str(i+1))
						self.window.list_ctrl.SetItem(i,1,str(angel))
						self.window.list_ctrl.SetItem(i,2,str(peakPower))
						#self.names['textCtrl%s'%int(angel/10)].SetValue(str(peakPower)+'dBmV')
						#print (peakPower)
						self.window.angel_peak[angel]=10**(peakPower/10)
						#####################将整帧扫描到的信号显示到坐标轴中
						#self.window.axeLeft.plot(self.freq,self.traceData)
						self.window.axesLeft.set_xlim(self.freq[0],self.freq[-1])
						self.window.axesLeft.set_ylim(min(self.traceData)-10,max(self.traceData)+10)
						self.window.l_userLeft.set_data(self.freq,self.traceData)
						self.window.axesLeft.draw_artist(self.window.l_userLeft)
						self.window.canvasLeft.draw()
			first_step += 1
			cache_num += 1
			if cache_num >5:
				self.window.draw_angel()
				cache_num = 1
			print (cache_num)
		#self.window.draw_direction()
		#self.window.Angel()
		#self.window.draw_angel()
		detection_state = 0	


		
class WorkerThread6(threading.Thread):     # 频谱查看功能中 画实时频谱动态图
	"""
	This just simulates some long-running task that periodically sends
	a message to the GUI thread.
	"""
	def __init__(self,threadNum,window,rsa_true,deviceSerial_true,span,t,anteid,start_freq,end_freq,rbw,vbw):
	#def __init__(self,threadNum,window):
		threading.Thread.__init__(self)
		self.threadNum = threadNum
		self.window = window
		self.rsa_true=rsa_true
		self.deviceSerial_true=deviceSerial_true
		self.span=span
		self.t=t
		self.anteid=anteid
		self.start_freq=start_freq
		self.end_freq=end_freq
		self.rbw=rbw
		self.vbw=vbw
		#print (type(rbw),rbw)
		#print (type(vbw),vbw)
		#self.q=q
		self.timeToQuit = threading.Event()
		self.timeToQuit.clear()
		self._running = True

	def stop(self):
		global detection_state
		print ('will be stopped')
		#self.timeToQuit.set()
		detection_state=0
		self._running = False

	def run(self):#运行一个线程
		global detection_state
		global longitude
		global latitude
		global height
		global start_spectrum_state
		global connect_change
		global simple_start_freq
		global simple_stop_freq
		global simple_rbw
		global has_rect
		global has_txt
		global lines
		global txts
		# 进行连接获得检测设备信息
		# print (average)
		# 参数设置
		# 获取并设置设置起始频率和终止频率
		self.window.list_ctrl.DeleteAllItems()  # 清空列表中的信号记录
		startFreq = c_double(float(self.start_freq))
		stopFreq = c_double(float(self.end_freq))
		# set span
		span = c_double(float(self.span))
		# # 设置rbw
		# rbw = c_double(float(self.rbw))
		# # 设置vbw
		# vbw = c_double(float(self.vbw))
		# 从别的数据库读取出所选用的天线类型
		# 设置step_size
		# step_size = c_double(float(input()))
		t = float(self.t)  # 持续时间
		time_ref = time.time()
		# 本次扫描的全部数据存储
		deviceSerial=self.deviceSerial_true
		anteid=self.anteid
		count = 0
		'''
		参数配置完之后就可以开始进行数据库的创建，之后具体信号的检测得到的数据在
		之后的程序中写入表中即可
		'''
		# 先建立主表即测试任务，起始时间，持续时间
		str_time = str(datetime.datetime.now().strftime('%F-%H-%M-%S'))  # 整个测试的起始的准确时间用于存储原始文件路径的因为路径中不能有：
		start_time = str(datetime.datetime.now().strftime('%F %H:%M:%S')) # 总表的起始时间
		end_time=(datetime.datetime.now() + datetime.timedelta(seconds=t)).strftime('%F %H:%M:%S')
		
		if longitude==-1:
			longitude_set = float(116.41)
			latitude_set = float(39.85)
			height_set = float(1)
		else:
			longitude_set= longitude
			latitude_set= latitude
			height_set = height
		# work_state=self.window.notebook.GetSelection() #0-月报检测  1-随机任务
		max_axis_value = -20  #设置坐标轴最大小值
		min_axis_value = -20
		num_signal = 1
		print ('Simple_watching thread running, work_state:',work_state)
		
		if lines and has_rect:
			for i in range(len(lines)):
				if lines[i]:
					lines[i][0].remove()
			has_rect = False
		if txts and has_txt:
			for j in range(len(txts)):
				txts[j].remove()
			has_txt = False
		lines=[]
		txts=[]
		# try:
		while time.time() - time_ref < t and self._running:
			average = method.detectNoise(self.rsa_true,self.start_freq,self.end_freq,self.rbw,self.vbw)
			#print ('#'*20)
			#print ('average:',average)
			count += 1
			str_tt1 = str(datetime.datetime.now().strftime('%F %H:%M:%S'))  # 内部扫频的时刻
			str_tt2 = str(datetime.datetime.now().strftime('%F-%H-%M-%S'))  # 作为内部细扫的文件名
			self.start_freq = simple_start_freq
			self.end_freq = simple_stop_freq
			self.rbw=simple_rbw    # add by vinson
			#spectrum1 = method.spectrum1(self.rsa_true,average, startFreq, stopFreq, span, self.rbw, self.vbw, str_time, count, str_tt1, str_tt2,longitude_set,latitude_set,num_signal,Sub_cf_all)
			spectrum1 = method.simple_spectrum(self.rsa_true,self.start_freq,self.end_freq,self.rbw,self.vbw)
			if spectrum1 != 0:
				freq1,traceData1= spectrum1
				
				#输出到底有多少信号
				if count % 100==0:
					print (count)
				# print(self.window.traceData[0:10])
				# self.window.l_user.set_xdata(self.window.freq)
				# self.window.l_user.set_ydata(self.window.traceData)
				if max(traceData1) > max_axis_value:
					max_axis_value = max(traceData1) + 5
				if min(traceData1) < min_axis_value:
					min_axis_value = average - 10
 
				self.window.axes_score.set_ylim(min_axis_value,max_axis_value)
				self.window.axes_score.set_xlim(freq1[0],freq1[-1])
				self.window.l_user.set_data(freq1,traceData1)
				self.window.axes_score.draw_artist(self.window.l_user)
				self.window.canvas.draw()
			else:
				self._running = False
				connect_change = 1
				wx.MessageBox(u"仪器连接不正常", "Message" ,wx.OK | wx.ICON_INFORMATION)
				self.window.m_button11.SetLabel(u"查看频谱")
				self.window.m_button11.SetValue(False)
				detection_state=0 #任务结束，监测状态归为0
				self.stop()
		# except:
			# #connect_change = 1
			# wx.MessageBox(u"频谱数据读取超时，任务结束！", "Warning" ,wx.OK | wx.ICON_INFORMATION)
			# self.window.m_button11.SetLabel(u"查看频谱")
			# self.window.m_button11.SetValue(False)
			# detection_state=0 #任务结束，监测状态归为0
			# return
		self.window.m_button11.SetLabel(u"查看频谱")
		self.window.m_button11.SetValue(False)
		detection_state=0 #任务结束，监测状态归为0
		print ('Specturm detection succeed')

		
###########################################################################
## Class MyPanel1 频谱回放和台站比对面板
###########################################################################

class MyPanel1 ( wx.Panel ):
	
	def __init__( self, parent ):
		wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 602,300 ), style = wx.TAB_TRAVERSAL )
		
		bSizer4 = wx.BoxSizer( wx.HORIZONTAL )
		
		bSizer5 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_staticline6 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer5.Add( self.m_staticline6, 0, wx.EXPAND |wx.ALL, 0 )
		
		##########################
		self.panelOne_one = MyPanel1_1(self)
		self.panelOne_two = MyPanel1_2(self)
		self.panelOne_two.Hide()

		
		#self.bSizer238 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer5.Add( self.panelOne_one, 13, wx.EXPAND |wx.ALL, 5 )
		bSizer5.Add( self.panelOne_two, 13, wx.EXPAND |wx.ALL, 5 )
		
		#bSizer5.Add( self.bSizer238, 3, wx.EXPAND, 0 )
		
		
		bSizer4.Add( bSizer5, 4, wx.EXPAND, 5 )
		
		self.m_staticline8 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_VERTICAL )
		bSizer4.Add( self.m_staticline8, 0, wx.EXPAND |wx.ALL, 0 )
		
		bSizer6 = wx.BoxSizer( wx.VERTICAL )
		
		self.bSizer19 = wx.BoxSizer( wx.VERTICAL )
		
		##############################################显示子信号列表
		self.bx1=wx.StaticBox( self, wx.ID_ANY, u"台站注册信号比对：" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		self.bx1.SetForegroundColour("SLATE BLUE")
		font = wx.Font(10, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bx1.SetFont(font)
		self.sbSizer35 = wx.StaticBoxSizer( self.bx1, wx.VERTICAL )
		self.list_ctrl = wx.ListCtrl(self, size=(-1,380),style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES|wx.BORDER_SUNKEN)
		self.list_ctrl.InsertColumn(0, 'ID',width=30)
		self.list_ctrl.InsertColumn(1, '频率/MHz',width=75)
		self.list_ctrl.InsertColumn(2, '带宽/MHz', width=80)
		self.list_ctrl.InsertColumn(3, '幅度/dBmV',width = 80)
		self.list_ctrl.InsertColumn(4, '业务类型', width=65)
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnClick_list, self.list_ctrl)
		
		self.sbSizer35.Add(self.list_ctrl,0,wx.ALL|wx.EXPAND,0)
		
		self.bSizer19.Add(self.sbSizer35,0,wx.ALL|wx.EXPAND,5)
		
		
		bSizer6.Add( self.bSizer19, 1, wx.EXPAND, 5 )
		
		self.m_staticline9 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer6.Add( self.m_staticline9, 0, wx.EXPAND|wx.ALL, 0 )
		
		self.bSizer20 = wx.BoxSizer( wx.VERTICAL )
		
		###############################################导入数据显示
		self.bx2=wx.StaticBox( self, wx.ID_ANY, u"历史数据导入信息" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		self.bx2.SetForegroundColour("SLATE BLUE")
		font = wx.Font(9, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bx2.SetFont(font)
		self.sbSizer3 = wx.StaticBoxSizer( self.bx2, wx.VERTICAL )
		
		self.m_choices1 = method.file_to_list(list(reversed(os.listdir(method.config_data['Spec_dir']))))
		self.choice_Num=len(self.m_choices1)
		self.m_combo2 = wx.ComboBox( self, wx.ID_ANY, u'请选择文件...',wx.DefaultPosition, (80,20), self.m_choices1, 0 )
		self.m_combo2.Bind(wx.EVT_COMBOBOX, self.OnCombo)
		self.task_name=0
		self.sbSizer3.Add(self.m_combo2,0,wx.ALL|wx.EXPAND,10)
		
		self.startSizer=wx.BoxSizer(wx.HORIZONTAL)
		self.m_button12 = wx.Button( self, wx.ID_ANY, u"频谱文件回放", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.startSizer.Add(self.m_button12,0,wx.ALL|wx.EXPAND,5)
		self.m_button13 = wx.Button(self,wx.ID_ANY,u"停止回放",wx.DefaultPosition,wx.DefaultSize,0)
		self.startSizer.Add(self.m_button13,0,wx.ALL|wx.EXPAND,5)
		self.m_button12.Bind( wx.EVT_BUTTON, self.data_import_show )
		self.m_button13.Bind( wx.EVT_BUTTON, self.stop_import_show )
		
		self.sbSizer3.Add(self.startSizer,0,wx.ALL|wx.EXPAND,10)
		
		self.bSizer20.Add( self.sbSizer3, 1, wx.ALL|wx.EXPAND, 8 )
		#################################################导入数据显示END
		
		#################################################经纬度显示
		self.bx3=wx.StaticBox( self, wx.ID_ANY, u"位置信息显示" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		self.bx3.SetForegroundColour("SLATE BLUE")
		font = wx.Font(9, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bx3.SetFont(font)
		self.sbSizer4 = wx.StaticBoxSizer( self.bx3, wx.VERTICAL )
		self.bSizer24=wx.BoxSizer(wx.VERTICAL)
		
		self.bSizer25=wx.BoxSizer(wx.HORIZONTAL)
		self.m_staticText21 = wx.StaticText( self, wx.ID_ANY, u"经度：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText21.Wrap( -1 )
		self.bSizer25.Add( self.m_staticText21, 0, wx.ALL, 5 )
		self.m_textCtrl4 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (80,20), 0 )
		self.bSizer25.Add( self.m_textCtrl4, 0, wx.ALL, 5 )
		#self.bSizer24.Add(self.bSizer25,1,wx.EXPAND,5)
		
		#bSizer26=wx.BoxSizer(wx.HORIZONTAL)
		self.m_staticText22 = wx.StaticText( self, wx.ID_ANY, u"纬度：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText22.Wrap( -1 )
		self.bSizer25.Add( self.m_staticText22, 0, wx.ALL, 5 )
		self.m_textCtrl5 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (80,20), 0 )
		self.bSizer25.Add( self.m_textCtrl5, 0, wx.ALL, 5 )
		self.bSizer24.Add(self.bSizer25,1,wx.EXPAND,5)
		
		self.bSizer27=wx.BoxSizer(wx.HORIZONTAL)
		self.m_staticText23 = wx.StaticText( self, wx.ID_ANY, u"高度：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText23.Wrap( -1 )
		self.bSizer27.Add( self.m_staticText23, 0, wx.ALL, 5 )
		self.m_textCtrl6 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (80,20), 0 )
		self.bSizer27.Add( self.m_textCtrl6, 0, wx.ALL, 5 )
		self.bSizer24.Add(self.bSizer27,1,wx.EXPAND,5)
		
		self.sbSizer4.Add(self.bSizer24,1,wx.EXPAND,5)
		self.bSizer20.Add( self.sbSizer4, 2, wx.ALL|wx.EXPAND, 8 )
		
		#####################################页面布局，加空白
		self.m_panel4 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.bSizer20.Add( self.m_panel4, 3, wx.EXPAND |wx.ALL, 5 )
		
		bSizer6.Add( self.bSizer20, 1, wx.EXPAND, 5 )
		
		bSizer4.Add( bSizer6, 2, wx.EXPAND, 5 )
		
		self.SetSizer( bSizer4 )
		
		self.Fit()
		
		self.threads3=[]
		
		#记录列表自频段的信息
		self.Sub_freq=[]
		self.Sub_Spectrum=[]
		self.lines = []
		self.txts =[]
		self.detail_information = [] #回放信号的具体信息
		self.point = [] #新号段的坐标信息
		self.label_information = []  #标注的信息文本
		
	def change_to_Spectrum(self):
		if self.panelOne_one.IsShown():
			pass
		else:
			self.panelOne_one.Show()
			self.panelOne_two.Hide()
		self.Layout()


	def change_to_sub_Spectrum(self):
		if self.panelOne_two.IsShown():
			pass
		else:
			self.panelOne_one.Hide()
			self.panelOne_two.Show()

		self.Layout()
	
	# 频谱数据回访，导入最后一帧合成的最大频谱数据，并回放频谱图
	def data_import_show(self,event):
		global detection_state
		global work_state
		if detection_state==0:
			if self.task_name !=0:
				self.point = []
				raw_path=method.config_data['Spec_dir']+'\\'+self.task_name
				file_all = os.listdir(raw_path)                #找出文件夹中所有数据文件
				map_maxSpectrum = lambda x:x[40:43]=='Max'
				file = list(filter(map_maxSpectrum,file_all))
				if len(file) != 0:
					file_name = file[0] #匹配出MaxSpectrum 文件
					#file_name=os.listdir(raw_path)[0][0:-4]
					print (raw_path,file_name)
					self.start_freq_cu,self.end_freq_cu,self.x_mat,self.y_mat,self.start_time_cu,self.end_time_cu,self.detail_information,self.point,self.label_information=method.importData_cu(self.task_name,file_name,raw_path)
					self.continue_time=(self.end_time_cu-self.start_time_cu).seconds
					self.list_ctrl.DeleteAllItems()
				################################
					work_state=0
					self.t3=WorkerThread3(self,self.start_freq_cu,self.end_freq_cu,self.x_mat,self.y_mat,self.continue_time,self.detail_information)
					self.threads3.append(self.t3)
					self.t3.start()
				else:
					wx.MessageBox(u'数据文件不存在！', "Message" ,wx.OK | wx.ICON_INFORMATION)
		else:
			wx.MessageBox(u'监测工作进行中，请停止监测任务后再试。', "Message" ,wx.OK | wx.ICON_INFORMATION)
	
	#数据导入显示
	def stop_import_show(self,event):
		while self.threads3:
			thread=self.threads3[0]
			thread.stop()
			self.threads3.remove(thread)
	
	#选择回放导入数据集
	def OnCombo(self,event):
		self.task_name=method.list_to_file(self.m_combo2.GetValue())
	
	#列表点击事件
	def OnClick_list(self,event):
		global has_rect
		global has_txt
		global work_state
		global lines
		global txts
		work_state = 1
		row=int(event.GetText())-1
		#去除最后一帧的框线
		
		if lines and  has_rect:
			for i in range(len(lines)):
				lines[i][0].remove()
			has_rect = False
		if txts and has_txt:
			for j in range(len(txts)):
				txts[j].remove()
			has_txt = False
		lines=[]
		txts=[]
		
		list_select_cf = float(self.list_ctrl.GetItemText(event.GetIndex(),1))*1e6
		list_select_peak = float(self.list_ctrl.GetItemText(event.GetIndex(),3))
		if self.panelOne_one.IsShown():
			self.panelOne_one.axes_score.set_xlim(self.Sub_freq[row][0],self.Sub_freq[row][-1])
			self.panelOne_one.l_user.set_data(self.Sub_freq[row],self.Sub_Spectrum[row])
			line = self.panelOne_one.axes_score.plot(list_select_cf,list_select_peak,'wD')
			lines.append(line)
			has_rect = True
			self.panelOne_one.axes_score.draw_artist(self.panelOne_one.l_user)
			self.panelOne_one.canvas.draw()
		else:
			self.panelOne_two.axes_score.set_xlim(self.Sub_freq[row][0],self.Sub_freq[row][-1])
			self.panelOne_two.l_user.set_data(self.Sub_freq[row],self.Sub_Spectrum[row])
			line = self.panelOne_two.axes_score.plot(list_select_cf,list_select_peak,'wD')
			lines.append(line)
			has_rect = True
			self.panelOne_two.axes_score.draw_artist(self.panelOne_two.l_user)
			self.panelOne_two.canvas.draw()


	###功能：鼠标移动到信号段框时，显示该信号段的各种信息

	def OnMove(self,evt):
		global has_txt
		global has_rect
		global mon_or_real
		global lines
		global txts
		pos = evt.GetPosition()
		#print (pos,self.point)
		if self.point:
			for i in range(len(self.point)):
				# print ('#'*10,'point','#'*10)
				#print (pos)
				#print (self.point)
				# print ('#'*20)
				if pos.x>=self.point[i][0] and pos.x<=self.point[i][1] and pos.y>=self.point[i][2] and pos.y<=self.point[i][3]:
					# print ('hahahahahahaahaha')
					#清除之前的显示文本
					if lines and  has_rect:
						for i in range(len(lines)):
							lines[i][0].remove()
						has_rect = False
					if txts and has_txt:
						for j in range(len(txts)):
							txts[j].remove()
						has_txt = False
					lines=[]
					txts=[]
					#显示当前鼠标所在的文本
					if mon_or_real ==1:
						txt = self.panelOne_one.axes_score.text(self.detail_information[i][1],self.detail_information[i][2],self.label_information[i],fontsize=7,color='r')
						txts.append(txt)
						self.panelOne_one.canvas.draw()
						has_txt = True
					# else:
						# txt = self.panelOne_two.axes_score.text(self.detail_information[i][1],self.detail_information[i][2],self.label_information[i],fontsize=7,color='r')
						# txts.append(txt)
						# self.panelOne_two.canvas.draw()
						# has_txt = True


###########################################################################
## Class Wait_GPS GPSGPS获取信息等待
###########################################################################
class Wait_GPS (wx.Dialog):
	def __init__( self, parent,title=u"GPS信息获取" ):
		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = title, pos = wx.DefaultPosition, size = wx.Size( 300,200 ), style = wx.CAPTION)
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		self.count=0
		self.count1=0
		vbox = wx.BoxSizer(wx.VERTICAL)
		
		hbox0 = wx.BoxSizer(wx.HORIZONTAL)
		self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, u"\n正在获取GPS信息中,\n        请稍等........", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )
		font2 = wx.Font(10, wx.ROMAN,wx.NORMAL, wx.BOLD)
		self.m_staticText1.SetFont(font2)
		self.m_staticText1.SetForegroundColour("TAN")
		hbox0.Add( self.m_staticText1, 1, wx.ALL|wx.ALIGN_CENTRE, 0 )
		
		hbox1 = wx.BoxSizer(wx.HORIZONTAL) 
		self.gause_range=1e5
		self.gauge = wx.Gauge(self, range = self.gause_range, size = (250, 25), style =  wx.GA_HORIZONTAL) 
		hbox1.Add(self.gauge, proportion = 1, flag = wx.ALIGN_CENTRE)
		
		hbox2 = wx.BoxSizer(wx.HORIZONTAL)
		#self.btn1 = wx.Button(self, label = "Start") 
		#self.Bind(wx.EVT_BUTTON, self.OnStart, self.btn1) 
		
		self.button1 = wx.Button( self, wx.ID_OK, "OK", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.button2 = wx.Button( self, wx.ID_ANY, "Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.Bind(wx.EVT_BUTTON,self.OnStop,self.button2)
		
		 
		#hbox2.Add(self.btn1, proportion = 1, flag = wx.RIGHT, border = 5) 
		hbox2.Add( self.button1, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )
		hbox2.Add( self.button2, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )
		self.button1.Enable(False)
		self.button2.Enable(True)
		
		vbox.Add((30, 0))
		vbox.Add(hbox0,1,wx.ALIGN_CENTRE)
		vbox.Add((0, 30))  #添加空白
		vbox.Add(hbox1, 3, flag = wx.ALIGN_CENTRE) 
		vbox.Add((0, 20)) 
		vbox.Add(hbox2, proportion = 2, flag = wx.ALIGN_CENTRE)
		
		self.SetSizer(vbox)
		self.Centre()
		self.threads4=[]
		self.GPS_wait=False  #是否用完等待时间
		self.GPS_state=False #是否获取到了GPS信号
		self.GPS_end=False   #是否结束搜寻GPS信号 
		self.location=[-1,-1,-1]
		
	def OnStart(self):
		########################用多线程
		print ("get into Wait_GPS")
		t4=WorkerThread4(self,self.count,self.gause_range)
		self.threads4.append(t4)
		t4.start()
		# print ('wait 10s')
		tn=threading.Thread(target=self.get_GPS2,args=(rsa_true,))
		tn.start()
		print ('Start getting GPS data')

	def OnStop(self,event):
		########################用多线程
		print ("get out of Wait_GPS")
		global GPS_end
		if self.count1!=self.gause_range:
			GPS_end=True
			while self.threads4:
				thread=self.threads4[0]
				thread.stop()
				self.threads4.remove(thread)
			self.Destroy()
		else:
			self.Destroy()
	
	def get_GPS2(self,rsa):
		try:
			eventID = c_int(1)  # 0:overrange, 1:ext trig, 2:1PPS
			eventOccurred = c_bool(False)
			eventTimestamp = c_uint64(0)
			hwInstalled = c_bool(False)

			"""#################SEARCH/CONNECT#################"""
			hwInstalled = self.setup_gnss(rsa)

			"""#################CONFIGURE INSTRUMENT#################"""
			rsa.CONFIG_Preset()

			rsa.DEVICE_Run()

			if hwInstalled == True:
				"""#######USE THIS IF YOU HAVE AN RSA500/600 WITH GPS ANTENNA########"""
				print('Waiting for internal 1PPS.')
				while eventOccurred.value == False:
					rsa.GNSS_Get1PPSTimestamp(byref(eventOccurred), byref(eventTimestamp))
				nmeaMessage = self.get_gnss_message(rsa)
				self.location=nmeaMessage
				print("nmeaMessage in get_GPS2:")
				print(nmeaMessage)
				return nmeaMessage
			else:
				"""#######USE THIS IF YOU HAVE AN RSA306 W/1PPS INPUT########"""
				print('Waiting for external 1PPS.')
				# while eventOccurred.value == False:
					# rsa.DEVICE_GetEventStatus(eventID, byref(eventOccurred), byref(eventTimestamp))
				self.location=[-1,-1,-1]
				return [-1,-1,-1]
		except:
			wx.MessageBox(u'GPS获取出错，请检查仪器连接！', "Message" ,wx.OK | wx.ICON_INFORMATION)

		'''
		rsa.DEVICE_Stop()
		print('Disconnecting.')
		ret = rsa.DEVICE_Disconnect()
		'''


	def setup_gnss(self, rsa, system=2):
		global GPS_end
		self.GPS_end=GPS_end
		# setup variables
		enable = c_bool(True)
		powered = c_bool(True)
		installed = c_bool(False)
		locked = c_bool(False)#############
		msgLength = c_int(0)
		message = c_char_p(b'')
		# 1:GPS/GLONASS, 2:GPS/BEIDOU, 3:GPS, 4:GLONASS, 5:BEIDOU
		satSystem = c_int(system)

		# check for GNSS hardware
		rsa.GNSS_GetHwInstalled(byref(installed))
		if installed.value != True:
			print('No GNSS hardware installed, ensure there is a 1PPS signal present at the trigger/synch input.')
			return False # add by vinson
			#input('Press ''ENTER'' to continue > ')
		else:
			# send setup commands to RSA
			rsa.GNSS_SetEnable(enable)
			rsa.GNSS_SetAntennaPower(powered)
			rsa.GNSS_SetSatSystem(satSystem)
			rsa.GNSS_GetEnable(byref(enable))
			rsa.GNSS_GetAntennaPower(byref(powered))
			rsa.GNSS_GetSatSystem(byref(satSystem))

		print('Waiting for GNSS lock.')
		waiti=0;
		while locked.value != True and not self.GPS_end:
			waiti+=1;
			if waiti%1000000==0:
				print (waiti)
			rsa.GNSS_GetStatusRxLock(byref(locked))
			self.GPS_end=GPS_end
		if self.GPS_end:
			return False
		else:
			print('GNSS locked.')
			return installed.value

	def get_gnss_message(self,rsa):
		msgLength = c_int(0)
		message = c_char_p(b'')
		numMessages = 100
		#gnssMessage = []
		nmeaMessages = []
		data1=''
		#data1.encode('utf-8')

		# grab a certain number of GNSS message strings
		for i in range(numMessages):
			time.sleep(.25)
			rsa.GNSS_GetNavMessageData(byref(msgLength), byref(message))
			# concatenate the new string
			
			#gnssMessage += message.value
			print ('H'*20)
			print(type(message.value))
			try:
				data1=data1+message.value.decode('cp1252')
			except TypeError as e:
				print ('X'*30)
				
			#print (message.value)
		print (data1)
		dataString=''.join(map(str,data1));
		datalist=dataString.split('$')
		print ('start')
		[longitude,latitude,height]=[-1,-1,-1]
		for i in range(len(datalist)): 
			if 'GNGGA' in datalist[i]:
				data=datalist[i].split(',')
				print ('@'*20)
				print (data)
				print (len(data))
				if len(data)>=10:
					if data[2]!='' and data[4]!='' and data[9]!='':
						# modified by vinson , seems mistake long with lat
						#longitude=float(str(data[2])[0:2])+float(str(data[2])[2:])/60
						#latitude=float(str(data[4])[0:3])+float(str(data[4])[3:])/60    
						latitude=float(str(data[2])[0:2])+float(str(data[2])[2:])/60
						longitude=float(str(data[4])[0:3])+float(str(data[4])[3:])/60
						height=float(data[9])
						print("location information in get_gnss_message:")
						print (longitude,latitude,height)
						break;
		return [longitude,latitude,height]

###########################################################################
## Class MyPanel1_1 自定义监测面板
###########################################################################
class MyPanel1_1 ( wx.Panel ):
	
	def __init__( self, parent ):
	
		wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 602,300 ), style = wx.TAB_TRAVERSAL )
		
		bSizer4 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticline6 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer4.Add( self.m_staticline6, 0, wx.EXPAND |wx.ALL, 0 )
		
		############# axes
		bSizer37 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer8 = wx.BoxSizer( wx.VERTICAL )

		
		#bSizer83 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_panel2 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		
		
		bSizer8.Add( self.m_panel2, 0, wx.EXPAND |wx.ALL, 0 )
		

		###########################################画图后的CF Span 显示bSizer84
		
		bSizer37.Add( bSizer8, 7, wx.EXPAND, 0 )
		

		self.panel2=wx.Panel(self)
		##################################################################################设置参数
		bSizer44 = wx.BoxSizer( wx.HORIZONTAL )
		
		bx1=wx.StaticBox( self.panel2, wx.ID_ANY, u"自定义监测" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		bx1.SetForegroundColour("SLATE BLUE")
		font = wx.Font(10, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		bx1.SetFont(font)
		sbSizer1 = wx.StaticBoxSizer(bx1, wx.VERTICAL )
		
		bSizer10 = wx.BoxSizer( wx.HORIZONTAL )
		
		bSizer11 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer13 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText3 = wx.StaticText( self.panel2, wx.ID_ANY, u"起始频率：", wx.DefaultPosition, wx.DefaultSize, 0 )
		#self.m_staticText3.Wrap( -1 )
		#self.m_staticText3.SetFont( wx.Font( 12, 70, 90, wx.BOLD, False, "宋体" ) )
		bSizer13.Add( self.m_staticText3, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		default_start_freq = str(config_data['start_freq'])
		self.m_textCtrl1 = wx.TextCtrl( self.panel2, wx.ID_ANY, default_start_freq, wx.DefaultPosition, (80,20) , wx.TE_PROCESS_ENTER )
		self.Bind(wx.EVT_TEXT_ENTER, self.change_startFreq, self.m_textCtrl1)
		self.m_textCtrl1.Bind(wx.EVT_KILL_FOCUS,self.change_startFreq)
		bSizer13.Add( self.m_textCtrl1, 0, wx.ALL|wx.ALIGN_CENTRE, 0 )
		
		m_choice1Choices = ['KHz','MHz','GHz']
		self.m_choice1 = wx.Choice( self.panel2, wx.ID_ANY, wx.DefaultPosition, (50,20), m_choice1Choices, 0 )
		self.m_choice1.SetSelection( 1 )
		bSizer13.Add( self.m_choice1, 0, wx.ALL|wx.ALIGN_CENTRE, 2 )
		self.m_choice1.Bind(wx.EVT_CHOICE,self.OnChangeStartFreUnit)
		
		bSizer11.Add( bSizer13, 1, wx.EXPAND, 0 )
		
		bSizer14 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText4 = wx.StaticText( self.panel2, wx.ID_ANY, u"终止频率：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText4.Wrap( -1 )
		bSizer14.Add( self.m_staticText4, 0, wx.ALIGN_CENTER|wx.ALL, 5 )
		
		default_end_freq = str(config_data['end_freq'])
		self.m_textCtrl2 = wx.TextCtrl( self.panel2, wx.ID_ANY, default_end_freq, wx.DefaultPosition, (80,20) , wx.TE_PROCESS_ENTER)
		self.Bind(wx.EVT_TEXT_ENTER, self.change_stopFreq, self.m_textCtrl2)
		self.m_textCtrl2.Bind(wx.EVT_KILL_FOCUS, self.change_stopFreq)
		bSizer14.Add( self.m_textCtrl2, 0, wx.ALIGN_CENTER|wx.ALL, 0 )
		
		m_choice2Choices = ['KHz','MHz','GHz',]
		self.m_choice2 = wx.Choice( self.panel2, wx.ID_ANY, wx.DefaultPosition, (50,20), m_choice2Choices, 0 )
		self.m_choice2.SetSelection( 1 )
		bSizer14.Add( self.m_choice2, 0, wx.ALIGN_CENTER|wx.ALL, 2 )
		self.m_choice2.Bind(wx.EVT_CHOICE,self.OnChangeStopFreUnit)
		
		
		bSizer11.Add( bSizer14, 1, wx.EXPAND, 0 )
		
		bSizer10.Add( bSizer11, 3, wx.EXPAND, 0 )
		

		
		bSizer27 = wx.BoxSizer( wx.VERTICAL )

		bSizer29 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText10 = wx.StaticText( self.panel2, wx.ID_ANY, u" 监测时长： ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText10.Wrap( -1 )
		bSizer29.Add( self.m_staticText10, 0, wx.ALIGN_CENTER|wx.ALL, 0 )
		
		self.m_tc_MonitorTime = wx.TextCtrl( self.panel2, wx.ID_ANY, '1', wx.DefaultPosition, (80,20), 0 )
		bSizer29.Add( self.m_tc_MonitorTime, 0, wx.ALIGN_CENTER|wx.ALL, 0 )
		
		self.m_staticText11 = wx.StaticText( self.panel2, wx.ID_ANY, u"小时", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText11.Wrap( -1 )
		bSizer29.Add( self.m_staticText11, 0, wx.ALIGN_CENTER|wx.ALL, 2 )
		
		
		bSizer27.Add( bSizer29, 1, wx.EXPAND, 0 )
		
		bSizer30 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText5 = wx.StaticText( self.panel2, wx.ID_ANY, u"  RBW    :   ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText5.Wrap( -1 )
		self.m_staticText5.SetFont( wx.Font( 9, 70, 90, 92, False, "@华文楷体" ) ) #@表示文字竖着写
		bSizer30.Add( self.m_staticText5, 0, wx.ALIGN_CENTER|wx.ALL, 5 )
        
		# textctrl box for RBW configuration in simple_watching
		default_rbw = str(config_data['RBW'])
		self.m_textCtrl3 = wx.TextCtrl( self.panel2, wx.ID_ANY, default_rbw, wx.DefaultPosition, (80,20), wx.TE_PROCESS_ENTER )
		self.m_textCtrl3.Bind(wx.EVT_TEXT_ENTER, self.OnChange_RBW)
		self.m_textCtrl3.Bind(wx.EVT_KILL_FOCUS,self.OnChange_RBW)
		bSizer30.Add( self.m_textCtrl3, 0, wx.ALIGN_CENTER|wx.ALL, 0 )
        
		m_choice3Choices = ['KHz','MHz']
		self.m_choice3 = wx.Choice( self.panel2, wx.ID_ANY, wx.DefaultPosition, (50,20), m_choice3Choices, 0 )
		self.m_choice3.SetSelection( 0 )
		bSizer30.Add( self.m_choice3, 0, wx.ALIGN_CENTER|wx.ALL, 2 )
		self.m_choice3.Bind(wx.EVT_CHOICE,self.OnChangeRBWUnit)
		
		
		bSizer27.Add( bSizer30, 1, wx.EXPAND, 0 )
		
		
		bSizer10.Add( bSizer27, 3, wx.EXPAND, 0 )
		
		
		sbSizer1.Add( bSizer10, 1, wx.EXPAND, 5 )
		
		bSizer44.Add(sbSizer1, 3 ,wx.EXPAND, 0)
		
		bSizer26 = wx.BoxSizer( wx.VERTICAL )
		# self.m_panel5 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		# bSizer26.Add( self.m_panel5, 1, wx.EXPAND |wx.ALL, 0 )
		
		
		self.m_button11 = wx.ToggleButton( self.panel2, wx.ID_ANY, u"查看频谱", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer26.Add( self.m_button11, 1, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND|wx.BOTTOM, 2 )
		self.m_button11.Bind(wx.EVT_TOGGLEBUTTON,self.Simple_Watching)
		self.m_button11.SetFont( wx.Font( 12, 70, 90, wx.BOLD, False, "华文楷体" ) )

		self.m_button10 = wx.ToggleButton( self.panel2, wx.ID_ANY, u"开始监测", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_button10.Bind(wx.EVT_PAINT, self.highlight_button)
		bSizer26.Add( self.m_button10, 1, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND|wx.BOTTOM, 2 )
		self.m_button10.Bind(wx.EVT_TOGGLEBUTTON,self.Start_Detect)
		self.m_button10.SetFont( wx.Font( 12, 70, 90, wx.BOLD, False, "华文楷体" ) )
		
		bSizer44.Add( bSizer26, 1, wx.EXPAND, 0)
		
		
		self.panel2.SetSizer(bSizer44)
		#############################################################################设置模式1参数END

		################################新加
		# read start_freq
		start_freq=self.m_textCtrl1.GetValue()
		self.m_choice1_string=self.m_choice1.GetString(self.m_choice1.GetSelection())
		if start_freq.strip()=='' or float(start_freq)<0:
			#print (config_data)
			start_freq=config_data['start_freq']
		else:
			try:
				start_freq=float(start_freq)
				if self.m_choice1_string=='GHz':
					start_freq=start_freq*(10**3)
				if self.m_choice1_string=='KHz':
					start_freq=start_freq/(10**3)
			except (ValueError,TypeError) as e:
				start_freq=config_data['start_freq']
				wx.MessageBox(u' 初始频率输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
		start_freq=start_freq*1e6
		if start_freq>6.2e9:
			start_freq = config_data['start_freq']
		elif start_freq<9e3:
			start_freq = 9e3
		if self.m_choice1_string=='GHz':
			self.m_textCtrl1.SetValue(str(start_freq/(10**9)))
		elif self.m_choice1_string=='KHz':
			self.m_textCtrl1.SetValue(str(start_freq/(10**3)))
		else:
			self.m_textCtrl1.SetValue(str(start_freq/1e6))
			
		#read end_freq
		end_freq=self.m_textCtrl2.GetValue()
		self.m_choice2_string=self.m_choice2.GetString(self.m_choice2.GetSelection())
		if end_freq.strip()=='' or float(end_freq)<0:
			end_freq=config_data['end_freq']
		else:
			try:
				end_freq=float(end_freq)
				if self.m_choice2_string=='GHz':
					end_freq=end_freq*(10**3)
				if self.m_choice2_string=='KHz':
					end_freq=end_freq/(10**3)
			except (ValueError,TypeError) as e:
				end_freq=config_data['end_freq']
				wx.MessageBox(u' 终止频率输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
		end_freq=end_freq*1e6
		if end_freq<9e3:
			end_freq = config_data['end_freq']
		elif end_freq>6.2e9:
			end_freq = 6.2e9
		if self.m_choice2_string=='GHz':
			self.m_textCtrl2.SetValue(str(end_freq/(10**9)))
		elif self.m_choice2_string=='KHz':
			self.m_textCtrl2.SetValue(str(end_freq/(10**3)))
		else:
			self.m_textCtrl2.SetValue(str(end_freq/1e6))
		#################################
		## 尝试一种新的画图方法
		self.figure_score = Figure((7.3,4.8),100)
		
		self.canvas = FigureCanvas(self.m_panel2, wx.ID_ANY, self.figure_score)
		#print (self.m_panel2.GetPosition())
		#print (self.canvas.GetPosition())
		self.canvas.Bind(wx.EVT_MOTION,self.OnMove)
		# self.figure_score.set_figheight(4)
		# self.figure_score.set_figwidth(6)
		self.axes_score = self.figure_score.add_subplot(111,facecolor='k')
		#self.axes_score.set_autoscale_on(False) #关闭坐标轴自动缩放
		self.traceData=[-100]*801
		self.freq=range(int(start_freq),int(end_freq)+int((end_freq-start_freq)/800),int((end_freq-start_freq)/800))
		self.l_user,=self.axes_score.plot(self.freq, self.traceData, 'y')
		#self.axes_score.axhline(y=average, color='r')
		self.axes_score.set_ylim(-80,0)
		self.axes_score.set_xlim(config_data['start_freq']*1e6,config_data['end_freq']*1e6)
		self.axes_score.set_title('Spectrum')
		self.axes_score.grid(True,color='dimgray')
		self.axes_score.set_xlabel('Frequency/Hz')
		self.axes_score.set_ylabel('Amplitude/dBmV')
		self.canvas.draw()
		
		bSizer37.Add(self.panel2, 2, wx.EXPAND, 0 )
		
		bSizer4.Add( bSizer37, 4, wx.EXPAND, 5 )
		
		self.m_staticline8 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_VERTICAL )
		bSizer4.Add( self.m_staticline8, 0, wx.EXPAND |wx.ALL, 0 )
		
		##################################################################################################
		##################  add list_table_infos
		##################################################################################################
		bSizer6 = wx.BoxSizer( wx.VERTICAL )
		
		self.bSizer19 = wx.BoxSizer( wx.VERTICAL )
		
		##############################################显示子信号列表
		self.bx1=wx.StaticBox( self, wx.ID_ANY, u"台站注册信号比对：" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		self.bx1.SetForegroundColour("SLATE BLUE")
		font = wx.Font(10, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bx1.SetFont(font)
		self.sbSizer35 = wx.StaticBoxSizer( self.bx1, wx.VERTICAL )
		self.list_ctrl = wx.ListCtrl(self, size=(-1,380),style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES|wx.BORDER_SUNKEN)
		self.list_ctrl.InsertColumn(0, 'ID',width=30)
		self.list_ctrl.InsertColumn(1, '频率/MHz',width=75)
		self.list_ctrl.InsertColumn(2, '带宽/MHz', width=80)
		self.list_ctrl.InsertColumn(3, '幅度/dBmV',width = 80)
		self.list_ctrl.InsertColumn(4, '业务类型', width=65)
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnClick_list, self.list_ctrl)
		
		self.sbSizer35.Add(self.list_ctrl,0,wx.ALL|wx.EXPAND,0)
		
		self.bSizer19.Add(self.sbSizer35,0,wx.ALL|wx.EXPAND,5)
		
		
		bSizer6.Add( self.bSizer19, 1, wx.EXPAND, 5 )
		
		self.m_staticline9 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer6.Add( self.m_staticline9, 0, wx.EXPAND|wx.ALL, 0 )
		
		self.bSizer20 = wx.BoxSizer( wx.VERTICAL )
		
		###############################################导入数据显示
		self.bx2=wx.StaticBox( self, wx.ID_ANY, u"历史数据导入信息" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		self.bx2.SetForegroundColour("SLATE BLUE")
		font = wx.Font(9, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bx2.SetFont(font)
		self.sbSizer3 = wx.StaticBoxSizer( self.bx2, wx.VERTICAL )
		
		self.m_choices1 = method.file_to_list(list(reversed(os.listdir(method.config_data['Spec_dir']))))
		self.choice_Num=len(self.m_choices1)
		self.m_combo2 = wx.ComboBox( self, wx.ID_ANY, u'请选择文件...',wx.DefaultPosition, (80,20), self.m_choices1, 0 )
		self.m_combo2.Bind(wx.EVT_COMBOBOX, self.OnCombo)
		self.task_name=0
		self.sbSizer3.Add(self.m_combo2,0,wx.ALL|wx.EXPAND,10)
		
		self.startSizer=wx.BoxSizer(wx.HORIZONTAL)
		self.m_button12 = wx.Button( self, wx.ID_ANY, u"频谱文件回放", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.startSizer.Add(self.m_button12,0,wx.ALL|wx.EXPAND,5)
		self.m_button13 = wx.Button(self,wx.ID_ANY,u"停止回放",wx.DefaultPosition,wx.DefaultSize,0)
		self.startSizer.Add(self.m_button13,0,wx.ALL|wx.EXPAND,5)
		self.m_button12.Bind( wx.EVT_BUTTON, self.data_import_show )
		self.m_button13.Bind( wx.EVT_BUTTON, self.stop_import_show )
		
		self.sbSizer3.Add(self.startSizer,0,wx.ALL|wx.EXPAND,10)
		
		self.bSizer20.Add( self.sbSizer3, 1, wx.ALL|wx.EXPAND, 8 )
		#################################################导入数据显示END
		
		#################################################经纬度显示
		self.bx3=wx.StaticBox( self, wx.ID_ANY, u"位置信息显示" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		self.bx3.SetForegroundColour("SLATE BLUE")
		font = wx.Font(9, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bx3.SetFont(font)
		self.sbSizer4 = wx.StaticBoxSizer( self.bx3, wx.VERTICAL )
		self.bSizer24=wx.BoxSizer(wx.VERTICAL)
		
		self.bSizer25=wx.BoxSizer(wx.HORIZONTAL)
		self.m_staticText21 = wx.StaticText( self, wx.ID_ANY, u"经度：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText21.Wrap( -1 )
		self.bSizer25.Add( self.m_staticText21, 0, wx.ALL, 5 )
		self.m_textCtrl4 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (80,20), 0 )
		self.bSizer25.Add( self.m_textCtrl4, 0, wx.ALL, 5 )
		#self.bSizer24.Add(self.bSizer25,1,wx.EXPAND,5)
		
		#bSizer26=wx.BoxSizer(wx.HORIZONTAL)
		self.m_staticText22 = wx.StaticText( self, wx.ID_ANY, u"纬度：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText22.Wrap( -1 )
		self.bSizer25.Add( self.m_staticText22, 0, wx.ALL, 5 )
		self.m_textCtrl5 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (80,20), 0 )
		self.bSizer25.Add( self.m_textCtrl5, 0, wx.ALL, 5 )
		self.bSizer24.Add(self.bSizer25,1,wx.EXPAND,5)
		
		self.list_bSizer27=wx.BoxSizer(wx.HORIZONTAL)
		self.m_staticText23 = wx.StaticText( self, wx.ID_ANY, u"高度：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText23.Wrap( -1 )
		self.list_bSizer27.Add( self.m_staticText23, 0, wx.ALL, 5 )
		self.m_textCtrl6 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (80,20), 0 )
		self.list_bSizer27.Add( self.m_textCtrl6, 0, wx.ALL, 5 )
		self.bSizer24.Add(self.list_bSizer27,1,wx.EXPAND,5)
		
		self.sbSizer4.Add(self.bSizer24,1,wx.EXPAND,5)
		self.bSizer20.Add( self.sbSizer4, 2, wx.ALL|wx.EXPAND, 8 )
		
		#####################################页面布局，加空白
		self.m_panel4 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.bSizer20.Add( self.m_panel4, 3, wx.EXPAND |wx.ALL, 5 )
		
		bSizer6.Add( self.bSizer20, 1, wx.EXPAND, 5 )
		
		bSizer4.Add( bSizer6, 2, wx.EXPAND, 5 )

		self.SetSizer( bSizer4 )
		self.count=0
		self.threads = []
		self.threads2 = []
		self.threads3 = []
		
		#记录整次扫描存在的有效（有不同频谱）的信息
		self.Sub_Spectrum=[]
		self.Sub_Spectrum2=[]
		self.Sub_cf_all=[]
		self.Sub_band_all=[]
		self.Sub_peak_all=[]
		
		#记录单帧扫描的基本信息
		self.Sub_cf_channel=[]
		self.Sub_span=[]
		self.Sub_cf=[]
		self.Sub_band=[]
		self.Sub_peak=[]
		
		#画方框的集合
		#self.point=[[307,307+53,202,202+154/3]]
		
		#记录列表自频段的信息
		self.Sub_freq=[]
		self.lines = []
		self.txts =[]
		self.detail_information = [] #回放信号的具体信息
		self.point = [] #新号段的坐标信息
		self.label_information = []  #标注的信息文本

	def Spectrum_Detect(self):
		global start_spectrum_state
		state = event.GetEventObject().GetValue()
		start_spectrum_state = not state
		if state == True:
			event.GetEventObject().SetLabel(u"停止监测")
			event.GetEventObject().SetValue(True)
			self.Start_Detect()
		else:
			event.GetEventObject().SetLabel(u"开始监测")
			event.GetEventObject().SetValue(False)
			self.Stop_Detect1()
	
	def Start_Detect(self,event):
		global uav_state
		global continue_time
		global detection_state
		global GPS_end
		global work_state
		global start_spectrum_state
		global simple_start_freq
		global simple_stop_freq
		global longitude
		global latitude
		global height
		# work_state = 1
		
		GPS_end=False
		if work_state==1:
			if connect_state==0:
				wx.MessageBox(u'仪表未连接！.', "Error" ,wx.OK | wx.ICON_ERROR)
			else:
				state = event.GetEventObject().GetValue()
				start_spectrum_state = not state
				if state == True:
					if detection_state==0:
						try:
							# 读取输入的数值参数并判断是否符合要求，若不符合则弹窗报错，并退出
							start_freq=self.m_textCtrl1.GetValue()
							self.m_choice1_string=self.m_choice1.GetString(self.m_choice1.GetSelection())
							if start_freq.strip()=='' or float(start_freq)<0:
								#print (config_data)
								start_freq=config_data['start_freq']
							else:
								try:
									start_freq=float(start_freq)
									if self.m_choice1_string=='GHz':
										start_freq=start_freq*(10**3)
									if self.m_choice1_string=='KHz':
										start_freq=start_freq/(10**3)
								except (ValueError,TypeError) as e:
									start_freq=config_data['start_freq']
									wx.MessageBox(u' 初始频率输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
							if start_freq>6.2e3:
								wx.MessageBox(u'起始频率设置超出仪表测量范围','Message',wx.OK)
								return
							elif start_freq<9e-3:
								wx.MessageBox(u'起始频率设置超出仪表测量范围','Message',wx.OK)
								return
							start_freq=start_freq*1e6

							# #print ('start_freq(MHz):',start_freq)
							# #read end_freq
							end_freq=self.m_textCtrl2.GetValue()
							self.m_choice2_string=self.m_choice2.GetString(self.m_choice2.GetSelection())
							if end_freq.strip()=='' or float(end_freq)<0:
								end_freq=config_data['end_freq']
							else:
								try:
									end_freq=float(end_freq)
									if self.m_choice2_string=='GHz':
										end_freq=end_freq*(10**3)
									if self.m_choice2_string=='KHz':
										end_freq=end_freq/(10**3)
								except (ValueError,TypeError) as e:
									end_freq=config_data['end_freq']
									wx.MessageBox(u' 终止频率输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
							if end_freq<9e-3:
								wx.MessageBox(u'终止频率设置超出仪表测量范围','Message',wx.OK)
								return
							elif end_freq>6.2e3:
								wx.MessageBox(u'终止频率设置超出仪表测量范围','Message',wx.OK)
								return
							end_freq=end_freq*1e6
							span=end_freq-start_freq
							# print (start_freq)
							# print (end_freq)
							# print (span)
							if span <=0:
								#event.GetEventObject().SetValue(not state)
								wx.MessageBox(u' 终止频率应大于起始频率', "Message" ,wx.OK | wx.ICON_INFORMATION)
								return 
							
							#read rbw
							rbw=self.m_textCtrl3.GetValue()
							self.m_choice3_string=self.m_choice3.GetString(self.m_choice3.GetSelection())
							if rbw.strip()=='' or float(rbw)<0:
								#rbw=config_data['RBW']
								wx.MessageBox(u' RBW设置错误！', "Warning" ,wx.OK | wx.ICON_INFORMATION)
								return 
							else:
								try:
									rbw=float(rbw)
									if self.m_choice3_string=='MHz':
										rbw=rbw*(10**3)
								except (ValueError,TypeError) as e:
									# rbw=config_data['RBW']
									wx.MessageBox(u' RBW输入需大于零的数值！', "Message" ,wx.OK | wx.ICON_INFORMATION)
									return
							rbw=rbw*1e3
							if rbw<1e2:
								rbw=100
							elif rbw>1e8:
								rbw=1e8
							simple_rbw=rbw
							if self.m_choice3_string=='MHz':
								self.m_textCtrl3.SetValue(str(rbw/1e6))
							else:
								self.m_textCtrl3.SetValue(str(rbw/1e3))
							
							#read vbw
							vbw=config_data['VBW']
							vbw=vbw*1e3
							
							#read time
							t=self.m_tc_MonitorTime.GetValue()
							if t.strip()=='' or float(t)<0:
								wx.MessageBox(u' 监测时长设置有误，请输入大于零的数值！', "Message" ,wx.OK | wx.ICON_INFORMATION)
								return
							else:
								try:
									t=float(t)
								except (ValueError,TypeError) as e:
									# t=0.01
									wx.MessageBox(u' 时间输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
									return
							# self.m_textCtrl5.SetValue(str(t))
							t=t*3600
							continue_time=t
							# 完成输入格式检查
							
                        # Achieve GPS location information.
							a = Wait_GPS(self)
							a.OnStart()
							 #while not a.GPS_end:
							if a.ShowModal()==wx.ID_OK:
								if a.GPS_state:
									#print("1962 GPS_state = "+str(a.GPS_state))
									longitude=a.location[0]
									latitude = a.location[1]
									height = a.location[2]
									self.m_textCtrl4.SetValue(str(a.location[0])[0:6])
									self.m_textCtrl5.SetValue(str(a.location[1])[0:6])
									self.m_textCtrl6.SetValue(str(a.location[2])[0:6]+' m')
									# method.freq_info = method.get_freq_range([112.54,37.84,2],method.threshold)
									method.freq_info = method.get_freq_range(a.location,method.threshold)

									##########################################################自定义监测
									# read start_freq

									event.GetEventObject().SetLabel(u"停止监测")


									#Set center_freq and span
									#self.m_textCtrl11.SetValue(str((start_freq+end_freq)/(2e6))+'MHz')
									#self.m_textCtrl12.SetValue(str(span/(1e6))+'MHz')
									
									#read step_size
									#Set step_size=span/801
									'''
									step_size=span/801
									self.m_choice8_string=self.m_choice8.GetString(self.m_choice8.GetSelection())
									if self.m_choice8_string=='GHz':
										step_size=step_size/(10**9)
									elif self.m_choice8_string=='KHz':
										step_size=step_size/(10**3)
									else:
										step_size=step_size/(10**6)
									self.m_textCtrl10.SetValue(str(step_size))
									'''
									#read Antenna_number
									#anteid=config_data['Antenna_number']
									anteid = method.anteid
									
									
									# disable textctrls
									self.m_textCtrl1.Enable(False)
									self.m_textCtrl2.Enable(False)
									self.m_textCtrl3.Enable(False)
									self.m_tc_MonitorTime.Enable(False)
									# 
									#q=Queue()
									self.count+=1
									detection_state=1
									self.point = []
									print ("2095:prepare to get trace of spectrum from rsa")
									t1=WorkerThread(self.count,self,rsa_true,deviceSerial_true,span,t,anteid,start_freq,end_freq,rbw,vbw)
									self.threads.append(t1)
									t1.start()
									print ('Cutomized detection succeeded.')
								else:
									print("2035"+a.GPS_state)
									#GPS_end=True;
									event.GetEventObject().SetLabel("开始监测")
									event.GetEventObject().SetValue(False)
									self.m_textCtrl1.Enable(True)
									self.m_textCtrl2.Enable(True)
									self.m_textCtrl3.Enable(True)
									self.m_tc_MonitorTime.Enable(True)
							else:
								print("2110    "+a.GPS_state)
								#GPS_end=False;
								event.GetEventObject().SetLabel("开始监测")
								event.GetEventObject().SetValue(False)
						except:
							#GPS_end=True;
							detection_state = 0
							event.GetEventObject().SetLabel("开始监测")
							event.GetEventObject().SetValue(False)
							self.m_textCtrl1.Enable(True)
							self.m_textCtrl2.Enable(True)
							self.m_textCtrl3.Enable(True)
							self.m_tc_MonitorTime.Enable(True)
					else:
						event.GetEventObject().SetLabel(u"开始监测")
						event.GetEventObject().SetValue(False)
						wx.MessageBox(u'已处于监测状态，请先停止当前任务，然后开始新的任务', "Message" ,wx.OK | wx.ICON_INFORMATION)
					
				else:
					event.GetEventObject().SetLabel(u"开始监测")
					event.GetEventObject().SetValue(False)
					self.Stop_Detect1()
					#event.GetEventObject().SetValue(start_spectrum_state)
		else:
			wx.MessageBox(u'频谱数据回放进行中，请稍后再试！', "Message" ,wx.OK | wx.ICON_INFORMATION)
			event.GetEventObject().SetLabel(u"开始监测")
			event.GetEventObject().SetValue(False)

	def Simple_Watching(self,event):
		global uav_state
		global continue_time
		global detection_state
		global GPS_end
		global work_state
		global start_spectrum_state
		global simple_start_freq
		global simple_stop_freq
		global simple_rbw
		#work_state = 1  # visnon: 为什么强制为1？后面的判断岂不是没用了？ 1为实时监测，2为数据导入
		#print ("work_state in Simple_Watching:" + str(work_state))
		
		
		GPS_end=False
		#self.panelOne.list_ctrl.DeleteAllItems()
		if work_state==1:
			if connect_state==0:
				wx.MessageBox(u'仪表未连接！.', "Error" ,wx.OK | wx.ICON_ERROR)
				event.GetEventObject().SetLabel(u"查看频谱")
				event.GetEventObject().SetValue(False)
			else:
				state = event.GetEventObject().GetValue()
				#print("state value in Simple_Watching:" + str(state))
				start_spectrum_state = not state
				if state == True:
					# 读取输入的数值参数并判断是否符合要求，若不符合则弹窗报错，并退出
					start_freq=self.m_textCtrl1.GetValue()
					self.m_choice1_string=self.m_choice1.GetString(self.m_choice1.GetSelection())
					if start_freq.strip()=='' or float(start_freq)<0:
						#print (config_data)
						start_freq=config_data['start_freq']
					else:
						try:
							start_freq=float(start_freq)
							if self.m_choice1_string=='GHz':
								start_freq=start_freq*(10**3)
							if self.m_choice1_string=='KHz':
								start_freq=start_freq/(10**3)
						except (ValueError,TypeError) as e:
							start_freq=config_data['start_freq']
							wx.MessageBox(u' 初始频率输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
					if start_freq>6.2e3:
						wx.MessageBox(u'起始频率设置超出仪表测量范围','Message',wx.OK)
						return
					elif start_freq<9e-3:
						wx.MessageBox(u'起始频率设置超出仪表测量范围','Message',wx.OK)
						return
					start_freq=start_freq*1e6

					# #print ('start_freq(MHz):',start_freq)
					# #read end_freq
					end_freq=self.m_textCtrl2.GetValue()
					self.m_choice2_string=self.m_choice2.GetString(self.m_choice2.GetSelection())
					if end_freq.strip()=='' or float(end_freq)<0:
						end_freq=config_data['end_freq']
					else:
						try:
							end_freq=float(end_freq)
							if self.m_choice2_string=='GHz':
								end_freq=end_freq*(10**3)
							if self.m_choice2_string=='KHz':
								end_freq=end_freq/(10**3)
						except (ValueError,TypeError) as e:
							end_freq=config_data['end_freq']
							wx.MessageBox(u' 终止频率输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
					if end_freq<9e-3:
						wx.MessageBox(u'终止频率设置超出仪表测量范围','Message',wx.OK)
						return
					elif end_freq>6.2e3:
						wx.MessageBox(u'终止频率设置超出仪表测量范围','Message',wx.OK)
						return
					end_freq=end_freq*1e6
					span=end_freq-start_freq
					# print (start_freq)
					# print (end_freq)
					# print (span)
					if span <=0:
						#event.GetEventObject().SetValue(not state)
						wx.MessageBox(u' 终止频率应大于起始频率', "Message" ,wx.OK | wx.ICON_INFORMATION)
						return 
					
					#read rbw
					rbw=self.m_textCtrl3.GetValue()
					self.m_choice3_string=self.m_choice3.GetString(self.m_choice3.GetSelection())
					if rbw.strip()=='' or float(rbw)<0:
						#rbw=config_data['RBW']
						wx.MessageBox(u' RBW设置错误！', "Warning" ,wx.OK | wx.ICON_INFORMATION)
						return 
					else:
						try:
							rbw=float(rbw)
							if self.m_choice3_string=='MHz':
								rbw=rbw*(10**3)
						except (ValueError,TypeError) as e:
							# rbw=config_data['RBW']
							wx.MessageBox(u' RBW输入需大于零的数值！', "Message" ,wx.OK | wx.ICON_INFORMATION)
							return
					rbw=rbw*1e3
					if rbw<1e2:
						rbw=100
					elif rbw>1e8:
						rbw=1e8
					simple_rbw=rbw
					if self.m_choice3_string=='MHz':
						self.m_textCtrl3.SetValue(str(rbw/1e6))
					else:
						self.m_textCtrl3.SetValue(str(rbw/1e3))
					
					#read vbw
					vbw=config_data['VBW']
					vbw=vbw*1e3
					
					#set watching time
					t=10*3600
					continue_time=t
					# 完成输入格式检查
					
					event.GetEventObject().SetLabel(u"停止查看")
					# event.GetEventObject().SetValue(False)
					if detection_state==0:
						#print("detection_state in simple_watching is :" + str(detection_state))
						try:
							# a = Wait_GPS(self)
							# a.OnStart()
							# #while not a.GPS_end:
							# if a.ShowModal()==wx.ID_OK:
								# if a.GPS_state:
									# self.m_textCtrl4.SetValue(str(a.location[0])[0:6])
									# self.m_textCtrl5.SetValue(str(a.location[1])[0:6])
									# self.m_textCtrl6.SetValue(str(a.location[2])[0:6]+' m')
									# method.freq_info = method.get_freq_range([112.54,37.84,2],method.threshold)

									##########################################################自定义监测

									#read Antenna_number
									#anteid=config_data['Antenna_number']
									anteid = method.anteid
									
									self.count+=1
									detection_state=1
									self.point = []
									print("prepare to begin simple_watching thread!")
									t1=WorkerThread6(self.count,self,rsa_true,deviceSerial_true,span,t,anteid,start_freq,end_freq,rbw,vbw)
									self.threads2.append(t1)
									t1.start()
						except:
							detection_state = 0
							event.GetEventObject().SetLabel(u"查看频谱")
							event.GetEventObject().SetValue(False)
					else:
					# 测试任务进行中 detection_state=1
						event.GetEventObject().SetLabel(u"查看频谱")
						event.GetEventObject().SetValue(False)
						print("a test task is ongoing, thus the sepctrum watching cann't start")
						#event.GetEventObject().SetValue(state)
						wx.MessageBox(u'已处于监测状态，请先停止当前任务，然后开始新的任务', "Message" ,wx.OK | wx.ICON_INFORMATION)
				else:   
					event.GetEventObject().SetLabel(u"查看频谱")
					#event.GetEventObject().SetValue(False)
					self.Stop_Watching()
					#event.GetEventObject().SetValue(start_spectrum_state)
		else:
			wx.MessageBox(u'正在进行数据导入中，请稍后重试！', "Message" ,wx.OK | wx.ICON_INFORMATION)
			event.GetEventObject().SetLabel(u"查看频谱")
			event.GetEventObject().SetValue(False)
	
	def Stop_Detect1(self):
		global GPS_end
		GPS_end=True
		self.m_textCtrl1.Enable(True)
		self.m_textCtrl2.Enable(True)
		self.m_textCtrl3.Enable(True)
		self.m_tc_MonitorTime.Enable(True)
		while self.threads:
			thread=self.threads[0]
			thread.stop()
			self.threads.remove(thread)
			
	def Stop_Watching(self):
		global GPS_end
		GPS_end=True
		while self.threads2:
			thread=self.threads2[0]
			thread.stop()
			self.threads2.remove(thread)
	
	def change_startFreq(self,event):
		global simple_start_freq
		global simple_stop_freq
		# print ('change_startFreq')
		start_freq=self.m_textCtrl1.GetValue()
		self.m_choice1_string=self.m_choice1.GetString(self.m_choice1.GetSelection())
		if start_freq.strip()=='' or float(start_freq)<0:
			#print (config_data)
			start_freq=config_data['start_freq']
		else:
			try:
				start_freq=float(start_freq)
				if self.m_choice1_string=='GHz':
					start_freq=start_freq*(10**3)
				if self.m_choice1_string=='KHz':
					start_freq=start_freq/(10**3)
			except (ValueError,TypeError) as e:
				start_freq=config_data['start_freq']
				wx.MessageBox(u' 初始频率输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
		start_freq=start_freq*1e6
		if start_freq>6.2e9:
			start_freq = config_data['start_freq']
		elif start_freq<9e3:
			start_freq = 9e3

		if start_freq >= simple_stop_freq:
			wx.MessageBox(u'开始频率必须小于截止频率', "Message" ,wx.OK | wx.ICON_INFORMATION)
		else:
			simple_start_freq = start_freq
		#print (simple_start_freq,simple_stop_freq)
		if self.m_choice1_string=='GHz':
			self.m_textCtrl1.SetValue(str(start_freq/1e9))
		elif self.m_choice1_string=='KHz':
			self.m_textCtrl1.SetValue(str(start_freq/1e3))
		else:
			self.m_textCtrl1.SetValue(str(start_freq/1e6))
		event.Skip()
		
	def change_stopFreq(self,event):
		global simple_start_freq
		global simple_stop_freq
		print ('change_stopFreq')
		end_freq=self.m_textCtrl2.GetValue()
		self.m_choice2_string=self.m_choice2.GetString(self.m_choice2.GetSelection())
		if end_freq.strip()=='' or float(end_freq)<0:
			end_freq=config_data['end_freq']
		else:
			try:
				end_freq=float(end_freq)
				if self.m_choice2_string=='GHz':
					end_freq=end_freq*(10**3)
				if self.m_choice2_string=='KHz':
					end_freq=end_freq/(10**3)
			except (ValueError,TypeError) as e:
				end_freq=config_data['end_freq']
				wx.MessageBox(u' 终止频率输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
		end_freq=end_freq*1e6
		if end_freq<9e3:
			end_freq = config_data['end_freq']
		elif end_freq>6.2e9:
			end_freq = 6.2e9
		if simple_start_freq >= end_freq:
			wx.MessageBox(u'开始频率必须小于截止频率', "Message" ,wx.OK | wx.ICON_INFORMATION)
		else:
			simple_stop_freq = end_freq
		print (simple_start_freq,simple_stop_freq)
		if self.m_choice2_string=='GHz':
			self.m_textCtrl2.SetValue(str(end_freq/1e9))
		elif self.m_choice2_string=='KHz':
			self.m_textCtrl2.SetValue(str(end_freq/1e3))
		else:
			self.m_textCtrl2.SetValue(str(end_freq/1e6))
		event.Skip()
        
	def OnChange_RBW(self, event):
		global simple_rbw
		print ('OnChange_RBW')
		rbw=self.m_textCtrl3.GetValue()
		self.m_choice3_string=self.m_choice3.GetString(self.m_choice3.GetSelection())
		if rbw.strip()=='' or float(rbw)<0:
			rbw=config_data['RBW']
		else:
			try:
				rbw=float(rbw)
				if self.m_choice3_string=='MHz':
					rbw=rbw*(10**3)
			except (ValueError,TypeError) as e:
				rbw=config_data['RBW']
				wx.MessageBox(u' RBW输入需大于零的数值！', "Message" ,wx.OK | wx.ICON_INFORMATION)
		rbw=rbw*1e3
		if rbw<1e2:
			rbw=100
		elif rbw>1e8:
			rbw=1e8
		simple_rbw=rbw
		if self.m_choice3_string=='MHz':
			self.m_textCtrl3.SetValue(str(rbw/1e6))
		else:
			self.m_textCtrl3.SetValue(str(rbw/1e3))
		event.Skip()
    
	def OnChangeStartFreUnit(self, event):
		print("StartFreUnit combo changed")
		self.m_textCtrl1.SetFocus()
		
	def OnChangeStopFreUnit(self, event):
		print("StopFreUnit combo changed")
		self.m_textCtrl2.SetFocus()
	
	def OnChangeRBWUnit(self, event):
		print("RBWUnit combo changed")
		self.m_textCtrl3.SetFocus()
	
	def highlight_button(self, event):
		"""
		Draw a red height line around button 1
		"""
		wind = self.m_button10
		pos = wind.GetPosition()
		size = wind.GetSize()
		dc = wx.PaintDC(self)
		dc.SetPen(wx.Pen('red', 5, wx.SOLID))
		dc.DrawRectangle(pos[0], pos[1], size[0], size[1])
		self.m_button10.Refresh()
		event.Skip()
	
	def change_to_Spectrum(self):
		print ("sub Loading...")
		if self.panelOne_one.IsShown():
			pass
		else:
			self.panelOne_one.Show()
			self.panelOne_two.Hide()
		self.Layout()


	def change_to_sub_Spectrum(self):
		print ("sub Loading...")
		if self.panelOne_two.IsShown():
			pass
		else:
			self.panelOne_one.Hide()
			self.panelOne_two.Show()

		self.Layout()
	
	#列表点击事件
	def OnClick_list(self,event):
		global has_rect
		global has_txt
		global work_state
		global lines
		global txts
		work_state = 1
		row=int(event.GetText())-1
		#去除最后一帧的框线
		
		if lines and  has_rect:
			for i in range(len(lines)):
				lines[i][0].remove()
			has_rect = False
		if txts and has_txt:
			for j in range(len(txts)):
				txts[j].remove()
			has_txt = False
		lines=[]
		txts=[]
		
		list_select_cf = float(self.list_ctrl.GetItemText(event.GetIndex(),1))*1e6
		list_select_peak = float(self.list_ctrl.GetItemText(event.GetIndex(),3))
		self.axes_score.set_xlim(self.Sub_freq[row][0],self.Sub_freq[row][-1])
		self.l_user.set_data(self.Sub_freq[row],self.Sub_Spectrum[row])
		line = self.axes_score.plot(list_select_cf,list_select_peak,'wD')
		lines.append(line)
		has_rect = True
		self.axes_score.draw_artist(self.l_user)
		self.canvas.draw()
	
	def data_import_show(self,event):
		global detection_state
		global work_state
		if detection_state==0:
			if self.task_name !=0:
				self.point = []
				raw_path=method.config_data['Spec_dir']+'\\'+self.task_name
				file_all = os.listdir(raw_path)                #找出文件夹中所有数据文件
				map_maxSpectrum = lambda x:x[40:43]=='Max'
				file = list(filter(map_maxSpectrum,file_all))
				if len(file) != 0:
					file_name = file[0] #匹配出MaxSpectrum 文件
					#file_name=os.listdir(raw_path)[0][0:-4]
					print (raw_path,file_name)
					self.start_freq_cu,self.end_freq_cu,self.x_mat,self.y_mat,self.start_time_cu,self.end_time_cu,self.detail_information,self.point,self.label_information=method.importData_cu(self.task_name,file_name,raw_path)
					self.continue_time=(self.end_time_cu-self.start_time_cu).seconds
					self.list_ctrl.DeleteAllItems()
				################################
					work_state=0
					self.t3=WorkerThread3(self,self.start_freq_cu,self.end_freq_cu,self.x_mat,self.y_mat,self.continue_time,self.detail_information)
					self.threads3.append(self.t3)
					self.t3.start()
				else:
					wx.MessageBox(u'数据文件不存在！', "Message" ,wx.OK | wx.ICON_INFORMATION)
		else:
			wx.MessageBox(u'监测工作进行中，请停止监测任务后再试。', "Message" ,wx.OK | wx.ICON_INFORMATION)

	#数据导入显示
	def stop_import_show(self,event):
		while self.threads3:
			thread=self.threads3[0]
			thread.stop()
			self.threads3.remove(thread)
	
	#选择回放导入数据集
	def OnCombo(self,event):
		self.task_name=method.list_to_file(self.m_combo2.GetValue())


	###功能：鼠标移动到信号段框时，显示该信号段的各种信息
	def OnMove(self,evt):
		global work_state
		global has_txt
		global has_rect
		global mon_or_real
		global lines
		global txts
		if work_state == 1:
			pos = evt.GetPosition()
			#print (pos,self.point)
			if self.point:
				for i in range(len(self.point)):
					# print ('#'*10,'point','#'*10)
					#print (pos)
					#print (self.point)
					# print ('#'*20)
					if pos.x>=self.point[i][0] and pos.x<=self.point[i][1] and pos.y>=self.point[i][2] and pos.y<=self.point[i][3]:
						# print ('hahahahahahaahaha')
						#清除之前的显示文本
						if lines and  has_rect:
							for i in range(len(lines)):
								lines[i][0].remove()
							has_rect = False
						if txts and has_txt:
							for j in range(len(txts)):
								txts[j].remove()
							has_txt = False
						lines=[]
						txts=[]
						#显示当前鼠标所在的文本
						txt = self.axes_score.text(self.detail_information[i][1],self.detail_information[i][2],self.label_information[i],fontsize=7,color='r')
						txts.append(txt)
						self.canvas.draw()
						has_txt = True

###########################################################################
## Class MyPanel1_2 月报监测面板
###########################################################################
class MyPanel1_2 ( wx.Panel ):
	
	def __init__( self, parent ):
		
		wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 500,300 ), style = wx.TAB_TRAVERSAL )
		
		self.bSizer4 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticline6 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		self.bSizer4.Add( self.m_staticline6, 0, wx.EXPAND |wx.ALL, 0 )
		
		############################axes
		bSizer37 = wx.BoxSizer( wx.VERTICAL )
		bSizer8 = wx.BoxSizer( wx.VERTICAL )
		
		#bSizer83 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_panel2 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		
		bSizer8.Add( self.m_panel2, 0, wx.EXPAND |wx.ALL, 0 )
		
		bSizer37.Add( bSizer8, 7, wx.EXPAND, 0 )
		
		self.panel3=wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL)
		#self.panel3 = wx.Panel(self)
		
		bSizer45=wx.BoxSizer( wx.HORIZONTAL )
		
		bx2=wx.StaticBox( self.panel3, wx.ID_ANY, u"月报监测" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		bx2.SetForegroundColour("SLATE BLUE")
		font = wx.Font(10, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		bx2.SetFont(font)
		sbSizer2 = wx.StaticBoxSizer(bx2, wx.VERTICAL )
		
		two_bSizer10 = wx.BoxSizer( wx.HORIZONTAL )
		
		two_bSizer11 = wx.BoxSizer( wx.VERTICAL )
		
		two_bSizer13 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.staticText3 = wx.StaticText( self.panel3, wx.ID_ANY, u"选择频率段：", wx.DefaultPosition, wx.DefaultSize, 0 )
		#self.staticText3.Wrap( -1 )
		#self.staticText3.SetFont( wx.Font( 12, 70, 90, wx.BOLD, False, "宋体" ) )
		two_bSizer13.Add( self.staticText3, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		
		# self.textCtrl1 = wx.TextCtrl( self.panel3, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (80,20), 0 )
		# two_bSizer13.Add( self.textCtrl1, 0, wx.ALL|wx.ALIGN_CENTRE, 0 )
		
		#servicedid,freqname,freqrange_list=method.servicedid,method.freqname,method.freqrange_list
		#print ('freqrange_list:',freqrange_list)
		choice1Choices = []
		self.choice1 = wx.Choice( self.panel3, wx.ID_ANY, wx.DefaultPosition, (145,20), choice1Choices, 0 )
		self.choice1.SetSelection( 0 )
		two_bSizer13.Add( self.choice1, 0, wx.ALL|wx.ALIGN_CENTRE, 2 )
		
		
		two_bSizer11.Add( two_bSizer13, 1, wx.EXPAND, 0 )
		
		two_bSizer15 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.staticText5 = wx.StaticText( self.panel3, wx.ID_ANY, u"  RBW    :    ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.staticText5.Wrap( -1 )
		self.staticText5.SetFont( wx.Font( 9, 70, 90, 92, False, "@华文楷体" ) ) #@表示文字竖着写
		
		two_bSizer15.Add( self.staticText5, 0, wx.ALIGN_CENTER|wx.ALL, 5 )
		
		default_rbw = str(config_data['RBW'])
		self.textCtrl3 = wx.TextCtrl( self.panel3, wx.ID_ANY, default_rbw, wx.DefaultPosition, (90,20), 0 )
		two_bSizer15.Add( self.textCtrl3, 0, wx.ALIGN_CENTER|wx.ALL, 0 )
		
		choice3Choices = ['KHz','MHz']
		self.choice3 = wx.Choice( self.panel3, wx.ID_ANY, wx.DefaultPosition, (60,20), choice3Choices, 0 )
		self.choice3.SetSelection( 0 )
		two_bSizer15.Add( self.choice3, 0, wx.ALIGN_CENTER|wx.ALL, 2 )
		
		
		two_bSizer11.Add( two_bSizer15, 1, wx.EXPAND, 0 )
		
		
		two_bSizer10.Add( two_bSizer11, 3, wx.EXPAND, 0 )
		
		
		two_bSizer27 = wx.BoxSizer( wx.VERTICAL )
		
		two_bSizer29 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.staticText10 = wx.StaticText( self.panel3, wx.ID_ANY, u" 监测时长： ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.staticText10.Wrap( -1 )
		two_bSizer29.Add( self.staticText10, 0, wx.ALIGN_CENTER|wx.ALL, 0 )
		
		self.textCtrl5 = wx.TextCtrl( self.panel3, wx.ID_ANY, '1', wx.DefaultPosition, (90,20), 0 )
		two_bSizer29.Add( self.textCtrl5, 0, wx.ALIGN_CENTER|wx.ALL, 0 )
		
		self.staticText11 = wx.StaticText( self.panel3, wx.ID_ANY, u"小时", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.staticText11.Wrap( -1 )
		two_bSizer29.Add( self.staticText11, 0, wx.ALIGN_CENTER|wx.ALL, 2 )
		
		
		two_bSizer27.Add( two_bSizer29, 1, wx.EXPAND, 0 )
		
		two_bSizer30 = wx.BoxSizer( wx.VERTICAL )
		
		# self.button10 = wx.ToggleButton( self, wx.ID_ANY, u"开始监测", wx.DefaultPosition, (200,50), 0 )
		# two_bSizer30.Add( self.button10, 0, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND|wx.BOTTOM, 2 )
		# self.button10.Bind(wx.EVT_TOGGLEBUTTON,self.OnToggle) 
		
		two_bSizer30 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.staticText17 = wx.StaticText( self.panel3, wx.ID_ANY, u"  VBW   :  ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.staticText17.Wrap( -1 )
		two_bSizer30.Add( self.staticText17, 0, wx.ALIGN_CENTER|wx.ALL, 0 )
		
		default_vbw = str(config_data['VBW'])
		self.textCtrl10 = wx.TextCtrl( self.panel3, wx.ID_ANY, default_vbw, wx.DefaultPosition, (90,20), 0 )
		two_bSizer30.Add( self.textCtrl10, 0, wx.ALIGN_CENTER|wx.ALL, 0 )
		
		choice2Choices = ['KHz']
		self.choice8 = wx.Choice( self.panel3, wx.ID_ANY, wx.DefaultPosition, (60,20), choice2Choices, 0 )
		self.choice8.SetSelection( 0 )
		two_bSizer30.Add( self.choice8, 0, wx.ALIGN_CENTER|wx.ALL, 2 )
		
		
		two_bSizer27.Add( two_bSizer30, 1, wx.EXPAND, 0 )
		
		
		two_bSizer10.Add( two_bSizer27, 3, wx.EXPAND, 0 )
		
		sbSizer2.Add( two_bSizer10, 1, wx.EXPAND, 5 )
		
		bSizer45.Add(sbSizer2, 3, wx.EXPAND, 0)
		
		two_bSizer26 = wx.BoxSizer( wx.VERTICAL )
		# self.panel5 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		# two_bSizer26.Add( self.panel5, 1, wx.EXPAND |wx.ALL, 0 )
		
		#self.button10 = wx.Button( self.panel3, wx.ID_ANY, u"开始监测", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_button10 = wx.ToggleButton( self.panel3, wx.ID_ANY, u"开始监测", wx.DefaultPosition, wx.DefaultSize, 0 )
		# modified by vinson 0805
		#self.m_button10 = wx.Button( self.panel3, wx.ID_ANY, u"开始监测", wx.DefaultPosition, wx.DefaultSize, 0 ) 
		#self.button10.Bind(wx.EVT_PAINT, self.highlight_button)
		two_bSizer26.Add( self.m_button10, 1, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND|wx.BOTTOM, 2 )
		#self.button10.Bind(wx.EVT_BUTTON,self.Start_Detect)
		self.m_button10.Bind(wx.EVT_TOGGLEBUTTON,self.Start_Detect)
		self.m_button10.SetFont( wx.Font( 20, 70, 90, wx.BOLD, False, "华文楷体" ) )
		'''
		self.button11 = wx.Button( self.panel3, wx.ID_ANY, u"停止监测", wx.DefaultPosition, wx.DefaultSize, 0 )
		two_bSizer26.Add( self.button11, 1, wx.ALIGN_CENTER|wx.ALL|wx.EXPAND|wx.BOTTOM, 2 )
		self.button11.Bind(wx.EVT_BUTTON,self.Stop_Detect) 
		self.button11.SetFont( wx.Font( 12, 70, 90, wx.BOLD, False, "华文楷体" ) )
		'''
		bSizer45.Add( two_bSizer26, 3, wx.EXPAND, 0)
		
		self.panel3.SetSizer(bSizer45)
		
		
		
		
		#############################################################################设置模式2参数END
		
		################################新加
		# read start_freq
		start_freq=config_data['start_freq']
		start_freq=start_freq*1e6
		#read end_freq
		end_freq=config_data['end_freq']
		end_freq=end_freq*1e6
		#################################
		## 尝试一种新的画图方法
		self.figure_score = Figure((7.5,4.82),100)
		
		self.canvas = FigureCanvas(self.m_panel2, wx.ID_ANY, self.figure_score)
		# print (self.m_panel2.GetPosition())
		# print (self.canvas.GetPosition())
		#self.canvas.Bind(wx.EVT_MOTION,self.OnMove)
		# self.figure_score.set_figheight(4)
		# self.figure_score.set_figwidth(6)
		self.axes_score = self.figure_score.add_subplot(111,facecolor='k')
		#self.axes_score.set_autoscale_on(False) #关闭坐标轴自动缩放
		self.traceData=[-110]*801
		self.freq=range(int(start_freq),int(end_freq)+int((end_freq-start_freq)/800),int((end_freq-start_freq)/800))
		self.l_user,=self.axes_score.plot(self.freq, self.traceData, 'y')
		#self.axes_score.axhline(y=average, color='r')
		self.axes_score.set_ylim(-80,0)
		self.axes_score.set_title('Spectrum')
		self.axes_score.grid(True,color='dimgray')
		self.axes_score.set_xlabel('Frequency/Hz')
		self.axes_score.set_ylabel('Amplitude/dBmVV')
		self.canvas.draw()
		
		bSizer37.Add(self.panel3, 2, wx.EXPAND, 0 )
		
		
		self.bSizer4.Add( bSizer37, 2, wx.EXPAND, 5 )
		
		self.m_staticline8 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_VERTICAL )
		self.bSizer4.Add( self.m_staticline8, 0, wx.EXPAND |wx.ALL, 0 )
		
		##################################################################################################
		##################  add list_table_infos
		##################################################################################################
		self.bSizer6 = wx.BoxSizer( wx.VERTICAL )
		
		self.bSizer19 = wx.BoxSizer( wx.VERTICAL )
		
		##############################################显示子信号列表
		self.bx1=wx.StaticBox( self, wx.ID_ANY, u"台站注册信号比对：" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		self.bx1.SetForegroundColour("SLATE BLUE")
		font = wx.Font(10, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bx1.SetFont(font)
		self.sbSizer35 = wx.StaticBoxSizer( self.bx1, wx.VERTICAL )
		self.list_ctrl = wx.ListCtrl(self, size=(-1,500),style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES|wx.BORDER_SUNKEN)
		self.list_ctrl.InsertColumn(0, 'ID',width=30)
		self.list_ctrl.InsertColumn(1, '频率/MHz',width=75)
		self.list_ctrl.InsertColumn(2, '带宽/MHz', width=80)
		self.list_ctrl.InsertColumn(3, '幅度/dBmV',width = 80)
		self.list_ctrl.InsertColumn(4, '业务类型', width=65)
		self.Bind(wx.EVT_LIST_ITEM_ACTIVATED, self.OnClick_list, self.list_ctrl)
		
		self.sbSizer35.Add(self.list_ctrl,0,wx.ALL|wx.EXPAND,0)
		
		self.bSizer19.Add(self.sbSizer35,0,wx.ALL|wx.EXPAND,5)
		
		
		self.bSizer6.Add( self.bSizer19, 1, wx.EXPAND, 5 )
		'''
		self.m_staticline9 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		self.bSizer6.Add( self.m_staticline9, 5, wx.EXPAND|wx.ALL, 0 )
		'''
		self.bSizer20 = wx.BoxSizer( wx.VERTICAL )
		
		###############################################导入数据显示
		'''
		self.bx2=wx.StaticBox( self, wx.ID_ANY, u"历史数据导入信息" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		self.bx2.SetForegroundColour("SLATE BLUE")
		font = wx.Font(9, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bx2.SetFont(font)
		self.sbSizer3 = wx.StaticBoxSizer( self.bx2, wx.VERTICAL )
		
		self.m_choices1 = method.file_to_list(list(reversed(os.listdir(method.config_data['Spec_dir']))))
		self.choice_Num=len(self.m_choices1)
		self.m_combo2 = wx.ComboBox( self, wx.ID_ANY, u'请选择文件...',wx.DefaultPosition, (80,20), self.m_choices1, 0 )
		self.m_combo2.Bind(wx.EVT_COMBOBOX, self.OnCombo)
		self.task_name=0
		self.sbSizer3.Add(self.m_combo2,0,wx.ALL|wx.EXPAND,10)
		
		self.startSizer=wx.BoxSizer(wx.HORIZONTAL)
		self.m_button12 = wx.Button( self, wx.ID_ANY, u"频谱文件回放", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.startSizer.Add(self.m_button12,0,wx.ALL|wx.EXPAND,5)
		self.m_button13 = wx.Button(self,wx.ID_ANY,u"停止回放",wx.DefaultPosition,wx.DefaultSize,0)
		self.startSizer.Add(self.m_button13,0,wx.ALL|wx.EXPAND,5)
		self.m_button12.Bind( wx.EVT_BUTTON, self.data_import_show )
		self.m_button13.Bind( wx.EVT_BUTTON, self.stop_import_show )
		
		self.sbSizer3.Add(self.startSizer,0,wx.ALL|wx.EXPAND,10)
		
		self.bSizer20.Add( self.sbSizer3, 1, wx.ALL|wx.EXPAND, 8 )
		'''
		#################################################导入数据显示END
		
		#################################################经纬度显示
		self.bx3=wx.StaticBox( self, wx.ID_ANY, u"位置信息显示" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		self.bx3.SetForegroundColour("SLATE BLUE")
		font = wx.Font(9, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bx3.SetFont(font)
		self.sbSizer4 = wx.StaticBoxSizer( self.bx3, wx.VERTICAL )
		self.bSizer24=wx.BoxSizer(wx.VERTICAL)
		
		self.bSizer25=wx.BoxSizer(wx.HORIZONTAL)
		self.m_staticText21 = wx.StaticText( self, wx.ID_ANY, u"经度：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText21.Wrap( -1 )
		self.bSizer25.Add( self.m_staticText21, 0, wx.ALL, 5 )
		self.m_textCtrl4 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (80,20), 0 )
		self.bSizer25.Add( self.m_textCtrl4, 0, wx.ALL, 5 )
		#self.bSizer24.Add(self.bSizer25,1,wx.EXPAND,5)
		
		#bSizer26=wx.BoxSizer(wx.HORIZONTAL)
		self.m_staticText22 = wx.StaticText( self, wx.ID_ANY, u"纬度：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText22.Wrap( -1 )
		self.bSizer25.Add( self.m_staticText22, 0, wx.ALL, 5 )
		self.m_textCtrl5 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (80,20), 0 )
		self.bSizer25.Add( self.m_textCtrl5, 0, wx.ALL, 5 )
		self.bSizer24.Add(self.bSizer25,1,wx.EXPAND,5)
		
		self.list_bSizer27=wx.BoxSizer(wx.HORIZONTAL)
		self.m_staticText23 = wx.StaticText( self, wx.ID_ANY, u"高度：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText23.Wrap( -1 )
		self.list_bSizer27.Add( self.m_staticText23, 0, wx.ALL, 5 )
		self.m_textCtrl6 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (80,20), 0 )
		self.list_bSizer27.Add( self.m_textCtrl6, 0, wx.ALL, 5 )
		self.bSizer24.Add(self.list_bSizer27,1,wx.EXPAND,5)
		
		self.sbSizer4.Add(self.bSizer24,1,wx.EXPAND,5)
		self.bSizer20.Add( self.sbSizer4, 2, wx.ALL|wx.EXPAND, 8 )
		
		#####################################页面布局，加空白
		'''
		self.m_panel4 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.bSizer20.Add( self.m_panel4, 3, wx.EXPAND |wx.ALL, 5 )
		'''
		self.bSizer6.Add( self.bSizer20, 1, wx.EXPAND, 5 )
		
		
		self.bSizer4.Add( self.bSizer6, 0, wx.EXPAND, 5 )

		self.SetSizer( self.bSizer4 )
		self.count=0
		self.threads = []
		
		#记录整次扫描存在的有效（有不同频谱）的信息
		self.Sub_Spectrum=[]
		self.Sub_Spectrum2=[]
		self.Sub_cf_all=[]
		self.Sub_band_all=[]
		self.Sub_peak_all=[]
		
		#记录单帧扫描的基本信息
		self.Sub_cf_channel=[]
		self.Sub_span=[]
		self.Sub_cf=[]
		self.Sub_band=[]
		self.Sub_peak=[]
		
		#画方框的集合
		#self.point=[[307,307+53,202,202+154/3]]
		self.point=[]

		#记录列表自频段的信息
		self.Sub_freq=[]
		self.lines = []
		self.txts =[]
		self.detail_information = [] #回放信号的具体信息
		self.point = [] #新号段的坐标信息
		self.label_information = []  #标注的信息文本
		self.threads3 = []

	# 开始月报监测
	def Start_Detect(self,event):
		global uav_state
		global continue_time
		global detection_state
		global GPS_end
		global work_state
		global start_spectrum_state
		global longitude
		global latitude
		global height
		# work_state = 1
		
		
		
		GPS_end=False
		if work_state==1:
			if connect_state==0:
				wx.MessageBox(u'仪表未连接！.', "Error" ,wx.OK | wx.ICON_ERROR)
			else:
				state = event.GetEventObject().GetValue()
				start_spectrum_state = not state
				if state == True:
					if detection_state==0:
						try:
				#---------------------GPS信息---------------------------
							a = Wait_GPS(self)
							a.OnStart()
							 #while not a.GPS_end:
							if a.ShowModal()==wx.ID_OK:
								if a.GPS_state:
									print("State of location in detection of Month_Monitor:"+str(a.GPS_state))
									longitude = a.location[0]
									latitude = a.location[1]
									height = a.location[2]
									self.m_textCtrl4.SetValue(str(a.location[0])[0:6])
									self.m_textCtrl5.SetValue(str(a.location[1])[0:6])
									self.m_textCtrl6.SetValue(str(a.location[2])[0:6]+' m')
									#method.freq_info = method.get_freq_range([112.54,37.84,2],method.threshold)
									method.freq_info = method.get_freq_range(a.location,method.threshold)
                 ###############---------------- 获取GPS信息结束----------------------------
									###################################################月报监测
									event.GetEventObject().SetLabel(u"停止监测")
									
									freq_select_string=self.choice1.GetString(self.choice1.GetSelection())
									freq_select=[float(freq) for freq in freq_select_string.split()[0].split('-')]
									start_freq=freq_select[0]*1e6
									end_freq=freq_select[1]*1e6
									span=end_freq-start_freq
									#print ('mode yuebao:',start_freq,end_freq,span)
									
									#Set center_freq and span
									#self.m_textCtrl11.SetValue(str((start_freq+end_freq)/(2e6))+'MHz')
									#self.m_textCtrl12.SetValue(str(span/(1e6))+'MHz')
									
									#read step_size
									'''
									step_size=span/801
									self.choice2_string=self.choice2.GetString(self.choice2.GetSelection())
									if self.choice2_string=='GHz':
										step_size=step_size/(10**9)
									elif self.choice2_string=='KHz':
										step_size=step_size/(10**3)
									else:
										step_size=step_size/(10**6)
									self.textCtrl2.SetValue("%.3f"%step_size)
									'''
									
									#read Antenna_number
									#anteid=config_data['Antenna_number']
									anteid = method.anteid
									
									#read rbw
									rbw=self.textCtrl3.GetValue()
									self.choice3_string=self.choice3.GetString(self.choice3.GetSelection())
									if rbw.strip()=='' or float(rbw)<0:
										rbw=config_data['RBW']
									else:
										try:
											rbw=float(rbw)
											if self.choice3_string=='MHz':
												rbw=rbw*(10**3)
										except (ValueError,TypeError) as e:
											rbw=config_data['RBW']
											wx.MessageBox(u' RBW输入需大于零的数值！', "Message" ,wx.OK | wx.ICON_INFORMATION)
									rbw=rbw*1e3
									if rbw<1e2:
										rbw=100
									elif rbw>1e8:
										rbw=1e8
									if self.choice3_string=='MHz':
										self.textCtrl3.SetValue(str(rbw/1e6))
									else:
										self.textCtrl3.SetValue(str(rbw/1e3))
									#read vbw
									vbw= self.textCtrl10.GetValue()
									if vbw.strip()=='' or float(vbw)<0:
										vbw=config_data['VBW']
										self.textCtrl10.SetValue(str(vbw))
									else:
										vbw = float(vbw)
									vbw=vbw*1e3
									
									#read time
									t=self.textCtrl5.GetValue()
									if t.strip()=='' or float(t)<0:
										t=0.001
									else:
										try:
											t=float(t)
										except (ValueError,TypeError) as e:
											t=0.002
											wx.MessageBox(u' 终止频率输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
									self.textCtrl5.SetValue(str(t))
									t=t*3600
									continue_time=t
									# disable the textctrls
									self.textCtrl3.Enable(False)
									self.textCtrl5.Enable(False)
									self.textCtrl10.Enable(False)
									#
									#q=Queue()
									self.count+=1
									detection_state=1
									t1=WorkerThread(self.count,self,rsa_true,deviceSerial_true,span,t,anteid,start_freq,end_freq,rbw,vbw)
									self.threads.append(t1)
									t1.start()
									print ('success')
                    #    add by vinson
								else:
									print(str(2806)+"   "+str(a.GPS_state))
									#GPS_end=False
									event.GetEventObject().SetLabel(u"开始监测")
									event.GetEventObject().SetValue(state)
							else:
								print("GPS was cancelled in month monitor")
								#GPS_end=False
								event.GetEventObject().SetLabel(u"开始监测")
								event.GetEventObject().SetValue(False)
                    #  add by vinson
						except:
							detection_state = 0
							self.textCtrl3.Enable(True)
							self.textCtrl5.Enable(True)
							self.textCtrl10.Enable(True)
							event.GetEventObject().SetLabel(u"开始监测")
							event.GetEventObject().SetValue(False)
					else:
						event.GetEventObject().SetLabel(u"开始监测")
						event.GetEventObject().SetValue(state)
						wx.MessageBox(u'已处于监测状态，请先停止当前任务，然后开始新的任务', "Message" ,wx.OK | wx.ICON_INFORMATION)
				else:
					self.Stop_Detect1()

		else:
			wx.MessageBox(u'数据频谱回放任务进行中，请稍后再试！', "Message" ,wx.OK | wx.ICON_INFORMATION)
			event.GetEventObject().SetLabel(u"开始监测")
			event.GetEventObject().SetValue(state)

	def Stop_Detect(self,event):
		global GPS_end
		GPS_end=True
		self.textCtrl3.Enable(True)
		self.textCtrl5.Enable(True)
		self.textCtrl10.Enable(True)
		event.GetEventObject().SetLabel(u"开始监测")
		while self.threads:
			thread=self.threads[0]
			thread.stop()
			self.threads.remove(thread)

	
	def Stop_Detect1(self):
		global GPS_end
		GPS_end=True
		self.textCtrl3.Enable(True)
		self.textCtrl5.Enable(True)
		self.textCtrl10.Enable(True)
		#event.GetEventObject().SetLabel(u"开始监测")
		while self.threads:
			thread=self.threads[0]
			thread.stop()
			self.threads.remove(thread)
		
	def change_to_Spectrum(self):
			print ("sub Loading...")
			if self.panelOne_one.IsShown():
				pass
			else:
				self.panelOne_one.Show()
				self.panelOne_two.Hide()
			self.Layout()

	#列表点击事件
	def OnClick_list(self,event):
		global has_rect
		global has_txt
		global work_state
		global lines
		global txts
		work_state = 1
		row=int(event.GetText())-1
		#去除最后一帧的框线
		
		if lines and  has_rect:
			for i in range(len(lines)):
				lines[i][0].remove()
			has_rect = False
		if txts and has_txt:
			for j in range(len(txts)):
				txts[j].remove()
			has_txt = False
		lines=[]
		txts=[]
		
		list_select_cf = float(self.list_ctrl.GetItemText(event.GetIndex(),1))*1e6
		list_select_peak = float(self.list_ctrl.GetItemText(event.GetIndex(),3))
		# if self.panelOne_one.IsShown():
			# self.panelOne_one.axes_score.set_xlim(self.Sub_freq[row][0],self.Sub_freq[row][-1])
			# self.panelOne_one.l_user.set_data(self.Sub_freq[row],self.Sub_Spectrum[row])
			# line = self.panelOne_one.axes_score.plot(list_select_cf,list_select_peak,'wD')
			# lines.append(line)
			# has_rect = True
			# self.panelOne_one.axes_score.draw_artist(self.panelOne_one.l_user)
			# self.panelOne_one.canvas.draw()
		# else:
		self.axes_score.set_xlim(self.Sub_freq[row][0],self.Sub_freq[row][-1])
		self.l_user.set_data(self.Sub_freq[row],self.Sub_Spectrum[row])
		line = self.axes_score.plot(list_select_cf,list_select_peak,'wD')
		lines.append(line)
		has_rect = True
		self.axes_score.draw_artist(self.l_user)
		self.canvas.draw()

'''
	def change_to_sub_Spectrum(self):
		print ("sub Loading...")
		if self.panelOne_two.IsShown():
			pass
		else:
			self.panelOne_one.Hide()
			self.panelOne_two.Show()

		self.Layout()
		
	def data_import_show(self,event):
		global detection_state
		global work_state
		if detection_state==0:
			if self.task_name !=0:
				self.point = []
				raw_path=method.config_data['Spec_dir']+'\\'+self.task_name
				file_all = os.listdir(raw_path)                #找出文件夹中所有数据文件
				map_maxSpectrum = lambda x:x[40:43]=='Max'
				file = list(filter(map_maxSpectrum,file_all))
				if len(file) != 0:
					file_name = file[0] #匹配出MaxSpectrum 文件
					#file_name=os.listdir(raw_path)[0][0:-4]
					print (raw_path,file_name)
					self.start_freq_cu,self.end_freq_cu,self.x_mat,self.y_mat,self.start_time_cu,self.end_time_cu,self.detail_information,self.point,self.label_information=method.importData_cu(self.task_name,file_name,raw_path)
					self.continue_time=(self.end_time_cu-self.start_time_cu).seconds
					self.list_ctrl.DeleteAllItems()
				################################
					work_state=0
					self.t3=WorkerThread3(self,self.start_freq_cu,self.end_freq_cu,self.x_mat,self.y_mat,self.continue_time,self.detail_information)
					self.threads3.append(self.t3)
					self.t3.start()
				else:
					wx.MessageBox(u'数据文件不存在！', "Message" ,wx.OK | wx.ICON_INFORMATION)
		else:
			wx.MessageBox(u'监测工作进行中，请停止监测任务后再试。', "Message" ,wx.OK | wx.ICON_INFORMATION)
	
	#数据导入显示
	def stop_import_show(self,event):
		while self.threads3:
			thread=self.threads3[0]
			thread.stop()
			self.threads3.remove(thread)
	
	#选择回放导入数据集
	def OnCombo(self,event):
		self.task_name=method.list_to_file(self.m_combo2.GetValue())

	###功能：鼠标移动到信号段框时，显示该信号段的各种信息

	def OnMove(self,evt):
		global has_txt
		global has_rect
		global mon_or_real
		global lines
		global txts
		global work_state
		pos = evt.GetPosition()
		#print (pos,self.point)
		if work_state == 1:
			if self.point:
				for i in range(len(self.point)):
					# print ('#'*10,'point','#'*10)
					#print (pos)
					#print (self.point)
					# print ('#'*20)
					if pos.x>=self.point[i][0] and pos.x<=self.point[i][1] and pos.y>=self.point[i][2] and pos.y<=self.point[i][3]:
						# print ('hahahahahahaahaha')
						#清除之前的显示文本
						if lines and  has_rect:
							for i in range(len(lines)):
								lines[i][0].remove()
							has_rect = False
						if txts and has_txt:
							for j in range(len(txts)):
								txts[j].remove()
							has_txt = False
						lines=[]
						txts=[]
						#显示当前鼠标所在的文本
						txt = self.axes_score.text(self.detail_information[i][1],self.detail_information[i][2],self.label_information[i],fontsize=7,color='r')
						txts.append(txt)
						self.canvas.draw()
						has_txt = True
						
'''
		
###########################################################################
## Class MyPanel1_3 子频段扫描面板
###########################################################################

class MyPanel1_3 ( wx.Panel ):
	
	def __init__( self, parent ):
		wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 500,300 ), style = wx.TAB_TRAVERSAL )
		
		bSizer37 = wx.BoxSizer( wx.VERTICAL )
		#############
		bSizer8 = wx.BoxSizer( wx.VERTICAL )

		
		#bSizer83 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_panel2 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		
		#面板上画坐标轴
		self.figure_score = Figure((6,4),100)
		self.canvas1=FigureCanvas(self.m_panel2, -1, self.figure_score)
		self.axes_score1 = self.figure_score.add_subplot(111,facecolor='k')
		self.l_user1,=self.axes_score1.plot([], [], 'b')
		#self.axes_score.axhline(y=average, color='r')
		self.axes_score1.set_ylim(-50,20)
		self.axes_score1.set_title('Sub-Spectrum')
		self.axes_score1.grid(True,color='y')
		self.axes_score1.set_xlabel('Frequency/Hz')
		self.axes_score1.set_ylabel('Amplitude/dBmV')
		self.canvas1.draw()
		
		
		bSizer8.Add( self.m_panel2, 10, wx.EXPAND |wx.ALL, 0 )
		

		
		bSizer84 = wx.BoxSizer( wx.HORIZONTAL )
		
		#bSizer84.AddStretchSpacer(1) 
		self.m_staticText18 = wx.StaticText( self, wx.ID_ANY, "                CF :", (200,20), wx.DefaultSize, 0 )
		self.m_staticText18.Wrap( -1 )
		bSizer84.Add( self.m_staticText18, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		self.m_textCtrl11 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (100,20), 0 )
		bSizer84.Add( self.m_textCtrl11, 0, wx.ALL|wx.ALIGN_CENTRE, 0 )
		
		#bSizer84.AddStretchSpacer(1) 
		
		self.m_staticText19 = wx.StaticText( self, wx.ID_ANY, "     Span :", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText19.Wrap( -1 )
		bSizer84.Add( self.m_staticText19, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		self.m_textCtrl12 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (100,20), 0 )
		bSizer84.Add( self.m_textCtrl12, 0, wx.ALL|wx.ALIGN_CENTRE, 0 )
		# bSizer83.Add( bSizer84, 10, wx.EXPAND, 0 )
		
		bSizer8.Add( bSizer84, 1, wx.EXPAND, 0 )
		##############
		
		bSizer37.Add( bSizer8, 3, wx.EXPAND, 0 )
		
		
		
			
		
		sbSizer2 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"子频段信息" ), wx.VERTICAL )
		
		bSizer232 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer233 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText106 = wx.StaticText( self, wx.ID_ANY, u"可能业务：    ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText106.Wrap( -1 )
		bSizer233.Add( self.m_staticText106, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		m_choice42Choices = []
		self.m_choice42 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_choice42Choices, 0 )
		self.m_choice42.SetSelection( 0 )
		bSizer233.Add( self.m_choice42, 0, wx.ALL, 5 )
		
		
		bSizer232.Add( bSizer233, 1, wx.EXPAND, 5 )
		
		bSizer234 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText107 = wx.StaticText( self, wx.ID_ANY, u"标称频率：    ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText107.Wrap( -1 )
		bSizer234.Add( self.m_staticText107, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		self.m_textCtrl54 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer234.Add( self.m_textCtrl54, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		self.m_staticText108 = wx.StaticText( self, wx.ID_ANY, u"  实测中心频率：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText108.Wrap( -1 )
		bSizer234.Add( self.m_staticText108, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		self.m_textCtrl55 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer234.Add( self.m_textCtrl55, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		
		bSizer232.Add( bSizer234, 1, wx.EXPAND, 5 )
		
		bSizer235 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText109 = wx.StaticText( self, wx.ID_ANY, u"标称信号带宽： ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText109.Wrap( -1 )
		bSizer235.Add( self.m_staticText109, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		self.m_textCtrl56 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer235.Add( self.m_textCtrl56, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		self.m_staticText110 = wx.StaticText( self, wx.ID_ANY, u"  实测信号带宽：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText110.Wrap( -1 )
		bSizer235.Add( self.m_staticText110, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		self.m_textCtrl57 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer235.Add( self.m_textCtrl57, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		
		bSizer232.Add( bSizer235, 1, wx.EXPAND, 5 )
		
		
		sbSizer2.Add( bSizer232, 1, wx.EXPAND, 5 )
		
		bSizer37.Add( sbSizer2, 1, wx.EXPAND, 0 )
		
		self.SetSizer( bSizer37 )
	
###########################################################################
## Class MyPanel2 台站检测模块（已去掉）
###########################################################################

class MyPanel2 ( wx.Panel ):
	
	def __init__( self, parent ):
		wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 500,300 ), style = wx.TAB_TRAVERSAL )
		
		bSizer33 = wx.BoxSizer( wx.HORIZONTAL )
		
		bSizer34 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_panel6 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		#self.bSizer102=wx.BoxSizer(wx.VERTICAL)
		# img1 = wx.Image(os.getcwd()+'\\beijing.png', wx.BITMAP_TYPE_ANY)
		# self.m_bitmap1 = wx.StaticBitmap( self, wx.ID_ANY, wx.Bitmap(img1), wx.DefaultPosition, (600,80), 0 )
		self.m_htmlWin2 = wx.html2.WebView.New(self.m_panel6,size=(700,600))
		#self.bSizer102.Add( self.m_htmlWin2, 0, wx.ALL, 0 )
		self.file_html='file:///'+os.getcwd()+'/map6.html'
		self.m_htmlWin2.LoadURL(self.file_html)
		self.longitude=-1
		self.latitude=-1
		
		#self.b,self.a=method.get_station_inf()
		# self.a={'1':[116.4,39.8],'2':[116.45,39.85]}
		# self.b={'1':[116.43,39.9]}
		self.pre_title='start'
		self.page_start=0
		self.start_freq=0
		self.end_freq=0
		#self.m_htmlWin2.Bind(wx.html2.EVT_WEBVIEW_LOADED, self.deal_html)
		self.Bind(wx.html2.EVT_WEBVIEW_LOADED,self.deal_html,self.m_htmlWin2)
		#self.Bind(wx.html2.EVT_WEBVIEW_TITLE_CHANGED, self.OnTitle)
		
		#self.m_panel6.SetSizer(self.bSizer102)
		bSizer34.Add( self.m_panel6, 1, wx.EXPAND |wx.ALL, 0 )
		
		
		bSizer33.Add( bSizer34, 0, wx.EXPAND, 5 )
		
		
		self.bSizer35=wx.BoxSizer(wx.VERTICAL)
		self.m_choices = list(reversed(os.listdir(method.config_data['Spec_dir'])))
		self.choice_Num=len(self.m_choices)
		self.m_combo1 = wx.ComboBox( self, wx.ID_ANY, u'请选择文件...',wx.DefaultPosition, (100,20), self.m_choices, 0 )
		self.m_combo1.Bind(wx.EVT_COMBOBOX, self.OnCombo2)
		self.bSizer35.Add(self.m_combo1,0,wx.ALL|wx.EXPAND,10)
		
		#在地图右侧添加表格
		#self.bSizer35=wx.BoxSizer(wx.VERTICAL)
		self.bx1=wx.StaticBox( self, wx.ID_ANY, u"检测数据信息表：" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		self.bx1.SetForegroundColour("SLATE BLUE")
		font = wx.Font(10, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bx1.SetFont(font)
		self.sbSizer35 = wx.StaticBoxSizer( self.bx1, wx.VERTICAL )
		self.list_ctrl = wx.ListCtrl(self, size=(-1,500),style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES|wx.BORDER_SUNKEN)
		self.list_ctrl.InsertColumn(0, 'id',width=40)
		self.list_ctrl.InsertColumn(1, 'cf/MHz',width=80)
		self.list_ctrl.InsertColumn(2, 'band/MHz', width=80)
		self.list_ctrl.InsertColumn(3, 'peak/dBmV', width=80)
		
		self.sbSizer35.Add(self.list_ctrl,0,wx.ALL|wx.EXPAND,0)
		
		self.bSizer35.Add(self.sbSizer35,0,wx.ALL|wx.EXPAND,5)
		
		'''
		# self.list_ctrl.InsertItem(0,'1')
		# self.list_ctrl.SetItem(0,1,'haha1')
		# self.list_ctrl.SetItem(0,2,'haha2')
		# self.list_ctrl.SetItem(0,3,'haha3')
		# self.list_ctrl.SetItemData(0,0)  #给每一行做一个句柄，以方便调用
		# self.list_ctrl.SetItemBackgroundColour(0, "red")
		################################################################################
		
		# self.bSizer35=wx.BoxSizer(wx.HORIZONTAL)
		# self.m_button1=wx.Button( self, wx.ID_ANY, u"台站检测", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.bSizer35.Add(self.m_button1,0,wx.ALL,0)
		# self.m_button1.Bind(wx.EVT_BUTTON,self.station_set)
		
		# self.m_button2=wx.Button(self,wx.ID_ANY,u"清除台站缓存",wx.DefaultPosition,wx.DefaultSize,0)
		# self.bSizer35.Add(self.m_button2,0,wx.ALL,0)
		# self.m_button2.Bind(wx.EVT_BUTTON,self.clear_station_data)
		'''
		#################################################################################
		'''
		# self.m_staticline3 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_VERTICAL )
		# bSizer33.Add( self.m_staticline3, 0, wx.EXPAND |wx.ALL, 0 )
		
		# bSizer35 = wx.BoxSizer( wx.VERTICAL )
		
		# # bSizer36 = wx.BoxSizer( wx.VERTICAL )
		
		# sbSizer2 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"台站数据" ), wx.VERTICAL )
		
		# # bSizer38 = wx.BoxSizer( wx.VERTICAL )
		
		# # self.m_staticText12 = wx.StaticText( self, wx.ID_ANY, u"台站数据 ：", wx.DefaultPosition, wx.DefaultSize, 0 )
		# # self.m_staticText12.Wrap( -1 )
		# # bSizer38.Add( self.m_staticText12, 0, wx.ALL, 0 )
		
		
		# # bSizer36.Add( bSizer38, 1, wx.EXPAND, 5 )
		
		# bSizer39 = wx.BoxSizer( wx.HORIZONTAL )
		
		# self.m_staticText13 = wx.StaticText( self, wx.ID_ANY, u"发射台站类型： ", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText13.Wrap( -1 )
		# bSizer39.Add( self.m_staticText13, 0, wx.ALL|wx.ALIGN_CENTRE, 0 )
		
		# self.m_textCtrl6 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		# bSizer39.Add( self.m_textCtrl6, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		
		# sbSizer2.Add( bSizer39, 1, wx.EXPAND, 5 )
		
		# bSizer41 = wx.BoxSizer( wx.HORIZONTAL )
		
		# self.m_staticText14 = wx.StaticText( self, wx.ID_ANY, u"业务频段：    ", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText14.Wrap( -1 )
		# bSizer41.Add( self.m_staticText14, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		# self.m_textCtrl7 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		# bSizer41.Add( self.m_textCtrl7, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		
		# sbSizer2.Add( bSizer41, 1, wx.EXPAND, 5 )
		
		# bSizer42 = wx.BoxSizer( wx.HORIZONTAL )
		
		# self.m_staticText15 = wx.StaticText( self, wx.ID_ANY, u"信道带宽：    ", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText15.Wrap( -1 )
		# bSizer42.Add( self.m_staticText15, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		# self.m_textCtrl8 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		# bSizer42.Add( self.m_textCtrl8, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		
		# sbSizer2.Add( bSizer42, 1, wx.EXPAND, 5 )
		
		# bSizer43 = wx.BoxSizer( wx.HORIZONTAL )
		
		# self.m_staticText16 = wx.StaticText( self, wx.ID_ANY, u"调制方式：    ", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText16.Wrap( -1 )
		# bSizer43.Add( self.m_staticText16, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		# self.m_textCtrl9 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		# bSizer43.Add( self.m_textCtrl9, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		
		# sbSizer2.Add( bSizer43, 1, wx.EXPAND, 5 )
		
		
		# bSizer35.Add( sbSizer2, 15, wx.EXPAND, 10 )
		
		# # self.m_staticline4 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		# # bSizer35.Add( self.m_staticline4, 0, wx.EXPAND |wx.ALL, 5 )
		
		# # bSizer49 = wx.BoxSizer( wx.VERTICAL )
		
		
		# # bSizer49.AddSpacer(0, 1, wx.EXPAND, 5 )
		
		
		# # bSizer35.Add( bSizer49, 1, wx.EXPAND, 5 )
		
		# bSizer35.AddStretchSpacer(1) 
		
		# bSizer50 = wx.BoxSizer( wx.VERTICAL )
		
		# sbSizer3 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"实际数据" ), wx.VERTICAL )
		
		# # bSizer51 = wx.BoxSizer( wx.VERTICAL )
		
		# # bSizer52 = wx.BoxSizer( wx.VERTICAL )
		
		# # self.m_staticText121 = wx.StaticText( self, wx.ID_ANY, u"实际数据 ：", wx.DefaultPosition, wx.DefaultSize, 0 )
		# # self.m_staticText121.Wrap( -1 )
		# # bSizer52.Add( self.m_staticText121, 0, wx.ALL, 5 )
		
		
		# # bSizer51.Add( bSizer52, 1, wx.EXPAND, 5 )
		

		
		# bSizer53 = wx.BoxSizer( wx.HORIZONTAL )
		
		# self.m_staticText131 = wx.StaticText( self, wx.ID_ANY, u"发射台站类型：", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText131.Wrap( -1 )
		# bSizer53.Add( self.m_staticText131, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		# self.m_textCtrl61 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		# bSizer53.Add( self.m_textCtrl61, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		
		# sbSizer3.Add( bSizer53, 1, wx.EXPAND, 5 )
		
		# bSizer54 = wx.BoxSizer( wx.HORIZONTAL )
		
		# self.m_staticText141 = wx.StaticText( self, wx.ID_ANY, u"业务频段：    ", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText141.Wrap( -1 )
		# bSizer54.Add( self.m_staticText141, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		# self.m_textCtrl71 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		# bSizer54.Add( self.m_textCtrl71, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		
		# sbSizer3.Add( bSizer54, 1, wx.EXPAND, 5 )
		
		# bSizer55 = wx.BoxSizer( wx.HORIZONTAL )
		
		# self.m_staticText151 = wx.StaticText( self, wx.ID_ANY, u"信道带宽：    ", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText151.Wrap( -1 )
		# bSizer55.Add( self.m_staticText151, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		# self.m_textCtrl81 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		# bSizer55.Add( self.m_textCtrl81, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		
		# sbSizer3.Add( bSizer55, 1, wx.EXPAND, 5 )
		
		# bSizer56 = wx.BoxSizer( wx.HORIZONTAL )
		
		# self.m_staticText161 = wx.StaticText( self, wx.ID_ANY, u"调制方式：    ", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText161.Wrap( -1 )
		# bSizer56.Add( self.m_staticText161, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		# self.m_textCtrl91 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		# bSizer56.Add( self.m_textCtrl91, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		
		# sbSizer3.Add( bSizer56, 1, wx.EXPAND, 5 )
		
		
		# bSizer50.Add( sbSizer3, 1, wx.EXPAND, 10 )
		
		
		# bSizer35.Add( bSizer50, 15, wx.EXPAND, 5 )
		'''
		
		bSizer33.Add( self.bSizer35, 1, wx.EXPAND, 5 )
		
		
		self.SetSizer( bSizer33 )
		
	
	# def station_set(self,event):
		# pass;
	
	# def clear_station_data(self,event):
		# pass;
		
	def OnCombo2(self,event):
		self.filename=self.m_combo1.GetValue()
		#print (self.filename)
		self.list_ctrl.DeleteAllItems()   #清空之前的数据
		cf,bf,ef,band,self.longitude,self.latitude,illegal,peakPower=method.taizhan_out(self.filename)
		print (len(cf))
		for i in range(len(cf)):
			#print (i)
			self.list_ctrl.InsertItem(i,str(i+1))
			self.list_ctrl.SetItem(i,1,str(cf[i]/1e6))
			self.list_ctrl.SetItem(i,2,str(band[i]/1e6))
			self.list_ctrl.SetItem(i,3,str(peakPower[i]))
			#如果判定为不合格则标注为红色
			if illegal[i]==0:
				self.list_ctrl.SetItemBackgroundColour(i, "red")
		
		#更新地图
		self.m_htmlWin2.LoadURL(os.getcwd()+'/map6.html')
		self.Bind(wx.html2.EVT_WEBVIEW_LOADED,self.deal_html,self.m_htmlWin2)
	
	
	def deal_html(self,event):
		'''
		for i in self.a:
			lng=self.a[i][0]
			lat=self.a[i][1]
			u1="document.getElementById('longitude').value="+str(lng)+";"
			self.m_htmlWin2.RunScript(u1)
			u2="document.getElementById('latitude').value="+str(lat)+";"
			self.m_htmlWin2.RunScript(u2)
			u3="document.getElementById('measure_point').value="+str(i)+";"
			self.m_htmlWin2.RunScript(u3)
			self.m_htmlWin2.RunScript("document.getElementById('add_point').click();")
		for j in self.b:
			lng=self.b[j][0]
			lat=self.b[j][1]
			u1="document.getElementById('longitude').value="+str(lng)+";"
			self.m_htmlWin2.RunScript(u1)
			u2="document.getElementById('latitude').value="+str(lat)+";"
			self.m_htmlWin2.RunScript(u2)
			u3="document.getElementById('station_NO').value="+str(j)+";"
			self.m_htmlWin2.RunScript(u3)
			self.m_htmlWin2.RunScript("document.getElementById('add_station').click();")
		'''
		#刷新地图
		#self.m_htmlWin2.RunScript("document.getElementById('change_title').click();")
		
		#增加结点
		if self.longitude!=-1:
			print ('no GPS')
			lng=self.longitude[0]
			lat=self.latitude[0]
			print ('location in deal_html: '+str(lng) +' , '+ str(lat))
			u1="document.getElementById('longitude').value="+str(lng)+";"
			self.m_htmlWin2.RunScript(u1)
			u2="document.getElementById('latitude').value="+str(lat)+";"
			self.m_htmlWin2.RunScript(u2)
			u3="document.getElementById('measure_point').value="+str('station')+";"
			self.m_htmlWin2.RunScript(u3)
			self.m_htmlWin2.RunScript("document.getElementById('add_point').click();")

'''
	def OnTitle(self,event):
		self.title_changed=event.GetString()
		self.title_changed1=self.title_changed[1:-1]
		print (self.title_changed1)
		if self.title_changed1=='start':
			self.page_start=1
		if self.page_start==1:
			if (self.pre_title!=self.title_changed) and (self.title_changed1!='start'):
				self.pre_title=self.title_changed
				print (self.pre_title,1)
				if self.pre_title[1]=='s':        #判断是否点击了台站
					number=int(self.pre_title[0])
					print (number)
					print (self.b[number])
					self.m_textCtrl6.SetValue(self.b[number][2][0])
					self.m_textCtrl7.SetValue(str(self.b[number][2][2]/(1e6))+'-'+str(self.b[number][2][3]/(1e6))+'MHz')
					self.m_textCtrl8.SetValue(str(self.b[number][2][1]/(1e6))+'MHz')
					self.m_textCtrl9.SetValue(self.b[number][2][4])
					self.start_freq=self.b[number][2][2]
					self.end_freq=self.b[number][2][3]
				if self.pre_title[1]=='p':        #判断是否点击了测量点
					number=self.pre_title[0]
					print (number)
					self.m_textCtrl61.SetValue(self.pre_title)
					self.m_textCtrl71.SetValue(self.pre_title)
					self.m_textCtrl81.SetValue(self.pre_title)
					self.m_textCtrl91.SetValue(self.pre_title)
'''

###########################################################################
## Class MyPanel8
###########################################################################
'''
class MyPanel8 ( wx.Panel ):
	
	def __init__( self, parent ):
		wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 500,300 ), style = wx.TAB_TRAVERSAL )
		
		bSizer72 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer73 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer76 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText32 = wx.StaticText( self, wx.ID_ANY, u"监测数据选择：", wx.DefaultPosition, wx.DefaultSize, 0 )
		#self.m_staticText32.Wrap( -1 )
		bSizer76.Add( self.m_staticText32, 0, wx.ALL, 5 )
		
		m_choice6Choices = []
		self.m_choice6 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, m_choice6Choices, 0 )
		self.m_choice6.SetSelection( 0 )
		bSizer76.Add( self.m_choice6, 0, wx.ALL, 5 )
		
		
		bSizer73.Add( bSizer76, 1, wx.EXPAND, 5 )
		
		bSizer77 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText33 = wx.StaticText( self, wx.ID_ANY, u"监测数据选取：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText33.Wrap( -1 )
		bSizer77.Add( self.m_staticText33, 0, wx.ALL, 5 )
		
		self.m_slider2 = wx.Slider( self, wx.ID_ANY, 50, 0, 100, wx.Point( -1,-1 ), wx.DefaultSize, wx.SL_HORIZONTAL )
		bSizer77.Add( self.m_slider2, 0, wx.ALL|wx.FIXED_MINSIZE, 5 )
		
		
		bSizer73.Add( bSizer77, 1, wx.EXPAND, 5 )
		
		bSizer78 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText34 = wx.StaticText( self, wx.ID_ANY, u"信道带宽选择：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText34.Wrap( -1 )
		bSizer78.Add( self.m_staticText34, 0, wx.ALL, 5 )
		
		self.m_slider3 = wx.Slider( self, wx.ID_ANY, 50, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		bSizer78.Add( self.m_slider3, 0, wx.ALL, 5 )
		
		
		bSizer73.Add( bSizer78, 1, wx.EXPAND, 5 )
		
		
		bSizer72.Add( bSizer73, 2, wx.EXPAND, 5 )
		
		self.m_staticline1 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer72.Add( self.m_staticline1, 0, wx.EXPAND |wx.ALL, 5 )
		
		bSizer74 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer79 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText35 = wx.StaticText( self, wx.ID_ANY, u"信道占用度", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText35.Wrap( -1 )
		bSizer79.Add( self.m_staticText35, 0, wx.ALL, 5 )
		
		bSizer79.AddStretchSpacer(1) 
		
		self.m_staticText36 = wx.StaticText( self, wx.ID_ANY, u"信道化宽度：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText36.Wrap( -1 )
		bSizer79.Add( self.m_staticText36, 0, wx.ALL, 5 )
		
		self.m_staticText37 = wx.StaticText( self, wx.ID_ANY, u"MyLabel", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText37.Wrap( -1 )
		bSizer79.Add( self.m_staticText37, 0, wx.ALL, 5 )
		
		
		bSizer74.Add( bSizer79, 1, wx.EXPAND, 5 )
		
		bSizer80 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_panel8 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer80.Add( self.m_panel8, 1, wx.EXPAND |wx.ALL, 5 )
		
		
		bSizer74.Add( bSizer80, 3, wx.EXPAND, 5 )
		
		
		bSizer72.Add( bSizer74, 4, wx.EXPAND, 5 )
		
		self.m_staticline2 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer72.Add( self.m_staticline2, 0, wx.EXPAND |wx.ALL, 5 )
		
		bSizer75 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer81 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_staticText38 = wx.StaticText( self, wx.ID_ANY, u"频谱占用度", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText38.Wrap( -1 )
		bSizer81.Add( self.m_staticText38, 0, wx.ALL, 5 )
		
		
		bSizer75.Add( bSizer81, 1, wx.EXPAND, 5 )
		
		bSizer82 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_panel9 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer82.Add( self.m_panel9, 1, wx.EXPAND |wx.ALL, 5 )
		
		
		bSizer75.Add( bSizer82, 3, wx.EXPAND, 5 )
		
		
		bSizer72.Add( bSizer75, 4, wx.EXPAND, 5 )
		
		
		self.SetSizer( bSizer72 )
'''
###########################################################################
## Class MyPanel3  频谱占用度
###########################################################################	

class MyPanel3 ( wx.Panel ):
	
	def __init__( self, parent ):
		wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 500,300 ), style = wx.TAB_TRAVERSAL )
		
		bSizer72 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer73 = wx.BoxSizer( wx.HORIZONTAL )
		
		bSizer283 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_staticText120 = wx.StaticText( self, wx.ID_ANY, u"监测数据选择：", wx.DefaultPosition, (200,20), 0 )
		self.m_staticText120.Wrap( -1 )
		bSizer283.Add( self.m_staticText120, 1, wx.ALL|wx.EXPAND, 5 )
		
		self.m_staticText121 = wx.StaticText( self, wx.ID_ANY, u"监测数据选取：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText121.Wrap( -1 )
		bSizer283.Add( self.m_staticText121, 1, wx.ALL, 5 )
		
		self.m_staticText122 = wx.StaticText( self, wx.ID_ANY, u"信道带宽选择：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText122.Wrap( -1 )
		bSizer283.Add( self.m_staticText122, 1, wx.ALL, 5 )
		
		
		bSizer73.Add( bSizer283, 1, wx.EXPAND, 5 )
		
		bSizer284 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer285=wx.BoxSizer(wx.HORIZONTAL)
		self.m_choice42Choices = method.file_to_list(list(reversed(os.listdir(method.config_data['Spec_dir']))))
		self.choice_Num=len(self.m_choice42Choices)
		self.m_combo1 = wx.ComboBox( self, wx.ID_ANY, u'请选择文件...',wx.DefaultPosition, (300,20), self.m_choice42Choices, 0 )
		self.m_combo1.Bind(wx.EVT_COMBOBOX, self.OnCombo1)
		bSizer285.Add( self.m_combo1, 0, wx.ALL, 5 )
		self.m_staticText127 = wx.StaticText( self, wx.ID_ANY, "           ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText127.Wrap( -1 )
		bSizer285.Add( self.m_staticText127,0, wx.ALL, 5 )
		#bSizer285.AddStretchSpacer(1)
		self.m_button51 = wx.Button( self, wx.ID_ANY, u"信道占用度分析", wx.DefaultPosition, (150,20), 0 )
		bSizer285.Add( self.m_button51,0, wx.ALL, 5 )
		self.m_button51.Bind( wx.EVT_BUTTON, self.start_channel_occ )
		self.m_button52 = wx.Button( self, wx.ID_ANY, u"频谱占用度分析", wx.DefaultPosition, (150,20), 0 )
		bSizer285.Add( self.m_button52,0, wx.ALL, 5 )
		self.m_button52.Bind( wx.EVT_BUTTON, self.start_spectrum_occ )
		
		bSizer284.Add( bSizer285, 2, wx.EXPAND, 5 )
		bSizer284.AddStretchSpacer(1) 
		
		bSizer290 = wx.BoxSizer( wx.HORIZONTAL )
		self.m_slider9 = wx.Slider( self, wx.ID_ANY, 25, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		bSizer290.Add( self.m_slider9, 1, wx.ALL|wx.EXPAND, 0 )
		self.m_staticText123 = wx.StaticText( self, wx.ID_ANY, "00:00:00", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText123.Wrap( -1 )
		bSizer290.Add( self.m_staticText123, 1, wx.ALL, 0 )
		self.m_slider11 = wx.Slider( self, wx.ID_ANY, 75, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL )
		bSizer290.Add( self.m_slider11, 1, wx.ALL|wx.EXPAND,0 )
		self.m_staticText124 = wx.StaticText( self, wx.ID_ANY, "00:00:00", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText124.Wrap( -1 )
		bSizer290.Add( self.m_staticText124, 1, wx.ALL, 0 )
		bSizer284.Add( bSizer290, 2, wx.EXPAND, 5 )
		
		bSizer291 = wx.BoxSizer( wx.HORIZONTAL )
		self.m_slider10 = wx.Slider( self, wx.ID_ANY, 25, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL)
		bSizer291.Add( self.m_slider10, 1, wx.ALL|wx.EXPAND, 0 )
		self.m_staticText125 = wx.StaticText( self, wx.ID_ANY, "0 MHz", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText125.Wrap( -1 )
		bSizer291.Add( self.m_staticText125, 1, wx.ALL, 0 )
		self.m_slider12 = wx.Slider( self, wx.ID_ANY, 75, 0, 100, wx.DefaultPosition, wx.DefaultSize, wx.SL_HORIZONTAL)
		bSizer291.Add( self.m_slider12, 1, wx.ALL|wx.EXPAND, 0 )
		self.m_staticText126 = wx.StaticText( self, wx.ID_ANY, "0 MHz", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText126.Wrap( -1 )
		bSizer291.Add( self.m_staticText126, 1, wx.ALL, 0 )
		bSizer284.Add( bSizer291,2, wx.EXPAND, 5 )
		
		
		bSizer73.Add( bSizer284, 6, wx.EXPAND, 5 )
		
		
		bSizer72.Add( bSizer73, 3, wx.EXPAND, 5 )
		
		self.m_staticline10 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer72.Add( self.m_staticline10, 0, wx.EXPAND |wx.ALL, 0 )
		
		bSizer74 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer79 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText35 = wx.StaticText( self, wx.ID_ANY, u"信道占用度", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText35.Wrap( -1 )
		bSizer79.Add( self.m_staticText35, 0, wx.ALL, 5 )
		
		bSizer79.AddStretchSpacer(1) 
		
		self.m_staticText36 = wx.StaticText( self, wx.ID_ANY, u"频率分辨率：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText36.Wrap( -1 )
		bSizer79.Add( self.m_staticText36, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		self.m_textCtrl37 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (150,20),wx.TE_RICH2)
		bSizer79.Add( self.m_textCtrl37, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		
		bSizer74.Add( bSizer79, 1, wx.EXPAND, 5 )
		
		bSizer80 = wx.BoxSizer( wx.HORIZONTAL)
		
		#面板凸起可以用 wx.BORDER_RAISED
		self.m_panel8 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL|wx.SIMPLE_BORDER)
		bSizer80.Add( self.m_panel8, 6, wx.EXPAND|wx.ALL, 5 )
		
		# self.m_panel10 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL|wx.SIMPLE_BORDER)
		# bSizer80.Add( self.m_panel10, 1, wx.EXPAND|wx.ALL, 5 )
		# self.bSizer1 = wx.BoxSizer( wx.VERTICAL )
		
		# self.m_panel11 = wx.Panel( self.m_panel10, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL|wx.SIMPLE_BORDER )
		# self.m_staticText35 = wx.StaticText( self_m_panel11, wx.ID_ANY, u"", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText35.Wrap( -1 )
		
		
		#面板上画坐标轴
		self.m_panel8_x,self.m_panel8_y=self.m_panel8.GetSize()
		# print (2,self.m_panel8_x,self.m_panel8_y)
		# print (wx.ScreenDC().GetPPI())
		#self.figure_score3,axes_score4,self.l_user1=method.draw_picture([],[],'The-signalChannel-occupancy',"Frequency/MHz","Percentage/%",2.2,9,'w','w')
		#self.figureCanvas1=FigureCanvas(self.m_panel8, -1, self.figure_score3)
		######
		self.figure_score3 = Figure((11.1,2.2),100)
		self.figureCanvas1=FigureCanvas(self.m_panel8, -1, self.figure_score3)
		self.axes_score4 = self.figure_score3.add_subplot(111,facecolor='w')
		#self.l_user1,=self.axes_score4.plot([], [], 'b')
		#self.axes_score.axhline(y=average, color='r')
		self.axes_score4.set_ylim(0,100)
		self.axes_score4.set_title('The-signalChannel-occupancy')
		self.axes_score4.grid(True,color='y')
		self.axes_score4.set_xlabel('Frequency/Hz')
		self.axes_score4.set_ylabel('Percentage/%')
		self.figureCanvas1.draw()
		
		#####
		#self.figureCanvas1.SetSize(self.m_panel8_x,self.m_panel8_y)
		
		bSizer74.Add( bSizer80, 8, wx.EXPAND, 5 )
		
		
		bSizer72.Add( bSizer74, 8, wx.EXPAND, 5 )
		
		self.m_staticline11 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		bSizer72.Add( self.m_staticline11, 0, wx.EXPAND |wx.ALL, 0 )
		
		bSizer75 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer81 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText38 = wx.StaticText( self, wx.ID_ANY, u"频谱占用度", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText38.Wrap( -1 )
		bSizer81.Add( self.m_staticText38, 0, wx.ALL, 5 )
		
		bSizer81.AddStretchSpacer(1) 
		
		self.m_staticText36 = wx.StaticText( self, wx.ID_ANY, u"时间分辨率：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText36.Wrap( -1 )
		bSizer81.Add( self.m_staticText36, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		self.m_textCtrl38= wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (150,20),wx.TE_RICH2)
		bSizer81.Add( self.m_textCtrl38, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		
		bSizer75.Add( bSizer81, 1, wx.EXPAND, 5 )
		
		bSizer82 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_panel9 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL|wx.SIMPLE_BORDER )
		bSizer82.Add( self.m_panel9, 1, wx.EXPAND |wx.ALL, 5 )
		
		
		
		#画板上画坐标轴
		#self.figure_score4,axes_score5,self.l_user2=method.draw_picture([],[],'The-Spectrum-Occupancy',"Time/hour","Percentage/%",2.2,9,'w','w')
		#FigureCanvas(self.m_panel9, -1, self.figure_score4)
		
		######
		self.figure_score4 = Figure((11.1,2.2),100)
		self.figureCanvas2=FigureCanvas(self.m_panel9, -1, self.figure_score4)
		self.axes_score5 = self.figure_score4.add_subplot(111,facecolor='w')
		self.l_user2,=self.axes_score5.plot([], [], 'b')
		#self.axes_score.axhline(y=average, color='r')
		self.axes_score5.set_ylim(0,100)
		self.axes_score5.set_title('The-Spectrum-Occupancy')
		self.axes_score5.grid(True,color='y')
		self.axes_score5.set_xlabel('Time/hour')
		self.axes_score5.set_ylabel('Percentage/%')
		self.figureCanvas2.draw()
		######
		
		bSizer75.Add( bSizer82, 8, wx.EXPAND, 5 )
		bSizer72.Add( bSizer75, 8, wx.EXPAND, 5 )
		

		# self.timer = wx.Timer(self)#创建定时器
		# self.Bind(wx.EVT_TIMER, self.onTimer,self.timer)  #设置定时事件
		# self.timer.Start(1000)
		self.start_time=0
		self.end_time=0
		self.retain_time=0
		self.start_freq=0
		self.end_freq=0
		self.initial_time1=0
		self.initial_time2=0
		self.initial_freq3=0
		self.initial_freq4=0
		self.SetSizer( bSizer72 )
		self.Fit()
		self.Layout()
		
	def OnCombo1(self,event):
		self.filename=method.list_to_file(self.m_combo1.GetValue())
		#print (self.filename)
		self.start_time,self.end_time,self.retain_time,self.start_freq,self.end_freq,self.path=method.read_file(self.filename)
		#print (self.start_time,self.end_time,self.retain_time)
		initial_value1=self.m_slider9.GetValue()
		self.initial_time1=self.start_time+datetime.timedelta(seconds=self.retain_time*initial_value1//100)
		#print (self.initial_time1)
		self.m_staticText123.SetLabel(str(self.initial_time1))
		
		initial_value2=self.m_slider11.GetValue()
		self.initial_time2=self.start_time+datetime.timedelta(seconds=self.retain_time*initial_value2//100)
		#print (self.initial_time2)
		self.m_staticText124.SetLabel(str(self.initial_time2))
		
		initial_value3=self.m_slider10.GetValue()
		self.initial_freq3=self.start_freq+(self.end_freq-self.start_freq)*initial_value3/100
		self.m_staticText125.SetLabel(str(self.initial_freq3/1e6)+'MHz')
		
		initial_value4=self.m_slider12.GetValue()
		self.initial_freq4=self.start_freq+(self.end_freq-self.start_freq)*initial_value4//100
		self.m_staticText126.SetLabel(str(self.initial_freq4/1e6)+'MHz')
		
	def start_channel_occ(self,event):
		#测试数据库的使用
		try:
			method.test_oracle_connection()
			print ('oracle_sucess')
		except:
			wx.MessageBox(u' 数据库连接不成功', "Message" ,wx.OK | wx.ICON_INFORMATION)
		if self.start_time!=0:
			if self.end_time!=0:
				if self.initial_time1>self.initial_time2:
					self.initial_time1,self.initial_time2=self.initial_time2,self.initial_time1
				if self.initial_freq3>self.initial_freq4:
					self.initial_freq3,self.initial_freq4=self.initial_freq4,self.initial_freq3
				self.figure_score,self.axes_score=self.channel_occ(self.initial_time1,self.initial_time2,self.filename[0:19],self.initial_freq3,self.initial_freq4)
				self.canvas3 = FigureCanvas(self.m_panel8, wx.ID_ANY, self.figure_score)
				self.canvas3.draw()
				self.m_panel8.Refresh()
	
	def start_spectrum_occ(self,event):
		#测试数据库的使用
		try:
			method.test_oracle_connection()
			print ('oracle_sucess')
		except:
			wx.MessageBox(u' 数据库连接不成功', "Message" ,wx.OK | wx.ICON_INFORMATION)
		if self.start_time!=0:
			if self.end_time!=0:
				if self.initial_time1>self.initial_time2:
					self.initial_time1,self.initial_time2=self.initial_time2,self.initial_time1
				if self.initial_freq3>self.initial_freq4:
					self.initial_freq3,self.initial_freq4=self.initial_freq4,self.initial_freq3
				self.figure_score1,self.axes_score1=self.plot_spectrum_occ(self.initial_time1,self.initial_time2,self.filename[0:19],self.initial_freq3,self.initial_freq4)
				self.canvas4 = FigureCanvas(self.m_panel9, wx.ID_ANY, self.figure_score1)
				self.canvas4.draw()
				self.m_panel9.Refresh()
				
	def channel_occ(self,start_time,stop_time,task_name,freq_start,freq_stop):
		# 输入就是起始时间、终止时间、任务名称、起始频率、终止频率
		step = float(freq_stop - freq_start) / 20
		self.m_textCtrl37.SetValue(str(step/1e6)+' MHz')
		sql2 = "select COUNT,Task_L from minitor_task where Task_Name='%s'" % (task_name)
		#con=mdb.connect(mysql_config['host'],mysql_config['user'],mysql_config['password'],mysql_config['database'])
		con = cx_Oracle.Connection(conn_str1) 
		#con = mdb.connect('localhost', 'root', 'cdk120803', 'ceshi1')
		b = pandas.read_sql(sql2, con)
		print ('Print task_name and b in channel_occ')
		print (task_name)
		print (b)
		retain_time = float(b['TASK_L'])
		l = (stop_time - start_time).seconds
		roid = l/retain_time
		#print (roid)
		# 绘制柱状图
		figure_score = Figure((11.1,2.2),100)
		axes_score = figure_score.add_subplot(111,facecolor='w')
		axes_score.set_title("Channel Occupation Rate")
		axes_score.set_xlabel("Frequency /MHz",fontsize=12)
		axes_score.set_ylabel("Channel Occupation /%")
		#axes_score.grid(True,color='w')
		if not b.empty:
			print('not empty')
			channel_occupied = []
			for i in range(20):
				start_f = freq_start + i * step
				stop_f = freq_start + (i + 1) * step
				sql1 = "select count1 from SPECTRUM_IDENTIFIED where Task_Name='%s' and FREQ_CF between %f and %f "%(task_name, float(start_f), float(stop_f))+"and Start_time between to_date('%s',"%(start_time)+ "'yyyy-MM-dd hh24:mi:ss')"+"and to_date('%s'," % (stop_time)+ "'yyyy-MM-dd hh24:mi:ss')"
				a = pandas.read_sql(sql1, con)
				a = a.drop_duplicates()  # 去电重复项
				channel_occupied1 = len(a) / float(b['COUNT'])
				channel_occupied.append(channel_occupied1*100)


			axis_x = arange(freq_start, freq_stop, step)
			axis_y = channel_occupied
			#print (axis_x,axis_y)
			# axes_score.bar(axis_x, array(axis_y)+10)
			# self.axes_score4.bar(axis_x, axis_y)
			
			above_index=[i for i in range(len(axis_y)) if axis_y[i]>=1]
			#print (above_index,axis_y[above_index[0]])
			label=[str(axis_y[i])[0:5]+'%' for i in above_index]
			axes_score.bar(axis_x+step/2, axis_y, step)
			axes_score.set_xticks(axis_x[::2])
			#axes_score.set_xticklabels(axis_x,rotation=40,fontproperties=5)
			#axes_score.set_xlim([axis_x[0],axis_x[-1]])
			
			for i in range(len(above_index)):
				#axes_score.plot(above_index[i],axis_y[above_index[i]],'ro')
				axes_score.get_children()[above_index[i]].set_color('r')
				txt=axes_score.text(axis_x[above_index[i]],axis_y[above_index[i]],'%s'%label[i],fontsize=7,color='r')
		else:
			print('empty')
		return figure_score,axes_score
		
	def plot_spectrum_occ(self,start_time,stop_time,task_name,freq_start,freq_stop):
		starttime = datetime.datetime.strptime(str(start_time), "%Y-%m-%d %H:%M:%S")
		stoptime = datetime.datetime.strptime(str(stop_time), "%Y-%m-%d %H:%M:%S")
		#print (starttime)
		#print (stoptime)
		delta = int((stoptime - starttime).seconds)  #先以s为单位
		slot2=delta/40;   #40个点，每个点代表的时间长度
		if delta>2400:
			self.m_textCtrl38.SetValue(str((slot2/(60)))[0:8]+' 分钟')
		else:
			self.m_textCtrl38.SetValue(str((slot2))[0:8]+' 秒')
		#print (delta)
		occ1 = []
		figure_score = Figure((11.1,2.2),100)
		axes_score = figure_score.add_subplot(111,facecolor='w')
		axes_score.set_title("Spectrum Occupation Rate")
		#axes_score.set_xlabel("Time")
		axes_score.set_ylabel("Spectrum Occupation Rate /%")
		divide=int(delta/slot2)
		#print (divide)
		for i in range(divide):
			s_t = starttime + datetime.timedelta(seconds = (i*slot2))
			e_t = starttime + datetime.timedelta(seconds = ((i+1)*slot2))
			s_t = str(s_t)[0:19]
			e_t = str(e_t)[0:19]
			occ1_1 = self.spectrum_occ(s_t,e_t,task_name,freq_start,freq_stop)
			occ1.append(occ1_1)
		#print('occ1',occ1)
		'''
		time_slot=linspace(1,divide,divide)
		dates=[]
		for i in range(divide):
			dates.append(str(starttime+datetime.timedelta(seconds=time_slot[i]*10)))
		a=[datetime.datetime.strptime(d,"%Y-%m-%d %H:%M:%S") for d in dates]
		#print (a)
		axes_score.xaxis.set_major_formatter(mdates.DateFormatter("%Y-%m-%d %H:%M:%S"))
		axes_score.xaxis.set_major_locator(mdates.MinuteLocator())
		if len(a)>=2:
			#axes_score.set_xlim(a[0],a[-1])
			axes_score.set_xlim(0,len(occ1))
		# for label in axes_score.get_xticklabels():
			# label.set_rotation(0)
		'''
		#print ('xinhao:',a,occ1)
		#axes_score.plot(a,occ1)
		axes_score.set_xlim(0,len(occ1)-1)
		axis_x=list(range(len(occ1)))
		peak=max(occ1)
		peak_index=argmax(occ1)
		above_index=[i for i in range(len(occ1)) if occ1[i]>=1]
		#label=[str(starttime+datetime.timedelta(seconds=slot2*i))[0:19]+' '+str(occ1[i])[0:4]+'%' for i in above_index];
		label=[str(occ1[i])[0:4]+'%' for i in above_index];
		#axes_score.plot(axis_x,occ1)
		step=1
		peak_occ=argmax(occ1)
		axes_score.bar(axis_x,occ1,step/2)
		
		for i in range(len(above_index)):
			axes_score.plot(above_index[i],occ1[above_index[i]],'ro')
			axes_score.get_children()[above_index[i]].set_color('r')
			#txt=axes_score.text(above_index[i]-1,occ1[above_index[i]],'%s'%label[i],fontsize=7,color='r')
		labelpeak = str(starttime+datetime.timedelta(seconds=slot2*peak_index))[0:39]+' '+'%.2f'%peak+'%'
		print (peak_index,labelpeak)
		txt = axes_score.text(peak_index-1,peak,labelpeak,fontsize=7,color='k')
		#print (occ1)
		return figure_score,axes_score
		
	def spectrum_occ(self,start_time,stop_time,task_name,freq_start,freq_stop):
		# 输入就是起始时间、终止时间、任务名称、起始频率、终止频率
		spectrum_span = freq_stop - freq_start
		# 以一个小时为单位
		#print (task_name,freq_start,freq_stop)
		sql3 = "select FreQ_BW, COUNT1 from SPECTRUM_IDENTIFIED where Task_Name='%s' and FREQ_CF between %f and %f" % (task_name, float(freq_start), float(freq_stop)) + "and Start_time between to_date('%s'," % (start_time) +"'yyyy-MM-dd hh24:mi:ss')" + "and to_date('%s'," % (stop_time) +"'yyyy-MM-dd hh24:mi:ss')"
		#con=mdb.connect(mysql_config['host'],mysql_config['user'],mysql_config['password'],mysql_config['database'])
		con = cx_Oracle.Connection(conn_str1) 
		#con = mdb.connect('localhost', 'root', 'cdk120803', 'ceshi1')
		c = pandas.read_sql(sql3, con)
		#print (c)
		con.commit()
		con.close()
		spectrum_occ1 = sum(c['FREQ_BW'])
		if len(c['COUNT1'])>0:
			c1 = array(c['COUNT1'])
			num = max(c['COUNT1']) - min(c['COUNT1'])+1
			spectrum_occ = spectrum_occ1 *100/ float(spectrum_span*num)
		else:
			#print ('count:',len(c['COUNT1']))
			spectrum_occ = 0
		return spectrum_occ  # 返回频谱占用度


###########################################################################
## Class MyPanel4 测向模块
###########################################################################

class MyPanel4 ( wx.Panel ):
	
	def __init__( self, parent ):
		wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 602,300 ), style = wx.TAB_TRAVERSAL )
		bSizer90=wx.BoxSizer(wx.HORIZONTAL)
		bSizerLeft=wx.BoxSizer(wx.VERTICAL)
		###############################################放置输入信息框
		self.bxLetft=wx.StaticBox( self, wx.ID_ANY, u"信号强度信息表：" )
		self.bxLetft.SetForegroundColour("SLATE BLUE")
		fontLeft = wx.Font(10, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bxLetft.SetFont(fontLeft)
		self.bSizer1 = wx.StaticBoxSizer( self.bxLetft, wx.HORIZONTAL )
		#self.bSizer1 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.bSizer2 = wx.BoxSizer( wx.VERTICAL )
		# 中心频率输入控件
		self.bSizer4 = wx.BoxSizer( wx.HORIZONTAL )
		self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, u"中心频率：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )
		self.bSizer4.Add( self.m_staticText1, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		#self.m_textCtrl1 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_textCtrl1 = wx.TextCtrl( self, wx.ID_ANY, '800', wx.DefaultPosition, wx.DefaultSize, wx.TE_PROCESS_ENTER  )
		self.Bind(wx.EVT_TEXT_ENTER, self.OnChangeDirectionFre, self.m_textCtrl1)
		self.m_textCtrl1.Bind(wx.EVT_KILL_FOCUS,self.OnChangeDirectionFre)
		self.bSizer4.Add( self.m_textCtrl1, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		m_choice1Choices = ['KHz','MHz','GHz']
		self.m_choice1 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, (50,20), m_choice1Choices, 0 )
		self.m_choice1.SetSelection( 1 )
		self.bSizer4.Add( self.m_choice1, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		#self.m_choice1.Bind(wx.EVT_CHOICE,self.OnChangeDirectionFreUnit)
		self.bSizer2.Add( self.bSizer4, 1, wx.EXPAND, 5 )
		
		# 测向带宽控件
		self.bSizer5 = wx.BoxSizer( wx.HORIZONTAL )
		self.m_staticText3 = wx.StaticText( self, wx.ID_ANY, u"测向带宽：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText3.Wrap( -1 )
		self.bSizer5.Add( self.m_staticText3, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		#self.m_textCtrl2 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_textCtrl2 = wx.TextCtrl( self, wx.ID_ANY, '20', wx.DefaultPosition, wx.DefaultSize, wx.TE_PROCESS_ENTER )
		self.Bind(wx.EVT_TEXT_ENTER, self.OnChangeDirectionBand, self.m_textCtrl2)
		self.m_textCtrl1.Bind(wx.EVT_KILL_FOCUS,self.OnChangeDirectionBand)
		self.bSizer5.Add( self.m_textCtrl2, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		m_choice2Choices = ['MHz']
		self.m_choice2 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, (50,20), m_choice2Choices, 0 )
		self.m_choice2.SetSelection( 0)
		self.bSizer5.Add( self.m_choice2, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		#self.m_choice2.Bind(wx.EVT_CHOICE,self.OnChangeDirectionBandUnit)
		self.bSizer2.Add( self.bSizer5, 1, wx.EXPAND, 5 )
		self.bSizer1.Add( self.bSizer2, 1, wx.EXPAND, 5 )
		
		# bSizer6 = wx.BoxSizer( wx.HORIZONTAL )
		
		# self.m_staticText5 = wx.StaticText( self, wx.ID_ANY, u"参考电平：", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText5.Wrap( -1 )
		# bSizer6.Add( self.m_staticText5, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		# #self.m_textCtrl3 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_textCtrl3 = wx.TextCtrl( self, wx.ID_ANY, '2', wx.DefaultPosition, wx.DefaultSize, wx.TE_PROCESS_ENTER )
		# bSizer6.Add( self.m_textCtrl3, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		# self.Bind(wx.EVT_TEXT_ENTER, self.OnChangeDirectionRefLevel, self.m_textCtrl3)
		# self.m_textCtrl3.Bind(wx.EVT_KILL_FOCUS,self.OnChangeDirectionRefLevel)
		
		# self.m_staticText6 = wx.StaticText( self, wx.ID_ANY, u"dBmV", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText6.Wrap( -1 )
		# bSizer6.Add( self.m_staticText6, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )

		
		# # self.bSizer2.Add( bSizer6, 1, wx.EXPAND, 5 )
		
		# self.bSizer1.Add( self.bSizer2, 1, wx.EXPAND, 5 )
		
		self.bSizer3 = wx.BoxSizer( wx.VERTICAL )
		# RBW输入控件
		self.bSizer7 = wx.BoxSizer( wx.HORIZONTAL )
		self.m_staticText7 = wx.StaticText( self, wx.ID_ANY, u"RBW :", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText7.Wrap( -1 )
		self.bSizer7.Add( self.m_staticText7, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		self.m_textCtrl4 = wx.TextCtrl( self, wx.ID_ANY,'1', wx.DefaultPosition, wx.DefaultSize, wx.TE_PROCESS_ENTER  )
		self.bSizer7.Add( self.m_textCtrl4, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		self.Bind(wx.EVT_TEXT_ENTER, self.OnChangeDirectionRBW, self.m_textCtrl4)
		self.m_textCtrl4.Bind(wx.EVT_KILL_FOCUS,self.OnChangeDirectionRBW)
		m_choice3Choices = ['KHz']
		self.m_choice3 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, (50,20), m_choice3Choices, 0 )
		self.m_choice3.SetSelection( 0 )
		self.bSizer7.Add( self.m_choice3, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		#self.m_choice3.Bind(wx.EVT_CHOICE,self.OnChangeDirectionRBWUnit)
		self.bSizer3.Add( self.bSizer7, 1, wx.EXPAND, 5 )
		
		# 参考电平控件
		self.bSizer8 = wx.BoxSizer( wx.HORIZONTAL )
		self.m_staticText5 = wx.StaticText( self, wx.ID_ANY, u"参考电平：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText5.Wrap( -1 )
		self.bSizer8.Add( self.m_staticText5, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		self.m_textCtrl3 = wx.TextCtrl( self, wx.ID_ANY, '0', wx.DefaultPosition, wx.DefaultSize, wx.TE_PROCESS_ENTER )
		self.bSizer8.Add( self.m_textCtrl3, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		self.Bind(wx.EVT_TEXT_ENTER, self.OnChangeDirectionRefLevel, self.m_textCtrl3)
		self.m_textCtrl3.Bind(wx.EVT_KILL_FOCUS,self.OnChangeDirectionRefLevel)
		self.m_staticText6 = wx.StaticText( self, wx.ID_ANY, u"dBmV", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText6.Wrap( -1 )
		self.bSizer8.Add( self.m_staticText6, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		self.bSizer3.Add( self.bSizer8, 1, wx.EXPAND, 5 )
		
		# VBW 输入控件
		# self.bSizer8 = wx.BoxSizer( wx.HORIZONTAL )
		# self.m_staticText9 = wx.StaticText( self, wx.ID_ANY, u"VBW :", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText9.Wrap( -1 )
		# self.bSizer8.Add( self.m_staticText9, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		# #self.m_textCtrl5 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, wx.TE_PROCESS_ENTER )
		# self.m_textCtrl5 = wx.TextCtrl( self, wx.ID_ANY, '1', wx.DefaultPosition, wx.DefaultSize, wx.TE_PROCESS_ENTER )
		# self.bSizer8.Add( self.m_textCtrl5, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		# self.Bind(wx.EVT_TEXT_ENTER, self.OnChangeVBW, self.m_textCtrl5)
		# self.m_textCtrl5.Bind(wx.EVT_KILL_FOCUS, self.OnChangeVBW)
		
		# # self.m_staticText11 = wx.StaticText( self, wx.ID_ANY, u"kHz", wx.DefaultPosition, wx.DefaultSize, 0 )
		# # self.m_staticText11.Wrap( -1 )
		# # self.bSizer8.Add( self.m_staticText11, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		# m_choice4Choices = ['KHz']
		# self.m_choice4 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, (50,20), m_choice4Choices, 0 )
		# self.m_choice4.SetSelection( 0 )
		# self.bSizer8.Add( self.m_choice4, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		# self.bSizer3.Add( self.bSizer8, 1, wx.EXPAND, 5 )
		
		# self.bSizer9 = wx.BoxSizer( wx.HORIZONTAL )
		
		# self.m_staticText12 = wx.StaticText( self, wx.ID_ANY, u"", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText12.Wrap( -1 )
		# self.bSizer9.Add( self.m_staticText12, 0, wx.ALIGN_CENTER_VERTICAL|wx.ALL, 5 )
		
		# self.bSizer3.Add( self.bSizer9, 1, wx.EXPAND, 5 )
		self.bSizer1.Add( self.bSizer3, 1, wx.EXPAND, 5 )
		bSizerLeft.Add(self.bSizer1, 2 ,wx.EXPAND,0)
		
		self.m_staticline15 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_VERTICAL )
		bSizerLeft.Add( self.m_staticline15, 0, wx.EXPAND |wx.ALL, 1 )
		
		###############################################放置坐标轴
		self.m_panelLeft = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizerLeft.Add( self.m_panelLeft, 3, wx.EXPAND |wx.ALL, 0 )
		
		self.figure_scoreLeft = Figure((7.5,2),100)
		self.canvasLeft = FigureCanvas(self.m_panelLeft, wx.ID_ANY, self.figure_scoreLeft)
		self.axesLeft = self.figure_scoreLeft.add_subplot(111,facecolor='k')
		#self.axesLeft.set_autoscale_on(False) #关闭坐标轴自动缩放
		self.traceData=[-100]*801
		start_freq,end_freq = 930e6,950e6
		self.freq=range(int(start_freq),int(end_freq)+int((end_freq-start_freq)/800),int((end_freq-start_freq)/800))
		self.l_userLeft,=self.axesLeft.plot(self.freq, self.traceData, 'y')
		#self.axesLeft.axhline(y=average, color='r')
		self.axesLeft.set_ylim(-50,20)
		self.axesLeft.set_title('Spectrum')
		self.axesLeft.grid(True,color='dimgray')
		self.axesLeft.set_xlabel('Frequency/Hz')
		self.axesLeft.set_ylabel('Amplitude/dBmV')
		self.canvasLeft.draw()
		
		self.m_staticline14 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_VERTICAL )
		bSizerLeft.Add( self.m_staticline14, 0, wx.EXPAND |wx.ALL, 1 )
		
		###############################################地图放置
		bSizer91=wx.BoxSizer(wx.VERTICAL)
		self.m_panel10 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.m_htmlWin3 = wx.html2.WebView.New(self.m_panel10,size=(750,600))
		#self.bSizer102.Add( self.m_htmlWin2, 0, wx.ALL, 0 )
		self.file_html='file:///'+os.getcwd()+'/map6.html'
		self.m_htmlWin3.LoadURL(self.file_html)
		self.Bind(wx.html2.EVT_WEBVIEW_LOADED,self.direction_html,self.m_htmlWin3)
		#self.point={'1':[116.5,39.8]}
		self.point={}
		bSizer91.Add( self.m_panel10, 0, wx.EXPAND |wx.ALL, 0 )
		bSizerLeft.Add(bSizer91,3,wx.EXPAND,0)
		
		bSizer90.Add( bSizerLeft, 10, wx.EXPAND, 0 )
		
		##################################################右侧数据显示框
		bSizer92=wx.BoxSizer(wx.VERTICAL)
		'''
		bSizer88 = wx.BoxSizer( wx.HORIZONTAL )
		self.m_staticText41 = wx.StaticText( self, wx.ID_ANY, u"测向频率：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText41.Wrap( -1 )
		bSizer88.Add( self.m_staticText41, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		self.m_textCtrl13 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer88.Add( self.m_textCtrl13, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		self.m_staticText42 = wx.StaticText( self, wx.ID_ANY, "MHz ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText42.Wrap( -1 )
		bSizer88.Add( self.m_staticText42, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		# self.m_button16 = wx.Button( self, wx.ID_ANY, u"开始测向", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_button16.Bind(wx.EVT_BUTTON,self.Angel)
		# bSizer88.Add( self.m_button16, 0, wx.ALL|wx.ALIGN_CENTRE, 0 )
		
		bSizer92.Add( bSizer88, 1, wx.ALL, 0 )
		self.m_staticline14 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_VERTICAL )
		bSizer92.Add( self.m_staticline14, 0, wx.EXPAND |wx.ALL, 1 )
		'''
		############################################信号测量控制按钮
		# self.bx2=wx.StaticBox( self, wx.ID_ANY, u"信号强度测量:" )
		# #bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		# self.bx2.SetForegroundColour("SLATE BLUE")
		# font2 = wx.Font(11, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		# self.bx2.SetFont(font2)
		# sbSizer6 = wx.StaticBoxSizer(self.bx2, wx.HORIZONTAL )
		sbSizer6 = wx.BoxSizer( wx.HORIZONTAL )
		self.sbSizer7 = wx.StaticBoxSizer(wx.StaticBox( self, wx.ID_ANY, u'控制按钮' ), wx.VERTICAL) #测量，清除，初始化
		self.button1=wx.Button(self,wx.ID_ANY,u"测 量",wx.DefaultPosition,(90,30),0)
		self.button_stop=wx.Button(self,wx.ID_ANY,u"停止测量",wx.DefaultPosition,(90,30),0)
		self.button2=wx.Button(self,wx.ID_ANY,u"清除数据",wx.DefaultPosition,(90,30),0)
		self.button3=wx.Button(self,wx.ID_ANY,u"初始化",wx.DefaultPosition,(90,30),0)
        
		self.button1.Bind(wx.EVT_BUTTON,self.compute_angel) #测量当前的方向和辐射强度
		self.button_stop.Bind(wx.EVT_BUTTON,self.stop_compute_angel) #测量当前的方向和辐射强度
		self.button2.Bind(wx.EVT_BUTTON,self.clear_angel) #清空列表数据
		self.button3.Bind(wx.EVT_BUTTON,self.clear_cache) #清空系统缓存
		#self.button4.Bind(wx.EVT_BUTTON,self.Angel)   # 画图键，控制最后的画图
		
		self.sbSizer7.Add( self.button1, 0, wx.ALL, 5 )
		self.sbSizer7.Add( self.button_stop, 0, wx.ALL, 5 )
		self.sbSizer7.Add( self.button2, 0, wx.ALL, 5 )
		self.sbSizer7.Add( self.button3, 0, wx.ALL, 5 )
		
		
		##############################################显示角度信息
		self.bx1=wx.StaticBox( self, wx.ID_ANY, u"信号强度信息表：" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		self.bx1.SetForegroundColour("SLATE BLUE")
		font = wx.Font(10, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bx1.SetFont(font)
		self.sbSizer8 = wx.StaticBoxSizer( self.bx1, wx.VERTICAL )
		self.list_ctrl = wx.ListCtrl(self, size=(-1,300),style=wx.LC_REPORT|wx.LC_HRULES|wx.LC_VRULES|wx.BORDER_SUNKEN)
		self.list_ctrl.InsertColumn(0, 'id',width=40)
		self.list_ctrl.InsertColumn(1, u'角度/度',width=80)
		self.list_ctrl.InsertColumn(2, u'信号强度/dBmV', width=100)
		self.sbSizer8.Add(self.list_ctrl,0,wx.ALL|wx.EXPAND,0)
		sbSizer6.Add(self.sbSizer8,4,wx.EXPAND,0)
		sbSizer6.Add(self.sbSizer7,2,wx.EXPAND,0)
		bSizer92.Add( sbSizer6, 8, wx.EXPAND, 0 )
		
		'''
		###########加滑动窗
		bSizer93 = wx.BoxSizer( wx.VERTICAL )
		self.m_scroll1 = wx.ScrolledWindow( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.HSCROLL|wx.VSCROLL )
		self.m_scroll1.SetScrollRate( 5, 5 )
		
		bSizer93 = wx.BoxSizer( wx.VERTICAL )
		# bSizer94=wx.BoxSizer(wx.VERTICAL)
		# bSizer95=wx.BoxSizer(wx.VERTICAL)
		# bSizer96=wx.BoxSizer(wx.VERTICAL)
		
		self.names=locals()
		for i in range(1,37):
			self.names['bSizer_u%s'%i]=wx.BoxSizer(wx.HORIZONTAL)
			if i<10:
				self.names['staticText%s'%i]=wx.StaticText( self.m_scroll1, wx.ID_ANY, str(i*10)+u"度: ", wx.DefaultPosition, wx.DefaultSize, 0 )
			else:
				self.names['staticText%s'%i]=wx.StaticText( self.m_scroll1, wx.ID_ANY, str(i*10)+u"度:", wx.DefaultPosition, wx.DefaultSize, 0 )
			self.names['textCtrl%s'%i] = wx.TextCtrl( self.m_scroll1, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
			self.names['button%s'%i]=wx.Button( self.m_scroll1, wx.ID_ANY, str(i*10)+u"度测量", wx.DefaultPosition, wx.DefaultSize, 0 )
			self.names['bSizer_u%s'%i].Add( self.names['staticText%s'%i], 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
			self.names['bSizer_u%s'%i].Add( self.names['textCtrl%s'%i], 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
			self.names['bSizer_u%s'%i].Add(self.names['button%s'%i], 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
			bSizer93.Add( self.names['bSizer_u%s'%i], 1, wx.EXPAND, 5 )
			self.names['button%s'%i].Bind( wx.EVT_BUTTON, self.compute_angel )
		
		self.button37=wx.Button(self.m_scroll1,wx.ID_ANY,u"清除当前次测量所有数据",wx.DefaultPosition,wx.DefaultSize,0)
		bSizer93.Add(self.button37,1,wx.EXPAND,20)
		self.button37.Bind(wx.EVT_BUTTON,self.clear_angel)
		
		self.button38=wx.Button(self.m_scroll1,wx.ID_ANY,u"清除位置缓存",wx.DefaultPosition,wx.DefaultSize,0)
		bSizer93.Add(self.button38,1,wx.EXPAND,20)
		self.button38.Bind(wx.EVT_BUTTON,self.clear_cache)
		
		self.m_scroll1.SetSizer( bSizer93 )
		self.m_scroll1.Layout()
		bSizer93.Fit( self.m_scroll1 )
		sbSizer6.Add( self.m_scroll1, 1, wx.EXPAND |wx.ALL, 5 )
		'''
		
		
		self.bSizer93=wx.BoxSizer(wx.HORIZONTAL)
		#################################################信号辐射图
		self.bx1=wx.StaticBox( self, wx.ID_ANY, u"信号辐射图:" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		self.bx1.SetForegroundColour("SLATE BLUE")
		font1 = wx.Font(10, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bx1.SetFont(font1)
		self.sbSizer5 = wx.StaticBoxSizer(self.bx1, wx.VERTICAL )
		
		self.m_panel11 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.figure_score1 = Figure((3.3,2.8),100)
		self.canvas1=FigureCanvas(self.m_panel11, -1, self.figure_score1)
		self.axes_score1 = self.figure_score1.add_subplot(111,facecolor='w')
		self.l_user1,=self.axes_score1.plot([], [], 'b')
		#self.axes_score.axhline(y=average, color='r')
		self.axes_score1.set_xlim(-1,1)
		#self.axes_score1.set_ylim(-1,1)
		# self.axes_score1.set_title('Sub-Spectrum')
		# self.axes_score1.grid(True,color='y')
		# self.axes_score1.set_xlabel('Frequency/Hz')
		# self.axes_score1.set_ylabel('Amplitude/dBmV')
		self.canvas1.draw()
		self.sbSizer5.Add( self.m_panel11, 1, wx.EXPAND , 5 )
		
		
		###############################################画辐射图控制键
		'''
		self.sbSizer9 = wx.StaticBoxSizer(wx.StaticBox( self, wx.ID_ANY, u'画图按钮' ), wx.VERTICAL) #测量，清除，初始化
		self.button4=wx.Button(self,wx.ID_ANY,u"画图显示",wx.DefaultPosition,wx.DefaultSize,0)
		self.sbSizer9.Add( self.button4, 0, wx.ALL, 5 )
		self.bSizer93.Add( self.sbSizer9,2,wx.EXPAND, 5)
		'''
		
		self.bSizer93.Add(self.sbSizer5,4,wx.EXPAND,0)
		
		
		bSizer92.Add( self.bSizer93, 10, wx.EXPAND, 0 )
		
		
		bSizer90.Add( bSizer92, 5, wx.EXPAND |wx.ALL, 5 )
		#bSizer86.Add( bSizer90, 20, wx.EXPAND |wx.ALL, 5 )
		
		self.SetSizer( bSizer90 )
		self.angel_peak={}
		
		
		#改变注册表，使得python 默认的ie版本为ie11,这样map功能的箭头和线条才能加上去
		self.input_state = 1 #输入参数状态正常
		self.threads = []

	def OnChangeDirectionFre(self, event):
		global Dir_cf
		fre_string=self.m_textCtrl1.GetValue()
		m_choice1_string = self.m_choice1.GetString(self.m_choice1.GetSelection())
		if fre_string.strip()=='' or float(fre_string) < 0:
			fre = 8e8
		else:
			fre = float(fre_string)
			if m_choice1_string == 'GHz':
				fre = fre*1e9
			elif m_choice1_string == 'MHz':
				fre = fre*1e6
			else:
				fre = fre*1e3
			if fre<9e3 or fre>6.2e9:
				wx.MessageBox('输入频率超出仪表支持范围！','Warning',wx.OK|wx.ICON_INFORMATION)
				fre = 8e8
		if m_choice1_string == 'GHz':
			self.m_textCtrl1.SetValue(str(fre/1e9))
		elif m_choice1_string == 'MHz':
			self.m_textCtrl1.SetValue(str(fre/1e6))
		else:
			self.m_textCtrl1.SetValue(str(fre/1e3))
		Dir_cf = fre
		event.Skip()
			
	def OnChangeDirectionBand(self, event):
		global Dir_BW
		band_string=self.m_textCtrl2.GetValue()
		if band_string.strip()=='' or float(band_string)<0:
			band = 20
		else:
			band = float(band_string)
			if band>3000:
				band = 20
		self.m_textCtrl2.SetValue(str(band))
		band = band * 1e6
		Dir_BW = band
		event.Skip()

	def OnChangeDirectionRefLevel(self, event):
		global Dir_rl
		ref_string=self.m_textCtrl3.GetValue()
		if ref_string.strip()=='':
			ref = 0
		else:
			ref = float(ref_string)
			if ref>70 or ref<-150:
				ref = 0
		Dir_rl = ref
		self.m_textCtrl3.SetValue(str(ref))
		event.Skip()

	def OnChangeDirectionRBW(self, event):
		global Dir_rbw
		rbw_string=self.m_textCtrl4.GetValue()
		#m_choice4_string = self.m_choice4.GetString(self.m_choice4.GetSelection())
		if rbw_string.strip()=='' or float(rbw_string)<0:
			rbw = 1
		else:
			rbw = float(rbw_string)
			if rbw>1e5 or rbw<0.1:
				rbw =1
		self.m_textCtrl4.SetValue(str(rbw))
		rbw = rbw * 1e3
		Dir_rbw = rbw
		event.Skip()
		
	'''
	def OnChangeVBW(self, event):
		vbw_string=self.m_textCtrl5.GetValue()
		#m_choice5_string = self.m_choice5.GetString(self.m_choice5.GetSelection())
		if vbw_string.strip()=='' or float(vbw_string)<0:
			vbw = 1
		else:
			vbw = float(vbw_string)
			if vbw > 1e5: 
				vbw = 1
			self.m_textCtrl5.SetValue(str(vbw))
		event.Skip()
	'''
	def getInput(self):
		#print ("get into getInput()")
		self.input_state = 0
		freq_string = self.m_textCtrl1.GetValue()
		self.m_choice1_string=self.m_choice1.GetString(self.m_choice1.GetSelection())
		#print (freq_string + "  "+ self.m_choice1_string) 
		#cf
		try:
			if freq_string.strip()=='' or float(freq_string)<0: 
				freq = 8e8
			else: 
				freq=float(freq_string)
				if self.m_choice1_string == 'MHz':
					freq = freq * 1e6
				elif self.m_choice1_string == 'GHz':
					freq = freq * 1e9
				else:
					freq = freq * 1e3
				if freq > 6.2e9:
					freq = 8e8
				elif freq<9e3:
					freq = 8e8
			if self.m_choice1_string == 'GHz':
				self.m_textCtrl1.SetValue(str(freq/1e9))
			elif self.m_choice1_string == 'MHz':
				self.m_textCtrl1.SetValue(str(freq/1e6))
			else:
				self.m_textCtrl1.SetValue(str(freq/1e3))
		except (ValueError,TypeError) as e:
			wx.MessageBox(u' 频率输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
			return
		#print ("4405 detection fre is :" + str(freq))
		#span
		span_string=self.m_textCtrl2.GetValue()
		#self.m_choice2_string=self.m_choice2.GetString(self.m_choice2.GetSelection())
		try:
			if span_string.strip() == '' or float(span_string) < 0:
				span=20
			else:
				span=float(span_string)
				span = span * 1e6
				if span>3e9:
					span = 2e7
			self.m_textCtrl2.SetValue(str(span/1e6))
		except (ValueError,TypeError) as e:
			wx.MessageBox(u' 带宽输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
			return
		print ("4419 detection band is : " + str(span)) 
		#参考电平
		#rfLevel = 10   # 即-37dBm
		rf_level=self.m_textCtrl3.GetValue()
		if rf_level.strip() == '' :
			rfLevel = 0
		else:
			try:
				rfLevel=float(rf_level)
				if rfLevel >70 or rfLevel<-150:
					rfLevel = 0
				self.m_textCtrl3.SetValue(str(rfLevel))
			except (ValueError,TypeError) as e:
				wx.MessageBox(u' 参考电平输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
				return
		print ("reference level of detection is :" + str(rfLevel))
		
		#RBW
		rbw_string=self.m_textCtrl4.GetValue()
		if rbw_string.strip() == '':
			rbw = 1e3   #默认值为1kHz
		else:
			try:
				rbw=float(rbw_string)
				if rbw>1e5 or rbw<0.1:
					rbw =1
				self.m_textCtrl4.SetValue(str(rbw))
				rbw = rbw*1e3
			except (ValueError,TypeError) as e:
				wx.MessageBox(u' RBW输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
				return
		print ("4448 detection rbw is :" + str(rbw))
		#VBW
		# vbw_string=self.m_textCtrl5.GetValue()
		# #self.m_choice4_string=self.m_choice4.GetString(self.m_choice4.GetSelection())
		# if vbw_string.strip() == '':
			# vbw = 1e3   #默认值为1kHz
		# else:
			# try:
				# vbw=float(vbw_string)
				# if vbw>1e5:
					# vbw =1
				# self.m_textCtrl5.SetValue(str(vbw))
				# vbw = vbw * 1e3
			# except (ValueError,TypeError) as e:
				# wx.MessageBox(u' VBW输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
				# return
		# print ("4464 detection vbw is :" + str(rbw))
		
		vbw = 1e3
		
		self.input_state = 1
		#print (freq,span,rfLevel,rbw,vbw)
		return [freq,span,rfLevel,rbw,vbw]

	def compute_angel(self,event):
		global detection_state
		global connect_state
		global connect_machine
		global GPS_end
		global longitude
		global latitude
		#print (str(connect_machine))
		GPS_end = False
		if connect_state==0:
			wx.MessageBox(u'仪表未连接！.', "Error" ,wx.OK | wx.ICON_ERROR)
		else:
			print ('Get into compute_angel()')
			if detection_state == 0:
				# self.m_textCtrl1.Enable(False)
				# self.m_textCtrl2.Enable(False)
				# self.m_textCtrl4.Enable(False)
				# self.m_textCtrl5.Enable(False)
				
				if connect_machine == b'RSA306B':
					#print ('22222')
					wx.MessageBox(u'仪器为RSA306，没有内置GPS模块，采用系统默认位置信息!', "Message" ,wx.OK | wx.ICON_INFORMATION)
				elif longitude == -1:
					print ("Gegin attaining GPS data in compute_angel")
					a = Wait_GPS(self)
					a.OnStart()
					if a.ShowModal()==wx.ID_OK:
						if a.GPS_state:
							longitude = a.location[0]
							latitude = a.location[1]
					else:
						wx.MessageBox(u'取消位置获取将自动退出测向功能！', 'Message', wx.OK |wx.ICON_INFORMATION)
						return
				print ("current location is :"+ str(longitude)+ ";"+str(latitude))
				try:
					self.list_ctrl.DeleteAllItems()
					self.angel_peak = {}
					#print ("ready to getinput()")
					self.input_detail = self.getInput()
					#print (str(self.input_detail))
					t = 360 #总共测试6分钟
					detection_state = 1
					self.t1=WorkerThread5(t,self,self.input_detail)
					self.threads.append(self.t1)
					print ('Compute_angel ongoing...')
					self.t1.start()
					print ('Comute_angel succeed')
				except:
					detection_state = 0
			else:
				wx.MessageBox(u'已处于监测状态，请先停止当前任务，然后开始新的任务', "Message" ,wx.OK | wx.ICON_INFORMATION)
	
	def stop_compute_angel(self,event):
		# self.m_textCtrl1.Enable(True)
		# self.m_textCtrl2.Enable(True)
		# self.m_textCtrl4.Enable(True)
		# self.m_textCtrl5.Enable(True)
		while self.threads:
			thread=self.threads[0]
			thread.stop()
			self.threads.remove(thread)
		self.Angel()
	
	def clear_angel(self,event):
		self.list_ctrl.DeleteAllItems()   #清空之前信号列表的数据
		self.angel_peak={}
		'''  delete by vinson. 清楚数据没必要判断是否连接仪表吧？
		if connect_state==0:
			wx.MessageBox(u'仪表未连接！.', "Error",wx.OK | wx.ICON_ERROR)
		else:
			dlg = wx.MessageDialog(None,u" Do you really want to clear all data?", u"Warning !", wx.YES_NO | wx.ICON_INFORMATION)
			if dlg.ShowModal() == wx.ID_YES:
				self.list_ctrl.DeleteAllItems()   #清空之前信号列表的数据
				self.angel_peak={}
		'''


	def clear_cache(self,event):
		self.list_ctrl.DeleteAllItems()   #清空之前信号列表的数据
		self.angel_peak={}
		self.figure_score = Figure((3.3,2.8),100)
		self.canvas = FigureCanvas(self.m_panel11, wx.ID_ANY, self.figure_score)
		self.axes = self.figure_score.add_subplot(111,projection='polar',facecolor='w')
		self.axes.plot([], [], 'b')
		
		self.canvas.draw()
		
		direction_cache['location']=[]
		direction_cache['theta']=[]
		jsObj1 = json.dumps(direction_cache)
		fileObject1 = open(os.getcwd()+'\\direction.json', 'w')
		fileObject1.write(jsObj1)
		fileObject1.close()
		#更新地图
		self.m_htmlWin3.LoadURL(os.getcwd()+'/map6.html')
		self.Bind(wx.html2.EVT_WEBVIEW_LOADED,self.direction_html,self.m_htmlWin3)
	
	
	def Angel(self):
		global longitude
		global latitude
		if len(self.angel_peak)==0:
			wx.MessageBox(u'No data', "Message" ,wx.OK | wx.ICON_INFORMATION)
			# self.figure_score = Figure((1,1),100)
			
			# self.canvas = FigureCanvas(self.m_panel11, wx.ID_ANY, self.figure_score)
			# self.axes = self.figure_score.add_subplot(111,facecolor='w')
			# self.axes.plot([1,2,3],[2,3,4],'b')
			self.t_score=[1,2,3]
			self.score=[2,3,4]
			self.l_user1.set_data([1,2,3],[2,3,4])
			self.axes_score1.set_xlim(self.t_score[0],self.t_score[-1])
			self.axes_score1.set_ylim(self.score[0],self.score[-1])
			self.axes_score1.draw_artist(self.l_user1)
			self.canvas1.draw()
		else:
			#print(self.angel_peak)
			angel=sorted(self.angel_peak.keys())
			#print (angel)
			if len(angel)==36:
				# theta=array([float(j)*pi/180 for j in angel]+[float(angel[0]+360)*pi/180])
				# peak=array([self.angel_peak[i] for i in angel]+[self.angel_peak[angel[0]]])
				theta=array([float(j)*pi/180 for j in angel])
				peak=array([self.angel_peak[i] for i in angel])
			else:
				theta=array([float(j)*pi/180 for j in angel])
				peak=array([self.angel_peak[i] for i in angel])
			
			#画方向图
			N=len(self.angel_peak)
			
			self.figure_score = Figure((3.3,2.8),100)
			self.canvas = FigureCanvas(self.m_panel11, wx.ID_ANY, self.figure_score)
			self.axes = self.figure_score.add_subplot(111,projection='polar',facecolor='w')
			#self.axes.set_theta_zero_location('N')  # add by vinson, set 0 degree to North
			#1、画圆形柱图
			radii =10 * peak
			# radii = peak
			width = pi / 50 * ones(N)
			bars = self.axes.bar(theta, radii, width=width, bottom=0.0)
			#self.axies.set_rlim(0,max(radii))
			for r, bar in zip(radii, bars):
				bar.set_facecolor(plt.cm.viridis(r / 10.))
				bar.set_alpha(0.5)
			max_theta=theta[argmax(radii)]
			#2、画辐射图
			'''
			xnew = linspace(theta.min(),theta.max(),300)
			power_smooth = spline(theta,radii,xnew)
			max_theta=xnew[argmax(power_smooth)]
			self.axes.plot(xnew,power_smooth,'b')
			'''
			self.canvas.draw()
			
			
			if max_theta>pi:
				max_theta=max_theta-2*pi  #保证角度为[-pi,pi]
			
			max_theta=max_theta*180/pi   #将弧度转换成角度
			print (max_theta)
			
			if longitude == -1:
				location=[116.400819, 39.935961]     # need modified
			else:
				location = [longitude, latitude]
				print("current location in Angel:" + str(longitude)+','+str(latitude))
			direction_cache['location'].append(location)
			direction_cache['theta'].append(max_theta)
			jsObj1 = json.dumps(direction_cache)
			fileObject1 = open(os.getcwd()+'\\direction.json', 'w')
			fileObject1.write(jsObj1)
			fileObject1.close()
			
			#更新地图
			self.m_htmlWin3.LoadURL(os.getcwd()+'/map6.html')
			self.Bind(wx.html2.EVT_WEBVIEW_LOADED,self.direction_html,self.m_htmlWin3)
			
			# self.axes_score1.set_xlim(-max(xnew),max(xnew))
			# self.axes_score1.set_ylim(-max(power_smooth),max(power_smooth))
			# self.l_user1.set_data(xnew,power_smooth)
			# self.axes_score1.draw_artist(self.l_user1)
			# self.canvas1.draw()
	
	def draw_angel(self):
		if len(self.angel_peak)==0:
			wx.MessageBox(u'No data', "Message" ,wx.OK | wx.ICON_INFORMATION)
			# self.figure_score = Figure((1,1),100)
			
			# self.canvas = FigureCanvas(self.m_panel11, wx.ID_ANY, self.figure_score)
			# self.axes = self.figure_score.add_subplot(111,facecolor='w')
			# self.axes.plot([1,2,3],[2,3,4],'b')
			self.t_score=[1,2,3]
			self.score=[2,3,4]
			self.l_user1.set_data([1,2,3],[2,3,4])
			self.axes_score1.set_xlim(self.t_score[0],self.t_score[-1])
			self.axes_score1.set_ylim(self.score[0],self.score[-1])
			self.axes_score1.draw_artist(self.l_user1)
			self.canvas1.draw()
		else:
			self.angel=sorted(self.angel_peak.keys())
			#print (angel)
			if len(self.angel)==36:
				# theta=array([float(j)*pi/180 for j in angel]+[float(angel[0]+360)*pi/180])
				# peak=array([self.angel_peak[i] for i in angel]+[self.angel_peak[angel[0]]])
				self.theta=array([float(j)*pi/180 for j in self.angel])
				self.peak=array([self.angel_peak[i] for i in self.angel])
			else:
				self.theta=array([float(j)*pi/180 for j in self.angel])
				self.peak=array([self.angel_peak[i] for i in self.angel])
			
			#画方向图
			N=len(self.angel_peak)
			
			self.figure_score = Figure((3.3,2.8),100)
			self.canvas = FigureCanvas(self.m_panel11, wx.ID_ANY, self.figure_score)
			self.axes = self.figure_score.add_subplot(111,projection='polar',facecolor='w')
			#self.axes.set_theta_zero_location('N')     # add by vinson, set 0 degree to north direction
			
			#1、画圆形柱图
			self.radii =10 * self.peak
			# self.axes.set_rlim(0,max(self.radii))    # add by vinson, set only two labels
			self.width = pi / 50 * ones(N)
			bars = self.axes.bar(self.theta, self.radii, width=self.width, bottom=0.0)
			for r, bar in zip(self.radii, bars):
				bar.set_facecolor(plt.cm.viridis(r / 10.))
				bar.set_alpha(0.5)
			#2、画辐射图
			self.canvas.draw()
	
	def draw_direction(self):
		global longitude
		global latitude
		
		print (self.angel_peak)
		self.draw_angel()
		self.max_theta=self.theta[argmax(self.radii)]
		if self.max_theta>pi:
			self.max_theta=self.max_theta-2*pi  #保证角度为[-pi,pi]
		self.max_theta=self.max_theta*180/pi   #将弧度转换成角度
		print (self.max_theta)
		
		if longitude == -1:
			location=[116.400819, 39.935961]
		else:	
			location = [longitude, latitude]
			
		direction_cache['location'].append(location)
		direction_cache['theta'].append(self.max_theta)
		jsObj1 = json.dumps(direction_cache)
		fileObject1 = open(os.getcwd()+'\\direction.json', 'w')
		fileObject1.write(jsObj1)
		fileObject1.close()
		
		#更新地图
		self.m_htmlWin3.LoadURL(os.getcwd()+'/map6.html')
		self.Bind(wx.html2.EVT_WEBVIEW_LOADED,self.direction_html,self.m_htmlWin3)
	
	def direction_html(self,event):
		print ('4786 Load direction_html')
		for i in self.point:
			lng=self.point[i][0]
			lat=self.point[i][1]
			print ("Points prepare to draw direction in direction_html: "+ str(lng)+';'+str(lat))
			u1="document.getElementById('longitude').value="+str(lng)+";"
			self.m_htmlWin3.RunScript(u1)
			u2="document.getElementById('latitude').value="+str(lat)+";"
			self.m_htmlWin3.RunScript(u2)
			u3="document.getElementById('direction_point').value="+str(i)+";"
			self.m_htmlWin3.RunScript(u3)
			self.m_htmlWin3.RunScript("document.getElementById('add_direction').click();")
		for j in range(len(direction_cache['theta'])):
			lng=direction_cache['location'][j][0]
			lat=direction_cache['location'][j][1]
			theta=direction_cache['theta'][j]
			u1="document.getElementById('longitude').value="+str(lng)+";"
			self.m_htmlWin3.RunScript(u1)
			u2="document.getElementById('latitude').value="+str(lat)+";"
			self.m_htmlWin3.RunScript(u2)
			u3="document.getElementById('direction_point').value="+str(j)+";"
			self.m_htmlWin3.RunScript(u3)
			u4="document.getElementById('theta').value="+str(theta)+";"
			self.m_htmlWin3.RunScript(u4)
			#self.m_htmlWin3.RunScript("document.getElementById('add_direction').click();")
			self.m_htmlWin3.RunScript("document.getElementById('add_arrow').click();")
	
	def get_direction(self):
		direction=-1  #-1表示未成功获取方向 
		#自动检测占用端口号
		port_list = list(serial.tools.list_ports.comports())
		current_port = 0
		for i in range(len(port_list)):
			port_list_i=list(port_list[i])
			if port_list_i[1][0:17]=='USB-SERIAL CH341A':
				current_port=port_list_i[0]
				break;
		if current_port:
			print (current_port)
			try: 
				ser = serial.Serial(current_port, 115200) 
			except Exception as e: 
				print ('open serial failed.')
				return direction
			print ('A Serial Echo Is Running...')
			iscommon=1
			data=[]

			while iscommon: 
				# echo 
				s = ser.read(1)    
				if s==b'\xa1':
					s = ser.read(1)
					data.append(s)
					s=ser.read(1)
					data.append(s)
					iscommon=0
			print (data)
			dir1=list(data[0])
			dir2=list(data[1])

			temp=dir1[0]
			temp <<= 8
			temp |= dir2[0]
			if (temp & 32768):
				temp=0-(temp&0x7ffff);
			else:
				temp =temp&0x7ffff
			yaw=float(temp/10)
			return yaw
		else:
			wx.MessageBox(u'测向模块未连接.', "Error",wx.OK | wx.ICON_ERROR)
			return -2


###########################################################################
## Class MyPanel5 无人机信号瀑布图
###########################################################################
class MyPanel5 ( wx.Panel ):
	
	def __init__( self, parent ):
		wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 500,349 ), style = wx.TAB_TRAVERSAL )
		
		bSizer173 = wx.BoxSizer( wx.HORIZONTAL )
		
		# bSizer92 = wx.BoxSizer( wx.VERTICAL )
		
		# bSizer93 = wx.BoxSizer( wx.VERTICAL )
		
		# bSizer98 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer100 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_panel9 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer100.Add( self.m_panel9, 1, wx.EXPAND |wx.ALL, 5 )
		
		#画板上画坐标轴
		#self.figure_score5,axes_score6=method.draw_picture([],[],'UAV-Spectrum',"Frequency/MHz","Amplitude/dBmV",4.4,6)
		#FigureCanvas(self.m_panel9, -1, self.figure_score5)
		#################################
		## 尝试一种新的画图方法
		self.figure_score = Figure((8.15,6.4),100)
		
		self.canvas = FigureCanvas(self.m_panel9, wx.ID_ANY, self.figure_score)
		# self.figure_score.set_figheight(4)
		# self.figure_score.set_figwidth(6)
		self.axes_score = self.figure_score.add_subplot(211,facecolor='k')
		#self.axes_score.set_autoscale_on(False) #关闭坐标轴自动缩放
		self.traceData=[-100]*801
		self.start_freq=float(2.4e9)
		self.end_freq=float(2.46e9)
		self.freq=arange(self.start_freq,self.end_freq,(self.end_freq-self.start_freq)/float(801))
		#self.l_user,=self.axes_score.plot(self.freq, self.traceData, 'b')
		self.l_user,=self.axes_score.plot([],[],'y')
		#self.axes_score.axhline(y=average, color='r')
		self.axes_score.set_ylim(-100,0)
		self.axes_score.set_title('UAV-Spectrum')
		self.axes_score.grid(True,color='dimgray')
		#self.axes_score.set_xlabel('Frequency/Hz')
		self.axes_score.set_ylabel('Amplitude/dBmV')
		#self.canvas.draw()
		#self.bg = self.canvas.copy_from_bbox(self.axes_score.bbox)
		
		#######加入第二个子图
		self.axes_score_new = self.figure_score.add_subplot(212,facecolor='k')
		#self.axes_score_new.set_autoscale_on(False) #关闭坐标轴自动缩放
		#self.freq=arange(self.start_freq,self.end_freq,(self.end_freq-self.start_freq)/float(801))
		#self.r_user,=self.axes_score_new.plot(self.freq, self.traceData, 'b')
		self.r_user,=self.axes_score.plot([],[],'b')
		#self.axes_score_new.axhline(y=average, color='r')
		self.axes_score_new.set_ylim(1,20)
		self.axes_score_new.set_title('UAV-Spectrum-waterfall')
		self.axes_score_new.grid(True,color='dimgray')
		self.axes_score_new.set_xlabel('Frequency/Hz')
		self.axes_score_new.set_ylabel('t/s')
		
		ymajorLocator= ticker.MultipleLocator(50) #将y轴主刻度标签设置为1的倍数
		yminorLocator= ticker.MultipleLocator(5) #将y轴主刻度标签设置为1的倍数
		self.axes_score_new.yaxis.set_minor_locator(yminorLocator)
		self.axes_score_new.yaxis.set_major_locator(ymajorLocator)
		
		self.canvas.draw()
		
		##############画图结束
		
		#bSizer98.Add( bSizer100, 10, wx.EXPAND, 5 )
		
		# bSizer101 = wx.BoxSizer( wx.VERTICAL )
		
		# self.m_staticText40 = wx.StaticText( self, wx.ID_ANY, u"    ", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText40.Wrap( -1 )
		# bSizer101.Add( self.m_staticText40, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )
		
		# bSizer98.Add( bSizer101, 1, wx.EXPAND|wx.ALIGN_CENTER_HORIZONTAL, 5 )
		
		
		#bSizer93.Add( bSizer98, 2, wx.EXPAND, 5 )
		
		
		##########################################输出模块
		'''
		# sbSizer3 = wx.StaticBoxSizer( wx.StaticBox( self, wx.ID_ANY, u"无人机信号信息" ), wx.VERTICAL )
		
		# bSizer181 = wx.BoxSizer( wx.HORIZONTAL )
		
		# self.m_staticText75 = wx.StaticText( self, wx.ID_ANY, u"中心频率：", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText75.Wrap( -1 )
		# bSizer181.Add( self.m_staticText75, 0, wx.ALL, 5 )
		
		# self.m_textCtrl37 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		# bSizer181.Add( self.m_textCtrl37, 0, wx.ALL, 5 )
		
		
		# self.m_staticText78 = wx.StaticText( self, wx.ID_ANY, u"   调频驻留时间：", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText78.Wrap( -1 )
		# bSizer181.Add( self.m_staticText78, 0, wx.ALL|wx.ALIGN_CENTER, 5 )
		
		# self.m_textCtrl40 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		# bSizer181.Add( self.m_textCtrl40, 0, wx.ALL|wx.ALIGN_CENTER, 5 )
		
		# self.m_staticText20 = wx.StaticText( self, wx.ID_ANY, "   ", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText20.Wrap( -1 )
		# bSizer181.Add( self.m_staticText20,0, wx.ALL, 5 )
		
		# self.m_button2=wx.Button(self,wx.ID_ANY,u"检测无人机信号",wx.DefaultPosition,(130,25),0)
		# bSizer181.Add(self.m_button2,0,wx.ALL|wx.ALIGN_CENTER,5)
		# self.m_button2.Bind(wx.EVT_BUTTON,self.start_uav)
		
		# sbSizer3.Add( bSizer181, 1, wx.EXPAND, 5 )
		
		# bSizer182 = wx.BoxSizer( wx.HORIZONTAL )
		
		# self.m_staticText76 = wx.StaticText( self, wx.ID_ANY, u"信道带宽：", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText76.Wrap( -1 )
		# bSizer182.Add( self.m_staticText76, 0, wx.ALL, 5 )
		
		# self.m_textCtrl38 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		# bSizer182.Add( self.m_textCtrl38, 0, wx.ALL, 5 )
		
		# bSizer182.AddStretchSpacer(1)
		# self.m_button3=wx.Button(self,wx.ID_ANY,u"停止检测",wx.DefaultPosition,(130,25),0)
		# bSizer182.Add(self.m_button3,0,wx.ALL|wx.ALIGN_CENTER,5)
		# self.m_button3.Bind(wx.EVT_BUTTON,self.stop_uav)
		
		
		# sbSizer3.Add( bSizer182, 1, wx.EXPAND, 5 )
		
		# bSizer183 = wx.BoxSizer( wx.HORIZONTAL )
		
		# self.m_staticText77 = wx.StaticText( self, wx.ID_ANY, u"调制方式：", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText77.Wrap( -1 )
		# bSizer183.Add( self.m_staticText77, 0, wx.ALL, 5 )
		
		# self.m_textCtrl39 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		# bSizer183.Add( self.m_textCtrl39, 0, wx.ALL, 5 )
		
		
		# sbSizer3.Add( bSizer183, 1, wx.EXPAND, 5 )
		# bSizer93.Add( sbSizer3, 2, wx.EXPAND, 5 )
		'''
		##########################################输出模块结束
		
		####################################################新模块
		'''
		# bSizer103 = wx.BoxSizer( wx.VERTICAL )
		
		# self.m_panel14 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		# bSizer103.Add( self.m_panel14, 1, wx.EXPAND |wx.ALL, 5 )
		
		# #画板上画坐标轴
		# #self.figure_score5,axes_score6=method.draw_picture([],[],'UAV-Spectrum',"Frequency/MHz","Amplitude/dBmV",4.4,6)
		# #FigureCanvas(self.m_panel9, -1, self.figure_score5)
		# #################################
		# ## 尝试一种新的画图方法
		# self.figure_score_new = Figure((6,4.4),100)
		
		# self.canvas_new = FigureCanvas(self.m_panel14, wx.ID_ANY, self.figure_score_new)
		# # self.figure_score.set_figheight(4)
		# # self.figure_score.set_figwidth(6)
		# self.axes_score_new = self.figure_score_new.add_subplot(111,facecolor='k')
		# #self.axes_score_new.set_autoscale_on(False) #关闭坐标轴自动缩放
		# self.traceData=[-100]*801
		# self.start_freq=float(840.5)
		# self.end_freq=float(845)
		# self.freq=arange(self.start_freq,self.end_freq,(self.end_freq-self.start_freq)/float(801))
		# self.r_user,=self.axes_score_new.plot(self.freq, self.traceData, 'b')
		# #self.axes_score_new.axhline(y=average, color='r')
		# self.axes_score_new.set_ylim(1,20)
		# self.axes_score_new.set_title('UAV-Spectrum-waterfall')
		# self.axes_score_new.grid(True,color='y')
		# self.axes_score_new.set_xlabel('Frequency/Hz')
		# self.axes_score_new.set_ylabel('t/s')
		# self.canvas_new.draw()
		# #self.bg = self.canvas.copy_from_bbox(self.axes_score.bbox)
		
		# ##############画图结束
		
		# bSizer93.Add( bSizer103, 10, wx.EXPAND, 5 )
		'''
		#######################################################新模块结束
		
		
		#bSizer92.Add( bSizer93, 4, wx.EXPAND, 5 )
		
		
		bSizer173.Add( bSizer100, 6, wx.EXPAND, 5 )
		
		self.m_staticline15 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_VERTICAL )
		bSizer173.Add( self.m_staticline15, 0, wx.EXPAND |wx.ALL, 0 )
		
		bSizer175 = wx.BoxSizer( wx.VERTICAL )
		
		bSizer176 = wx.BoxSizer( wx.VERTICAL )
		
		################
		bSizer174 = wx.BoxSizer(wx.HORIZONTAL)
		self.m_button2=wx.Button(self,wx.ID_ANY,u"开始监测",wx.DefaultPosition,(120,25),0)
		bSizer174.Add(self.m_button2,0,wx.ALL|wx.ALIGN_CENTER,0)
		self.m_button2.Bind(wx.EVT_BUTTON,self.start_uav)
		
		self.m_button3=wx.Button(self,wx.ID_ANY,u"停止监测",wx.DefaultPosition,(130,25),0)
		bSizer174.Add(self.m_button3,0,wx.ALL|wx.ALIGN_CENTER,5)
		self.m_button3.Bind(wx.EVT_BUTTON,self.stop_uav)
		bSizer176.Add( bSizer174, 0, wx.ALL, 0 )
		
		self.m_staticline17 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
		bSizer176.Add( self.m_staticline17, 0, wx.EXPAND |wx.ALL, 0 )
		###############
		
		self.m_staticText74 = wx.StaticText( self, wx.ID_ANY, u"无人机频段:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText74.Wrap( -1 )
		bSizer176.Add( self.m_staticText74, 0, wx.ALL, 5 )
		self.m_staticText74.SetForegroundColour("SLATE BLUE")
		self.m_staticText74.SetFont( wx.Font( 10, 70, 90, wx.BOLD, False, "宋体" ) )
		
		#self.m_listBox8Choices = ['800-900 MHz','2400-2483 MHz']
		self.m_listBox8Choices = list(method.uav_config['uav_freq'])
		self.m_listBox8 = wx.ListBox( self, wx.ID_ANY, wx.DefaultPosition, (270,250), self.m_listBox8Choices, wx.LB_ALWAYS_SB )
		bSizer176.Add( self.m_listBox8, 0, wx.ALL, 5 )
		self.m_listBox8.Bind( wx.EVT_LISTBOX, self.select_uav )
		
		
		bSizer175.Add( bSizer176, 1, wx.EXPAND, 5 )
		
		# self.m_staticline16 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL)
		# bSizer175.Add( self.m_staticline16, 0, wx.EXPAND |wx.ALL, 0 )
		'''
		bSizer177 = wx.BoxSizer( wx.VERTICAL )
		self.m_panel23 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		bSizer177.Add( self.m_panel23, 1, wx.EXPAND |wx.ALL, 5 )
		# #画板上画坐标轴
		# self.figure_score6,self.axes_score7,self.l_user1=method.draw_picture([],[],'UAV-IQ',"","",2.8,2.8)
		# FigureCanvas(self.m_panel23, -1, self.figure_score6)
		
		#面板上画坐标轴
		self.figure_score6 = Figure((2.8,2.8),100)
		self.canvas1=FigureCanvas(self.m_panel23, -1, self.figure_score6)
		self.axes_score7 = self.figure_score6.add_subplot(111,facecolor='k')
		self.l_user1,=self.axes_score7.plot([], [], 'b')
		#self.axes_score.axhline(y=average, color='r')
		self.axes_score7.set_ylim(-1,1)
		self.axes_score7.set_xlim(-1,1)
		self.axes_score7.set_title('UAV-IQ')
		self.axes_score7.grid(True,color='y')
		self.canvas1.draw()
		
		bSizer175.Add( bSizer177, 1, wx.EXPAND, 5 )
		'''
		# 加入无人机参数设置
		self.bx1=wx.StaticBox( self, wx.ID_ANY, u"自定义参数设置" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		self.bx1.SetForegroundColour("SLATE BLUE")
		self.font = wx.Font(10, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bx1.SetFont(self.font)
		self.sbSizer1 = wx.StaticBoxSizer(self.bx1, wx.VERTICAL )
		#self.sbSizer1 = wx.BoxSizer( wx.VERTICAL )
		
		# self.m_staticText75 = wx.StaticText( self, wx.ID_ANY, u"参数设置:", wx.DefaultPosition, wx.DefaultSize, 0 )
		# self.m_staticText75.Wrap( -1 )
		# self.sbSizer1.Add( self.m_staticText75, 0, wx.ALL, 5 )
		# self.m_staticText75.SetForegroundColour("SLATE BLUE")
		# self.m_staticText75.SetFont( wx.Font( 10, 70, 90, wx.BOLD, False, "宋体" ) )
		
		self.bSizer11 = wx.BoxSizer( wx.VERTICAL )
		self.bSizer13 = wx.BoxSizer( wx.HORIZONTAL )
		'''
		self.m_staticText3 = wx.StaticText( self, wx.ID_ANY, u"起始频率  ：", wx.DefaultPosition, wx.DefaultSize, 0 )
		#self.m_staticText3.Wrap( -1 )
		#self.m_staticText3.SetFont( wx.Font( 12, 70, 90, wx.BOLD, False, "宋体" ) )
		self.bSizer13.Add( self.m_staticText3, 0, wx.ALL|wx.ALIGN_CENTRE, 5 )
		
		
		self.m_textCtrl1 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (80,20), 0 )
		self.bSizer13.Add( self.m_textCtrl1, 0, wx.ALL|wx.ALIGN_CENTRE, 0 )
		
		m_choice1Choices = ['MHz','GHz','KHz']
		self.m_choice1 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, (50,20), m_choice1Choices, 0 )
		self.m_choice1.SetSelection( 0 )
		self.bSizer13.Add( self.m_choice1, 0, wx.ALL|wx.ALIGN_CENTRE, 2 )
		
		self.bSizer11.Add( self.bSizer13, 1, wx.EXPAND, 0 )
		
		self.bSizer14 = wx.BoxSizer( wx.HORIZONTAL )
		self.m_staticText4 = wx.StaticText( self, wx.ID_ANY, u"终止频率  ：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText4.Wrap( -1 )
		self.bSizer14.Add( self.m_staticText4, 0, wx.ALIGN_CENTER|wx.ALL, 5 )
		
		self.m_textCtrl2 = wx.TextCtrl( self, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, (80,20), 0 )
		self.bSizer14.Add( self.m_textCtrl2, 0, wx.ALIGN_CENTER|wx.ALL, 0 )
		
		m_choice2Choices = ['MHz','GHz','KHz']
		self.m_choice2 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, (50,20), m_choice2Choices, 0 )
		self.m_choice2.SetSelection( 0 )
		self.bSizer14.Add( self.m_choice2, 0, wx.ALIGN_CENTER|wx.ALL, 2 )
		
		self.bSizer11.Add( self.bSizer14, 1, wx.EXPAND, 5 )
		'''
		self.bSizer15 = wx.BoxSizer( wx.HORIZONTAL )
		self.m_staticText4 = wx.StaticText( self, wx.ID_ANY, u"   RBW ：   ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText4.Wrap( -1 )
		self.bSizer15.Add( self.m_staticText4, 0, wx.ALIGN_CENTER|wx.ALL, 5 )
		
		self.m_textCtrl2 = wx.TextCtrl( self, wx.ID_ANY, str(config_data['RBW']), wx.DefaultPosition, (80,20), wx.TE_PROCESS_ENTER )
		self.m_textCtrl2.Bind(wx.EVT_TEXT_ENTER, self.OnChange_UAV_RBW)
		self.m_textCtrl2.Bind(wx.EVT_KILL_FOCUS, self.OnChange_UAV_RBW)
		self.bSizer15.Add( self.m_textCtrl2, 0, wx.ALIGN_CENTER|wx.ALL, 0 )
		#self.m_textCtrl2.Bind(wx.EVT_TEXT_ENTER,self.OnChange_UAV_RBW)
		
		m_choice2Choices = ['KHz','Hz']
		self.m_choice2 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, (50,20), m_choice2Choices, 0 )
		self.m_choice2.SetSelection( 0 )
		self.bSizer15.Add( self.m_choice2, 0, wx.ALIGN_CENTER|wx.ALL, 2 )
		self.m_choice2.Bind(wx.EVT_CHOICE, self.OnChangeUAVRBWUnit)
		
		self.bSizer11.Add( self.bSizer15, 1, wx.EXPAND, 5 )
		
		# 占位
		self.m_panel1 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.bSizer11.Add( self.m_panel1, 6, wx.EXPAND |wx.ALL, 5 )
		
		
		self.sbSizer1.Add(self.bSizer11,1,wx.EXPAND,5)
		
		bSizer175.Add(self.sbSizer1,1,wx.EXPAND,5)
		
		bSizer173.Add( bSizer175, 1, wx.EXPAND, 5 )

		self.SetSizer( bSizer173 )
		
		self.threads2=[]
		self.count=0
		self.freq_interval=[2400,2483] #默认频率段
		
	def OnChange_UAV_RBW(self,event):
		global uav_rbw
		rbw=self.m_textCtrl2.GetValue()
		self.m_choice2_string=self.m_choice2.GetString(self.m_choice2.GetSelection())
		if rbw.strip()=='' or float(rbw)<0:
			rbw=config_data['RBW']
		else:
			try:
				rbw=float(rbw)
				if self.m_choice2_string=='MHz':
					rbw=rbw*(1e3)
			except (ValueError,TypeError) as e:
				rbw=config_data['RBW']
				wx.MessageBox(u' RBW输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
		rbw = rbw * 1e3
		if rbw<1e2:
			rbw=100
		elif rbw>1e8:
			rbw=1e8

		if self.m_choice2_string=='MHz':
			self.m_textCtrl2.SetValue(str(rbw/(10**6)))
		else :
			self.m_textCtrl2.SetValue(str(rbw/(10**3)))
		uav_rbw=rbw     # 赋值给全局变量
		event.Skip()
		#print("uav_rbw = " + str(uav_rbw))

	def OnChangeUAVRBWUnit(self, event):
		self.m_textCtrl2.SetFocus()
	
        
	def start_uav(self,event):
		global detection_state
		global uav_rbw
		if connect_state==0:
			wx.MessageBox(u'仪表未连接！.', "Error" ,wx.OK | wx.ICON_ERROR)
		else:
			#读取rbw
			if detection_state==0:
				try:
					rbw=self.m_textCtrl2.GetValue()
					self.m_textCtrl2.Enable(False)
					self.m_choice2_string=self.m_choice2.GetString(self.m_choice2.GetSelection())
					if rbw.strip()=='' or float(rbw)<0:
						rbw=config_data['RBW']
					else:
						try:
							rbw=float(rbw)
							if self.m_choice2_string=='MHz':
								rbw=rbw*(1e3)
						except (ValueError,TypeError) as e:
							rbw=config_data['RBW']
							wx.MessageBox(u' RBW输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
					rbw = rbw * 1e3
					if rbw<1e2:
						rbw=100
					elif rbw>1e8:
						rbw=1e8

					if self.m_choice2_string=='MHz':
						self.m_textCtrl2.SetValue(str(rbw/(10**6)))
					else :
						self.m_textCtrl2.SetValue(str(rbw/(10**3)))
					self.rbw=rbw
					uav_rbw=rbw     # 赋值给全局变量
					
					self.count+=1
					t=50*36000
					# self.peak_freq=Queue()
					# self.band=Queue()
					self.I=[]
					self.Q=[]
					self.peak_freq_list=[]
					self.band_list=[]
					#anteid=config_data['Antenna_number']
					anteid = method.anteid
					#self.rbw=config_data['RBW']*1e3
					self.vbw=config_data['VBW']*1e3
					detection_state = 1
					self.t2=WorkerThread2(self.count,self,rsa_true,deviceSerial_true,t,13,anteid,self.rbw,self.vbw,self.freq_interval)
					self.t2.start()
					self.threads2.append(self.t2)
					# self.peak_freq_list=self.peak_freq.get()
					# self.band_list=self.band.get()
				except:
					wx.MessageBox(u'无人机监测出现错误，请重新开始', "Message" ,wx.OK | wx.ICON_INFORMATION)
					detection_state = 0
					self.m_textCtrl2.Enable(True)
			else:
				wx.MessageBox(u'已处于监测状态，请先停止当前任务，然后开始新的任务', "Message" ,wx.OK | wx.ICON_INFORMATION)
			
			
	def stop_uav(self,event):
		global detection_state
		self.m_textCtrl2.Enable(True)
		while self.threads2:
			thread=self.threads2[0]
			thread.stop()
			self.threads2.remove(thread)
		detection_state = 0

	def select_uav(self,uav):
		#print (peak_freq)
		#print (band)
		select_pos=self.m_listBox8.GetSelection()
		print (select_pos)
		freq_select=self.m_listBox8Choices[select_pos]
		self.freq_interval=[float(freq) for freq in freq_select.split()[0].split('-')]
		
		'''
		# ##########因瀑布图去掉
		# self.m_textCtrl37.SetValue(peak_freq[select_pos])
		# self.m_textCtrl38.SetValue(str(band[select_pos]))
		# ##########
		
		####画IQ图
		# self.axes_score7.set_xlim(-max(self.I[select_pos]),max(self.I[select_pos]))
		# self.axes_score7.set_ylim(-max(self.Q[select_pos]),max(self.Q[select_pos]))
		# self.l_user1.set_data(self.I[select_pos],self.Q[select_pos])
		# self.axes_score7.draw_artist(self.l_user1)
		# self.canvas1.draw()
		
		#面板上画IQ图
		# self.figure_score6 = Figure((2.8,2.8),100)
		# self.canvas1=FigureCanvas(self.m_panel23, -1, self.figure_score6)
		# self.axes_score7 = self.figure_score6.add_subplot(111,facecolor='k')
		# self.l_user1=self.axes_score7.scatter(self.I[select_pos], self.Q[select_pos], c='b')
		# #self.axes_score.axhline(y=average, color='r')
		# self.axes_score7.set_xlim(min(self.I[select_pos]),max(self.I[select_pos]))
		# self.axes_score7.set_ylim(min(self.Q[select_pos]),max(self.Q[select_pos]))
		# self.axes_score7.set_title('UAV-IQ')
		# self.axes_score7.grid(True,color='y')
		# self.canvas1.draw()
		# self.m_panel23.Refresh()
		'''
				
###########################################################################
## Class MyPanel6 自定义检测界面功能选择
###########################################################################

class MyPanel6 ( wx.Panel ):
	#实时频谱监测界面
	def __init__( self, parent ):
		wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 1000,349 ), style = wx.TAB_TRAVERSAL )
		
		#self.SetSizeHintsSz( wx.DefaultSize, wx.DefaultSize )
		
		bSizer1 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_panel1 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		#self.m_panel1.SetBackgroundColour("blue")  
		self.m_panel1.Bind(wx.EVT_ERASE_BACKGROUND,self.OnEraseBack)  
		# bSizer2 = wx.BoxSizer( wx.VERTICAL )
		
		# bSizer3 = wx.BoxSizer( wx.VERTICAL )
		# self.m_panel3 = wx.Panel( self.m_panel1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		# self.m_panel3.SetTransparent(1000000)
		# bSizer3.Add( self.m_panel3, 1, wx.EXPAND |wx.ALL, 5 )
		
		# self.m_staticText1 = wx.StaticText( self.m_panel1, wx.ID_ANY, u"功能选择", (200,120), wx.DefaultSize, 0 )
		# self.m_staticText1.Wrap( -1 )
		# self.m_staticText1.SetForegroundColour("SLATE BLUE")
		# font = wx.Font(20, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		# self.m_staticText1.SetFont(font)
		
		# bSizer3.Add( self.m_staticText1, 2, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )
		
		
		# bSizer2.Add( bSizer3, 1, wx.ALIGN_BOTTOM|wx.EXPAND, 5 )
		
		# bSizer4 = wx.BoxSizer( wx.VERTICAL )
		
		# bSizer5 = wx.BoxSizer( wx.HORIZONTAL )
		
		bmp = wx.Image("button1.bmp", wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		bmp1 = wx.Image("button111.bmp", wx.BITMAP_TYPE_BMP).ConvertToBitmap()
		bmp2 = wx.Image("button112.bmp", wx.BITMAP_TYPE_BMP).ConvertToBitmap()
		bmp3 = wx.Image("button113.bmp", wx.BITMAP_TYPE_BMP).ConvertToBitmap()
		bmp4 = wx.Image("button116.bmp", wx.BITMAP_TYPE_BMP).ConvertToBitmap()
		bmp5 = wx.Image("button115.bmp", wx.BITMAP_TYPE_BMP).ConvertToBitmap()
		
		# self.m_bpButton1 = buttons.GenBitmapTextButton(self.m_panel1, -1, bmp, u"频谱监控  ",(120,220),wx.DefaultSize,style=wx.NO_BORDER)#位图文本按钮
		# self.m_bpButton1.SetUseFocusIndicator(False)
		# font = wx.Font(20, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		# self.m_bpButton1.SetFont(font)
		# self.m_bpButton1.SetBackgroundColour("AQUAMARINE")
		self.m_bpButton1 = wx.BitmapButton( self.m_panel1, wx.ID_ANY, bmp1, (270,140),wx.DefaultSize, wx.BU_AUTODRAW )
		print(self.m_panel1.Size)				   
		#self.m_bpButton1 = wx.BitmapButton( self.m_panel1,wx.ID_ANY,bmp1,(self.m_panel1.Size()))																				   
		#bSizer5.Add( self.m_bpButton1, 0, wx.ALL, 5 )
		
		# self.m_bpButton2 = buttons.GenBitmapTextButton(self.m_panel1, -1, bmp, u"台站检测  ",(380,220),wx.DefaultSize,style=wx.NO_BORDER)#位图文本按钮
		# self.m_bpButton2.SetUseFocusIndicator(False)
		# font = wx.Font(20, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		# self.m_bpButton2.SetFont(font)
		# self.m_bpButton2.SetBackgroundColour("AQUAMARINE")
		
		#self.m_bpButton2 = wx.BitmapButton( self.m_panel1, wx.ID_ANY, bmp2, (380,140),wx.DefaultSize, wx.BU_AUTODRAW )
		
		#bSizer5.Add( self.m_bpButton2, 0, wx.ALL, 5 )
		
		
		# bSizer4.Add( bSizer5, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )
		
		# bSizer6 = wx.BoxSizer( wx.HORIZONTAL )
		
		# self.m_bpButton3 = buttons.GenBitmapTextButton(self.m_panel1, -1, bmp, u"占用度分析 ",(120,360),wx.DefaultSize,style=wx.NO_BORDER)#位图文本按钮
		# self.m_bpButton3.SetUseFocusIndicator(False)
		# font = wx.Font(20, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		# self.m_bpButton3.SetFont(font)
		# self.m_bpButton3.SetBackgroundColour("AQUAMARINE")
		self.m_bpButton3 = wx.BitmapButton( self.m_panel1, wx.ID_ANY, bmp3, (270,390),wx.DefaultSize, wx.BU_AUTODRAW )
		#bSizer6.Add( self.m_bpButton3, 0, wx.ALL, 5 )
		
		# self.m_bpButton4 = buttons.GenBitmapTextButton(self.m_panel1, -1, bmp, u"无线测向  ",(380,360),wx.DefaultSize,style=wx.NO_BORDER)#位图文本按钮
		# self.m_bpButton4.SetUseFocusIndicator(False)
		# font = wx.Font(20, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		# self.m_bpButton4.SetFont(font)
		# self.m_bpButton4.SetBackgroundColour("AQUAMARINE")
		self.m_bpButton4 = wx.BitmapButton( self.m_panel1, wx.ID_ANY, bmp4, (670,390),wx.DefaultSize, wx.BU_AUTODRAW )
		# bSizer6.Add( self.m_bpButton4, 0, wx.ALL, 5 )
		
		# self.m_bpButton5 = buttons.GenBitmapTextButton(self.m_panel1, -1, bmp, u"无人机信号 ",(640,220),wx.DefaultSize,style=wx.NO_BORDER)#位图文本按钮
		# self.m_bpButton5.SetUseFocusIndicator(False)
		# font = wx.Font(20, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		# self.m_bpButton5.SetFont(font)
		# self.m_bpButton5.SetBackgroundColour("AQUAMARINE")
		self.m_bpButton5 = wx.BitmapButton( self.m_panel1, wx.ID_ANY, bmp5, (670,140),wx.DefaultSize, wx.BU_AUTODRAW )
		# bSizer4.Add( bSizer6, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )
		
		# self.m_panel2 = wx.Panel( self.m_panel1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		# bSizer4.Add( self.m_panel2, 1, wx.EXPAND |wx.ALL, 5 )
		
		
		# bSizer2.Add( bSizer4, 3, wx.EXPAND, 5 )
		
		
		# self.m_panel1.SetSizer( bSizer2 )
		# self.m_panel1.Layout()
		# bSizer2.Fit( self.m_panel1 )
		bSizer1.Add( self.m_panel1, 1, wx.EXPAND |wx.ALL, 5 )
		
		
		self.SetSizer( bSizer1 )
		self.Layout()
		
		self.Centre( wx.BOTH )
	
	def __del__( self ):
		pass
		
	def OnEraseBack(self, evt):
		"""
		Add a picture to the background
		"""
		# yanked from ColourDB.py
		dc = evt.GetDC()

		if not dc:
			dc = wx.ClientDC(self)
			rect = self.GetUpdateRegion().GetBox()
			dc.SetClippingRect(rect)
		dc.Clear()
		bmp = wx.Bitmap("interface2.bmp")
		#print ('bmp')
		dc.DrawBitmap(bmp, 0, 0,)

###########################################################################
## Class MyPanel7 自定义检测 or 月报检测界面功能选择
###########################################################################
class MyPanel7( wx.Panel):
	
	def __init__( self, parent ):
		wx.Panel.__init__ ( self, parent, id = wx.ID_ANY, pos = wx.DefaultPosition, size = wx.Size( 1000,349 ), style = wx.TAB_TRAVERSAL )
		
		bSizer1 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_panel1 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		#self.m_panel1.SetBackgroundColour("blue")  
		self.m_panel1.Bind(wx.EVT_ERASE_BACKGROUND,self.OnEraseBack)  
		# bSizer2 = wx.BoxSizer( wx.VERTICAL )
		
		# bSizer3 = wx.BoxSizer( wx.VERTICAL )
		# self.m_panel3 = wx.Panel( self.m_panel1, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		# self.m_panel3.SetTransparent(1000000)
		# bSizer3.Add( self.m_panel3, 1, wx.EXPAND |wx.ALL, 5 )
		
		# self.m_staticText1 = wx.StaticText( self.m_panel1, wx.ID_ANY, u"功能选择", (200,120), wx.DefaultSize, 0 )
		# self.m_staticText1.Wrap( -1 )
		# self.m_staticText1.SetForegroundColour("SLATE BLUE")
		# font = wx.Font(20, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		# self.m_staticText1.SetFont(font)
		
		# bSizer3.Add( self.m_staticText1, 2, wx.ALIGN_CENTER_VERTICAL|wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )
		
		
		# bSizer2.Add( bSizer3, 1, wx.ALIGN_BOTTOM|wx.EXPAND, 5 )
		
		# bSizer4 = wx.BoxSizer( wx.VERTICAL )
		
		# bSizer5 = wx.BoxSizer( wx.HORIZONTAL )
		
		bmp = wx.Image("button1.bmp", wx.BITMAP_TYPE_PNG).ConvertToBitmap()
		'''
		bmp1 = wx.Image("button111.bmp", wx.BITMAP_TYPE_BMP).ConvertToBitmap()
		bmp2 = wx.Image("button112.bmp", wx.BITMAP_TYPE_BMP).ConvertToBitmap()
		bmp3 = wx.Image("button113.bmp", wx.BITMAP_TYPE_BMP).ConvertToBitmap()
		bmp4 = wx.Image("button116.bmp", wx.BITMAP_TYPE_BMP).ConvertToBitmap()
		bmp5 = wx.Image("button115.bmp", wx.BITMAP_TYPE_BMP).ConvertToBitmap()
		'''
		
		self.m_bpButton1 = buttons.GenBitmapTextButton(self.m_panel1, -1, bmp, u"月报监测  ",(140,170),(280,280),style=wx.NO_BORDER)#位图文本按钮
		# modified by vinosn
		#self.m_bpButton1 = buttons.GenBitmapTextButton(self.m_panel1, -1, bmp, u"月报监测  ",(self.m_panel1.Size.GetWidth()*4/7,self.m_panel1.Size.GetHeight()/3),(self.m_panel1.Size.GetWidth()*2/7,self.m_panel1.Size.GetHeight()/8),style=wx.NO_BORDER)#位图文本按钮

		self.m_bpButton1.SetUseFocusIndicator(False)
		font = wx.Font(30, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.m_bpButton1.SetFont(font)
		self.m_bpButton1.SetBackgroundColour("SKY BLUE")
		#self.m_bpButton1 = wx.BitmapButton( self.m_panel1, wx.ID_ANY, bmp1, (120,140),wx.DefaultSize, wx.BU_AUTODRAW )
		#bSizer5.Add( self.m_bpButton1, 0, wx.ALL, 5 )
		
		self.m_bpButton3 = buttons.GenBitmapTextButton(self.m_panel1, -1, bmp, u"实时频谱查看  ",(550,170),(380,120),style=wx.NO_BORDER)#位图文本按钮
		# modified by vinson
		#self.m_bpButton3 = buttons.GenBitmapTextButton(self.m_panel1, -1, bmp, u"实时频谱查看  ",(self.m_panel1.Size.GetWidth()*4/7,self.m_panel1.Size.GetHeight()*5/24),(self.m_panel1.Size.GetWidth()*2/7,self.m_panel1.Size.GetHeight()/8),style=wx.NO_BORDER)
		
		self.m_bpButton3.SetUseFocusIndicator(False)
		font = wx.Font(30, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.m_bpButton3.SetFont(font)
		self.m_bpButton3.SetBackgroundColour("SKY BLUE")
		
		self.m_bpButton2 = buttons.GenBitmapTextButton(self.m_panel1, -1, bmp, u"自定义频谱监测  ",(550,330),(380,120),style=wx.NO_BORDER)#位图文本按钮 
		# modified by vinson
		#self.m_bpButton2 = buttons.GenBitmapTextButton(self.m_panel1, -1, bmp, u"自定义频谱监测  ",(self.m_panel1.Size.GetWidth()/7,self.m_panel1.Size.GetHeight()/3),(self.m_panel1.Size.GetWidth()*2/7,self.m_panel1.Size.GetHeight()/3),style=wx.NO_BORDER)#位图文本按钮
        
		self.m_bpButton2.SetUseFocusIndicator(False)
		font = wx.Font(30, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.m_bpButton2.SetFont(font)
		self.m_bpButton2.SetBackgroundColour("SKY BLUE")


		
		bSizer1.Add( self.m_panel1, 1, wx.EXPAND |wx.ALL, 5 )
		self.SetSizer( bSizer1 )
		self.Layout()
		
		self.Centre( wx.BOTH )
	
	def __del__( self ):
		pass
		
	def OnEraseBack(self, evt):
		"""
		Add a picture to the background
		"""
		# yanked from ColourDB.py
		dc = evt.GetDC()

		if not dc:
			dc = wx.ClientDC(self)
			rect = self.GetUpdateRegion().GetBox()
			dc.SetClippingRect(rect)
		dc.Clear()
		bmp = wx.Bitmap("interface2.bmp")
		#print ('bmp')
		dc.DrawBitmap(bmp, 0, 0,)

###########################################################################
## Class MyDialog 配置参数设置
###########################################################################
class MyDialog1 ( wx.Dialog ):
	
	def __init__( self, parent,title=u"默认配置" ):

		wx.Dialog.__init__ ( self, parent, id = wx.ID_ANY, title = title, pos = wx.DefaultPosition, size = wx.Size( 580,570 ), style = wx.DEFAULT_DIALOG_STYLE|wx.SYSTEM_MENU )
		
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		
		bSizer169 = wx.BoxSizer( wx.VERTICAL )
		
		self.bx1=wx.StaticBox( self, wx.ID_ANY, u"基本设置:" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		self.bx1.SetForegroundColour("SLATE BLUE")
		font = wx.Font(10, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bx1.SetFont(font)
		sbSizer3 = wx.StaticBoxSizer(self.bx1, wx.VERTICAL )
		
		bSizer177 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText78 = wx.StaticText( self, wx.ID_ANY, u"起始频率：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText78.Wrap( -1 )
		bSizer177.Add( self.m_staticText78, 0, wx.ALL, 5 )
		
		self.m_textCtrl41 = wx.TextCtrl( self, wx.ID_ANY, str(config_data['start_freq']), wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer177.Add( self.m_textCtrl41, 0, wx.ALL, 5 )
		
		m_choice22Choices = ['MHz','GHz','KHz']
		self.m_choice22 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, (60,20), m_choice22Choices, 0 )
		self.m_choice22.SetSelection( 0 )
		bSizer177.Add( self.m_choice22, 0, wx.ALL, 5 )
		
		self.m_staticText79 = wx.StaticText( self, wx.ID_ANY, u"   RBW:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText79.Wrap( -1 )
		bSizer177.Add( self.m_staticText79, 0, wx.ALL, 5 )
		
		self.m_textCtrl42 = wx.TextCtrl( self, wx.ID_ANY, str(config_data['RBW']), wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer177.Add( self.m_textCtrl42, 0, wx.ALL, 5 )
		
		m_choice23Choices = ['KHz','GHz','MHz']
		self.m_choice23 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, (60,20), m_choice23Choices, 0 )
		self.m_choice23.SetSelection( 0 )
		bSizer177.Add( self.m_choice23, 0, wx.ALL, 5 )
		
		
		sbSizer3.Add( bSizer177, 1, wx.EXPAND, 5 )
		
		bSizer178 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText80 = wx.StaticText( self, wx.ID_ANY, u"终止频率：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText80.Wrap( -1 )
		bSizer178.Add( self.m_staticText80, 0, wx.ALL, 5 )
		
		self.m_textCtrl43 = wx.TextCtrl( self, wx.ID_ANY, str(config_data['end_freq']), wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer178.Add( self.m_textCtrl43, 0, wx.ALL, 5 )
		
		m_choice24Choices = ['MHz','GHz','KHz']
		self.m_choice24 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, (60,20), m_choice24Choices, 0 )
		self.m_choice24.SetSelection( 0 )
		bSizer178.Add( self.m_choice24, 0, wx.ALL, 5 )
		
		self.m_staticText81 = wx.StaticText( self, wx.ID_ANY, u"   VBW:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText81.Wrap( -1 )
		bSizer178.Add( self.m_staticText81, 0, wx.ALL, 5 )
		
		self.m_textCtrl44 = wx.TextCtrl( self, wx.ID_ANY, str(config_data['VBW']), wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer178.Add( self.m_textCtrl44, 0, wx.ALL, 5 )
		
		m_choice25Choices = ['KHz','GHz','MHz']
		self.m_choice25 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, (60,20), m_choice25Choices, 0 )
		self.m_choice25.SetSelection( 0 )
		bSizer178.Add( self.m_choice25, 0, wx.ALL, 5 )
		
		
		sbSizer3.Add( bSizer178, 1, wx.EXPAND, 5 )
		'''
		bSizer179 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText82 = wx.StaticText( self, wx.ID_ANY, u"频率步进：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText82.Wrap( -1 )
		bSizer179.Add( self.m_staticText82, 0, wx.ALL, 5 )
		
		self.m_textCtrl45 = wx.TextCtrl( self, wx.ID_ANY, str(config_data['step_freq']), wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer179.Add( self.m_textCtrl45, 0, wx.ALL, 5 )
		
		m_choice26Choices = ['MHz','GHz','KHz']
		self.m_choice26 = wx.Choice( self, wx.ID_ANY, wx.DefaultPosition, (60,20), m_choice26Choices, 0 )
		self.m_choice26.SetSelection( 0 )
		bSizer179.Add( self.m_choice26, 0, wx.ALL, 5 )
		
		
		sbSizer3.Add( bSizer179, 1, wx.EXPAND, 5 )
		'''
		
		bSizer169.Add( sbSizer3, 2, wx.EXPAND, 5 )
		
		
		self.bx2=wx.StaticBox( self, wx.ID_ANY, u"触发电平:" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		self.bx2.SetForegroundColour("SLATE BLUE")
		font = wx.Font(10, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bx2.SetFont(font)
		sbSizer4 = wx.StaticBoxSizer( self.bx2, wx.HORIZONTAL )
		
		self.m_staticText83 = wx.StaticText( self, wx.ID_ANY, u"  触发电平：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText83.Wrap( -1 )
		sbSizer4.Add( self.m_staticText83, 0, wx.ALL, 5 )
		
		self.m_textCtrl46 = wx.TextCtrl( self, wx.ID_ANY, str(config_data['trigger_level']), wx.DefaultPosition, wx.DefaultSize, 0 )
		sbSizer4.Add( self.m_textCtrl46, 0, wx.ALL, 5 )
		
		self.m_staticText84 = wx.StaticText( self, wx.ID_ANY, u"dB", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText84.Wrap( -1 )
		sbSizer4.Add( self.m_staticText84, 0, wx.ALL, 5 )
		
		
		bSizer169.Add( sbSizer4, 1, wx.EXPAND, 5 )
		
		
		self.bx3=wx.StaticBox( self, wx.ID_ANY, u"数据文件存储:" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		self.bx3.SetForegroundColour("SLATE BLUE")
		font = wx.Font(10, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bx3.SetFont(font)
		sbSizer5 = wx.StaticBoxSizer( self.bx3, wx.HORIZONTAL )
		
		bSizer180 = wx.BoxSizer( wx.VERTICAL )
		bSizer188 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_staticText85 = wx.StaticText( self, wx.ID_ANY, u"频谱数据存储路径：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText85.Wrap( -1 )
		bSizer188.Add( self.m_staticText85, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )
		bSizer180.Add( bSizer188, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )
		
		bSizer189 = wx.BoxSizer( wx.VERTICAL )
		self.m_staticText87 = wx.StaticText( self, wx.ID_ANY, u"Tek仪器程序路径： ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText87.Wrap( -1 )
		bSizer189.Add( self.m_staticText87, 0, wx.ALL|wx.ALIGN_CENTER_HORIZONTAL, 5 )
		bSizer180.Add( bSizer189, 1, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )
		sbSizer5.Add( bSizer180, 1, wx.EXPAND, 5 )
		

		
		bSizer181 = wx.BoxSizer( wx.VERTICAL)
		self.m_dirPicker2 = wx.DirPickerCtrl( self, wx.ID_ANY, config_data['Spec_dir'], u"Select a folder", wx.DefaultPosition, wx.DefaultSize, wx.DIRP_DEFAULT_STYLE )
		bSizer181.Add( self.m_dirPicker2, 0, wx.ALL|wx.EXPAND, 5 )

		
		self.m_filepath = wx.FilePickerCtrl( self, wx.ID_ANY, config_data['IQ_dir'], u"Select a file", u"", wx.DefaultPosition, wx.DefaultSize, wx.FLP_DEFAULT_STYLE )
		bSizer181.Add( self.m_filepath, 0, wx.ALL|wx.EXPAND, 5 )
		
		
		sbSizer5.Add( bSizer181, 4, wx.EXPAND, 5 )
		
		
		bSizer169.Add( sbSizer5, 2, wx.EXPAND, 5 )
		
		
		self.bx4=wx.StaticBox( self, wx.ID_ANY, u"月报频率段添加:" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		self.bx4.SetForegroundColour("SLATE BLUE")
		font = wx.Font(10, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bx4.SetFont(font)
		sbSizer6 = wx.StaticBoxSizer(self.bx4, wx.VERTICAL )
		
		bSizer183 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.m_staticText89 = wx.StaticText( self, wx.ID_ANY, u"初始频率：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText89.Wrap( -1 )
		bSizer183.Add( self.m_staticText89, 0, wx.ALL|wx.ALIGN_CENTER, 5 )
		self.m_textCtrl48 = wx.TextCtrl( self, wx.ID_ANY, str(config_data['start_freq']), wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer183.Add( self.m_textCtrl48, 0, wx.ALL|wx.ALIGN_CENTER, 5 )
		self.m_staticText1 = wx.StaticText( self, wx.ID_ANY, u"MHz", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText1.Wrap( -1 )
		bSizer183.Add( self.m_staticText1, 0, wx.ALL|wx.ALIGN_CENTER, 5 )
		
		self.m_staticText90 = wx.StaticText( self, wx.ID_ANY, u"  终止频率：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText90.Wrap( -1 )
		bSizer183.Add( self.m_staticText90, 0, wx.ALL|wx.ALIGN_CENTER, 5 )
		self.m_textCtrl49 = wx.TextCtrl( self, wx.ID_ANY, str(config_data['end_freq']), wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer183.Add( self.m_textCtrl49, 0, wx.ALL|wx.ALIGN_CENTER, 5 )
		self.m_staticText91 = wx.StaticText( self, wx.ID_ANY, u"MHz  ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText91.Wrap( -1 )
		bSizer183.Add( self.m_staticText91, 0, wx.ALL|wx.ALIGN_CENTER, 5 )
		
		'''
		self.m_button1=wx.Button(self,wx.ID_ANY,u"添加",wx.DefaultPosition,(120,25),0)
		bSizer183.Add(self.m_button1,1,wx.ALL|wx.ALIGN_CENTER,0)
		self.m_button1.Bind(wx.EVT_BUTTON,self.add_freqList)
		'''
		
		
		sbSizer6.Add( bSizer183, 1, wx.EXPAND, 5 )
		bSizer169.Add( sbSizer6, 1, wx.EXPAND, 5 )
		
		self.bx5=wx.StaticBox( self, wx.ID_ANY, u"数据库连接:" )
		#bx1.SetBackgroundColour("MEDIUM GOLDENROD")
		self.bx5.SetForegroundColour("SLATE BLUE")
		font = wx.Font(10, wx.DECORATIVE,wx.NORMAL,wx.BOLD)
		self.bx5.SetFont(font)
		sbSizer7 = wx.StaticBoxSizer( self.bx5, wx.VERTICAL )
		bSizer187 = wx.BoxSizer( wx.VERTICAL )
		bSizer188 = wx.BoxSizer( wx.HORIZONTAL )
		
		# self.m_radioBtn1 = wx.RadioButton( self, wx.ID_ANY, u"connection", wx.DefaultPosition, wx.DefaultSize, style = wx.RB_GROUP )
		# bSizer188.Add( self.m_radioBtn1, 0, wx.ALL, 5 )
		
		self.m_staticText_interface = wx.StaticText( self, wx.ID_ANY, u"接口:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText_interface.Wrap( -1 )
		bSizer188.Add( self.m_staticText_interface, 0, wx.ALL, 5 )
		
		self.m_textCtrl_interface = wx.TextCtrl( self, wx.ID_ANY, mysql_config['interface'], wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer188.Add( self.m_textCtrl_interface, 0, wx.ALL, 5 )
		
		self.m_staticText104 = wx.StaticText( self, wx.ID_ANY, u"台站 :  ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText104.Wrap( -1 )
		bSizer188.Add( self.m_staticText104, 0, wx.ALL, 5 )
		
		self.m_textCtrl20 = wx.TextCtrl( self, wx.ID_ANY, mysql_config['user3'], wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer188.Add( self.m_textCtrl20, 0, wx.ALL, 5 )
		
		self.m_staticText105 = wx.StaticText( self, wx.ID_ANY, u"password0: ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText105.Wrap( -1 )
		bSizer188.Add( self.m_staticText105, 0, wx.ALL, 5 )
		
		self.m_textCtrl21 = wx.TextCtrl( self, wx.ID_ANY, mysql_config['password3'], wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer188.Add( self.m_textCtrl21, 0, wx.ALL, 5 )
		
		# self.m_radioBtn2 = wx.RadioButton( self, wx.ID_ANY, u"no connection", wx.DefaultPosition, wx.DefaultSize, 0 )
		# bSizer188.Add( self.m_radioBtn2, 0, wx.ALL, 5 )
		self.Bind(wx.EVT_RADIOBUTTON, self.OnRadiogroup)
		bSizer187.Add( bSizer188, 1, wx.EXPAND, 5 )
		
		bSizer189 = wx.BoxSizer( wx.HORIZONTAL )
		self.m_staticText86 = wx.StaticText( self, wx.ID_ANY, u"host:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText86.Wrap( -1 )
		bSizer189.Add( self.m_staticText86, 0, wx.ALL, 5 )
		
		self.m_textCtrl14 = wx.TextCtrl( self, wx.ID_ANY, mysql_config['host'], wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer189.Add( self.m_textCtrl14, 0, wx.ALL, 5 )
		
		self.m_staticText88 = wx.StaticText( self, wx.ID_ANY, u"user1: ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText88.Wrap( -1 )
		bSizer189.Add( self.m_staticText88, 0, wx.ALL, 5 )
		
		self.m_textCtrl15 = wx.TextCtrl( self, wx.ID_ANY, mysql_config['user1'], wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer189.Add( self.m_textCtrl15, 0, wx.ALL, 5 )
		
		self.m_staticText102 = wx.StaticText( self, wx.ID_ANY, u"password1: ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText102.Wrap( -1 )
		bSizer189.Add( self.m_staticText102, 0, wx.ALL, 5 )
		
		self.m_textCtrl18 = wx.TextCtrl( self, wx.ID_ANY, mysql_config['password1'], wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer189.Add( self.m_textCtrl18, 0, wx.ALL, 5 )
		bSizer187.Add( bSizer189, 1, wx.EXPAND, 5 )
		
		bSizer190 = wx.BoxSizer( wx.HORIZONTAL )
		self.m_staticText100 = wx.StaticText( self, wx.ID_ANY, u"SID :", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText100.Wrap( -1 )
		bSizer190.Add( self.m_staticText100, 0, wx.ALL, 5 )
		
		self.m_textCtrl16 = wx.TextCtrl( self, wx.ID_ANY, mysql_config['SID'], wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer190.Add( self.m_textCtrl16, 0, wx.ALL, 5 )
		
		self.m_staticText101 = wx.StaticText( self, wx.ID_ANY, u"user2: ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText101.Wrap( -1 )
		bSizer190.Add( self.m_staticText101, 0, wx.ALL, 5 )
		
		self.m_textCtrl17 = wx.TextCtrl( self, wx.ID_ANY, mysql_config['user2'], wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer190.Add( self.m_textCtrl17, 0, wx.ALL, 5 )
		
		self.m_staticText103 = wx.StaticText( self, wx.ID_ANY, u"password2: ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText103.Wrap( -1 )
		bSizer190.Add( self.m_staticText103, 0, wx.ALL, 5 )
		
		self.m_textCtrl19 = wx.TextCtrl( self, wx.ID_ANY, mysql_config['password2'], wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer190.Add( self.m_textCtrl19, 0, wx.ALL, 5 )
		bSizer187.Add( bSizer190, 1, wx.EXPAND, 5 )
		'''
		bSizer191 = wx.BoxSizer( wx.HORIZONTAL )
		self.m_staticText104 = wx.StaticText( self, wx.ID_ANY, u"station: ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText104.Wrap( -1 )
		bSizer191.Add( self.m_staticText104, 0, wx.ALL, 5 )
		
		self.m_textCtrl20 = wx.TextCtrl( self, wx.ID_ANY, mysql_config['user3'], wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer191.Add( self.m_textCtrl20, 0, wx.ALL, 5 )
		
		self.m_staticText105 = wx.StaticText( self, wx.ID_ANY, u"password2: ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText105.Wrap( -1 )
		bSizer191.Add( self.m_staticText105, 00, wx.ALL, 5 )
		
		self.m_textCtrl21 = wx.TextCtrl( self, wx.ID_ANY, mysql_config['password3'], wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer191.Add( self.m_textCtrl21, 0, wx.ALL, 5 )
		bSizer187.Add( bSizer191, 1, wx.EXPAND, 5 )
		'''
		
		sbSizer7.Add( bSizer187, 1, wx.EXPAND, 5 )
		bSizer169.Add( sbSizer7, 1, wx.EXPAND, 5 )
		
		bSizer184 = wx.BoxSizer( wx.HORIZONTAL )
		
		bSizer185 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_button44 = wx.Button( self, wx.ID_OK, "OK", wx.DefaultPosition, wx.DefaultSize, 0 )
		#self.Bind(wx.EVT_BUTTON, self.Save_config, self.m_button44) 
		bSizer185.Add( self.m_button44, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )
		
		
		bSizer184.Add( bSizer185, 1, wx.EXPAND, 5 )
		
		bSizer186 = wx.BoxSizer( wx.VERTICAL )
		
		self.m_button45 = wx.Button( self, wx.ID_CANCEL, u"Cancel", wx.DefaultPosition, wx.DefaultSize, 0 )
		bSizer186.Add( self.m_button45, 0, wx.ALIGN_CENTER_HORIZONTAL|wx.ALL, 5 )
		
		
		bSizer184.Add( bSizer186, 1, wx.EXPAND, 5 )
		
		
		bSizer169.Add( bSizer184, 1, wx.EXPAND, 0 )
		
		
		self.SetSizer( bSizer169 )
		
		
	def get_config_value(self):
		config_value=[]
		config_value.append(self.m_textCtrl41.GetValue())
		config_value.append(self.m_textCtrl43.GetValue())
		config_value.append(self.m_textCtrl42.GetValue())
		config_value.append(self.m_textCtrl44.GetValue())
		#config_value.append(self.m_textCtrl45.GetValue())
		config_value.append(0) #没有输入，暂留空
		config_value.append(self.m_textCtrl46.GetValue())
		config_value.append(self.m_dirPicker2.GetPath())
		config_value.append(self.m_filepath.GetPath())
		config_value.append(self.m_textCtrl48.GetValue())
		config_value.append(self.m_textCtrl49.GetValue())
		return config_value
	
	def get_mysql_value(self):
		mysql_config_data=[]
		mysql_config_data.append(self.m_textCtrl14.GetValue())  #host
		mysql_config_data.append(self.m_textCtrl16.GetValue())  #SID
		mysql_config_data.append(self.m_textCtrl15.GetValue())  #user1
		mysql_config_data.append(self.m_textCtrl18.GetValue())  #password1
		mysql_config_data.append(self.m_textCtrl17.GetValue())  #user2
		mysql_config_data.append(self.m_textCtrl19.GetValue())  #password2
		mysql_config_data.append(self.m_textCtrl20.GetValue())  #user3
		mysql_config_data.append(self.m_textCtrl21.GetValue())  #password3
		mysql_config_data.append(self.m_textCtrl_interface.GetValue())  #interface 1521
		return mysql_config_data
	
	def OnRadiogroup(self,event):
		rb = event.GetEventObject() 
		if rb.GetLabel()=='connection':
			database_state=1
		if rb.GetLabel()=='no connection':
			database_state=0
		print (database_state)
		
###########################################################################
## Class MyFrame1 主框架
###########################################################################
class MyFrame1 ( wx.Frame ):
	def __init__( self, parent ):
		# wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"无线电监测分析与测向软件", pos = wx.DefaultPosition, size = wx.Size( 1126,740 ), style = wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.CLIP_CHILDREN|wx.TAB_TRAVERSAL )
		wx.Frame.__init__ ( self, parent, id = wx.ID_ANY, title = u"无线电监测分析与测向软件", \
			pos = wx.DefaultPosition, size = wx.Size( 1126,755 ), \
			style = wx.MINIMIZE_BOX|wx.SYSTEM_MENU|wx.CAPTION|wx.CLOSE_BOX|wx.CLIP_CHILDREN|wx.TAB_TRAVERSAL )
		'''
		# #改变注册表，使得python 默认的ie版本为ie11,只有高版本的ie才能在地图上加线条，箭头
		# self.key = winreg.OpenKey(winreg.HKEY_CURRENT_USER, 
			  # r"SOFTWARE\Microsoft\Internet Explorer\Main\FeatureControl\FEATURE_BROWSER_EMULATION", 0, winreg.KEY_ALL_ACCESS)
		# try:
			# # 设置注册表python.exe 值为 11000(IE11)
			# print ('ie11')
			# winreg.SetValueEx(self.key, 'python.exe', 0, winreg.REG_DWORD, 0x00002af8)
		# except:
			# # 设置出现错误
			# print('error in set value!')
		'''
		#self.SetOwnBackgroundColour('red')
		#self.SetBackgroundColour("WHITE")
		#self.Bind(wx.EVT_PAINT, self.OnPaint)
		self.SetSizeHints( wx.DefaultSize, wx.DefaultSize )
		self.SetFont( wx.Font( 9, 70, 90, 92, False, "宋体" ) )
		
		#self.m_statusBar1 = self.CreateStatusBar( 1, wx.ST_SIZEGRIP, wx.ID_ANY )
		self.m_menubar1 = wx.MenuBar( 0 )
		self.m_menu1 = wx.Menu()
		mDetection=self.m_menu1.Append(-1, u"功能模块")
		#self.Data_input=self.m_menu1.AppendRadioItem(-1, "数据导入")
		self.m_menubar1.Append( self.m_menu1, u"功能模块" )
		self.Bind(wx.EVT_MENU, self.Detection1, mDetection)																								 
		module_select = wx.Menu()
		month_monitor = module_select.Append(-1,u"月报监测")
		free_monitor = wx.Menu()
		free_spectrum = free_monitor.Append(-1,u"频谱监测")
		airplane_spectrum = free_monitor.Append(-1,u"无人机监测")
		spectrum_occupancy = free_monitor.Append(-1,u"信号占用度")
		signal_direction = free_monitor.Append(-1,u"信号测向")
		
		module_select.Append(wx.ID_ANY,u"自定义监测",free_monitor)
		Tek_monitor = module_select.Append(-1,u"实时频谱查看")
		self.m_menu1.Append(wx.ID_ANY,u"模块选择",module_select)
		
		self.Bind(wx.EVT_MENU, self.switch_to_monReport, month_monitor)
		self.Bind(wx.EVT_MENU, self.openTek, Tek_monitor)
		self.Bind(wx.EVT_MENU, self.switch_to_spectrum, free_spectrum)
		self.Bind(wx.EVT_MENU, self.switch_to_UAV, airplane_spectrum)
		self.Bind(wx.EVT_MENU, self.switch_to_occupancy,spectrum_occupancy)
		self.Bind(wx.EVT_MENU, self.switch_to_radio, signal_direction)
		
		#self.m_menubar1.Append( self.m_menu1, u"功能模块" )
		
		self.m_menu3 = wx.Menu()
		config=self.m_menu3.Append(-1,u"默认参数设置")
		station_update = self.m_menu3.Append(-1,u"台站数据更新")
		self.m_menubar1.Append( self.m_menu3, u"参数配置" ) 
		self.Bind(wx.EVT_MENU, self.select_Config, config)
		self.Bind(wx.EVT_MENU, self.station_data_update, station_update)
		
		self.m_menu4 = wx.Menu()

		Connect=self.m_menu4.Append( -1, u"连接仪器" )
		disConnect=self.m_menu4.Append( -1, u"断开仪器" )
		self.ID_connect=Connect.GetId()
		self.ID_disConnect=disConnect.GetId()
		print (self.ID_connect,self.ID_disConnect)
		
		
		self.m_menubar1.Append( self.m_menu4, u"仪器连接" ) 
		self.m_menubar1.Enable(self.ID_disConnect, False) 
		self.Bind(wx.EVT_MENU,self.connect,Connect)
		self.Bind(wx.EVT_MENU,self.disconnect,disConnect)
		
		self.m_menu5 = wx.Menu()
		self.helpTxt = self.m_menu5.Append( -1, u"帮助文档")
		self.m_menubar1.Append( self.m_menu5, u"帮助" ) 
		self.Bind(wx.EVT_MENU,self.get_help_txt,self.helpTxt)
		
		self.SetMenuBar( self.m_menubar1 )
		
     # toolbar create  by vinson
		#toolbar = wx.ToolBar(self,wx.ID_ANY,wx.DefaultPosition,wx.DefaultSize, wx.TB_HORZ_TEXT,"")
		toolbar=self.CreateToolBar()
		month_monitor_tool = toolbar.AddTool(wx.ID_ANY,"",wx.Bitmap("iMonthMonitor.ico"),u"月报监测")
		free_spectrum_tool = toolbar.AddTool(wx.ID_ANY,"",wx.Bitmap("iCustomMonitor.ico"),u"自定义监测")
		airplane_spectrum_tool = toolbar.AddTool(wx.ID_ANY,"",wx.Bitmap("iUAV.ico"),u"无人机监测")
		spectrum_occupancy_tool = toolbar.AddTool(wx.ID_ANY,"",wx.Bitmap("iOccupation.ico"),u"占用度分析")
		signal_direction_tool = toolbar.AddTool(wx.ID_ANY,"",wx.Bitmap("iDirectionFind.ico"),u"测向")
		connect_tool = toolbar.AddTool(wx.ID_ANY,"",wx.Bitmap("iConnect.ico"),u"连接仪表")
		disConnect_tool = toolbar.AddTool(wx.ID_ANY,"",wx.Bitmap("iDisconnect.ico"),u"断开仪表")
		help_tool=toolbar.AddTool(wx.ID_ANY,"",wx.Bitmap("iHelp.ico"),u"帮助")
		openTek_tool=toolbar.AddTool(wx.ID_ANY,"",wx.Bitmap("iSpectrum.ico"),u"实时频谱")
		toolbar.Realize()
		
		self.Bind(wx.EVT_TOOL, self.switch_to_monReport, month_monitor_tool)
		self.Bind(wx.EVT_TOOL, self.switch_to_spectrum, free_spectrum_tool)
		self.Bind(wx.EVT_TOOL, self.switch_to_UAV, airplane_spectrum_tool)
		self.Bind(wx.EVT_TOOL, self.switch_to_occupancy,spectrum_occupancy_tool)
		self.Bind(wx.EVT_TOOL, self.switch_to_radio, signal_direction_tool)     #测向
		self.Bind(wx.EVT_TOOL, self.openTek, openTek_tool)
		self.Bind(wx.EVT_TOOL, self.connect, connect_tool)
		self.Bind(wx.EVT_TOOL, self.disconnect,disConnect_tool)
		self.Bind(wx.EVT_TOOL, self.get_help_txt, help_tool)
		
		self.mainSizer=wx.BoxSizer( wx.VERTICAL )
		
		self.bSizer1 = wx.BoxSizer( wx.HORIZONTAL )
		
		self.buttom_color="lightgray"
		
		
		self.panelOne_one = MyPanel1_1(self)    # 自定义频谱信号载入回放，共享面板
		self.panelOne_two = MyPanel1_2(self)    # 月报频谱信号载入回放，共享面板
		self.panelTwo = MyPanel2(self)    # 台站检测模块，已去掉该功能
		self.panelThree = MyPanel3(self)  # 频谱占用度
		self.panelFour = MyPanel4(self)   # 测向
		self.panelFive= MyPanel5(self)    # 无人机界面
		self.panelSix = MyPanel6(self)    # 自定义监测，无人机监测， 占用度分析等功能选择界面
		self.panelSeven= MyPanel7(self)    # 月报监测，频谱实时查看和自定义监测 功能选择界面
		self.panelOne_one.Hide()
		self.panelOne_two.Hide()
		self.panelTwo.Hide()
		self.panelThree.Hide()
		self.panelFour.Hide()
		self.panelFive.Hide()
		self.panelSix.Hide()
		###################################
		###更新panelThree中选择的目录

		####################################
		self.bSizer3 = wx.BoxSizer( wx.VERTICAL )
		
		self.bSizer3.Add( self.panelOne_one, 1, wx.EXPAND , 5 )
		self.bSizer3.Add( self.panelOne_two, 1, wx.EXPAND , 5 )
		self.bSizer3.Add( self.panelTwo, 1, wx.EXPAND , 5 )
		self.bSizer3.Add( self.panelThree, 1, wx.EXPAND , 5 )
		self.bSizer3.Add( self.panelFour, 1, wx.EXPAND , 5 )
		self.bSizer3.Add( self.panelFive, 1, wx.EXPAND , 5 )
		self.bSizer3.Add( self.panelSix, 1, wx.EXPAND , 5 )
		self.bSizer3.Add( self.panelSeven,1,wx.EXPAND, 5 )
		
		self.bSizer1.Add( self.bSizer3, 10, wx.EXPAND, 5 )
		
		
		self.mainSizer.Add( self.bSizer1, 40, wx.EXPAND, 0 )
		
		# self.m_staticline11 = wx.StaticLine( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.LI_HORIZONTAL )
		# self.mainSizer.Add( self.m_staticline11, 0, wx.EXPAND |wx.ALL, 0 )
		
		self.statusBar=self.CreateStatusBar()
		self.statusBar.SetFieldsCount(10)
		self.statusBar.SetStatusWidths([-6,-1,-1,-1,-1,-1,-2,-3,-1,-3])
		self.statusBar.SetStatusText(u"北京昊翔通讯有限公司",0)
		self.statusBar.SetStatusText(u"连接的仪表为：",6)
		self.statusBar.SetStatusText(u"序列号:",8)

		'''										
		self.stateSizer1=wx.BoxSizer( wx.VERTICAL)
		self.m_panel13 = wx.Panel( self, wx.ID_ANY, wx.DefaultPosition, wx.DefaultSize, wx.TAB_TRAVERSAL )
		self.m_panel13.SetBackgroundColour(self.buttom_color)
		self.stateSizer=wx.BoxSizer(wx.HORIZONTAL)
		
		
		self.m_staticText61 = wx.StaticText( self.m_panel13, wx.ID_ANY, u" 北京吴翔通讯有限公司 ", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText61.Wrap( -1 )
		self.stateSizer.Add( self.m_staticText61, 3, wx.ALL, 5 )
		
		self.stateSizer.AddStretchSpacer(3) 
		
		self.m_staticText62 = wx.StaticText( self.m_panel13, wx.ID_ANY, u"测试仪器信息：", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText62.Wrap( -1 )
		self.stateSizer.Add( self.m_staticText62, 1, wx.ALL|wx.ALIGN_CENTER, 5 )
		
		self.m_textCtrl50 = wx.TextCtrl( self.m_panel13, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.stateSizer.Add( self.m_textCtrl50, 1, wx.ALL|wx.ALIGN_CENTER, 5 )
		
		self.m_staticText64 = wx.StaticText( self.m_panel13, wx.ID_ANY, u"     序列号:", wx.DefaultPosition, wx.DefaultSize, 0 )
		self.m_staticText64.Wrap( -1 )
		self.stateSizer.Add( self.m_staticText64, 1, wx.ALL|wx.ALIGN_CENTER, 5 )
		
		self.m_textCtrl51 = wx.TextCtrl( self.m_panel13, wx.ID_ANY, wx.EmptyString, wx.DefaultPosition, wx.DefaultSize, 0 )
		self.stateSizer.Add( self.m_textCtrl51, 1, wx.ALL|wx.ALIGN_CENTER, 5 )
		
		self.m_panel13.SetSizer(self.stateSizer)
		self.m_panel13.Layout()
		self.stateSizer.Fit( self.m_panel13 )
		self.stateSizer1.Add( self.m_panel13, 1, wx.EXPAND, 5 )
		
		self.mainSizer.Add( self.stateSizer1, 1, wx.EXPAND, 5 )
		
		'''
		self.SetSizer( self.mainSizer )
		self.Layout()
		
		self.Centre( wx.BOTH )
		
		# Connect Events
		# self.m_button1.Bind( wx.EVT_BUTTON, self.switch_to_spectrum )
		# self.m_button2.Bind( wx.EVT_BUTTON, self.switch_to_station )
		# self.m_button3.Bind( wx.EVT_BUTTON, self.switch_to_occupancy )
		# self.m_button4.Bind( wx.EVT_BUTTON, self.switch_to_radio )
		# self.m_button5.Bind( wx.EVT_BUTTON, self.switch_to_UAV )
		
		self.panelSix.m_bpButton1.Bind( wx.EVT_BUTTON, self.switch_to_spectrum )
		#self.panelSix.m_bpButton2.Bind( wx.EVT_BUTTON, self.switch_to_station )
		self.panelSix.m_bpButton3.Bind( wx.EVT_BUTTON, self.switch_to_occupancy )
		self.panelSix.m_bpButton4.Bind( wx.EVT_BUTTON, self.switch_to_radio )
		self.panelSix.m_bpButton5.Bind( wx.EVT_BUTTON, self.switch_to_UAV )
		self.panelSeven.m_bpButton1.Bind( wx.EVT_BUTTON, self.switch_to_monReport )
		self.panelSeven.m_bpButton2.Bind( wx.EVT_BUTTON, self.switch_to_real_time_report )
		self.panelSeven.m_bpButton3.Bind( wx.EVT_BUTTON, self.openTek )
		#self.m_button6.Bind( wx.EVT_BUTTON, self.data_import_show )
		#self.m_button7.Bind( wx.EVT_BUTTON, self.stop_import_show )
		self.Bind(wx.EVT_CLOSE, self.OnClose)
		# self.timer = wx.Timer(self)#创建定时器
		# self.Bind(wx.EVT_TIMER, self.onTimer,self.timer)  #设置定时事件
		# self.timer.Start(1000)
		self.threads3=[]
		
		#设置定时器
		self.timer = wx.Timer(self)#创建定时器
		self.Bind(wx.EVT_TIMER, self.onTimer,self.timer)  #设置定时事件
		self.timer.Start(1000)
	
	def __del__( self ):
		pass
	
	
	# 面板切换
	def switch_to_monReport(self,event):
		global mon_or_real
		global connect_state
		print ("Loading...")
		if self.panelOne_two.IsShown():
		    pass
		else:
			mon_or_real = 0
			self.panelTwo.Hide()
			self.panelThree.Hide()
			self.panelFour.Hide()
			self.panelFive.Hide()
			self.panelSix.Hide()
			self.panelSeven.Hide()
			#self.panelOne.Show()
			#self.panelOne.list_ctrl.DeleteAllItems() # delete all exixted data
			self.panelOne_one.Hide()
			self.panelOne_two.Show()
			#self.panelOne_one.list_ctrl.DeleteAllItems()   #清空之前信号列表的数据
			#self.panelOne_one.point = []                   #导入数据清理
			self.Refresh() 
		self.Layout()

    # panel1在上面已经show过了，这里不是应该 self.Hide(),就可以了么？
    # 为什么要又hide又show的?
    
		# self.Centre( wx.BOTH )
		self.Hide()
		self.Show() #?????
		event.Skip()

	def switch_to_real_time_report(self,event):
		global mon_or_real
		global connect_state
		print ("6235 Loading switch_to_real_time_report")
		if self.panelSix.IsShown():
		    pass
		else:
			mon_or_real = 1
			self.panelOne_one.Hide()
			self.panelOne_two.Hide()
			self.panelTwo.Hide()
			self.panelThree.Hide()
			self.panelFour.Hide()
			self.panelFive.Hide()
			self.panelSix.Show()
			self.panelSeven.Hide()
			#self.panelOne.list_ctrl.DeleteAllItems()   #清空之前信号列表的数据
			self.Refresh() 
		self.Layout()

		# self.Centre( wx.BOTH )
		self.Hide()
		self.Show() #
		event.Skip()
		
	def switch_to_spectrum( self, event ):
		global mon_or_real
		print ("Loading...")
		if self.panelOne_one.IsShown():
		    pass
		else:
			mon_or_real = 1
			self.panelTwo.Hide()
			self.panelThree.Hide()
			self.panelFour.Hide()
			self.panelFive.Hide()
			self.panelSix.Hide()
			self.panelSeven.Hide()
			#self.panelOne.Show()
			#self.panelOne.list_ctrl.DeleteAllItems() # clear all existed data
			self.panelOne_one.Show()
			self.panelOne_two.Hide()
			#self.panelOne.point = []                   #导入数据清理
			self.Refresh()
			#self.panelOne.Refresh()

			# self.bSizer3 = wx.BoxSizer( wx.VERTICAL )

			# self.bSizer3.Add( self.panelOne, 1, wx.EXPAND |wx.ALL, 5 )
				
			# self.bSizer1.Add( self.bSizer3, 5, wx.EXPAND, 5 )

			# self.SetSizer( self.bSizer1 )
		self.Layout()

		# self.Centre( wx.BOTH )
		self.Hide()
		self.Show() #?????
		
		event.Skip()
	
	def switch_to_station( self, event ):
		print ("Loading...")
		if self.panelTwo.IsShown():
		    pass
		else:
			self.panelOne_one.Hide()
			self.panelOne_two.Hide()
			self.panelTwo.Show()
			self.panelThree.Hide()
			self.panelFour.Hide()
			self.panelFive.Hide()
			self.panelSix.Hide()
			self.panelSeven.Hide()
			# self.m_panel6.SetBackgroundColour("MEDIUM TURQUOISE")
			# self.m_panel5.SetBackgroundColour(self.buttom_color)
			# self.m_panel7.SetBackgroundColour(self.buttom_color)
			# self.m_panel8.SetBackgroundColour(self.buttom_color)
			# self.m_panel9.SetBackgroundColour(self.buttom_color)
			# self.m_panel10.SetBackgroundColour(self.buttom_color)
			# self.m_panel11.SetBackgroundColour(self.buttom_color)
			self.Refresh() 
		self.Layout()

		event.Skip()
	
	def switch_to_occupancy( self, event ):
		print ("Loading occupancy")
		print ("Loading occupancy")
		if self.panelThree.IsShown():
		    pass
		else:
			self.panelOne_one.Hide()
			self.panelOne_two.Hide()
			self.panelTwo.Hide()
			self.panelThree.Show()
			self.panelFour.Hide()
			self.panelFive.Hide()
			self.panelSix.Hide()
			self.panelSeven.Hide()
			# self.m_panel7.SetBackgroundColour("MEDIUM TURQUOISE")
			# self.m_panel6.SetBackgroundColour(self.buttom_color)
			# self.m_panel5.SetBackgroundColour(self.buttom_color)
			# self.m_panel8.SetBackgroundColour(self.buttom_color)
			# self.m_panel9.SetBackgroundColour(self.buttom_color)
			# self.m_panel10.SetBackgroundColour(self.buttom_color)
			# self.m_panel11.SetBackgroundColour(self.buttom_color)
			self.Refresh() 

		self.Layout()

		# self.Centre( wx.BOTH )
			
		event.Skip()
	
	def switch_to_radio( self, event ):
		print ("Loading radio")
		if self.panelFour.IsShown():
		    pass
		else:
			self.panelOne_one.Hide()
			self.panelOne_two.Hide()
			self.panelTwo.Hide()
			self.panelThree.Hide()
			self.panelFour.Show()
			self.panelFive.Hide()
			self.panelSix.Hide()
			self.panelSeven.Hide()
			# self.m_panel8.SetBackgroundColour("MEDIUM TURQUOISE")
			# self.m_panel6.SetBackgroundColour(self.buttom_color)
			# self.m_panel7.SetBackgroundColour(self.buttom_color)
			# self.m_panel5.SetBackgroundColour(self.buttom_color)
			# self.m_panel9.SetBackgroundColour(self.buttom_color)
			# self.m_panel10.SetBackgroundColour(self.buttom_color)
			# self.m_panel11.SetBackgroundColour(self.buttom_color)
			self.Refresh() 

		self.Layout()
		event.Skip()
	
	def switch_to_UAV( self, event ):
		print ("Loading UAV monitor")
		if self.panelFive.IsShown():
		    pass
		else:
			self.panelOne_one.Hide()
			self.panelOne_two.Hide()
			self.panelTwo.Hide()
			self.panelThree.Hide()
			self.panelFour.Hide()
			self.panelFive.Show()
			self.panelSix.Hide()
			self.panelSeven.Hide()
			# self.m_panel9.SetBackgroundColour("MEDIUM TURQUOISE")
			# self.m_panel6.SetBackgroundColour(self.buttom_color)
			# self.m_panel7.SetBackgroundColour(self.buttom_color)
			# self.m_panel8.SetBackgroundColour(self.buttom_color)
			# self.m_panel5.SetBackgroundColour(self.buttom_color)
			# self.m_panel10.SetBackgroundColour(self.buttom_color)
			# self.m_panel11.SetBackgroundColour(self.buttom_color)
			self.Refresh() 
		self.Layout()

		event.Skip()
	
	def data_import_show(self):
		self.m_panel10.SetBackgroundColour("MEDIUM TURQUOISE")
		self.m_panel6.SetBackgroundColour(self.buttom_color)
		self.m_panel7.SetBackgroundColour(self.buttom_color)
		self.m_panel8.SetBackgroundColour(self.buttom_color)
		self.m_panel9.SetBackgroundColour(self.buttom_color)
		self.m_panel5.SetBackgroundColour(self.buttom_color)
		self.m_panel11.SetBackgroundColour(self.buttom_color)
		self.Refresh() 
		if work_state==0:
			################################
			# 尝试一种新的画图方法
			self.panelOne.figure_score = Figure((6,4),100)
			
			self.panelOne.canvas = FigureCanvas(self.panelOne.panelOne_one.m_panel2, wx.ID_ANY, self.panelOne.figure_score)
			self.panelOne.axes_score = self.panelOne.figure_score.add_subplot(111,facecolor='k')
			#self.axes_score.set_autoscale_on(False) #关闭坐标轴自动缩放
			self.panelOne.traceData=[-100]*801
			self.panelOne.freq=self.x_mat[0,:]
			#self.freq=range(int(self.start_freq_cu),int(self.end_freq_cu)+int((self.end_freq_cu-self.start_freq_cu)/800),int((self.end_freq_cu-self.start_freq_cu)/800))
			self.panelOne.l_user,=self.panelOne.axes_score.plot(self.panelOne.freq, self.panelOne.traceData, 'b')
			self.panelOne.axes_score.set_ylim(-90,-30)
			#self.panelOne.axes_score.set_ylim(min(self.panelOne.traceData)-10,max(self.panelOne.traceData)+5)  # modified by vinson
			self.panelOne.axes_score.set_title('Spectrum')
			self.panelOne.axes_score.grid(True,color='y')
			self.panelOne.axes_score.set_xlabel('Frequency/MHz')
			self.panelOne.axes_score.set_ylabel('Amplitude/dBmV')
			self.panelOne.canvas.draw()
			self.panelOne.bg = self.panelOne.canvas.copy_from_bbox(self.panelOne.axes_score.bbox)
			self.t3 = WorkerThread3(self.panelOne,self.start_freq_cu,self.end_freq_cu,self.x_mat,self.y_mat,self.continue_time)
			self.threads3.append(self.t3)
			self.t3.start()
		else:
			wx.MessageBox('The current working mode isn\'t data_import', "Message" ,wx.OK | wx.ICON_INFORMATION)

	def stop_import_show(self):
		self.m_panel11.SetBackgroundColour("MEDIUM TURQUOISE")
		self.m_panel6.SetBackgroundColour(self.buttom_color)
		self.m_panel7.SetBackgroundColour(self.buttom_color)
		self.m_panel8.SetBackgroundColour(self.buttom_color)
		self.m_panel9.SetBackgroundColour(self.buttom_color)
		self.m_panel10.SetBackgroundColour(self.buttom_color)
		self.m_panel5.SetBackgroundColour(self.buttom_color)
		self.Refresh()
		while self.threads3:
			thread=self.threads3[0]
			thread.stop()
			self.threads3.remove(thread)

	
	def connect(self,event):
		print ('connect')
		global rsa_true
		global deviceSerial_ture
		global connect_state
		global connect_machine
		try:
			[connect_result,self.rsa,self.message]=method.instrument_connect()
			if connect_result==0:
				wx.MessageBox(u'仪表未正常连接，无法执行测试任务！', "Error" ,wx.OK | wx.ICON_ERROR)
			elif connect_result==2:
				wx.MessageBox(u'仪表检测错误，请重新连接，并确认只连接一台仪表！', "Error" ,wx.OK | wx.ICON_ERROR)
			else:
				connect_machine = self.message[0]
				#self.m_textCtrl50.SetValue(self.message[0])
				self.statusBar.SetStatusText(self.message[0],7)
				self.statusBar.SetStatusText(self.message[1],9)
#				#self.m_textCtrl51.SetValue(self.message[1])
				wx.MessageBox('设备已正常连接，可执行测试任务！', "Message" ,wx.OK | wx.ICON_INFORMATION )
				enabled = self.m_menubar1.IsEnabled(self.ID_connect) 
				self.m_menubar1.Enable(self.ID_connect, not enabled) 
				self.m_menubar1.Enable(self.ID_disConnect, enabled) 
				print (self.message)
				rsa_true=self.rsa
				deviceSerial_true=self.message[1]
				connect_state=1
				#servicedid,freqname,freqrange_list = method.read_service(method.conn_str2)
				method.month_freq_list,method.month_freq_str = method.read_month_freq_list()
				freqrange_list = method.month_freq_str
				self.panelOne_two.choice1.SetItems(freqrange_list)
				self.panelOne_two.choice1.SetSelection(0)
		except Exception as e:
			wx.MessageBox(str(e), "Message" ,wx.OK | wx.ICON_INFORMATION)
	
	def disconnect(self,event):
		print ('disconnect')
		global connect_state
		try:
			method.instrument_disconnect(self.rsa)
			self.message=[]
            
#			self.m_textCtrl50.SetValue('')
#			self.m_textCtrl51.SetValue('')
			self.statusBar.SetStatusText("",7)
			self.statusBar.SetStatusText("",9)
			enabled = self.m_menubar1.IsEnabled(self.ID_disConnect) 
			self.m_menubar1.Enable(self.ID_disConnect, not enabled) 
			self.m_menubar1.Enable(self.ID_connect, enabled)
			wx.MessageBox(u'设备连接已断开！', "Message" ,wx.OK | wx.ICON_INFORMATION )
			connect_state=0
		except Exception as e:
			wx.MessageBox(str(e), "Message" ,wx.OK | wx.ICON_INFORMATION)
			
	def Ontimer_disconnect(self):
		print ('disconnect')
		global connect_state
		try:
			method.instrument_disconnect(self.rsa)
			self.message=[]
#			self.m_textCtrl50.SetValue('')
#			self.m_textCtrl51.SetValue('')
			self.statusBar.SetStatusText("",7)
			self.statusBar.SetStatusText("",9)
			enabled = self.m_menubar1.IsEnabled(self.ID_disConnect) 
			self.m_menubar1.Enable(self.ID_disConnect, not enabled) 
			self.m_menubar1.Enable(self.ID_connect, enabled)
			connect_state=0
		except Exception as e:
			wx.MessageBox(str(e), "Message" ,wx.OK | wx.ICON_INFORMATION)
	
	def first_connect(self):
		print ('connect')
		global rsa_true
		global deviceSerial_ture
		global connect_state
		global connect_machine
		try:
			[connect_result,self.rsa,self.message]=method.instrument_connect()
			if connect_result==0:
				wx.MessageBox(u'仪表未正常连接，无法执行测试任务！', "Error" ,wx.OK | wx.ICON_ERROR)
			elif connect_result==2:
				wx.MessageBox(u'仪表检测错误，请重新连接，并确认只连接一台仪表！', "Error" ,wx.OK | wx.ICON_ERROR)
			else:
				connect_machine = self.message[0]
#				self.m_textCtrl50.SetValue(self.message[0])
#				self.m_textCtrl51.SetValue(self.message[1])
				self.statusBar.SetStatusText(self.message[0],7)
				self.statusBar.SetStatusText(self.message[1],9)												  
				wx.MessageBox(u'设备已正常连接，可执行测试任务！', "Message" ,wx.OK | wx.ICON_INFORMATION )
				enabled = self.m_menubar1.IsEnabled(self.ID_connect) 
				self.m_menubar1.Enable(self.ID_connect, not enabled) 
				self.m_menubar1.Enable(self.ID_disConnect, enabled) 
				print (self.message)
				rsa_true=self.rsa
				deviceSerial_true=self.message[1]
				connect_state=1
				#servicedid,freqname,freqrange_list = method.read_service(method.conn_str2)
				method.month_freq_list,method.month_freq_str = method.read_month_freq_list()
				freqrange_list = method.month_freq_str
				self.panelOne_two.choice1.SetItems(freqrange_list)
				self.panelOne_two.choice1.SetSelection(0)
		except Exception as e:
			wx.MessageBox(str(e), "Message" ,wx.OK | wx.ICON_INFORMATION)
	
	def select_Config(self,event):
		a = MyDialog1(self)
		if a.ShowModal()==wx.ID_OK:
			value=a.get_config_value()
			print (value)
			#message=Change_global_config(value)
			global config_data
			global mysql_config
			try:
				a.m_choice22_string=a.m_choice22.GetString(a.m_choice22.GetSelection())
				if a.m_choice22_string=='GHz':
					config_data['start_freq']=float(value[0])*(1e3)
				elif a.m_choice22_string=='KHz':
					config_data['start_freq']=float(value[0])/(1e3)
				else:
					config_data['start_freq']=float(value[0])
			except (ValueError,TypeError) as e:
				wx.MessageBox(u' 初始频率输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
				return
			try:
				a.m_choice24_string=a.m_choice24.GetString(a.m_choice24.GetSelection())
				if a.m_choice24_string=='GHz':
					config_data['end_freq']=float(value[1])*(1e3)
				elif a.m_choice24_string=='KHz':
					config_data['end_freq']=float(value[1])/(1e3)
				else:
					config_data['end_freq']=float(value[1])
			except (ValueError,TypeError) as e:
				wx.MessageBox(u' 终止频率输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
				return
			try:
				a.m_choice23_string=a.m_choice23.GetString(a.m_choice23.GetSelection())
				if a.m_choice23_string=='GHz':
					config_data['RBW']=float(value[2])*(1e6)
				elif a.m_choice23_string=='MHz':
					config_data['RBW']=float(value[2])*(1e3)
				else:
					config_data['RBW']=float(value[2])
			except (ValueError,TypeError) as e:
				wx.MessageBox(u' RBW输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
				return
			try:
				a.m_choice25_string=a.m_choice25.GetString(a.m_choice25.GetSelection())
				if a.m_choice25_string=='GHz':
					config_data['VBW']=float(value[3])*(1e6)
				elif a.m_choice25_string=='MHz':
					config_data['VBW']=float(value[3])*(1e3)
				else:
					config_data['VBW']=float(value[3])
			except (ValueError,TypeError) as e:
				wx.MessageBox(u' VBW输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
				return
			# try:
				# config_data['step_freq']=float(value[4])
			# except (ValueError,TypeError) as e:
				# wx.MessageBox(u' 频率步进输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
				# return	
			try:
				config_data['trigger_level']=float(value[5])
			except (ValueError,TypeError) as e:
				wx.MessageBox(u' 触发电平输入须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
				return
			try:
				config_data['month_start_freq']=float(value[8])
			except (ValueError,TypeError) as e:
				wx.MessageBox(u' 输入频率须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
				return
			try:
				config_data['month_end_freq']=float(value[9])
			except (ValueError,TypeError) as e:
				wx.MessageBox(u' 输入频率须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
				return
				
			config_data['Spec_dir']=value[6]
			config_data['IQ_dir']=value[7]
			method.config_data = config_data
			
			##################存数据库参数
			mysql_value=a.get_mysql_value()
			mysql_config['host']=mysql_value[0]
			mysql_config['SID']=mysql_value[1]
			mysql_config['user1']=mysql_value[2]
			mysql_config['password1']=mysql_value[3]
			mysql_config['user2']=mysql_value[4]
			mysql_config['password2']= mysql_value[5]
			mysql_config['user3']=mysql_value[6]
			mysql_config['password3']= mysql_value[7]
			mysql_config['interface']= mysql_value[8]
			
			#存储配置参数
			jsObj = json.dumps(config_data)
			fileObject = open(os.getcwd()+'\\wxpython.json', 'w')
			fileObject.write(jsObj)  
			fileObject.close()
			#存储数据库参数
			jsObj1 = json.dumps(mysql_config)
			fileObject1 = open(os.getcwd()+'\\mysql.json', 'w')
			fileObject1.write(jsObj1)
			fileObject1.close()
			
			#添加频率段
			self.add_freqList(self, a)
			
	def add_freqList(self, dialog):
		start_freq_input = str(dialog.m_textCtrl48.GetValue())
		end_freq_input = str(dialog.m_textCtrl49.GetValue())
		try:
			start_freq=float(start_freq_input)
		except (ValueError,TypeError) as e:
			wx.MessageBox(u' 输入频率须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION) 
			return
		try:
			end_freq=float(end_freq_input)
		except (ValueError,TypeError) as e:
			wx.MessageBox(u' 输入频率须为数值', "Message" ,wx.OK | wx.ICON_INFORMATION)
			return
		is_has = 0   #判断插入的频率段是否已经存在
		for freq_list in method.month_freq_list:
			if freq_list==[start_freq,end_freq]:
				is_has = 1
				break;
		if is_has == 0:
			method.month_freq_list.append([start_freq,end_freq])
			method.month_freq_str.append(str(start_freq)+'-'+str(end_freq)+' MHz')
			method.write_month_freq_list([start_freq,end_freq])
			panelOne_two.choice1.SetItems(method.month_freq_str)
			panelOne_two.choice1.SetSelection(0)

	def station_data_update(self,event):
		try:
			method.station_info_update()
		except:
			wx.MessageBox(u'本地台站数据更新失败.', "Error" ,wx.OK | wx.ICON_ERROR)
	
	def Detection1(self,event):
		print ("6735 Loading Detection1.")
		self.panelOne_one.Hide()
		self.panelOne_two.Hide()
		self.panelTwo.Hide()
		self.panelThree.Hide()
		self.panelFour.Hide()
		self.panelFive.Hide()
		self.panelSix.Hide()
		self.Refresh()
		self.panelSeven.Refresh()
		self.panelSeven.Show()
		self.Layout()

	def Detection2(self,event):
		global mon_or_real
		mon_or_real = 1
		print ("Loading.Detection2..")
		self.panelOne_one.Hide()
		self.panelOne_two.Hide()
		self.panelTwo.Hide()
		self.panelThree.Hide()
		self.panelFour.Hide()
		self.panelFive.Hide()
		self.panelSix.Show()
		self.panelSeven.Hide()
		self.Layout()

		
	def get_help_txt(self,event):
		print ('get help txt')
		filepath = 'file:///' + os.getcwd() + '/help.html'
		filepath = filepath.replace('\\' , '/')
		print (filepath)
		web.open_new_tab(filepath)
	
	def openTek(self, event):
		try:
			file_path = config_data['SignalVu_dir']
			print (file_path)
			#os.system(file_path)
			subprocess.Popen(file_path)
		except:
			wx.MessageBox(u"SignalVu软件安装路径错误，请在wxpython.json文件中配置软件安装路径", "Message" ,wx.OK | wx.ICON_INFORMATION)

	def OnClose(self,event):
		#wx.Exit()
		# # 用完取消注册表设置
		# winreg.DeleteValue(self.key, 'python.exe')
		# # 关闭打开的注册表
		# winreg.CloseKey(self.key)
		
		#event.Skip()
		global GPS_end
		GPS_end=True
		try:
			method.instrument_disconnect(self.rsa)
		except Exception as e:
			self.Destroy()
		self.Destroy()
		#wx.GetApp().ExitMainLoop()

	def onTimer(self, evt):
		global connect_change
		self.panelThree.m_choice42Choices = method.file_to_list(list(reversed(os.listdir(method.config_data['Spec_dir']))))
		if self.panelThree.choice_Num!=len(self.panelThree.m_choice42Choices):
			self.panelThree.choice_Num=len(self.panelThree.m_choice42Choices)
			self.panelThree.m_combo1.SetItems(self.panelThree.m_choice42Choices)
			self.panelTwo.m_combo1.SetItems(self.panelThree.m_choice42Choices)
			self.panelOne_one.m_combo2.SetItems(self.panelThree.m_choice42Choices)
		if self.panelThree.start_time!=0:
			initial_value1=self.panelThree.m_slider9.GetValue()
			self.panelThree.initial_time1=self.panelThree.start_time+datetime.timedelta(seconds=self.panelThree.retain_time*initial_value1//100)
			self.panelThree.m_staticText123.SetLabel(str(self.panelThree.initial_time1))

			initial_value2=self.panelThree.m_slider11.GetValue()
			self.panelThree.initial_time2=self.panelThree.start_time+datetime.timedelta(seconds=self.panelThree.retain_time*initial_value2//100)
			self.panelThree.m_staticText124.SetLabel(str(self.panelThree.initial_time2))
			
			initial_value3=self.panelThree.m_slider10.GetValue()
			self.panelThree.initial_freq3=self.panelThree.start_freq+(self.panelThree.end_freq-self.panelThree.start_freq)*initial_value3/100
			self.panelThree.m_staticText125.SetLabel(str(self.panelThree.initial_freq3/1e6)+'MHz')
			
			initial_value4=self.panelThree.m_slider12.GetValue()
			self.panelThree.initial_freq4=self.panelThree.start_freq+(self.panelThree.end_freq-self.panelThree.start_freq)*initial_value4//100
			self.panelThree.m_staticText126.SetLabel(str(self.panelThree.initial_freq4/1e6)+'MHz')
		
		#监测仪器连接状态需要调整与否
		if connect_change == 1:
			connect_change = 0
			self.Ontimer_disconnect()

	
	def OnPaint(self, event):
		dc = wx.PaintDC(self)
		dc = wx.GCDC(dc)
		w, h = self.GetSize()
		r = 10
		dc.SetPen( wx.Pen("#806666",2 ) )
		dc.SetBrush( wx.Brush("#80A0B0"))
		dc.DrawRoundedRectangle( 0,0,w,h,r )
		self.Refresh()
		event.Skip()

class PaintApp(wx.App):  
    def OnInit(self):  
        bmp = wx.Image("SOAR.bmp").ConvertToBitmap()  
        adv.SplashScreen(bmp,  
                        adv.SPLASH_CENTER_ON_SCREEN | adv.SPLASH_TIMEOUT,  
                        1500,  
                        None,  
                        -1)  
        wx.Yield()
        win = MyFrame1(None)
        win.Show()
        self.SetTopWindow(win)
        if connect_state == 0:
            win.first_connect()
        return True

def main():
	
	app = PaintApp()
	# win = MyFrame1(None)
	# win.Show()
	app.MainLoop()

if __name__ == "__main__":
	main()


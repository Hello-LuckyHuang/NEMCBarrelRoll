# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()


class Main(ScreenNode):
	def __init__(self, namespace, name, param):
		ScreenNode.__init__(self, namespace, name, param)
		self.client_sys = param['client']#获取客户端
		self.SwitchButton = "/SwitchPanel/barrelSwitchButton"#为UI json文件中的路径关系
		self.SwitchLabel = "/SwitchPanel/barrelSwitchButton/switch_label"
		self.SettingButton = "/SettingPanel/barrelSettingButton"#为UI json文件中的路径关系

		self.player_comp = clientApi.GetEngineCompFactory().CreatePlayer(clientApi.GetLocalPlayerId())

	def Create(self):
		self.SwitchButtonItem = self.GetBaseUIControl(self.SwitchButton).asButton()
		self.SwitchLabelItem = self.GetBaseUIControl(self.SwitchLabel).asLabel()
		self.SwitchSettingItem = self.GetBaseUIControl(self.SettingButton).asButton()

		#设置UI事件
		self.SwitchButtonItem.AddTouchEventParams({"isSwallow": True})
		self.SwitchSettingItem.AddTouchEventParams({"isSwallow": True})

		self.SwitchButtonItem.SetButtonTouchUpCallback(self.switchbarrel)#按钮按下时触发
		self.SwitchSettingItem.SetButtonTouchUpCallback(self.openSettingPanel)#按钮按下时触发

		self.SetScreenVisible(False)
		if self.player_comp.isGliding():
			self.SetScreenVisible(True)
		"""
		@description UI创建成功时调用
		"""
		pass

	def Destroy(self):
		"""
		@description UI销毁时调用
		"""
		pass

	def OnActive(self):
		"""
		@description UI重新回到栈顶时调用
		"""
		pass

	def OnDeactive(self):
		"""
		@description 栈顶UI有其他UI入栈时调用
		"""
		pass

	def Update(self):
		if self.player_comp.isGliding():
			self.SetScreenVisible(True)
		else:
			self.SetScreenVisible(False)

	def switchbarrel(self, event):
		pop_comp = clientApi.GetEngineCompFactory().CreateGame(clientApi.GetLevelId())
		if self.client_sys.barrelflySwitch == True:
			self.client_sys.barrelflySwitch = False
			self.SwitchLabelItem.SetText("off")
			self.SwitchLabelItem.SetTextColor((150, 0, 0))
			pop_comp.SetTipMessage("翻滚飞行："+clientApi.GenerateColor("RED") + "关闭")
		else:
			self.client_sys.barrelflySwitch = True
			self.SwitchLabelItem.SetText("on")
			self.SwitchLabelItem.SetTextColor((0, 150, 0))
			pop_comp.SetTipMessage("翻滚飞行："+clientApi.GenerateColor("GREEN") + "开启")

	def openSettingPanel(self, event):
		self.client_sys.settingPanel = clientApi.CreateUI('BarrelUI', 'barrelsetting',{"isHud" : 0, "client" : self.client_sys})


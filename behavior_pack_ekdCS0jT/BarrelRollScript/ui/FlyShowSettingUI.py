# -*- coding: utf-8 -*-
import mod.client.extraClientApi as clientApi
ViewBinder = clientApi.GetViewBinderCls()
ViewRequest = clientApi.GetViewViewRequestCls()
ScreenNode = clientApi.GetScreenNodeCls()


class Main(ScreenNode):
	def __init__(self, namespace, name, param):
		ScreenNode.__init__(self, namespace, name, param)
		self.client_sys = param['client']#获取客户端

		self.closeButton = "/setting_title/close_button"#为UI json文件中的路径关系
		self.barrelSettingButton = "/setting_title/to_barrel_button"
		self.saveButton = "/setting_title/flyshow_setting_panel/save_button"
		self.cancelButton = "/setting_title/flyshow_setting_panel/cancel_button"

		self.angleToggle = "/setting_title/flyshow_setting_panel/angle_switch"
		self.HUDToggle = "/setting_title/flyshow_setting_panel/HUD_switch"
		self.durabilityToggle = "/setting_title/flyshow_setting_panel/elytra_switch"
		self.speedToggle = "/setting_title/flyshow_setting_panel/speed_switch"
		self.directionToggle = "/setting_title/flyshow_setting_panel/direction_switch"
		self.mapToggle = "/setting_title/flyshow_setting_panel/map_switch"
		self.HUDScreenToggle = "/setting_title/flyshow_setting_panel/use_HUD_switch"
		

	def Create(self):
		self.closeButtonItem = self.GetBaseUIControl(self.closeButton).asButton()
		self.saveButtonItem = self.GetBaseUIControl(self.saveButton).asButton()
		self.barrelSettingButtonItem = self.GetBaseUIControl(self.barrelSettingButton).asButton()
		self.cancelButtonItem = self.GetBaseUIControl(self.cancelButton).asButton()

		self.angleToggleItem = self.GetBaseUIControl(self.angleToggle).asSwitchToggle()
		self.HUDToggleItem = self.GetBaseUIControl(self.HUDToggle).asSwitchToggle()
		self.durabilityToggleItem = self.GetBaseUIControl(self.durabilityToggle).asSwitchToggle()
		self.speedToggleItem = self.GetBaseUIControl(self.speedToggle).asSwitchToggle()
		self.directionToggleItem = self.GetBaseUIControl(self.directionToggle).asSwitchToggle()
		self.mapToggleItem = self.GetBaseUIControl(self.mapToggle).asSwitchToggle()
		self.HUDScreenToggleItem = self.GetBaseUIControl(self.HUDScreenToggle).asSwitchToggle()

		self.closeButtonItem.AddTouchEventParams({"isSwallow": True})
		self.barrelSettingButtonItem.AddTouchEventParams({"isSwallow": True})
		self.cancelButtonItem.AddTouchEventParams({"isSwallow": True})
		self.saveButtonItem.AddTouchEventParams({"isSwallow": True})

		self.closeButtonItem.SetButtonTouchUpCallback(self.closeSettingPanel)#按钮按下时触发
		self.barrelSettingButtonItem.SetButtonTouchUpCallback(self.openFlySetting)#按钮按下时触发
		self.saveButtonItem.SetButtonTouchUpCallback(self.saveSetting)#按钮按下时触发
		self.cancelButtonItem.SetButtonTouchUpCallback(self.closeSettingPanel)#按钮按下时触发

		self.angleToggleItem.SetToggleState(self.client_sys.angleshow)
		self.HUDToggleItem.SetToggleState(self.client_sys.flyHUDshow)
		self.durabilityToggleItem.SetToggleState(self.client_sys.elytradurabilityshow)
		self.speedToggleItem.SetToggleState(self.client_sys.flyspeedshow)
		self.directionToggleItem.SetToggleState(self.client_sys.directionshow)
		self.mapToggleItem.SetToggleState(self.client_sys.mapshow)
		self.HUDScreenToggleItem.SetToggleState(self.client_sys.HUDScreen)

	def closeSettingPanel(self, event):
		self.client_sys.flySettingPanel.SetRemove()
	
	def openFlySetting(self, event):
		self.client_sys.settingPanel = clientApi.CreateUI('BarrelUI', 'barrelsetting',{"isHud" : 0, "client" : self.client_sys})
		self.client_sys.flySettingPanel.SetRemove()

	def saveSetting(self, event):
		self.client_sys.angleshow = self.angleToggleItem.GetToggleState()
		self.client_sys.flyHUDshow = self.HUDToggleItem.GetToggleState()
		self.client_sys.elytradurabilityshow = self.durabilityToggleItem.GetToggleState()
		self.client_sys.flyspeedshow = self.speedToggleItem.GetToggleState()
		self.client_sys.directionshow = self.directionToggleItem.GetToggleState()
		self.client_sys.mapshow = self.mapToggleItem.GetToggleState()
		self.client_sys.HUDScreen = self.HUDScreenToggleItem.GetToggleState()
		self.client_sys.saveflyHUDConfig()
		self.client_sys.flyHUDPanel.fleshHUDShow()
		self.client_sys.flySettingPanel.SetRemove()

	def Destroy(self):
		pass

	def OnActive(self):
		pass

	def OnDeactive(self):
		pass
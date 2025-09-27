#!/usr/bin/python
#
## @file
#
# Focus lock control specialized for STORM4.
#
# Hazen 03/12
#
from PIL import Image
import sc_library.parameters as params
from simple_pid import PID

# camera and stage.
from sc_hardware.ASI.ASI_ZController import ASIZStage
from sc_hardware.Daheng.DahengCamera import CameraQPD

# focus lock control thread.
import IX73.focusLock.stageOffsetControl_bx as stageOffsetControl

# ir laser control
#import sc_hardware.thorlabs.LDC210 as LDC210

# focus lock dialog.
import IX73.focusLock.focusLockZ as focusLockZ

#
# Focus Lock Dialog Box specialized for STORM4 with 
# USB offset detector and MCL objective Z positioner.
#
class AFocusLockZ(focusLockZ.FocusLockZCam):
    def __init__(self, hardware, parameters, parent = None):

        # —— 相机（大恒图像水星系列）——
        cam = CameraQPD(camera_id = 1, x_width = 176, y_width = 176,
                        offset_file = "cam_offsets_IX73.txt", background = 0)
                                #
        # offset_file  provides the top-left coordinates of the ROI (int)
        # x_width,y_width   ROI size (int)

#        image = cam.cam.captureImage()
#        im = Image.fromarray(image)
#        im.save("haha.png")

        # —— 位移台（ASI MS-2000）——
        stage = ASIZStage(port="COM3", baud=9600)
        stage.zMoveTo(0)
        stage.zPosition()

        # 定义 PID 控制器
        pid = PID(Kp=0.0080,Ki=0.0008, Kd=0.0008, setpoint=0)
        pid.output_limits = (-0.01, 0.01)                                # 设置输出范围，防止控制器输出过大

        # buffer_length 存储最近几次的锁焦判断，对locked状态要求更严格
        # offset_thresh 锁焦判断的阈值
        control_thread = stageOffsetControl.StageCamThread(cam,
                                                           stage,
                                                           pid,
                                                           parameters.get("focuslock.qpd_sum_min", 25),
                                                           parameters.get("focuslock.qpd_zcenter"),
                                                           parameters.get("focuslock.is_locked_buffer_length", 1),
                                                           parameters.get("focuslock.is_locked_offset_thresh", 0.1))

        ir_laser = 0
        focusLockZ.FocusLockZCam.__init__(self,parameters, control_thread, ir_laser, parent)

#
# The MIT License
#
# Copyright (c) 2012 Zhuang Lab, Harvard University
#
# Permission is hereby granted, free of charge, to any person obtaining a copy
# of this software and associated documentation files (the "Software"), to deal
# in the Software without restriction, including without limitation the rights
# to use, copy, modify, merge, publish, distribute, sublicense, and/or sell
# copies of the Software, and to permit persons to whom the Software is
# furnished to do so, subject to the following conditions:
#
# The above copyright notice and this permission notice shall be included in
# all copies or substantial portions of the Software.
#
# THE SOFTWARE IS PROVIDED "AS IS", WITHOUT WARRANTY OF ANY KIND, EXPRESS OR
# IMPLIED, INCLUDING BUT NOT LIMITED TO THE WARRANTIES OF MERCHANTABILITY,
# FITNESS FOR A PARTICULAR PURPOSE AND NONINFRINGEMENT. IN NO EVENT SHALL THE
# AUTHORS OR COPYRIGHT HOLDERS BE LIABLE FOR ANY CLAIM, DAMAGES OR OTHER
# LIABILITY, WHETHER IN AN ACTION OF CONTRACT, TORT OR OTHERWISE, ARISING FROM,
# OUT OF OR IN CONNECTION WITH THE SOFTWARE OR THE USE OR OTHER DEALINGS IN
# THE SOFTWARE.
#

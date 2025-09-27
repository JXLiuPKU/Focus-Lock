#%%
# Run focus lock control only.
# 此为主程序
                                                                       
import sys
import os
import halLib.standalone as standalone

# print("current working directory: ",os.getcwd())
script_path = os.path.abspath(__file__)
# 获取脚本所在的目录
script_dir = os.path.dirname(script_path)
# print("script_path: ",script_path)
# print("script_dir: ",script_dir)
os.chdir(script_dir)

#%%
if (len(sys.argv)==2):
    standalone.runModule("focuslock", sys.argv[1])
else:
    standalone.runModule("focuslock")
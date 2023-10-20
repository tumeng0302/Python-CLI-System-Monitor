# Python CLI System Monitor
## A simple system monitor tool for ubuntu 

This tool is for user who want to check both CPU and GPU information.  
This is an early release version, and only test on { ubuntu 22.04; python3.10; single CPU; single GPU} .  

## Install
This tool is depends on the lm-sensors library, please install with:  
```bash
# sudo apt install lm-sensors
```
In addition, this tool also depends on python psutil package, please install with:
```
pip3 install psutil
```

## Usage
```
python3 Get_Hardware_Info.py -I <interval (s)> (-ST if you want to show per core temperature)
```


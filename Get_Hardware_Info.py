import subprocess
import re
import psutil
import time
import argparse
import _thread
class Hardware_Info():
    def __init__(self):
        cpu_info = subprocess.Popen("lscpu", stdout=subprocess.PIPE).stdout.read().decode('utf-8')
        role = re.compile(r'Model name:(.*)\n')
        self.cpu_name = role.search(cpu_info).group().split(':')[1].strip()
        self.gpu_command = "nvidia-smi --query-gpu={args} --format=csv"
        try:
            subprocess.Popen('nvidia-smi', stdout=subprocess.PIPE)
            self.gpu_available = True
            self.get_gpu_name()
        except:
            self.gpu_available = False
            self.gpu_name = 'None'

    def get_gpu_name(self):
        command = self.gpu_command.format(args='name')
        gpu_info = subprocess.Popen(command.split(), stdout=subprocess.PIPE).stdout.read()
        self.gpu_name = gpu_info.decode('utf-8').split('\n')[1]

    def get_gpu_info(self):
        command = self.gpu_command.format(args='temperature.gpu,utilization.gpu,memory.used,memory.total')
        gpu_info = subprocess.Popen(command.split(), stdout=subprocess.PIPE).stdout.read()
        gpu_info = gpu_info.decode('utf-8').split('\n')[1].split(',')
        gpu_info = [float(i.split()[0]) for i in gpu_info]
        self.gpu_temp = gpu_info[0]
        self.gpu_util = gpu_info[1]
        self.gpu_mem_used = gpu_info[2]
        self.gpu_mem_total = gpu_info[3]
    
    def get_cpu_info(self):
        self.pkg_cpu_percent = psutil.cpu_percent()
        self.all_cpu_percent = psutil.cpu_percent(percpu=True)
        self.total_memory = psutil.virtual_memory().total/1024**3
        self.used_memory = psutil.virtual_memory().used/1024**3

    def get_cpu_temp(self):
        cpu_temp = subprocess.Popen("sensors", stdout=subprocess.PIPE).stdout.read().decode('utf-8')
        pkg_role = re.compile(r'Package id 0: *[\+\-](.*)°C ')
        core_role = re.compile(r'Core \d+: *[\+\-](.*)°C ')
        core_temp = core_role.findall(cpu_temp)
        self.core_temp = [float(temp) for temp in core_temp]
        self.pkg_temp = pkg_role.findall(cpu_temp)[0]

    def get_all_info(self):
        if self.gpu_available:
            self.get_gpu_info()
        self.get_cpu_info()
        self.get_cpu_temp()

class Monitor(Hardware_Info):
    def __init__(self, interval: float=1, show_cpu_temp: bool=False):
        super(Monitor, self).__init__()
        self.interval = interval
        self.show_cpu_temp = show_cpu_temp
        

    def get_info_bar(self, percent: float, length: int=10):
        bar = "▇"
        per_bar = 100/length
        num = int(float(percent)/per_bar)
        return colored(bar*num, 'green', bright=False) + colored(bar*(length-num), 'red', bright=False)
    
    def monitor_core(self):
        self.get_all_info()
        total_len = 110
        line_len = (total_len-18)//2
        main_line = colored(f"+{'-'*line_len}+ SYSTEM  INFO +{'-'*line_len}+\n", bg_color='cyan')
        main_line += f"|| {colored('CPU', 'purple')}: {self.cpu_name:^46}|| {colored('GPU', 'purple')}: {self.gpu_name:^46}||\n"
        # adaptively adjust the length of the line
        line_len = (total_len-14)//2
        main_line += colored(f"\n+{'-'*line_len}+ CPU INFO +{'-'*line_len}+\n", bg_color='cyan')
        cpu_bar = self.get_info_bar(self.pkg_cpu_percent, length=20)
        cpu_temp_bar = self.get_info_bar(self.pkg_temp, length=20)
        main_line += f"{colored('CPU Package Usage', 'green')}: |{cpu_bar} {str(self.pkg_cpu_percent):5}%|" + \
                   f"  {colored('CPU Package Temp', 'green')}: |{cpu_temp_bar} {str(self.pkg_temp):5}°C|\n"
        memory_bar = self.get_info_bar((self.used_memory/self.total_memory)*100, length=69)

        main_line += f"{colored('Main Memory Usage', 'green')}: |{memory_bar}" + colored(f' {self.used_memory:3.1f}GB/ {self.total_memory:3.1f}GB', 'yellow', bright=False) + '|\n'
        line_len = (total_len-23)//2
        main_line += colored(f"\n+-{'-'*line_len}+ CPU Per Core INFO +{'-'*line_len}+\n", bg_color='cyan')
        core_list = []
        for i, core in enumerate(self.all_cpu_percent):
            core_bar = self.get_info_bar(core, length=10)
            core_list.append(colored(f"C_{i:02d}", 'green') + f"|{core_bar} {str(core):5}%|  ")
        # show 4 cores usage per line and constant width
        core_info = ''
        for i in range(len(core_list)):
            core_info += core_list[i]
            if i % 4 == 3:
                core_info += '\n'
        main_line += core_info
        if self.show_cpu_temp:
            line_len = (total_len-23)//2
            core_list = []
            main_line += "\n" + colored(f"+-{'-'*line_len}+ CPU Per Core Temp +{'-'*line_len}+", bg_color='cyan') + "\n"
            for i, core in enumerate(self.core_temp):
                core_bar = self.get_info_bar(core, length=10)
                core_list.append(colored(f" Die_{i:02d}", "green") + f"|{core_bar} {str(core):5}°C|")
            # show 4 cores usage per line and constant width
            core_temp_info = ''
            for i in range(len(core_list)):
                core_temp_info += f"{core_list[i]}"
                if i % 4 == 3:
                    core_temp_info += '\n'
            main_line += core_temp_info
        line_len = (total_len-14)//2
        main_line += "\n" + colored(f"+{'-'*line_len}+ GPU INFO +{'-'*line_len}+", bg_color='cyan') + "\n"
        if not self.gpu_available:
            main_line += "No GPU Available"
        else:
            gpu_temp = self.gpu_temp
            gpu_util = self.gpu_util
            gpu_mem_used = self.gpu_mem_used
            gpu_mem_total = self.gpu_mem_total
            gpu_mem_percent = gpu_mem_used/gpu_mem_total*100
            gpu_mem_bar = self.get_info_bar(gpu_mem_percent, length=67)
            gpu_util_bar = self.get_info_bar(gpu_util, length=34)
            gpu_temp_bar = self.get_info_bar(gpu_temp, length=34)
            main_line += colored("GPU Usage", 'green') + f": |{gpu_util_bar} {str(gpu_util):5}|" + \
                       colored("   GPU Temp", 'green') + f": |{gpu_temp_bar} {str(gpu_temp):5}°C|\n" + \
                       colored("GPU Memory Usage", 'green') + f": |{gpu_mem_bar} " + \
                       colored(f"{gpu_mem_used:3.1f}MiB/ {gpu_mem_total:3.1f}MiB", 'yellow', bright=False) + "|\n"
        self.print_line = main_line
    
    def monitor_start(self):
        while True:
            self.monitor_core()
            time.sleep(self.interval)

    def monitor_log(self):
        while True:
            subprocess.call('clear')
            print(self.print_line)
            time.sleep(self.interval)
        

def colored(text: str, txt_color: str="white", bg_color: str='default', bright: bool=True):
    txt_dict = {
        'black':30, 'red':31, 'green':32, 'yellow':33,
        'blue':34, 'purple':35, 'cyan':36, 'white':37,
    }
    bg_dict = {
        'black':40, 'red':41, 'green':42, 'yellow':43,
        'blue':44, 'purple':45, 'cyan':46, 'white':47,
        'default':0,
    }
    if bright:
        return f"\033[{bg_dict[bg_color]};{txt_dict[txt_color]}m\033[1m{text}\033[0m"
    return f"\033[{bg_dict[bg_color]};{txt_dict[txt_color]}m{text}\033[0m"

if __name__ == "__main__":
    parser = argparse.ArgumentParser()
    parser.add_argument('-ST','--show_cpu_temp', action='store_true', help='show per die cpu temperature')
    parser.add_argument('-I', '--interval', type=float, default=1, help='interval of monitor')
    args = parser.parse_args()
    monitor = Monitor(interval=args.interval, show_cpu_temp=args.show_cpu_temp)
    _thread.start_new_thread(monitor.monitor_start, ())
    time.sleep(0.5)
    monitor.monitor_log()

import subprocess
import os
import time

current_path = os.path.dirname(os.path.abspath(__name__))

def exec_trojan() -> subprocess.Popen:
	'''执行trojan子进程
	Returns:
		subprocess.Popen: 返回Popen类对象
	'''
	trojan_command = f'{current_path}{os.path.sep}trojan.exe'
	trojan_config = f'{current_path}{os.path.sep}client.json'
	# trojan_log = f'{current_path}{os.path.sep}trojan.log'
	print(trojan_command, trojan_config)
	# creationflags=subprocess.CREATE_NO_WINDOW 参数防止在执行时显示黑窗口
	trojan_p = subprocess.Popen(args=[trojan_command,'-c', trojan_config], creationflags=subprocess.CREATE_NO_WINDOW, stdout=subprocess.PIPE, stderr=subprocess.STDOUT, text=True)
	return trojan_p

	
def kill_trojan(p: subprocess.Popen):
	"""终止trojan进程
	"""
	p.kill()

def read_log(p: subprocess.Popen):
	"""读取trojan日志
	Args:
		p(subprocess.Popen): Popen类对象
	Returns:
		str: trojan日志
	"""
	while True:
		if p.poll() is not None:
			return f'Trojan进程已被终止({p.poll()}).'
		return p.stdout.readline().strip()
			

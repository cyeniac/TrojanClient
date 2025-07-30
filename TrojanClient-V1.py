import tkinter as tk
from tkinter import ttk, filedialog
from threading import Thread
from PIL import Image
import os
import subprocess
import json
import utils
import pystray


current_path = os.path.dirname(os.path.abspath(__name__))

class TrojanClient:
	def __init__(self):
		# 初始化界面
		self.setup_ui()

		# 加载配置文件
		self.load_config()


	def setup_ui(self):
		# 根窗口
		self.root = tk.Tk()
		self.root.iconbitmap('favicon16x16.ico')
		self.root.title('Trojan客户端')
		screen_width = self.root.winfo_screenwidth()
		screen_height = self.root.winfo_screenheight()
		app_width = 800
		app_height = 600
		self.root.geometry(f'{app_width}x{app_height}+{int(screen_width/2-app_width/2)}+{int(screen_height/2-app_width/2)}')
		self.root.resizable(width=False, height=False)
		self.root.protocol("WM_DELETE_WINDOW", self.on_closing)
		self.root.bind('<Unmap>', self.hide_windows)  # 窗口最小化事件

		# 可修改的配置信息
		self.config = {
			'local_addr': tk.StringVar(value='127.0.0.1'),
			'local_port': tk.IntVar(value=18080),
			'remote_addr': tk.StringVar(value='vpn.example.com'),
			'remote_port': tk.IntVar(value=443),
			'password': tk.StringVar(value='password'),
			'ssl_verify': tk.BooleanVar(value=True),
			'ssl_cert_path': tk.StringVar(value='test.crt')
		}

		# 地址信息
		config_info_frame = ttk.LabelFrame(self.root, text='配置信息')
		config_info_frame.pack(fill=tk.X, padx='5px')

		ttk.Label(master=config_info_frame, text='本地代理地址').grid(row=0, column=0, padx='5px', pady='2px')
		ttk.Entry(master=config_info_frame, textvariable=self.config['local_addr']).grid(row=0, column=1, padx='5px', pady='2px')

		ttk.Label(master=config_info_frame, text='本地代理端口').grid(row=1, column=0, padx='5px', pady='2px')
		ttk.Entry(master=config_info_frame, textvariable=self.config['local_port']).grid(row=1, column=1, padx='5px', pady='2px')

		ttk.Label(master=config_info_frame, text='远程服务器地址').grid(row=2, column=0, padx='5px', pady='2px')
		ttk.Entry(master=config_info_frame, textvariable=self.config['remote_addr']).grid(row=2, column=1, padx='5px', pady='2px')
		
		ttk.Label(master=config_info_frame, text='远程服务器端口').grid(row=3, column=0, padx='5px', pady='2px')
		ttk.Entry(master=config_info_frame, textvariable=self.config['remote_port']).grid(row=3, column=1, padx='5px', pady='2px')

		ttk.Label(master=config_info_frame, text='密码').grid(row=4, column=0, padx='5px', pady='2px')
		ttk.Entry(master=config_info_frame, textvariable=self.config['password'], show='*').grid(row=4, column=1, padx='5px', pady='2px')

		ttk.Label(master=config_info_frame, text='日志级别').grid(row=0, column=2,padx='5px', pady='2px')
		self.log_level = ttk.Combobox(master=config_info_frame, values=['调试','信息','告警','错误','致命','关闭'])
		self.log_level.grid(row=0, column=3,padx='5px', pady='2px')
		
		ttk.Label(master=config_info_frame, text='是否启用SSL').grid(row=1, column=2,padx='5px', pady='2px')
		# variable使用同一个对象，代表一个互斥组，选择一个，其他的就会失效
		ttk.Radiobutton(master=config_info_frame, variable=self.config['ssl_verify'], value=True, text='是').grid(row=1, column=3,padx='5px', pady='2px') 
		ttk.Radiobutton(master=config_info_frame, variable=self.config['ssl_verify'], value=False, text='否').grid(row=1, column=4,padx='5px', pady='2px')

		ttk.Label(master=config_info_frame, text='SSL证书').grid(row=2, column=2,padx='5px', pady='2px')
		ttk.Entry(master=config_info_frame, textvariable=self.config['ssl_cert_path']).grid(row=2, column=3,padx='5px', pady='2px')
		self.select_cert_button = ttk.Button(master=config_info_frame, text='选择证书', command=self.select_cert)
		self.select_cert_button.grid(row=2, column=4,padx='5px', pady='2px')
		ttk.Label(master=config_info_frame, text='不启用SSL，不选择证书', foreground='Red').grid(row=2, column=5,padx='5px', pady='2px')
		
		
		# 按钮区域
		buttons_frame = ttk.Frame(master=self.root)
		buttons_frame.pack(fill=tk.X, padx='5px')

		self.start_button = ttk.Button(master=buttons_frame, text='启动', command=self.start)
		self.start_button.pack(side=tk.LEFT, padx='10px', pady='5px')
		self.stop_button = ttk.Button(master=buttons_frame, text='停止', command=self.stop, state=tk.DISABLED)
		self.stop_button.pack(side=tk.LEFT, padx='10px', pady='5px')

		# 日志区域
		log_frame = ttk.LabelFrame(master=self.root, text='日志')
		log_frame.pack(fill=tk.BOTH,padx='5px', expand=True)

		self.log_listbox = tk.Listbox(master=log_frame)
		log_scrollbar_x = ttk.Scrollbar(master=log_frame, orient='horizontal', command=self.log_listbox.xview)
		log_scrollbar_x.pack(side=tk.BOTTOM, fill=tk.X)
		self.log_listbox.pack(side=tk.LEFT, padx='10px', pady='5px', fill=tk.BOTH, expand=True)
		log_scrollbar_y = ttk.Scrollbar(master=log_frame, orient='vertical', command=self.log_listbox.yview)
		log_scrollbar_y.pack(side=tk.RIGHT, fill=tk.Y)
		self.log_listbox.config(xscrollcommand=log_scrollbar_x.set)
		self.log_listbox.config(yscrollcommand=log_scrollbar_y.set)

		# 状态栏
		status_frame = ttk.Frame(master=self.root)
		status_frame.pack(fill=tk.X, padx='5px')
		self.state = ttk.Label(master=status_frame, text='未运行')
		self.state.pack(side=tk.LEFT,padx='5px', pady='5px')
		ttk.Label(master=status_frame, text='作者: YOUNG').pack(side='right')


		# 系统托盘
		strap_menu = (
			pystray.MenuItem(text='显示', action=self.show_window, default=True),
			pystray.Menu.SEPARATOR, # 分割线
			pystray.MenuItem(text='退出', action=self.on_closing)
		)
		image = Image.open('favicon16x16.ico')
		self.ico = pystray.Icon("TrojanClient", image, 'Trojan客户端', strap_menu)
		Thread(target=self.ico.run, daemon=True).start()


	def load_config(self):
		config_file = f'{current_path}{os.path.sep}client.json'
		try:
			with open(config_file,'r', encoding='utf-8') as f:
				res = json.load(f)
				self.config['local_addr'].set(res['local_addr'])
				self.config['local_port'].set(res['local_port'])
				self.config['remote_addr'].set(res['remote_addr'])
				self.config['remote_port'].set(res['remote_port'])
				self.config['password'].set(res['password'][0])
				if res['log_level'] == 0:
					self.log_level.set('调试')
				elif res['log_level'] == 1:
					self.log_level.set('信息')
				elif res['log_level'] == 2:
					self.log_level.set('告警')
				elif res['log_level'] == 3:
					self.log_level.set('错误')
				elif res['log_level'] == 4:
					self.log_level.set('致命')
				else:
					self.log_level.set('关闭')
				self.config['ssl_verify'].set(res['ssl']['verify'])
				self.config['ssl_cert_path'].set(res['ssl']['cert'])
					
		except Exception as e:
			self.log_listbox.insert(tk.END, e.args[0])
			self.log_listbox.yview(tk.END)

	def write_log(self, p:subprocess.Popen):
		while True:
			if p.poll() is not None:
				self.log_listbox.insert(tk.END, f'进程被终止{p.poll()}')
				self.log_listbox.yview(tk.END)
				break
			self.log_listbox.insert(tk.END, p.stdout.readline().strip())
			self.log_listbox.yview(tk.END)

	def start(self):
		config_file = f'{current_path}{os.path.sep}client.json'
		with open(config_file, 'r') as f:
			res = json.load(f)
		res['local_addr'] = self.config['local_addr'].get()
		res['local_port'] = self.config['local_port'].get()
		res['remote_addr'] = self.config['remote_addr'].get()
		res['remote_port'] = self.config['remote_port'].get()
		res['password'][0] = self.config['password'].get()
		if self.log_level.get() == '调试':
			res['log_level'] = 0
		elif self.log_level.get() == '信息':
			res['log_level'] = 1
		elif self.log_level.get() == '告警':
			res['log_level'] = 2
		elif self.log_level.get() == '错误':
			res['log_level'] = 3
		elif self.log_level.get() == '致命':
			res['log_level'] = 4
		else:
			res['log_level'] = 5
		res['ssl']['verify'] = self.config['ssl_verify'].get()
		res['ssl']['cert'] = self.config['ssl_cert_path'].get()

		with open(config_file, 'w') as f:
			json.dump(res, f, indent=4)
		self.p = utils.exec_trojan()
		t = Thread(target=self.write_log, args=(self.p,))
		t.start()
		self.start_button.config(state=tk.DISABLED)
		self.stop_button.config(state=tk.NORMAL)
		self.state.config(text='已运行')
	
	def on_closing(self):
		self.stop()
		self.root.quit()
		
	def stop(self):
		try:
			utils.kill_trojan(self.p)
		except Exception as e:
			pass
		self.log_listbox.insert(tk.END, '已停止...')
		self.log_listbox.yview(tk.END)
		self.start_button.config(state=tk.NORMAL)
		self.stop_button.config(state=tk.DISABLED)
		self.state.config(text='未运行')
	
	def show_window(self):
		self.root.deiconify()
	
	def hide_windows(self, other):
		self.root.withdraw()
		print(other)
	
	def select_cert(self):
		path = filedialog.askopenfilename()
		self.config['ssl_cert_path'].set(path)

	
	def run(self):
		self.root.mainloop()

if __name__ == '__main__':
	app = TrojanClient()
	app.run()
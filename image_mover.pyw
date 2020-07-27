import tkinter as tk
from tkinter import filedialog 
import tkinter.ttk as ttk
import time
import os
from PIL import Image
from shutil import copyfile
import subprocess
from threading import Thread
from datetime import datetime
import hashlib


"""
	NOTES:
		- Getting MD5's of all files is super slow
			TODO:
				- build a caching mechanism (external JSON: path: MD5)
				- only check checksum against files in same date folder
			DONE:
				- generate checksum for only first 1MB
					- improved speed: from 18s to 0.1s
					- not as reliable (?)

		- implement settings (save destination path)

"""
class ImageMover:
	def __init__(self, master):
		self.master = master
		master.title("ImageMover")
		master.minsize(200, 200)

		# Program parameters
		self.accepted_extensions = (".jpg", ".jpeg", ".png", ".raw", ".gif", ".bmp", ".cr2")

		# GUI elements
		self.file_btn = tk.Button(master, text="Select folders", command=self.start)
		self.file_btn.grid(columnspan=2, rowspan=2,
						   padx=15, pady=15,
						   ipadx=5, ipady=5)

		self.label = tk.Label(master, text="")	# Label that displays images to move
		self.label.grid(columnspan=2, rowspan=3,
						padx=5, pady=5)


	def start(self):
		self.select_folders()
		self.init_cache()
		self.generate_differences()


	def select_folders(self):
		self.origin = filedialog.askdirectory()
		self.to = filedialog.askdirectory()


	def init_cache(self):
		# Create the JSON file if it doesn't exist
		# TODO
		pass


	def generate_differences(self):
		t = time.time()
		print("start")
		origin = self.get_images(self.origin)
		to 	   = self.get_images(self.to)
		print("end of get images  ", time.time()-t)
		print("start of md5 list")
		to_md5 = self.get_md5_list(to)

		print("end of md5 list  ", time.time()-t)
		print("start of md5 checking")

		# Find images that are in 'origin' but aren't in 'to' folder
		self.images_to_move = []
		if len(origin) > 0:
			for image in origin:
				if self.get_md5(image) not in to_md5:
					self.images_to_move.append(image)

		print("end of md5 checking  ", time.time()-t)

		# Display all images that need to be moved in label
		if len(self.images_to_move) > 0:
			self.label["text"] = "Images to move:  \n"
			c = 0
			n_count = 0
			max_n = 12
			for i in self.images_to_move:
				self.label["text"] += i[i.rfind("/")+1:] + ",  "
				c += 1
				n_count += 1
				if n_count >= max_n-1:
					self.label["text"] += f"\n +{len(self.images_to_move)-n_count} more"
					break
				if c == 3:
					c = 0
					self.label["text"] += "\n"

			# Show start button
			self.start_btn = tk.Button(self.master, text="Move images", command=self.move_images)
			self.start_btn.grid(columnspan=2, rowspan=2,
							   padx=15, pady=15,
							   ipadx=5, ipady=5)
		else:
			self.label["text"] = "No new images found"


	def get_images(self, path:str, recursive=True) -> list:
		images = []
		for current_path, subfolders, files in os.walk(path):
			for file in files:
				if file.lower().endswith(self.accepted_extensions):
					images.append(os.path.join(current_path, file))

			if recursive:
				for subfolder in subfolders:
					additions = self.get_images(subfolder)
					if len(additions) > 0:
						images.append(additions)

		# Filters out None and replaces '\\' with '/' in all paths
		return [x.replace("\\", "/") for x in images if x is not None]


	def get_date(self, path:str) -> str:
		"""
			Parameter:
				path: type str, path to image file
			Returns:
				str:  date in "YYYY_MM_DD" format
		"""
		try:
			# CR2 files do not have "date taken" EXIF data for some reason
			if path.lower().endswith(".cr2"):	
				date = datetime.fromtimestamp(os.path.getctime(path)).strftime("%Y_%m_%d")
			else:
				with Image.open(path) as opened:
					date = opened.getexif().get(36867)
				date = date[:date.find(" ")].replace(":", "_")
		except:
			date = None

		return "None" if date == None else date


	def get_md5_list(self, arr:list) -> list:
		try:
			return [self.get_md5(x) for x in arr]
		except:
			return []	


	def get_md5(self, path:str) -> str:
		"""
			Description:
				Generates a MD5 checksum for the first 1MB of the file
			Parameter:
				path: type str, path to file
			Returns:
				str:  MD5 checksum of the file
		"""
		chunk_size = 2**20	# 1MB
		try:
			with open(path, "rb") as file:
				data = file.read(chunk_size)
				return hashlib.md5(data).hexdigest()
		except:
			return None


	def move_images(self):
		if self.images_to_move != None and len(self.images_to_move) > 0:
			# Sort by dates
			date_sorted = {}
			for img in self.images_to_move:
				date = self.get_date(img)
				if date not in date_sorted:
					date_sorted[date] = []
				date_sorted[date].append(img)

			for date, images in date_sorted.items():
				# Create missing date folder
				path = os.path.join(self.to, date)
				os.makedirs(path, exist_ok=True)

				# Copy images
				for img in images:
					dest = os.path.join(path, os.path.basename(img))
					copyfile(img, dest)

			# Copying completed
			EXPLORER_PATH = os.path.join(os.getenv("WINDIR"), "explorer.exe")
			path = os.path.normpath(self.to)
			if os.path.isdir(path):
				subprocess.run([EXPLORER_PATH, path])
			self.master.quit()
		



if __name__ == "__main__":
	root = tk.Tk()
	imagemover = ImageMover(root)
	root.mainloop()
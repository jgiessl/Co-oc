import tkinter as tk
from tkinter import filedialog
import os
import json
from tkinter import ttk
import threading
from main_program import calculate
import queue
import ctypes


class GUI(tk.Tk):

    def __init__(self):

        super().__init__()

        self.title('Co-Oc')

        # setting exit condition
        self.protocol("WM_DELETE_WINDOW", self.on_exit)
        self.loop_flag = True

        # getting default options from file
        self.opt = self.get_options(os.path.dirname(os.path.abspath(__file__)), "parameters.json")
        self.opt_tk = {}
        # laying out the grid
        for r in range(18):
            self.rowconfigure(r, weight=1)
        for c in range(10):
            self.grid_columnconfigure(c, weight=1)

        # creating containers
        self.queue = queue.Queue()
        self.output = OutputFrame(self)
        self.options = OptionsFrame(self, self.opt, self.opt_tk, text="options", padx=5, pady=5)
        self.control = ControlFrame(self, self.opt, self.opt_tk, self.options, self.queue, padx=5, pady=5)

        # positioning of the containers
        self.output.grid(row=14, column=1, rowspan=4, columnspan=8, sticky="nsew")
        self.options.grid(row=0, column=1, rowspan=13, columnspan=8, sticky="nsew")
        self.control.grid(row=13, column=3, rowspan=1, columnspan=5, sticky="nsew")

        self.after_id = self.after(100, self.process_queue)

    @staticmethod
    def get_options(path, filename):
        """
        Gets the run parameters from file
        :param path: path to the directory of the parameters file
        :param filename: name of the parameters file, i.e 'parameters.json'
        """
        with open(os.path.join(path, filename), 'r', encoding='utf8',
                  errors='ignore') as f:
            data = json.load(f)
        return data

    def process_queue(self):
        """
        Processing the thread queue
        """
        try:
            msg = self.queue.get(0)
            if msg == 'X':
                self.output.listbox.insert(tk.END, 'finished')
                self.control.enable_options()
            else:
                if self.opt['log']:
                    self.output.listbox.insert(tk.END, msg)
        except queue.Empty:
            self.after_cancel(self.after_id)
            self.after_id = self.after(100, self.process_queue)

    def changed_update(self):
        """
        Function for incorporating the thread queue into the main loop
        """
        self.process_queue()
        self.update_idletasks()
        self.update()

    def on_exit(self):
        """
        Function to exit the program
        """
        if self.control.program_thread is None:
            self.after_cancel(self.after_id)
            self.loop_flag = False
            self.destroy()
        elif self.control.program_thread.is_alive():
            self.control.cancel()
        else:
            self.after_cancel(self.after_id)
            self.loop_flag = False
            self.destroy()


class OptionsFrame(tk.LabelFrame):

    def __init__(self, parent, opt, opt_tk, **kwargs):

        super().__init__(parent, **kwargs)

        # laying out the grid
        for r in range(15):
            self.rowconfigure(r, weight=1)
        for c in range(9):
            self.grid_columnconfigure(c, weight=1)

        self.options = opt
        self.get_default_paths()
        self.options_tk = opt_tk
        self.set_up_tk_opt(self.options)

        # creating options

        self.path_to_data_objects_lab = tk.Label(self, text="Path/to/data-objects-folder:", anchor='w')
        self.path_to_data_objects = tk.Entry(self, text=self.options_tk['path_to_objects'])
        self.path_to_data_objects_browse = tk.Button(self, text="Browse", command=lambda: self.browse_button_do())

        self.path_to_environments_lab = tk.Label(self, text="Path/to/environments-folder:", anchor='w')
        self.path_to_environments = tk.Entry(self, text=self.options_tk['path_to_environments'])
        self.path_to_environments_browse = tk.Button(self, text="Browse", command=lambda: self.browse_button_env())

        self.global_lab = tk.Label(self, text="Weight of global co-occurrences:", anchor='w')
        self.global_w = tk.Entry(self, text=self.options_tk['global'])

        self.global_dir_lab = tk.Label(self, text="Weight of global co-occurrences in directories:", anchor='w')
        self.global_w_dir = tk.Entry(self, text=self.options_tk['global_dir'])

        self.local_lab = tk.Label(self, text="Weight of local co-occurrences:", anchor='w')
        self.local_w = tk.Entry(self, text=self.options_tk['local'])

        self.local_dir_lab = tk.Label(self, text="Weight of local co-occurrences in directories:", anchor='w')
        self.local_w_dir = tk.Entry(self, text=self.options_tk['local_dir'])

        self.offset_lab = tk.Label(self, text="Weight of self-co-occurrences:", anchor='w')
        self.offset_w = tk.Entry(self, text=self.options_tk['offset'])

        self.bm25_k_lab = tk.Label(self, text="Control parameter k for the okapi-bm25-tf-idf-scheme:", anchor='w')
        self.bm25_k = tk.Entry(self, text=self.options_tk['bm25_k'])

        self.bm25_b_lab = tk.Label(self, text="Control parameter b for the okapi-bm25-tf-idf-scheme:", anchor='w')
        self.bm25_b = tk.Entry(self, text=self.options_tk['bm25_b'])

        self.create_format_co_oc_save_file_label = tk.Label(self, text="Create save files for the format co-occurrences"
                                                                       " for each format:", anchor='w')
        self.create_format_co_oc_save_file = tk.Checkbutton(self,
                                                            variable=self.options_tk['create_format_co_occurrence'
                                                                                     '_save_files'],
                                                            command=lambda: self.call_back('create_format_'
                                                                                           'co_occurrence_save_files')
                                                            )

        self.read_environments_from_file_lab = tk.Label(self, text="Read the readable formats for each environment "
                                                                   "from a save file:", anchor='w')
        self.read_environments_from_file = tk.Checkbutton(self, variable=self.options_tk['read_from_file'],
                                                          command=lambda: self.call_back('read_from_file'))

        self.save_environment_readable_formats_lab = tk.Label(self, text="Save the readable formats for each "
                                                                         "environment in a save file:", anchor='w')
        self.save_environment_readable_formats = tk.Checkbutton(self,
                                                                variable=self.options_tk['save_environments_read'],
                                                                command=lambda: self.call_back('save_environments_read')
                                                                )

        self.create_log_lab = tk.Label(self, text="Print log messages:", anchor='w')
        self.create_log = tk.Checkbutton(self, variable=self.options_tk['log'], command=lambda: self.call_back('log'))

        # positioning
        self.path_to_data_objects_lab.grid(row=0, column=0, rowspan=1, columnspan=4, sticky='nsew')
        self.path_to_data_objects.grid(row=0, column=4, rowspan=1, columnspan=4, sticky='nsew')
        self.path_to_data_objects_browse.grid(row=0, column=8, rowspan=1, columnspan=1, sticky='nsew')

        self.path_to_environments_lab.grid(row=1, column=0, rowspan=1, columnspan=4, sticky='nsew')
        self.path_to_environments.grid(row=1, column=4, rowspan=1, columnspan=4, sticky='nsew')
        self.path_to_environments_browse.grid(row=1, column=8, rowspan=1, columnspan=1, sticky='nsew')

        self.global_lab.grid(row=2, column=0, rowspan=1, columnspan=4, sticky='nsew')
        self.global_w.grid(row=2, column=4, rowspan=1, columnspan=4, sticky='nsew')

        self.global_dir_lab.grid(row=3, column=0, rowspan=1, columnspan=4, sticky='nsew')
        self.global_w_dir.grid(row=3, column=4, rowspan=1, columnspan=4, sticky='nsew')

        self.local_lab.grid(row=4, column=0, rowspan=1, columnspan=4, sticky='nsew')
        self.local_w.grid(row=4, column=4, rowspan=1, columnspan=4, sticky='nsew')

        self.local_dir_lab.grid(row=5, column=0, rowspan=1, columnspan=4, sticky='nsew')
        self.local_w_dir.grid(row=5, column=4, rowspan=1, columnspan=4, sticky='nsew')

        self.offset_lab.grid(row=6, column=0, rowspan=1, columnspan=4, sticky='nsew')
        self.offset_w.grid(row=6, column=4, rowspan=1, columnspan=4, sticky='nsew')

        self.bm25_k_lab.grid(row=7, column=0, rowspan=1, columnspan=4, sticky='nsew')
        self.bm25_k.grid(row=7, column=4, rowspan=1, columnspan=4, sticky='nsew')

        self.bm25_b_lab.grid(row=8, column=0, rowspan=1, columnspan=4, sticky='nsew')
        self.bm25_b.grid(row=8, column=4, rowspan=1, columnspan=4, sticky='nsew')

        self.create_format_co_oc_save_file_label.grid(row=9, column=0, rowspan=1, columnspan=4, sticky='nsew')
        self.create_format_co_oc_save_file.grid(row=9, column=4, rowspan=1, columnspan=4, sticky='nsew')

        self.read_environments_from_file_lab.grid(row=10, column=0, rowspan=1, columnspan=4, sticky='nsew')
        self.read_environments_from_file.grid(row=10, column=4, rowspan=1, columnspan=4, sticky='nsew')

        self.save_environment_readable_formats_lab.grid(row=11, column=0, rowspan=1, columnspan=4, sticky='nsew')
        self.save_environment_readable_formats.grid(row=11, column=4, rowspan=1, columnspan=4, sticky='nsew')

        self.create_log_lab.grid(row=12, column=0, rowspan=1, columnspan=4, sticky='nsew')
        self.create_log.grid(row=12, column=4, rowspan=1, columnspan=4, sticky='nsew')

    def call_back(self, key):
        """
        Function for setting the options to the inputs
        :param key: option key
        """
        self.options[key] = self.options_tk[key].get()

    def browse_button_env(self):
        """
        Select a directory and store it in variable
        """
        foldername = filedialog.askdirectory(initialdir=os.path.dirname(os.path.abspath(__file__)),
                                             title="Select Folder with the environments")
        self.options_tk['path_to_environments'].set(foldername)
        print(foldername)

    def browse_button_do(self):
        """
        Select a directory and store it in variable
        """
        foldername = filedialog.askdirectory(initialdir=os.path.dirname(os.path.abspath(__file__)),
                                             title="Select Folder with the data objects")
        self.options_tk['path_to_objects'].set(foldername)
        print(foldername)

    def set_up_tk_opt(self, opt):
        """
        Creates a tkinter workable options dictionary from the options dictionary
        :param opt: options dictionary
        """
        for key, value in opt.items():
            if (key == 'global' or key == 'global_dir' or key == 'local' or key == 'local_dir' or key == 'offset'
                    or key == 'bm25_k' or key == 'bm25_b'):
                self.options_tk[key] = tk.DoubleVar(self)
                self.options_tk[key].set(value)
            elif key == 'path_to_objects' or key == 'path_to_environments':
                self.options_tk[key] = tk.StringVar(self)
                self.options_tk[key].set(value)
            else:
                self.options_tk[key] = tk.BooleanVar(self)
                self.options_tk[key].set(value)

    def get_default_paths(self):
        """
        Gets the default path for the environments and the data objects
        """
        base_path = os.path.dirname(os.path.abspath(__file__))
        if self.options['path_to_objects'] is None:
            obj_path = os.path.join(base_path, 'sfdata2')
            self.options['path_to_objects'] = obj_path
        if self.options['path_to_environments'] is None:
            env_path = os.path.join(base_path, 'environment_collection')
            self.options['path_to_environments'] = env_path


class OutputFrame(ttk.Frame):
    def __init__(self, parent, *args, **kwargs):
        super().__init__(parent, *args, **kwargs)
        self.yScroll = tk.Scrollbar(self, orient=tk.VERTICAL)
        self.yScroll.pack(side="right", fill="y")

        self.listbox = tk.Listbox(self,
                                  yscrollcommand=self.yScroll.set)
        self.listbox.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)
        self.yScroll['command'] = self.listbox.yview


class ControlFrame(tk.Frame):

    def __init__(self, parent, opt, opt_tk, sister, q, **kwargs):
        super().__init__(parent, **kwargs)

        self.sister = sister
        self.parent = parent
        self.opt = opt
        self.opt_tk = opt_tk
        self.queue = q

        self.program_thread = None

        # laying out the grid
        self.rowconfigure(0, weight=1)
        for c in range(10):
            self.grid_columnconfigure(c, weight=1)

        # self.but_start = tk.Button(self, text="Start", command=lambda: self.start())
        self.but_start = tk.Button(self, text="Start", command=lambda: self.start())
        self.but_canc = tk.Button(self, text="Cancel", command=lambda: self.cancel())
        self.but_start.grid(row=0, column=3, columnspan=1, sticky='nsew')
        self.but_canc.grid(row=0, column=4, columnspan=1, sticky='nsew')

    def start(self):
        """
        Starts the thread of the main program
        """
        self.clear_listbox()
        self.parent.output.listbox.insert(tk.END, 'start program')
        self.synchronize_options()
        path = os.path.dirname(os.path.abspath(__file__))
        with open(os.path.join(path, "parameters.json"), 'w+', encoding='utf8',
                  errors='ignore') as json_file:
            json.dump(self.opt, json_file)
        path_to_objects = self.opt['path_to_objects']

        path_to_environments = self.opt['path_to_environments']
        self.program_thread = CalculatorThread(self.queue, path_to_objects, path_to_environments)
        self.program_thread.start()
        self.disable_options()

    def clear_listbox(self):
        """
        Deletes the current outputs displayed in the output box
        """
        count = None
        for i, listbox_item in enumerate(self.parent.output.listbox.get(0, tk.END)):
            count = i
        if count is not None:
            self.parent.output.listbox.delete(0, i)

    def disable_options(self):
        """
        Disables all the Buttons, Entries and Checkboxes except cancel
        """
        self.sister.path_to_data_objects.config(state=tk.DISABLED)
        self.sister.path_to_data_objects_browse.config(state=tk.DISABLED)
        self.sister.path_to_environments.config(state=tk.DISABLED)
        self.sister.path_to_environments_browse.config(state=tk.DISABLED)
        self.sister.global_w.config(state=tk.DISABLED)
        self.sister.global_w_dir.config(state=tk.DISABLED)
        self.sister.local_w.config(state=tk.DISABLED)
        self.sister.local_w_dir.config(state=tk.DISABLED)
        self.sister.offset_w.config(state=tk.DISABLED)
        self.sister.bm25_k.config(state=tk.DISABLED)
        self.sister.bm25_b.config(state=tk.DISABLED)
        self.sister.create_format_co_oc_save_file.config(state=tk.DISABLED)
        self.sister.read_environments_from_file.config(state=tk.DISABLED)
        self.sister.save_environment_readable_formats.config(state=tk.DISABLED)
        self.sister.create_log.config(state=tk.DISABLED)
        self.but_start.config(state=tk.DISABLED)

    def enable_options(self):
        """
        Enables all the Buttons, Entries and Checkboxes
        """
        self.sister.path_to_data_objects.config(state=tk.NORMAL)
        self.sister.path_to_data_objects_browse.config(state=tk.NORMAL)
        self.sister.path_to_environments.config(state=tk.NORMAL)
        self.sister.path_to_environments_browse.config(state=tk.NORMAL)
        self.sister.global_w.config(state=tk.NORMAL)
        self.sister.global_w_dir.config(state=tk.NORMAL)
        self.sister.local_w.config(state=tk.NORMAL)
        self.sister.local_w_dir.config(state=tk.NORMAL)
        self.sister.offset_w.config(state=tk.NORMAL)
        self.sister.bm25_k.config(state=tk.NORMAL)
        self.sister.bm25_b.config(state=tk.NORMAL)
        self.sister.create_format_co_oc_save_file.config(state=tk.NORMAL)
        self.sister.read_environments_from_file.config(state=tk.NORMAL)
        self.sister.save_environment_readable_formats.config(state=tk.NORMAL)
        self.sister.create_log.config(state=tk.NORMAL)
        self.but_start.config(state=tk.NORMAL)

    def cancel(self):
        """
        Stops the program thread
        """
        self.program_thread.raise_exception()
        self.program_thread.join()
        with self.queue.mutex:
            self.queue.queue.clear()
        self.enable_options()

    def synchronize_options(self):
        """
        Setting the options the input values
        """
        for key, value in self.opt_tk.items():
            self.opt[key] = value.get()


class CalculatorThread(threading.Thread):
    def __init__(self, queue_list, path_to_objects, path_to_environments):
        threading.Thread.__init__(self)
        self.queue = queue_list
        self.path_to_objects = path_to_objects
        self.path_to_environments = path_to_environments

    def run(self):

        try:
            calculate(self.path_to_objects, self.path_to_environments, self.queue)
        finally:
            print('ended')

    def get_id(self):
        """
        returns id of the respective thread
        :return: id
        """
        if hasattr(self, '_thread_id'):
            return self._thread_id
        for id, thread in threading._active.items():
            if thread is self:
                return id

    def raise_exception(self):
        """
        :raises Exception - used to cancel the thread
        """
        thread_id = self.get_id()
        res = ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id,
                                                         ctypes.py_object(SystemExit))
        if res > 1:
            ctypes.pythonapi.PyThreadState_SetAsyncExc(thread_id, 0)
            print('Exception raise failure')



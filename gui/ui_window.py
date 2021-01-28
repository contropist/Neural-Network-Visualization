import ntpath
from tkinter import *
from tkinter import filedialog, messagebox
from typing import List, Dict
from definitions import DATA_PATH
from data.data_handler import ImportanceDataHandler, ProcessedNNHandler
from gui.general_setting import SettingField, RadioButtons
from gui.neural_network_setting import LayerSettings
from gui.processing_setting import ProcessingSetting
from gui.render_setting import RenderSettings
from processing.processing_config import ProcessingConfig
from rendering.rendering_config import RenderingConfig
from utility.window_config import WindowConfig


class OptionGui:
    def __init__(self):
        self.window_config: WindowConfig = WindowConfig('ui')

        self.gui_root: Tk = Tk()
        self.layer_settings: List[LayerSettings] = []
        self.settings: Dict[str, any] = {"Closed": False, "current_layer_data": []}
        self.render_config: RenderingConfig = RenderingConfig()
        self.processing_config: ProcessingConfig = ProcessingConfig()

        self.gui_root.title("NNVIS Options")

        # - Stats shown in the GUI ----------------------------------------------------------------------------------- #
        self.stats_frame: LabelFrame = LabelFrame(self.gui_root, text="Statistics", width=60, padx=5, pady=5)
        self.stats_frame.grid(row=0, column=0, padx=5, pady=5)
        self.field_text: dict = {"edge_count": "Edges", "sample_count": "Samples", "cell_count": "Grid Cells",
                                 "pruned_edges": "Pruned Edges", "fps": "FPS"}
        stats_rows: int = 0
        for field in self.field_text.keys():
            self.settings[field] = SettingField(self.stats_frame, self.field_text[field] + ":", row=stats_rows,
                                                column=0)
            stats_rows += 1
        # ------------------------------------------------------------------------------------------------------------ #

        # - Architecture section of the GUI -------------------------------------------------------------------------- #
        self.architecture_frame: LabelFrame = LabelFrame(self.gui_root, text="Neural Network Architecture", width=60,
                                                         padx=5, pady=5)
        self.architecture_frame.grid(row=1, column=0, rowspan=2, padx=5, pady=5)
        self.architecture_buttons: List[Button] = []
        self.save_processed_button: Button = Button(self.architecture_frame, text="Save Processed Network", width=20,
                                                    command=self.save_processed_nn_file)
        self.save_processed_button.grid(row=0, column=0, columnspan=3)
        self.load_processed_button: Button = Button(self.architecture_frame, text="Load Processed Network", width=20,
                                                    command=self.open_processed_nn_file)
        self.load_processed_button.grid(row=1, column=0, columnspan=3)
        self.load_button: Button = Button(self.architecture_frame, text="Load Network", width=20,
                                          command=self.open_importance_file)
        self.load_button.grid(row=2, column=0, columnspan=3)
        self.generate_button: Button = Button(self.architecture_frame, text="Generate Network", width=20,
                                              command=self.generate)
        self.generate_button.grid(row=3, column=0, columnspan=3)
        self.layer_label: Label = Label(self.architecture_frame, text="Modify:")
        self.add_layer_button: Button = Button(self.architecture_frame, text="Add Layer", command=self.add_layer)
        self.clear_layer_button: Button = Button(self.architecture_frame, text="Clear Layer", command=self.clear_layer)
        self.layer_label.grid(row=4, column=0)
        self.add_layer_button.grid(row=4, column=1)
        self.clear_layer_button.grid(row=4, column=2)
        # ------------------------------------------------------------------------------------------------------------ #

        # - Render settings section of the GUI ----------------------------------------------------------------------- #
        self.render_frame: LabelFrame = LabelFrame(self.gui_root, text="Render Settings", width=60,
                                                   padx=5, pady=5)
        self.render_frame.grid(row=0, column=3, columnspan=2, rowspan=3, padx=5, pady=5)

        self.grid_render_settings: RenderSettings = \
            RenderSettings(self.render_frame,
                           "Grid",
                           self.change_render_config,
                           self.render_config,
                           "grid_render_mode",
                           None,
                           row=0,
                           column=0)
        edge_shader_settings: List[str] = ["edge_object_radius", "edge_base_opacity", "edge_importance_opacity",
                                           "edge_depth_opacity", "edge_opacity_exponent", "edge_importance_threshold"]
        self.edge_render_settings: RenderSettings = \
            RenderSettings(self.render_frame,
                           "Edge",
                           self.change_render_config,
                           self.render_config,
                           "edge_render_mode",
                           edge_shader_settings,
                           row=1,
                           column=0)
        node_shader_settings: List[str] = ["node_object_radius", "node_base_opacity", "node_importance_opacity",
                                           "node_depth_opacity", "node_opacity_exponent", "node_importance_threshold"]
        self.node_render_settings: RenderSettings = \
            RenderSettings(self.render_frame,
                           "Node",
                           self.change_render_config,
                           self.render_config,
                           "node_render_mode",
                           node_shader_settings,
                           row=2,
                           column=0)

        self.class_setting_frame: LabelFrame = LabelFrame(self.render_frame, text="Class Visibility", width=60,
                                                          padx=5, pady=5)
        self.class_setting_frame.grid(row=0, column=1, rowspan=3, padx=5, pady=5)
        self.class_show: IntVar = IntVar(value=0)

        show_class_names: List[str] = ["Independent", "All"]
        for class_id in range(9):
            show_class_names.append("Class " + str(class_id))
        self.class_show_options: RadioButtons = RadioButtons(self.class_setting_frame,
                                                             show_class_names, self.class_show,
                                                             command=self.change_setting, option="show",
                                                             sub_option="class", row=0, column=0, width=10, height=2)
        # ------------------------------------------------------------------------------------------------------------ #

        # - Processing section of the GUI --------------------------------------------------------------------- #
        self.processing_frame: LabelFrame = LabelFrame(self.gui_root, text="Processing", width=60, padx=5, pady=5)
        self.processing_frame.grid(row=0, column=1, columnspan=2, rowspan=3, padx=5, pady=5)

        self.action_frame: LabelFrame = LabelFrame(self.processing_frame, text="Actions", width=60,
                                                   padx=5, pady=5)
        self.action_frame.grid(row=1, column=0, rowspan=2, padx=5, pady=5)
        self.sample_button: Button = Button(self.action_frame, text="Resample Edges", width=15,
                                            command=lambda: self.change_setting("trigger_network", "sample", 1, True))
        self.sample_button.grid(row=0, column=0)
        self.action_state: IntVar = IntVar(value=0)
        self.action_buttons: RadioButtons = RadioButtons(self.action_frame,
                                                         ["Stop Everything", "Node Advect", "Node Diverge",
                                                          "Node Noise", "Edge Advect", "Edge Diverge", "Edge Noise"],
                                                         self.action_state, command=self.change_setting,
                                                         option="action", sub_option="state", row=2, column=0)

        self.smoothing_status: IntVar = IntVar(value=self.processing_config["smoothing"])
        self.smoothing_checkbox: Checkbutton = Checkbutton(self.action_frame, text="Smoothing",
                                                           variable=self.smoothing_status,
                                                           command=lambda: self.change_processing_config(
                                                               "smoothing",
                                                               self.smoothing_status.get()))
        self.change_setting("edge", "smoothing", self.smoothing_status.get())
        self.smoothing_checkbox.grid(row=1, column=0)

        self.setting_frame: LabelFrame = LabelFrame(self.processing_frame, text="Settings", width=60,
                                                    padx=5, pady=5)
        self.setting_frame.grid(row=0, column=0, padx=5, pady=5)
        self.processing_setting: ProcessingSetting = ProcessingSetting(self.processing_config, self.setting_frame)

        # ------------------------------------------------------------------------------------------------------------ #

        self.gui_root.protocol("WM_DELETE_WINDOW", self.on_closing)
        screen_width = self.gui_root.winfo_reqwidth()
        screen_height = self.gui_root.winfo_reqheight()
        self.gui_root.geometry(
            '+%d+%d' % (self.window_config['screen_x'], self.window_config['screen_y']))
        self.gui_root.bind("<Configure>", self.handle_configure)

    def start(self, layer_data: List[int] = None):
        if layer_data is None:
            default_layer_data = [4, 9, 9]
            for nodes in default_layer_data:
                self.add_layer(nodes)
        else:
            for nodes in layer_data:
                self.add_layer(nodes)

        self.processing_setting.set()
        self.generate()

        self.gui_root.mainloop()
        self.settings["Closed"] = True

    def handle_configure(self, event):
        self.window_config['screen_x'] = self.gui_root.winfo_x()
        self.window_config['screen_y'] = self.gui_root.winfo_y()
        self.window_config.store()

    def save_processed_nn_file(self):
        filename = filedialog.asksaveasfilename()
        if not filename:
            return
        self.settings["save_processed_nn_path"] = filename
        self.settings["save_file"] = True

    def open_processed_nn_file(self):
        filename = filedialog.askopenfilename(initialdir=DATA_PATH, title="Select A File",
                                              filetypes=(("processed nn files", "*.npz"),))
        data_loader: ProcessedNNHandler = ProcessedNNHandler(filename)
        self.settings['network_name'] = ntpath.basename(filename) + "_processed"
        self.update_layer(data_loader.layer_data, processed_nn=data_loader)

    def open_importance_file(self):
        filename = filedialog.askopenfilename(initialdir=DATA_PATH, title="Select A File",
                                              filetypes=(("importance files", "*.npz"),))
        data_loader: ImportanceDataHandler = ImportanceDataHandler(filename)
        self.settings['network_name'] = ntpath.basename(filename) + "_raw"
        self.update_layer(data_loader.layer_data, importance_data=data_loader)

    def update_layer(self, layer_data: List[int], importance_data: ImportanceDataHandler = None,
                     processed_nn: ProcessedNNHandler = None):
        self.clear_layer()

        for nodes in layer_data:
            self.add_layer(nodes)

        self.generate(importance_data, processed_nn)
        self.set_classes(layer_data[len(layer_data) - 1])

    def add_layer(self, nodes: int = 9):
        layer_id: int = len(self.layer_settings)
        self.layer_settings.append(LayerSettings(self.architecture_frame, layer_id, 5, 0, self.remove_layer))
        self.layer_settings[layer_id].set_neurons(nodes)

    def clear_layer(self):
        for ls in self.layer_settings:
            ls.remove()
        self.layer_settings = []

    def remove_layer(self, layer_id: int):
        self.layer_settings[layer_id].remove()
        self.layer_settings.remove(self.layer_settings[layer_id])

        for i, ls in enumerate(self.layer_settings):
            ls.layer_id = i
            ls.grid()
        self.layer_label.grid(row=0, column=0)

    def generate(self, importance_data: ImportanceDataHandler = None, processed_nn: ProcessedNNHandler = None):
        self.action_buttons.press(0)
        layer_data: List[int] = []
        for ls in self.layer_settings:
            layer_data.append(ls.get_neurons())
        self.settings["current_layer_data"] = layer_data
        self.settings["importance_data"] = importance_data
        self.settings["processed_nn"] = processed_nn
        self.processing_setting.update_config()
        self.settings["update_model"] = True
        self.processing_config.store()

    def change_setting(self, setting_type: str, sub_type: str, value: int, stop_action: bool = False):
        if stop_action:
            self.action_buttons.press(0)
        self.settings[setting_type + "_" + sub_type] = value

    def change_render_config(self, name: str, value: int, stop_action: bool = False):
        if stop_action:
            self.action_buttons.press(0)
        self.render_config[name] = value
        self.render_config.store()

    def change_processing_config(self, name: str, value: int):
        self.processing_config[name] = value
        self.processing_config.store()

    def on_closing(self):
        if messagebox.askokcancel("Quit", "Do you want to quit?"):
            self.settings["Closed"] = True

    def set_classes(self, num_classes: int):
        show_class_names: List[str] = ["Independent", "All"]
        for class_id in range(num_classes):
            show_class_names.append("Class " + str(class_id))
        self.class_show_options.set_buttons(show_class_names)

    def destroy(self):
        self.gui_root.destroy()

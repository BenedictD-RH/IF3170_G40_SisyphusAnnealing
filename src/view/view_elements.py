import pyray as rl
try:
    from .plotter import launch_plot_subprocess, show_plot
except ImportError:
    from plotter import launch_plot_subprocess, show_plot

_mouse_uses_render_coords = False

def get_ui_mouse_position() -> rl.Vector2:
    global _mouse_uses_render_coords
    mouse = rl.get_mouse_position()
    sw = rl.get_screen_width()
    sh = rl.get_screen_height()
    rw = rl.get_render_width()
    rh = rl.get_render_height()

    if sw > 0 and sh > 0 and rw > 0 and rh > 0:
        scale_x = rw / sw
        scale_y = rh / sh
        if scale_x > 1.05 or scale_y > 1.05:
            if mouse.x > sw or mouse.y > sh:
                _mouse_uses_render_coords = True
            if _mouse_uses_render_coords:
                return rl.Vector2(mouse.x / scale_x, mouse.y / scale_y)
    return mouse


class TextEntry:
    def __init__(self, label, x, y, w=180, h=30, text="", numeric=False, max_len=8, on_commit=None):
        self.label = str(label)
        self.bb = rl.Rectangle(x, y, w, h)
        self.text = text
        self.numeric = numeric
        self.max_len = max_len
        self.on_commit = on_commit      # called with the text on Enter / click-away
        self.focused = False
        self.enabled = True

    def _commit(self):
        if self.on_commit and self.text:
            self.on_commit()

    def draw(self):
        if self.enabled :
            mouse_pos = get_ui_mouse_position()
            hitbox = rl.Rectangle(self.bb.x, self.bb.y - 20, self.bb.width, self.bb.height + 20)
            hover = rl.check_collision_point_rec(mouse_pos, hitbox)

            # focus handling
            if rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT):
                was_focused = self.focused
                self.focused = hover
                if was_focused and not hover:
                    self._commit()

            # keyboard input
            if self.focused:
                while True:
                    ch = rl.get_char_pressed()
                    if ch == 0:
                        break
                    c = chr(ch)
                    ok = (c.isdigit() or c in ".-") if self.numeric else (32 <= ch < 127)
                    if ok and len(self.text) < self.max_len:
                        self.text += c

                if (rl.is_key_pressed(rl.KeyboardKey.KEY_BACKSPACE)
                        or rl.is_key_pressed_repeat(rl.KeyboardKey.KEY_BACKSPACE)):
                    self.text = self.text[:-1]

                if rl.is_key_pressed(rl.KeyboardKey.KEY_ENTER):
                    self._commit()
                    self.focused = False

            # drawing
            rl.draw_text(self.label, int(self.bb.x), int(self.bb.y) - 20, 16, rl.WHITE)
            rl.draw_rectangle_rec(self.bb, rl.WHITE if self.focused else rl.LIGHTGRAY)
            rl.draw_rectangle_lines_ex(self.bb, 2, rl.BLUE if self.focused else rl.GRAY)

            shown = str(self.text)
            # blinking cursor
            if self.focused and int(rl.get_time() * 2) % 2 == 0:
                shown += "|"
            rl.draw_text(str(shown), int(self.bb.x) + 8, int(self.bb.y) + 7, 17, rl.BLACK)

class Button:
    def __init__(self, label, x, y, w=180, h=50, font_size=17, on_click=None,
                 color=rl.LIGHTGRAY, hover_color=rl.GRAY, text_color=rl.BLACK):
        self.label = label
        self.bb = rl.Rectangle(x, y, w, h)
        self.font_size = font_size
        self.on_click = on_click
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.enabled = True

    def draw(self):
        if not self.enabled:
            disabled_color = rl.Color(100, 100, 100, 255)
            rl.draw_rectangle_rec(self.bb, disabled_color)
            rl.draw_rectangle_lines_ex(self.bb, 1, rl.Color(70, 70, 70, 255))
            text_w = rl.measure_text(self.label, self.font_size)
            tx = int(self.bb.x + (self.bb.width - text_w) / 2)
            ty = int(self.bb.y + (self.bb.height - self.font_size) / 2)
            rl.draw_text(self.label, tx, ty, self.font_size, rl.Color(160, 160, 160, 255))
            return

        mouse_pos = get_ui_mouse_position()
        hover = rl.check_collision_point_rec(mouse_pos, self.bb)
        clicked = hover and rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT)

        if clicked and self.on_click:
            self.on_click()

        rl.draw_rectangle_rec(self.bb, self.hover_color if hover else self.color)

        # center the label inside the button
        text_w = rl.measure_text(self.label, self.font_size)
        tx = int(self.bb.x + (self.bb.width - text_w) / 2)
        ty = int(self.bb.y + (self.bb.height - self.font_size) / 2)
        rl.draw_text(self.label, tx, ty, self.font_size, self.text_color)


class Switch:
    def __init__(self, label_pool, x, y, w=180, h=50, font_size=17, on_click=None,
                 color=rl.LIGHTGRAY, hover_color=rl.GRAY, text_color=rl.BLACK):
        self.label_pool = label_pool
        self.label_idx = 0
        self.bb = rl.Rectangle(x, y, w, h)
        self.font_size = font_size
        self.on_click = on_click
        self.color = color
        self.hover_color = hover_color
        self.text_color = text_color
        self.enabled = True
        

    def get_current_label(self) :
        return self.label_pool[self.label_idx]

    def draw(self):
        if self.enabled :
            mouse_pos = get_ui_mouse_position()
            hover = rl.check_collision_point_rec(mouse_pos, self.bb)
            clicked = hover and rl.is_mouse_button_pressed(rl.MouseButton.MOUSE_BUTTON_LEFT)

            if clicked :
                self.label_idx = (self.label_idx + 1) % len(self.label_pool)
                if self.on_click :
                    self.on_click()
                

            rl.draw_rectangle_rec(self.bb, self.hover_color if hover else self.color)

            # center the label inside the button
            text_w = rl.measure_text(self.label_pool[self.label_idx], self.font_size)
            tx = int(self.bb.x + (self.bb.width - text_w) / 2)
            ty = int(self.bb.y + (self.bb.height - self.font_size) / 2)
            rl.draw_text(self.label_pool[self.label_idx], tx, ty, self.font_size, self.text_color)
        

class HUD :
    def __init__(self, x=0, y=0, w=300, h=800, color=rl.DARKGRAY):
        self.bb = rl.Rectangle(x, y, w, h)
        self.color = color
        self.command = ""
        self.input_file_text_entry = TextEntry("Input Initial State File", 60, 45, 180, 30, 
                                                text="input5.json",
                                                on_commit=lambda :setattr(self, 'command', "INPUT_INITIAL_STATE_FILE"),
                                                numeric=False, 
                                                max_len=20)
        self.random_init_btn = Button("Random Initial State", 60, 95, 180, 40, 16, 
                                     on_click=lambda : setattr(self, 'command', "RANDOM_INIT_STATE"),
                                     color=rl.LIGHTGRAY, 
                                     hover_color=rl.GRAY, 
                                     text_color=rl.BLACK)
        self.random_init_btn.enabled = False

        self.algorithm_switch = Switch(["Hill Climbing", "Simulated Annealing", "Genetic Algorithm"], 60, 145, 180, 40, 16, 
                                     on_click=lambda: self.enable_disabled(),
                                     color=rl.LIGHTGRAY, 
                                     hover_color=rl.GRAY, 
                                     text_color=rl.BLACK)
        self.algorithm_switch.enabled = False

        self.hc_switch = Switch(["Steepest", "Sideways", "Random Restart", "Stochastic"], 60, 195, 180, 40, 16, 
                                on_click=lambda: self.enable_disabled(),
                                color=rl.LIGHTGRAY, 
                                hover_color=rl.GRAY, 
                                text_color=rl.BLACK)
        self.hc_switch.enabled = False

        self.max_iter_text_entry = TextEntry("Max Iterations", 20, 265, 120, 28,
                                    text="1000",
                                    numeric=True, 
                                    max_len=20)
        self.max_iter_text_entry.enabled = False

        self.step_size_text_entry = TextEntry("Step Size", 20, 320, 120, 28,
                                            text="2",
                                            numeric=True, 
                                            max_len=20)
        self.step_size_text_entry.enabled = False

        self.max_sideways_move_text_entry = TextEntry("Max Sideways Move", 20, 375, 120, 28,
                                            text="100",
                                            numeric=True, 
                                            max_len=20)
        self.max_sideways_move_text_entry.enabled = False

        self.max_restart_text_entry = TextEntry("Max Restart", 20, 375, 120, 28,
                                            text="10",
                                            numeric=True, 
                                            max_len=20)
        self.max_restart_text_entry.enabled = False

        self.temperature_text_entry = TextEntry("Temperature", 20, 375, 120, 28,
                                            text="1.0",
                                            numeric=True, 
                                            max_len=20)
        self.temperature_text_entry.enabled = False

        self.sa_init_temp_text_entry = TextEntry("Initial Temperature", 20, 210, 120, 28,
                                    text="1000",
                                    numeric=True, 
                                    max_len=20)
        self.sa_init_temp_text_entry.enabled = False

        self.sa_cooling_rate_text_entry = TextEntry("Cooling Rate", 20, 262, 120, 28,
                                    text="0.995",
                                    numeric=True, 
                                    max_len=20)
        self.sa_cooling_rate_text_entry.enabled = False

        self.sa_min_temp_text_entry = TextEntry("Min Temperature", 20, 314, 120, 28,
                                    text="0.001",
                                    numeric=True, 
                                    max_len=20)
        self.sa_min_temp_text_entry.enabled = False

        self.sa_max_iter_text_entry = TextEntry("Max Iterations", 20, 366, 120, 28,
                                    text="1000",
                                    numeric=True, 
                                    max_len=20)
        self.sa_max_iter_text_entry.enabled = False

        self.sa_step_per_temp_text_entry = TextEntry("Steps per Temperature", 20, 418, 120, 28,
                                    text="1",
                                    numeric=True, 
                                    max_len=20)
        self.sa_step_per_temp_text_entry.enabled = False

        self.sa_step_size_text_entry = TextEntry("Steps Size", 20, 470, 120, 28,
                                    text="2",
                                    numeric=True, 
                                    max_len=20)
        self.sa_step_size_text_entry.enabled = False

        self.sa_schedule_switch = Switch(["Geometric", "Linear", "Logarithmic", "Cosine"], 160, 230, 120, 40, 16, 
                                on_click=lambda: self.enable_disabled(),
                                color=rl.LIGHTGRAY, 
                                hover_color=rl.GRAY, 
                                text_color=rl.BLACK)
        self.sa_schedule_switch.enabled = False

        self.ga_population_size_text_entry = TextEntry("Population Size", 20, 210, 120, 28,
                                    text="100",
                                    numeric=True, 
                                    max_len=20)
        self.ga_population_size_text_entry.enabled = False

        self.ga_generations_text_entry = TextEntry("Generations", 20, 262, 120, 28,
                                    text="200",
                                    numeric=True, 
                                    max_len=20)
        self.ga_generations_text_entry.enabled = False

        self.ga_tour_size_text_entry = TextEntry("Tournament Size", 20, 314, 120, 28,
                                    text="3",
                                    numeric=True, 
                                    max_len=20)
        self.ga_tour_size_text_entry.enabled = False

        self.ga_crossover_prob_text_entry = TextEntry("Crossover Probability", 20, 366, 120, 28,
                                    text="0.8",
                                    numeric=True, 
                                    max_len=20)
        self.ga_crossover_prob_text_entry.enabled = False

        self.ga_pkg_mutation_prob_text_entry = TextEntry("Package Mutation Probability", 20, 418, 120, 28,
                                    text="0.2",
                                    numeric=True, 
                                    max_len=20)
        self.ga_pkg_mutation_prob_text_entry.enabled = False
        
        self.ga_plcment_mutation_prob_text_entry = TextEntry("Placement Mutation Probability", 20, 470, 120, 28,
                                    text="0.05",
                                    numeric=True, 
                                    max_len=20)
        self.ga_plcment_mutation_prob_text_entry.enabled = False

        self.run_btn = Button("Run", 60, 565, 180, 45, 17, 
                            on_click=lambda : setattr(self, 'command', "RUN"),
                            color=rl.LIGHTGRAY, 
                            hover_color=rl.GRAY, 
                            text_color=rl.BLACK)
        self.run_btn.enabled = False

        self.scroll_y = 0.0
        self.max_scroll = 0.0
        self.scrollable_widgets = [
            self.hc_switch,
            self.max_iter_text_entry,
            self.step_size_text_entry,
            self.max_sideways_move_text_entry,
            self.max_restart_text_entry,
            self.temperature_text_entry,
            self.sa_init_temp_text_entry,
            self.sa_cooling_rate_text_entry,
            self.sa_min_temp_text_entry,
            self.sa_max_iter_text_entry,
            self.sa_step_per_temp_text_entry,
            self.sa_step_size_text_entry,
            self.sa_schedule_switch,
            self.ga_population_size_text_entry,
            self.ga_generations_text_entry,
            self.ga_tour_size_text_entry,
            self.ga_crossover_prob_text_entry,
            self.ga_pkg_mutation_prob_text_entry,
            self.ga_plcment_mutation_prob_text_entry,
        ]
        self.scrollable_base_y = [w.bb.y for w in self.scrollable_widgets]
        self.widgets = self.scrollable_widgets
        self.base_positions = self.scrollable_base_y

    def enable_disabled(self) :
        self.random_init_btn.enabled = True
        self.algorithm_switch.enabled = True
        self.run_btn.enabled = True
        self.hc_switch.enabled = False
        self.max_iter_text_entry.enabled = False
        self.step_size_text_entry.enabled = False
        self.max_sideways_move_text_entry.enabled = False
        self.max_restart_text_entry.enabled = False
        self.temperature_text_entry.enabled = False
        self.sa_init_temp_text_entry.enabled = False
        self.sa_cooling_rate_text_entry.enabled = False
        self.sa_min_temp_text_entry.enabled = False
        self.sa_max_iter_text_entry.enabled = False
        self.sa_step_per_temp_text_entry.enabled = False
        self.sa_step_size_text_entry.enabled = False
        self.sa_schedule_switch.enabled = False
        self.ga_population_size_text_entry.enabled = False
        self.ga_generations_text_entry.enabled = False
        self.ga_crossover_prob_text_entry.enabled = False
        self.ga_tour_size_text_entry.enabled = False
        self.ga_pkg_mutation_prob_text_entry.enabled = False
        self.ga_plcment_mutation_prob_text_entry.enabled = False
        if (self.algorithm_switch.get_current_label() == "Hill Climbing") :
            self.hc_switch.enabled = True
            self.max_iter_text_entry.enabled = True
            self.step_size_text_entry.enabled = True
            if self.hc_switch.get_current_label() == "Sideways" :
                self.max_sideways_move_text_entry.enabled = True
            elif self.hc_switch.get_current_label() == "Random Restart" :
                self.max_restart_text_entry.enabled = True
            elif self.hc_switch.get_current_label() == "Stochastic" :
                self.temperature_text_entry.enabled = True
        elif (self.algorithm_switch.get_current_label() == "Simulated Annealing") :
            self.sa_init_temp_text_entry.enabled = True
            self.sa_cooling_rate_text_entry.enabled = True
            self.sa_min_temp_text_entry.enabled = True
            self.sa_max_iter_text_entry.enabled = True
            self.sa_step_per_temp_text_entry.enabled = True
            self.sa_step_size_text_entry.enabled = True
            self.sa_schedule_switch.enabled = True
        elif (self.algorithm_switch.get_current_label() == "Genetic Algorithm") :
            self.ga_population_size_text_entry.enabled = True
            self.ga_generations_text_entry.enabled = True
            self.ga_crossover_prob_text_entry.enabled = True
            self.ga_tour_size_text_entry.enabled = True
            self.ga_pkg_mutation_prob_text_entry.enabled = True
            self.ga_plcment_mutation_prob_text_entry.enabled = True

    def draw(self) :
        screen_h = float(rl.get_screen_height())
        self.bb.height = screen_h
        self.bb.y = 0.0

        header_h = 190.0

        # Determine dynamic base Y for run_btn right below the active parameters
        algo = self.algorithm_switch.get_current_label()
        if algo == "Hill Climbing":
            hc_mode = self.hc_switch.get_current_label()
            if hc_mode == "Steepest":
                run_base_y = 370.0
            else: # Sideways, Random Restart, Stochastic
                run_base_y = 425.0
        elif algo == "Simulated Annealing":
            run_base_y = 520.0
        else: # Genetic Algorithm
            run_base_y = 520.0

        # Compute max scroll if content + run_btn exceeds current window height
        total_content_bottom = run_base_y + 42.0 + 20.0
        self.max_scroll = max(0.0, total_content_bottom - screen_h)
        if self.max_scroll <= 0.0:
            self.scroll_y = 0.0
        else:
            self.scroll_y = max(0.0, min(self.max_scroll, self.scroll_y))

        # Scroll handling for HUD panel below header
        mouse_pos = get_ui_mouse_position()
        if mouse_pos.x <= self.bb.width and mouse_pos.y >= header_h:
            wheel = rl.get_mouse_wheel_move()
            if wheel == 0.0 and hasattr(rl, 'get_mouse_wheel_move_v'):
                try:
                    wheel_v = rl.get_mouse_wheel_move_v()
                    if hasattr(wheel_v, 'y') and wheel_v.y != 0.0:
                        wheel = wheel_v.y
                except Exception:
                    pass
            if wheel != 0.0 and self.max_scroll > 0.0:
                self.scroll_y = max(0.0, min(self.max_scroll, self.scroll_y - wheel * 24.0))

        # Dynamically position run_btn relative to active parameters and scroll
        self.run_btn.bb.x = 60.0
        self.run_btn.bb.width = 180.0
        self.run_btn.bb.height = 42.0
        self.run_btn.bb.y = run_base_y - self.scroll_y

        # Update scroll positions of parameter widgets
        for widget, base_y in zip(self.scrollable_widgets, self.scrollable_base_y):
            widget.bb.y = base_y - self.scroll_y

        # 1. Base HUD background
        rl.draw_rectangle_rec(self.bb, self.color)

        # 2. Draw active parameter widgets (only if inside visible area below header)
        def draw_param(w):
            if w.bb.y >= header_h - 25.0 and w.bb.y <= screen_h + 10.0:
                w.draw()

        if algo == "Hill Climbing":
            draw_param(self.hc_switch)
            draw_param(self.max_iter_text_entry)
            draw_param(self.step_size_text_entry)
            hc_mode = self.hc_switch.get_current_label()
            if hc_mode == "Sideways":
                draw_param(self.max_sideways_move_text_entry)
            elif hc_mode == "Random Restart":
                draw_param(self.max_restart_text_entry)
            elif hc_mode == "Stochastic":
                draw_param(self.temperature_text_entry)
        elif algo == "Simulated Annealing":
            draw_param(self.sa_init_temp_text_entry)
            draw_param(self.sa_cooling_rate_text_entry)
            draw_param(self.sa_min_temp_text_entry)
            draw_param(self.sa_max_iter_text_entry)
            draw_param(self.sa_step_per_temp_text_entry)
            draw_param(self.sa_step_size_text_entry)
            draw_param(self.sa_schedule_switch)
        elif algo == "Genetic Algorithm":
            draw_param(self.ga_population_size_text_entry)
            draw_param(self.ga_generations_text_entry)
            draw_param(self.ga_crossover_prob_text_entry)
            draw_param(self.ga_tour_size_text_entry)
            draw_param(self.ga_pkg_mutation_prob_text_entry)
            draw_param(self.ga_plcment_mutation_prob_text_entry)

        # 3. Dynamic run button directly below active parameters
        if self.run_btn.bb.y >= header_h - 20.0 and self.run_btn.bb.y <= screen_h + 10.0:
            self.run_btn.draw()

        # 4. Middle scrollbar thumb if content exceeds window height
        if self.max_scroll > 0.0:
            track_y = header_h + 5.0
            track_h = screen_h - track_y - 10.0
            thumb_h = max(24.0, track_h * (track_h / (track_h + self.max_scroll)))
            thumb_y = track_y + (self.scroll_y / self.max_scroll) * (track_h - thumb_h)
            rl.draw_rectangle(int(self.bb.width) - 6, int(thumb_y), 4, int(thumb_h), rl.fade(rl.LIGHTGRAY, 0.7))

        # 5. Fixed Header: background guard, separator line, and top widgets
        rl.draw_rectangle(0, 0, int(self.bb.width), int(header_h), self.color)
        rl.draw_line(15, int(header_h), int(self.bb.width) - 15, int(header_h), rl.fade(rl.GRAY, 0.7))
        self.input_file_text_entry.draw()
        self.random_init_btn.draw()
        self.algorithm_switch.draw()

def plot_history(history):
    launch_plot_subprocess(history)


class ResultView:
    def __init__(self, exec_time, final_objective_value, actual_value, is_valid, history=[], stuck_info=None, loss_details=None):
        self.exec_time = exec_time
        self.final_objective_value = final_objective_value
        self.actual_value = actual_value
        self.is_valid = is_valid
        self.history = history
        self.stuck_info = stuck_info
        self.loss_details = loss_details

        height = 300
        if stuck_info:
            height += 36
        if loss_details:
            height += 105

        self.bb = rl.Rectangle(300, 0, 220, height)
        self.plot_btn = Button("Display Plot", 360, int(height) - 48, 100, 36, 16, 
                               on_click=lambda: plot_history(self.history), 
                               color=rl.GRAY, 
                               hover_color=rl.DARKGRAY, 
                               text_color=rl.WHITE)

    def hasResult(self):
        return not (self.exec_time == 0 and self.final_objective_value == 0 and self.actual_value == 0 and self.is_valid == False)

    def draw(self):
        rl.draw_rectangle_pro(self.bb, (0, 0), 0, rl.LIGHTGRAY)
        rl.draw_rectangle_lines_ex(self.bb, 2, rl.GRAY)

        x = int(self.bb.x) + 12
        y = int(self.bb.y) + 10

        rl.draw_text("Result", x, y, 20, rl.BLACK)
        y += 30

        lines = [
            ("Exec time", f"{self.exec_time:.3f} s", rl.BLACK),
            ("Objective", f"{self.final_objective_value:,.1f}", rl.BLACK),
            ("Actual value", f"{self.actual_value:,.1f}", rl.BLACK),
            ("Valid", "Yes" if self.is_valid else "No",
             rl.DARKGREEN if self.is_valid else rl.MAROON),
        ]

        if self.loss_details:
            loaded_c = self.loss_details.get("loaded_count", 0)
            lost_c = self.loss_details.get("lost_count", 0)
            lost_v = self.loss_details.get("total_lost_value", 0.0)
            w_load = self.loss_details.get("total_loaded_weight", 0)
            max_w = self.loss_details.get("max_capacity", 0)
            lines.append(("Box Loaded/Lost", f"{loaded_c} in / {lost_c} loss", rl.BLACK if lost_c == 0 else rl.MAROON))
            lines.append(("Loss Value", f"{lost_v:,.1f}", rl.BLACK if lost_v == 0 else rl.MAROON))
            lines.append(("Weight", f"{w_load} / {max_w}", rl.BLACK if w_load <= max_w else rl.RED))

        if self.stuck_info:
            lines.append(("Stuck Freq", str(self.stuck_info), rl.DARKBLUE))

        for label, value, color in lines:
            rl.draw_text(label, x, y, 13, rl.DARKGRAY)
            rl.draw_text(value, x, y + 14, 16, color)
            y += 33
        self.plot_btn.draw()

import os
import sys

BASE_DIR = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
if BASE_DIR not in sys.path:
    sys.path.insert(0, BASE_DIR)
SRC_DIR = os.path.abspath(os.path.dirname(__file__))
if SRC_DIR not in sys.path:
    sys.path.insert(0, SRC_DIR)

try:
    from data_struct.data_struct import TruckState, objectiveFunction, isValid, getTotalValue
    from algorithm import SteepestHillClimbing, SidewaysHillClimbing, RandomRestartHillClimbing, StochasticHillClimbing, SimulatedAnnealing, genetic_algorithm
    from view.view_elements import TextEntry, Button, HUD, get_ui_mouse_position, ResultView
except ImportError:
    from src.data_struct.data_struct import TruckState, objectiveFunction, isValid, getTotalValue
    from src.algorithm import SteepestHillClimbing, SidewaysHillClimbing, RandomRestartHillClimbing, StochasticHillClimbing, SimulatedAnnealing, genetic_algorithm
    from src.view.view_elements import TextEntry, Button, HUD, get_ui_mouse_position, ResultView

import pyray as rl
import json
import threading
import copy

color_dict = {}

def drawTruckState(state : TruckState, camera) :
    rl.begin_mode_3d(camera)
    rl.draw_cube_wires((state.truck.dimensions['w']/2, state.truck.dimensions['h']/2, state.truck.dimensions['l']/2),
                       state.truck.dimensions['w'], state.truck.dimensions['h'], state.truck.dimensions['l'], rl.BLACK)
    mouse_pos = rl.get_mouse_position()
    ray = rl.get_screen_to_world_ray(mouse_pos, camera)
    for p in state.packages :
        if p.isInTruck(state.truck.dimensions) :
            x1, y1, z1, x2, y2, z2 = p.getAbsoluteBB()
            w = x2 - x1
            l = y2 - y1
            h = z2 - z1
            if p.getID() not in color_dict :
                color_dict[p.getID()] = rl.Color(
                    rl.get_random_value(0, 255),
                    rl.get_random_value(0, 255),
                    rl.get_random_value(0, 255),
                    255)
            color = color_dict[p.getID()] if not p.isFragile() else rl.fade(color_dict[p.getID()], 0.5)

            package_bb = rl.BoundingBox((x1, z1, y1), (x2, z2, y2))
                                    
            collision = rl.get_ray_collision_box(ray, package_bb)

            rl.draw_cube((x1 + w/2, z1 + h/2, y1 + l/2), w, h, l, color)
            
            rl.draw_cube_wires((x1 + w/2, z1 + h/2, y1 + l/2), w, h, l, rl.WHITE if collision.hit else rl.BLACK)

    
    rl.end_mode_3d()

    for p in state.packages :
        if p.isInTruck(state.truck.dimensions) :
            x1, y1, z1, x2, y2, z2 = p.getAbsoluteBB()
            w = x2 - x1
            l = y2 - y1
            h = z2 - z1
            
            package_bb = rl.BoundingBox((x1, z1, y1), (x2, z2, y2))
            

            collision = rl.get_ray_collision_box(ray, package_bb)

            if collision.hit and mouse_pos.x > hud.bb.width and not (result_view.hasResult() and rl.check_collision_point_rec(get_ui_mouse_position(), result_view.bb)):
                screenPos = rl.get_world_to_screen((x1 + w/2, z1 + h/2, y1 + l/2), camera)
                rl.draw_rectangle(int(screenPos.x), int(screenPos.y), 310, 165, rl.LIGHTGRAY)
                rl.draw_text(p.getStateString(), int(screenPos.x) + 5, int(screenPos.y) + 5, 18, rl.BLACK)
                break





SCREEN_WIDTH = 1024
SCREEN_HEIGHT = 640
rl.set_trace_log_level(rl.LOG_NONE)
rl.set_config_flags(rl.FLAG_WINDOW_HIGHDPI | rl.FLAG_WINDOW_RESIZABLE)
rl.init_window(SCREEN_WIDTH, SCREEN_HEIGHT, "Raylib Python - Basic 3D")
rl.set_target_fps(60)


currentState = None
initialState = None
finalState = None
exec_time = 0.0
objective_function = 0.0
true_state_value = 0.0
is_valid = False

is_optimizing = False
optimization_data = {
    "done": False,
    "finalState": None,
    "exec_time": 0.0,
    "objective_function": 0.0,
    "true_state_value": 0.0,
    "is_valid": False,
    "history": [],
    "error": None,
}

def run_optimization_worker(params):
    global optimization_data
    try:
        init_st = params["initial_state"]
        algo_name = params["algo_name"]
        hc_name = params["hc_name"]
        final = None
        dur = 0.0
        hist = []

        if algo_name == "Hill Climbing":
            if hc_name == "Steepest":
                hc = SteepestHillClimbing(init_st, params["max_iter"], params["step_size"], False)
                final = hc.optimize()
                dur = hc.execution_time
            elif hc_name == "Sideways":
                hc = SidewaysHillClimbing(init_st, params["max_iter"], params["step_size"], False, params["max_sideways"])
                final = hc.optimize()
                dur = hc.execution_time
            elif hc_name == "Random Restart":
                hc = RandomRestartHillClimbing(init_st, params["max_iter"], params["step_size"], False, params["max_restart"])
                final = hc.optimize()
                dur = hc.execution_time
            elif hc_name == "Stochastic":
                hc = StochasticHillClimbing(init_st, params["max_iter"], params["step_size"], params["temperature"], False)
                final = hc.optimize()
                dur = hc.execution_time
            if hc is not None and hasattr(hc, "history"):
                for entry in hc.history:
                    hist.append(entry['current_cost'])
        elif algo_name == "Simulated Annealing":
            sa = SimulatedAnnealing(
                init_st,
                params["sa_init_temp"],
                params["sa_cooling_rate"],
                params["sa_min_temp"],
                params["sa_max_iter"],
                params["sa_step_per_temp"],
                params["sa_schedule"],
                params["sa_step_size"],
                False
            )
            final = sa.optimize()
            dur = sa.execution_time
            if hasattr(sa, "history"):
                for entry in sa.history:
                    hist.append(entry['current_cost'])
        elif algo_name == "Genetic Algorithm":
            res = genetic_algorithm(
                init_st,
                params["ga_pop_size"],
                params["ga_generations"],
                params["ga_tour_size"],
                params["ga_crossover_prob"],
                params["ga_pkg_mutation"],
                params["ga_plcment_mutation"]
            )
            final = res.final_state
            dur = res.duration
            if hasattr(res, "history"):
                for entry in res.history:
                    hist.append(entry.best_feasible_fitness)

        if final is not None:
            optimization_data["finalState"] = final
            optimization_data["exec_time"] = dur
            optimization_data["objective_function"] = objectiveFunction(final)
            optimization_data["true_state_value"] = getTotalValue(final)
            optimization_data["is_valid"] = isValid(final)
            optimization_data["history"] = hist
            optimization_data["error"] = None
        optimization_data["done"] = True
    except Exception as e:
        optimization_data["error"] = str(e)
        optimization_data["done"] = True


hud = HUD()
result_view = ResultView(0, 0, 0, False)
# with open("output/output7.json", "w", encoding="utf-8") as file:
#     json.dump(currentState.to_dict(), file, indent=4, ensure_ascii=False)

# Muat file input awal secara otomatis jika tersedia
default_input_candidates = [
    os.path.join(BASE_DIR, "input", hud.input_file_text_entry.text),
    os.path.join("input", hud.input_file_text_entry.text),
]
for cand in default_input_candidates:
    if os.path.exists(cand):
        try:
            initialState = TruckState.from_json(cand)
            currentState = initialState
            hud.enable_disabled()
            break
        except Exception:
            pass

truck_w = currentState.truck.dimensions['w'] if currentState != None else 15
truck_l = currentState.truck.dimensions['l'] if currentState != None else 25
truck_h = currentState.truck.dimensions['h'] if currentState != None else 10

camera = rl.Camera3D(
    rl.Vector3(-truck_w*1.25, truck_h*1.75, -truck_l*1.25),
    rl.Vector3(truck_w*2, -truck_h*0.25, truck_l*1.5),
    rl.Vector3(0.0, 1.0, 0.0),
    45.0,
    rl.CAMERA_PERSPECTIVE
)

camera_mode = rl.CAMERA_PERSPECTIVE
history = []

while not rl.window_should_close():
    mouse_pos = get_ui_mouse_position()
    if mouse_pos.x > hud.bb.width and not (result_view.hasResult() and rl.check_collision_point_rec(mouse_pos, result_view.bb)):
        rl.update_camera(camera, camera_mode)
    rl.begin_drawing()
    rl.clear_background(rl.RAYWHITE)

    if rl.is_key_pressed(rl.KeyboardKey.KEY_V) :
        camera_mode = rl.CAMERA_FREE if camera_mode == rl.CAMERA_PERSPECTIVE else rl.CAMERA_PERSPECTIVE
    
    rl.begin_mode_3d(camera)
    rl.draw_grid(20, 1.0)
    rl.end_mode_3d()
    if currentState != None :
        drawTruckState(currentState, camera)
    
    hud.draw()
    if result_view.hasResult() :
        result_view.draw()

    # Worker status update and UI banners
    if is_optimizing:
        hud.run_btn.label = "Running..."
        hud.run_btn.color = rl.ORANGE
        hud.run_btn.hover_color = rl.ORANGE

        banner_w = 340
        banner_h = 36
        banner_x = int(hud.bb.width) + 15
        banner_y = 15
        rl.draw_rectangle(banner_x, banner_y, banner_w, banner_h, rl.fade(rl.BLACK, 0.75))
        dots = "." * ((int(rl.get_time() * 3) % 4) + 1)
        rl.draw_text(f"Optimizing in background{dots}", banner_x + 12, banner_y + 10, 16, rl.WHITE)

        if optimization_data["done"]:
            is_optimizing = False
            hud.run_btn.label = "Run"
            hud.run_btn.color = rl.LIGHTGRAY
            hud.run_btn.hover_color = rl.GRAY
            if optimization_data["error"]:
                print(f"Error during optimization: {optimization_data['error']}")
            elif optimization_data["finalState"] is not None:
                finalState = optimization_data["finalState"]
                currentState = finalState
                exec_time = optimization_data["exec_time"]
                objective_function = optimization_data["objective_function"]
                true_state_value = optimization_data["true_state_value"]
                is_valid = optimization_data["is_valid"]
                history = optimization_data["history"]
                result_view = ResultView(exec_time, objective_function, true_state_value, is_valid, history)
                print(f"Optimization finished in {exec_time:.3f}s | Obj: {objective_function:.2f} | Value: {true_state_value:.1f} | Valid: {is_valid}")

    resetState = False
    if is_optimizing:
        hud.command = ""
    elif (hud.command == "INPUT_INITIAL_STATE_FILE") :
        fname = hud.input_file_text_entry.text.strip()
        candidates = [
            os.path.join(BASE_DIR, "input", fname),
            os.path.join("input", fname),
            fname
        ]
        target_path = None
        for cand in candidates:
            if os.path.exists(cand):
                target_path = cand
                break
        if target_path:
            try:
                initialState = TruckState.from_json(target_path)
                currentState = initialState
                resetState = True
                result_view = ResultView(0, 0, 0, False)
                hud.enable_disabled()
            except Exception as e:
                print(f"Error loading state from {target_path}: {e}")
        else:
            print(f"File not found: {fname}")
    elif (hud.command == "RANDOM_INIT_STATE") :
        initialState = currentState.generate_random_state()
        currentState = initialState
        result_view = ResultView(0, 0, 0, False)
    elif (hud.command == "RUN") :
        if not is_optimizing and currentState is not None:
            try:
                result_view = ResultView(0, 0, 0, False)
                base_st = initialState if initialState is not None else currentState
                init_clone = base_st.clone() if hasattr(base_st, 'clone') else copy.deepcopy(base_st)
                params = {
                    "initial_state": init_clone,
                    "algo_name": hud.algorithm_switch.get_current_label(),
                    "hc_name": hud.hc_switch.get_current_label(),
                    "max_iter": int(hud.max_iter_text_entry.text),
                    "step_size": int(hud.step_size_text_entry.text),
                    "max_sideways": int(hud.max_sideways_move_text_entry.text),
                    "max_restart": int(hud.max_restart_text_entry.text),
                    "temperature": float(hud.temperature_text_entry.text),
                    "sa_init_temp": float(hud.sa_init_temp_text_entry.text),
                    "sa_cooling_rate": float(hud.sa_cooling_rate_text_entry.text),
                    "sa_min_temp": float(hud.sa_min_temp_text_entry.text),
                    "sa_max_iter": int(hud.sa_max_iter_text_entry.text),
                    "sa_step_per_temp": int(hud.sa_step_per_temp_text_entry.text),
                    "sa_schedule": hud.sa_schedule_switch.get_current_label(),
                    "sa_step_size": int(hud.sa_step_size_text_entry.text),
                    "ga_pop_size": int(hud.ga_population_size_text_entry.text),
                    "ga_generations": int(hud.ga_generations_text_entry.text),
                    "ga_tour_size": int(hud.ga_tour_size_text_entry.text),
                    "ga_crossover_prob": float(hud.ga_crossover_prob_text_entry.text),
                    "ga_pkg_mutation": float(hud.ga_pkg_mutation_prob_text_entry.text),
                    "ga_plcment_mutation": float(hud.ga_plcment_mutation_prob_text_entry.text),
                }
                is_optimizing = True
                optimization_data["done"] = False
                optimization_data["error"] = None
                opt_thread = threading.Thread(target=run_optimization_worker, args=(params,), daemon=True)
                opt_thread.start()
            except Exception as e:
                print(f"Error starting optimization thread: {e}")

    if resetState :
        truck_w = currentState.truck.dimensions['w'] if currentState != None else 15
        truck_l = currentState.truck.dimensions['l'] if currentState != None else 25
        truck_h = currentState.truck.dimensions['h'] if currentState != None else 10

        camera = rl.Camera3D(
            rl.Vector3(-truck_w*1.25, truck_h*1.75, -truck_l*1.25),
            rl.Vector3(truck_w*2, -truck_h*0.25, truck_l*1.5),
            rl.Vector3(0.0, 1.0, 0.0),
            45.0,
            rl.CAMERA_PERSPECTIVE
        )

        camera_mode = rl.CAMERA_PERSPECTIVE
    hud.command = ""
    


    rl.end_drawing()

rl.close_window()
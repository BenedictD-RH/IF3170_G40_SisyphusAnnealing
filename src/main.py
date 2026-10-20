import os
import sys
import math

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
    
    hovered_box = None

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

            if collision.hit and not hovered_box:
                hovered_box = (x1 + w/2, z1 + h/2, y1 + l/2, p.getStateString(), False)

    # Tampilkan box yang loss (di luar peti kemas truk)
    lost_y = 0.0
    for p in state.packages :
        if not p.isInTruck(state.truck.dimensions) :
            w = p.package.dimensions[p.orientation["x"]]
            l = p.package.dimensions[p.orientation["y"]]
            h = p.package.dimensions[p.orientation["z"]]
            
            x1 = -w - 3.0
            z1 = 0.0
            y1 = lost_y
            x2 = -3.0
            z2 = h
            y2 = lost_y + l
            lost_y += l + 1.5

            if p.getID() not in color_dict :
                color_dict[p.getID()] = rl.Color(
                    rl.get_random_value(0, 255),
                    rl.get_random_value(0, 255),
                    rl.get_random_value(0, 255),
                    255)

            loss_color = rl.fade(color_dict[p.getID()], 0.35)
            package_bb = rl.BoundingBox((x1, z1, y1), (x2, z2, y2))
            collision = rl.get_ray_collision_box(ray, package_bb)

            rl.draw_cube((x1 + w/2, z1 + h/2, y1 + l/2), w, h, l, loss_color)
            rl.draw_cube_wires((x1 + w/2, z1 + h/2, y1 + l/2), w, h, l, rl.YELLOW if collision.hit else rl.RED)

            if collision.hit and not hovered_box:
                loss_info_str = f"STATUS: [LOSS / UNLOADED]\n" + p.getStateString()
                hovered_box = (x1 + w/2, z1 + h/2, y1 + l/2, loss_info_str, True)

    rl.end_mode_3d()

    if hovered_box and mouse_pos.x > hud.bb.width and not (result_view.hasResult() and rl.check_collision_point_rec(get_ui_mouse_position(), result_view.bb)):
        cx, cy, cz, txt, is_loss = hovered_box
        screenPos = rl.get_world_to_screen((cx, cy, cz), camera)
        card_h = 185 if is_loss else 165
        rl.draw_rectangle(int(screenPos.x), int(screenPos.y), 310, card_h, rl.LIGHTGRAY)
        rl.draw_rectangle_lines(int(screenPos.x), int(screenPos.y), 310, card_h, rl.RED if is_loss else rl.GRAY)
        rl.draw_text(txt, int(screenPos.x) + 5, int(screenPos.y) + 5, 17, rl.MAROON if is_loss else rl.BLACK)





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
    "stuck_info": None,
    "benchmark_row": None,
    "loss_details": None,
    "error": None,
}


def _safe_int(val, default):
    try:
        return int(str(val).strip())
    except Exception:
        return default

def _safe_float(val, default):
    try:
        return float(str(val).strip())
    except Exception:
        return default


def run_optimization_worker(params):
    global optimization_data
    try:
        init_st = params["initial_state"]
        algo_name = params["algo_name"]
        hc_name = params["hc_name"]
        final = None
        dur = 0.0
        hist = []
        stuck_info = None
        algo_display_name = algo_name
        accepted_moves = 0
        sa_stuck_table_str = "-"
        iterations = params.get("max_iter", 1000)

        if algo_name == "Hill Climbing":
            if hc_name == "Steepest":
                hc = SteepestHillClimbing(init_st, params["max_iter"], params["step_size"], False)
                final = hc.optimize()
                dur = hc.execution_time
                algo_display_name = "Steepest HC"
                accepted_moves = getattr(hc, "accepted_moves", 0)
                iterations = params["max_iter"]
            elif hc_name == "Sideways":
                hc = SidewaysHillClimbing(init_st, params["max_iter"], params["step_size"], False, params["max_sideways"])
                final = hc.optimize()
                dur = hc.execution_time
                algo_display_name = f"Sideways HC (max={params['max_sideways']})"
                accepted_moves = getattr(hc, "accepted_moves", 0)
                iterations = params["max_iter"]
            elif hc_name == "Random Restart":
                hc = RandomRestartHillClimbing(init_st, params["max_iter"], params["step_size"], False, params["max_restart"])
                final = hc.optimize()
                dur = hc.execution_time
                algo_display_name = f"Random Restart HC (max={params['max_restart']})"
                accepted_moves = getattr(hc, "accepted_moves", 0)
                iterations = getattr(hc, "total_iterations", params["max_iter"])
            elif hc_name == "Stochastic":
                hc = StochasticHillClimbing(init_st, params["max_iter"], params["step_size"], params["temperature"], False)
                final = hc.optimize()
                dur = hc.execution_time
                algo_display_name = f"Stochastic HC (T={params['temperature']})"
                accepted_moves = getattr(hc, "accepted_moves", 0)
                iterations = params["max_iter"]
            if hc is not None and hasattr(hc, "history"):
                if hc_name == "Random Restart":
                    hist = {
                        "iteration": [entry["iteration"] for entry in hc.history],
                        "current": [entry["current_cost"] for entry in hc.history],
                        "run_iterations": hc.run_iterations
                    }
                else:
                    for entry in hc.history:
                        hist.append(entry['current_cost'])
        elif algo_name == "Simulated Annealing":
            iterations = params["sa_max_iter"]
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
            accepted_moves = getattr(sa, "accepted_moves", getattr(sa, "accepted_better_moves", 0) + getattr(sa, "accepted_worse_moves", 0))
            sched = str(params["sa_schedule"])
            if sched.lower() == "geometric":
                algo_display_name = f"Simulated Annealing (T0={params['sa_init_temp']:.0f}, alpha={params['sa_cooling_rate']})"
            elif sched.lower() == "linear":
                algo_display_name = f"Simulated Annealing (T0={params['sa_init_temp']:.0f}, Linear)"
            elif sched.lower() == "logarithmic":
                algo_display_name = f"Simulated Annealing (T0={params['sa_init_temp']:.0f}, Logarithmic)"
            else:
                algo_display_name = f"Simulated Annealing (T0={params['sa_init_temp']:.0f}, {sched})"

            if hasattr(sa, "history"):
                objectives = [entry['current_cost'] for entry in sa.history]
                probabilities = [entry.get('probability', 1.0) for entry in sa.history]
                stuck_data = sa.get_stuck_metrics()
                stuck_info = f"{stuck_data['stuck_episodes']}x ({stuck_data['rejected_moves']} rej)"
                sa_stuck_table_str = f"{stuck_data['stuck_episodes']:.1f} eps ({stuck_data['rejection_rate']:.1f}% rej)"
                hist = {
                    "algo": "Simulated Annealing",
                    "objectives": objectives,
                    "probabilities": probabilities,
                    "stuck_metrics": stuck_data
                }
        elif algo_name == "Genetic Algorithm":
            iterations = params["ga_generations"]
            algo_display_name = f"Genetic Algorithm (pop={params['ga_pop_size']}, gen={params['ga_generations']})"
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
            accepted_moves = len(res.history) if hasattr(res, "history") else 0
            if hasattr(res, "history"):
                hist = {"maximum": [entry.maximum_fitness for entry in res.history],
                        "mean": [entry.mean_fitness for entry in res.history],
                        "best_feasible": [s.best_feasible_fitness for s in res.history]}

        if final is not None:
            init_cost = objectiveFunction(init_st)
            best_cost = objectiveFunction(final)
            imprv = best_cost - init_cost

            truck_dims = final.truck.dimensions
            max_cap = final.truck.maxCapacity
            total_pkgs = len(final.packages)
            loaded_pkgs = [p for p in final.packages if p.isInTruck(truck_dims)]
            lost_pkgs = [p for p in final.packages if not p.isInTruck(truck_dims)]

            total_loaded_weight = sum(p.getWeight() for p in loaded_pkgs)
            total_loaded_value = sum(p.getValue() for p in loaded_pkgs)
            total_lost_value = sum(p.getValue() for p in lost_pkgs)
            total_potential_value = total_loaded_value + total_lost_value

            loss_details = {
                "total_packages": total_pkgs,
                "loaded_count": len(loaded_pkgs),
                "lost_count": len(lost_pkgs),
                "lost_ids": [p.getID() for p in lost_pkgs],
                "loaded_ids": [p.getID() for p in loaded_pkgs],
                "total_loaded_weight": total_loaded_weight,
                "max_capacity": max_cap,
                "total_loaded_value": total_loaded_value,
                "total_lost_value": total_lost_value,
                "total_potential_value": total_potential_value,
                "is_valid": isValid(final)
            }

            optimization_data["finalState"] = final
            optimization_data["exec_time"] = dur
            optimization_data["objective_function"] = best_cost
            optimization_data["true_state_value"] = getTotalValue(final)
            optimization_data["is_valid"] = isValid(final)
            optimization_data["history"] = hist
            optimization_data["stuck_info"] = stuck_info
            optimization_data["loss_details"] = loss_details
            optimization_data["benchmark_row"] = {
                "name": algo_display_name,
                "filename": params.get("filename", "initial_state.json"),
                "packages_count": len(init_st.packages),
                "capacity": init_st.truck.maxCapacity,
                "iterations": iterations,
                "avg_init": init_cost,
                "avg_best": best_cost,
                "max_best": best_cost,
                "improvement": imprv,
                "avg_accepted": float(accepted_moves),
                "avg_time": dur,
                "sa_stuck_info": sa_stuck_table_str
            }
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
    rl.Vector3(-truck_w*1.5, truck_h*2.0, -truck_l*1.5),
    rl.Vector3(truck_w/2.0, truck_h/2.0, truck_l/2.0),
    rl.Vector3(0.0, 1.0, 0.0),
    45.0,
    rl.CAMERA_PERSPECTIVE
)

history = []

while not rl.window_should_close():
    mouse_pos = get_ui_mouse_position()
    in_viewport = mouse_pos.x > hud.bb.width and not (result_view.hasResult() and rl.check_collision_point_rec(mouse_pos, result_view.bb))

    mouse_delta = rl.get_mouse_delta()
    wheel = rl.get_mouse_wheel_move()
    if wheel == 0.0 and hasattr(rl, 'get_mouse_wheel_move_v'):
        try:
            wheel_v = rl.get_mouse_wheel_move_v()
            if hasattr(wheel_v, 'y') and wheel_v.y != 0.0:
                wheel = wheel_v.y
        except Exception:
            pass

    is_rotating = in_viewport and (
        rl.is_mouse_button_down(rl.MouseButton.MOUSE_BUTTON_RIGHT) or
        rl.is_mouse_button_down(rl.MouseButton.MOUSE_BUTTON_LEFT)
    )
    is_panning = in_viewport and (
        rl.is_mouse_button_down(rl.MouseButton.MOUSE_BUTTON_MIDDLE) or
        (rl.is_key_down(rl.KeyboardKey.KEY_LEFT_SHIFT) and rl.is_mouse_button_down(rl.MouseButton.MOUSE_BUTTON_RIGHT))
    )

    dx = camera.position.x - camera.target.x
    dy = camera.position.y - camera.target.y
    dz = camera.position.z - camera.target.z
    radius = math.sqrt(dx * dx + dy * dy + dz * dz)
    if radius < 0.001:
        radius = 1.0

    theta = math.atan2(dz, dx)
    phi = math.asin(max(-0.999, min(0.999, dy / radius)))

    if is_rotating and not is_panning and (mouse_delta.x != 0 or mouse_delta.y != 0):
        sensitivity = 0.008
        theta -= mouse_delta.x * sensitivity
        phi += mouse_delta.y * sensitivity
        max_phi = math.pi / 2.0 - 0.02
        phi = max(-max_phi, min(max_phi, phi))

    # Scroll up & down: Zoom in / Zoom out via wheel
    shift_pressed = rl.is_key_down(rl.KeyboardKey.KEY_LEFT_SHIFT) or rl.is_key_down(rl.KeyboardKey.KEY_RIGHT_SHIFT)
    if in_viewport and wheel != 0 and not shift_pressed:
        zoom_speed = max(1.2, radius * 0.12)
        radius = max(3.0, radius - wheel * zoom_speed)

    # Scroll up & down: Vertically scroll camera height via Shift+wheel or UP/DOWN / PageUp/PageDown
    vert_scroll = 0.0
    if in_viewport and wheel != 0 and shift_pressed:
        vert_scroll += wheel * 1.5

    if rl.is_key_down(rl.KeyboardKey.KEY_UP) or rl.is_key_down(rl.KeyboardKey.KEY_PAGE_UP):
        vert_scroll += 0.5
    if rl.is_key_down(rl.KeyboardKey.KEY_DOWN) or rl.is_key_down(rl.KeyboardKey.KEY_PAGE_DOWN):
        vert_scroll -= 0.5

    if vert_scroll != 0.0:
        camera.target.y += vert_scroll
        camera.position.y += vert_scroll

    cos_phi = math.cos(phi)
    new_pos_x = camera.target.x + radius * cos_phi * math.cos(theta)
    new_pos_y = camera.target.y + radius * math.sin(phi)
    new_pos_z = camera.target.z + radius * cos_phi * math.sin(theta)

    if is_panning and (mouse_delta.x != 0 or mouse_delta.y != 0):
        pan_factor = 0.003 * radius
        right_x = math.sin(theta)
        right_z = -math.cos(theta)
        pan_dx = (-mouse_delta.x * right_x) * pan_factor
        pan_dz = (-mouse_delta.x * right_z) * pan_factor
        pan_dy = (mouse_delta.y) * pan_factor
        camera.target.x += pan_dx
        camera.target.y += pan_dy
        camera.target.z += pan_dz
        new_pos_x += pan_dx
        new_pos_y += pan_dy
        new_pos_z += pan_dz

    camera.position.x = new_pos_x
    camera.position.y = new_pos_y
    camera.position.z = new_pos_z

    if rl.is_key_pressed(rl.KeyboardKey.KEY_R):
        tw = currentState.truck.dimensions['w'] if currentState != None else 15
        tl = currentState.truck.dimensions['l'] if currentState != None else 25
        th = currentState.truck.dimensions['h'] if currentState != None else 10
        camera.target = rl.Vector3(tw / 2.0, th / 2.0, tl / 2.0)
        camera.position = rl.Vector3(-tw * 1.5, th * 2.0, -tl * 1.5)

    rl.begin_drawing()
    rl.clear_background(rl.RAYWHITE)
    
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
                stuck_info = optimization_data.get("stuck_info")
                loss_details = optimization_data.get("loss_details")
                result_view = ResultView(exec_time, objective_function, true_state_value, is_valid, history, stuck_info, loss_details)
                row = optimization_data.get("benchmark_row")
                if row:
                    header = f"{'Algoritma':<42} | {'Avg Init':>9} | {'Avg Best':>9} | {'Max Best':>9} | {'Avg Imprv':>9} | {'Avg Acc':>7} | {'Avg Time':>9} | {'SA Stuck':>15}"
                    sep = "=" * len(header)
                    banner = f" BENCHMARK OPTIMASI: {row['filename']} | {row['packages_count']} Kotak | Kapasitas: {row['capacity']} | Iterasi: {row['iterations']}"
                    divider = "-" * len(header)
                    row_str = (
                        f"{row['name']:<42} | {row['avg_init']:>9.2f} | {row['avg_best']:>9.2f} | {row['max_best']:>9.2f} | "
                        f"{row['improvement']:>+9.2f} | {row['avg_accepted']:>7.1f} | {row['avg_time']:>8.4f}s | {row['sa_stuck_info']:>15}"
                    )
                    
                    lines = [
                        "",
                        sep,
                        banner,
                        sep,
                        header,
                        divider,
                        row_str,
                        sep
                    ]

                    if loss_details:
                        pct_loaded = (loss_details['loaded_count'] / loss_details['total_packages'] * 100) if loss_details['total_packages'] > 0 else 0
                        pct_lost = (loss_details['lost_count'] / loss_details['total_packages'] * 100) if loss_details['total_packages'] > 0 else 0
                        lost_id_str = str(loss_details['lost_ids']) if loss_details['lost_ids'] else "None (Semua Termuat)"
                        lines.extend([
                            " Detail Muatan & Box Loss:",
                            f" - Kotak Termuat (Loaded) : {loss_details['loaded_count']} / {loss_details['total_packages']} ({pct_loaded:.1f}%)",
                            f" - Kotak Loss (Unloaded)  : {loss_details['lost_count']} / {loss_details['total_packages']} ({pct_lost:.1f}%)",
                            f" - Total Nilai Loss       : {loss_details['total_lost_value']:,.1f} (dari total nilai potensial {loss_details['total_potential_value']:,.1f})",
                            f" - Nilai Aktual Terangkut : {true_state_value:,.1f}",
                            f" - Daftar ID Box Loss     : {lost_id_str}",
                            f" - Bobot Terangkut        : {loss_details['total_loaded_weight']} / {loss_details['max_capacity']}",
                            f" - Status Solusi          : {'Valid (Memenuhi Batasan)' if loss_details['is_valid'] else 'Invalid (Ada Pelanggaran)'}",
                            sep
                        ])

                    benchmark_output = "\n".join(lines) + "\n"
                    print(benchmark_output)
                    try:
                        out_dir = os.path.join(BASE_DIR, "output")
                        os.makedirs(out_dir, exist_ok=True)
                        with open(os.path.join(out_dir, "result.txt"), "a", encoding="utf-8") as f:
                            f.write(benchmark_output + "\n")
                    except Exception:
                        pass
                else:
                    stuck_log = f" | SA Stuck: {stuck_info}" if stuck_info else ""
                    print(f"Optimization finished in {exec_time:.3f}s | Obj: {objective_function:.2f} | Value: {true_state_value:.1f} | Valid: {is_valid}{stuck_log}")

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
        hud.enable_disabled()
    elif (hud.command == "RUN") :
        if not is_optimizing and currentState is not None:
            try:
                result_view = ResultView(0, 0, 0, False)
                base_st = initialState if initialState is not None else currentState
                init_clone = base_st.clone() if hasattr(base_st, 'clone') else copy.deepcopy(base_st)
                params = {
                    "filename": hud.input_file_text_entry.text.strip(),
                    "initial_state": init_clone,
                    "algo_name": hud.algorithm_switch.get_current_label(),
                    "hc_name": hud.hc_switch.get_current_label(),
                    "max_iter": _safe_int(hud.max_iter_text_entry.text, 1000),
                    "step_size": _safe_int(hud.step_size_text_entry.text, 2),
                    "max_sideways": _safe_int(hud.max_sideways_move_text_entry.text, 100),
                    "max_restart": _safe_int(hud.max_restart_text_entry.text, 10),
                    "temperature": _safe_float(hud.temperature_text_entry.text, 1.0),
                    "sa_init_temp": _safe_float(hud.sa_init_temp_text_entry.text, 1000.0),
                    "sa_cooling_rate": _safe_float(hud.sa_cooling_rate_text_entry.text, 0.995),
                    "sa_min_temp": _safe_float(hud.sa_min_temp_text_entry.text, 0.001),
                    "sa_max_iter": _safe_int(hud.sa_max_iter_text_entry.text, 1000),
                    "sa_step_per_temp": _safe_int(hud.sa_step_per_temp_text_entry.text, 1),
                    "sa_schedule": hud.sa_schedule_switch.get_current_label(),
                    "sa_step_size": _safe_int(hud.sa_step_size_text_entry.text, 2),
                    "ga_pop_size": _safe_int(hud.ga_population_size_text_entry.text, 100),
                    "ga_generations": _safe_int(hud.ga_generations_text_entry.text, 200),
                    "ga_tour_size": _safe_int(hud.ga_tour_size_text_entry.text, 3),
                    "ga_crossover_prob": _safe_float(hud.ga_crossover_prob_text_entry.text, 0.8),
                    "ga_pkg_mutation": _safe_float(hud.ga_pkg_mutation_prob_text_entry.text, 0.2),
                    "ga_plcment_mutation": _safe_float(hud.ga_plcment_mutation_prob_text_entry.text, 0.05),
                }
                is_optimizing = True
                optimization_data["done"] = False
                optimization_data["error"] = None
                opt_thread = threading.Thread(target=run_optimization_worker, args=(params,), daemon=True)
                opt_thread.start()
            except Exception as e:
                print(f"Error starting optimization thread: {e}")

    if resetState:
        truck_w = currentState.truck.dimensions['w'] if currentState != None else 15
        truck_l = currentState.truck.dimensions['l'] if currentState != None else 25
        truck_h = currentState.truck.dimensions['h'] if currentState != None else 10

        camera = rl.Camera3D(
            rl.Vector3(-truck_w * 1.5, truck_h * 2.0, -truck_l * 1.5),
            rl.Vector3(truck_w / 2.0, truck_h / 2.0, truck_l / 2.0),
            rl.Vector3(0.0, 1.0, 0.0),
            45.0,
            rl.CAMERA_PERSPECTIVE
        )
    hud.command = ""
    


    rl.end_drawing()

rl.close_window()
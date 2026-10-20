from data_struct.data_struct import TruckState, objectiveFunction, isValid, getTotalValue
from algorithm import SteepestHillClimbing, SidewaysHillClimbing, RandomRestartHillClimbing, StochasticHillClimbing, SimulatedAnnealing, genetic_algorithm
from view.view_elements import TextEntry, Button, HUD, ResultView
import pyray as rl
import matplotlib.pyplot as plt
import json



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

            if collision.hit and mouse_pos.x > hud.bb.width:
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
# hc = SteepestHillClimbing(initialState, max_iterations=1000, random_init=False, step_size=20)
# currentState = hc.optimize()
# print(objectiveFunction(currentState))
# print(getTotalValue(currentState))
# print(getTotalWeight(currentState))
# print("Execution time: ", hc.execution_time, "s")


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
    if mouse_pos.x > hud.bb.width:
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

    resetState = False
    if (hud.command == "INPUT_INITIAL_STATE_FILE") :
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
                hud.enable_disabled()
            except Exception as e:
                print(f"Error loading state from {target_path}: {e}")
        else:
            print(f"File not found: {fname}")
    elif (hud.command == "RANDOM_INIT_STATE") :
        initialState = currentState.generate_random_state()
        currentState = initialState
    elif (hud.command == "RUN") :
        hc = None
        history = []
        if hud.algorithm_switch.get_current_label() == "Hill Climbing" :
            if hud.hc_switch.get_current_label() == "Steepest" :
                hc = SteepestHillClimbing(initialState, 
                                          int(hud.max_iter_text_entry.text), 
                                          int(hud.step_size_text_entry.text),
                                          False)
                finalState = hc.optimize()
            elif hud.hc_switch.get_current_label() == "Sideways" :
                hc = SidewaysHillClimbing(initialState, 
                                        int(hud.max_iter_text_entry.text), 
                                        int(hud.step_size_text_entry.text),
                                        False,
                                        int(hud.max_sideways_move_text_entry.text))
                finalState = hc.optimize()
            elif hud.hc_switch.get_current_label() == "Random Restart" :
                hc = RandomRestartHillClimbing(initialState, 
                                        int(hud.max_iter_text_entry.text), 
                                        int(hud.step_size_text_entry.text),
                                        False,
                                        int(hud.max_restart_text_entry.text))
                finalState = hc.optimize()
            elif hud.hc_switch.get_current_label() == "Stochastic" :
                hc = StochasticHillClimbing(initialState, 
                                        int(hud.max_iter_text_entry.text), 
                                        int(hud.step_size_text_entry.text),
                                        float(hud.temperature_text_entry.text),
                                        False)
                finalState = hc.optimize()
            exec_time = hc.execution_time
            for entry in hc.history :
                history.append(entry['current_cost'])
        elif hud.algorithm_switch.get_current_label() == "Simulated Annealing" :
            sa = SimulatedAnnealing(initialState,
                                    int(hud.sa_init_temp_text_entry.text),
                                    float(hud.sa_cooling_rate_text_entry.text),
                                    float(hud.sa_min_temp_text_entry.text),
                                    int(hud.sa_max_iter_text_entry.text),
                                    int(hud.sa_step_per_temp_text_entry.text),
                                    hud.sa_schedule_switch.get_current_label(),
                                    int(hud.sa_step_size_text_entry.text), 
                                    False)
            finalState = sa.optimize()
            exec_time = sa.execution_time
            for entry in sa.history :
                history.append(entry['current_cost'])
        elif hud.algorithm_switch.get_current_label() == "Genetic Algorithm" :
            result = genetic_algorithm(initialState,
                                       int(hud.ga_population_size_text_entry.text),
                                       int(hud.ga_generations_text_entry.text),
                                       int(hud.ga_tour_size_text_entry.text),
                                       float(hud.ga_crossover_prob_text_entry.text),
                                       float(hud.ga_pkg_mutation_prob_text_entry.text),
                                       float(hud.ga_plcment_mutation_prob_text_entry.text))
            finalState = result.final_state
            exec_time = result.duration
            for entry in result.history :
                history.append(entry.best_feasible_fitness)
        objective_function = objectiveFunction(finalState)
        true_state_value = getTotalValue(finalState)
        is_valid = isValid(finalState) 
        currentState = finalState
        result_view = ResultView(exec_time, objective_function, true_state_value, is_valid, history)

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
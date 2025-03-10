import eventlet
eventlet.monkey_patch()

from flask import Flask, render_template, request, jsonify, Response
from flask_socketio import SocketIO, emit
import threading
import pygame
import io, base64
from PIL import Image
import config
import os
os.environ["SDL_VIDEODRIVER"] = "dummy"  # Force headless mode

import main as sim


from soil import SOIL_TYPES, SEASONS

app = Flask(__name__)
socketio = SocketIO(app, async_mode='eventlet')

@app.route('/')
def index():
    return render_template('index.html')
def capture_frame():
    frame_str = pygame.image.tostring(sim.screen, 'RGB')
    image = Image.frombytes('RGB', sim.SCREEN_SIZE, frame_str)
    byte_io = io.BytesIO()
    image.save(byte_io, 'JPEG')
    data = byte_io.getvalue()
    return base64.b64encode(data).decode('utf-8')

def frame_emitter():
    while True:
        try:
            # print("Capturing frame now...")
            frame_data = capture_frame()
            # print("Frame length:", len(frame_data))
            socketio.emit('frame', {'data': frame_data})
        except Exception as e:
            print("Error in frame_emitter:", e)
        socketio.sleep(0.2)




@socketio.on('connect')
def on_connect():
    print("Client connected via SocketIO")



# @app.route('/')
# def index():
#     return render_template('index.html')

# def capture_frame():
#     with sim.screen_lock:
#         surface_copy = screen.copy()
#         pygame.image.save(surface_copy, "debug_frame.jpg")  # Save frame
        
#         try:
#             frame_str = pygame.image.tostring(surface_copy, 'RGB')
#             image = Image.frombytes('RGB', sim.SCREEN_SIZE, frame_str)
#             byte_io = io.BytesIO()
#             image.save(byte_io, 'JPEG')
#             byte_io.seek(0)
#             print("Frame successfully converted to string")  # Debugging
#             return byte_io
#         except Exception as e:
#             print("Error converting frame:", e)
#             return None



@app.route('/video_feed')
def video_feed():
    def generate():
        while True:
            frame = capture_frame()
            yield (b'--frame\r\n'
                   b'Content-Type: image/jpeg\r\n\r\n' + frame.read() + b'\r\n')
    return Response(generate(), mimetype='multipart/x-mixed-replace; boundary=frame')

@app.route('/set_overlay', methods=['POST'])
def set_overlay():
    data = request.get_json()
    mode = data.get('mode', None)  
    sim.set_overlay_mode(mode)
    print("Overlay mode set to", mode)
    return '', 204


@app.route('/mouse_event', methods=['POST'])
def mouse_event():
    data = request.get_json()
    mouse_x = data['x']
    mouse_y = data['y']
    size = int(data.get('size', 4))
    seed_type = data.get('seed_type', 'normal')
    print(f"Mouse event type: {data['type']} / seed_type: {seed_type}")
    if data.get('type') == 'water':
        sim.water_blocks.append(sim.WaterBlock(mouse_x, mouse_y, size))
    else:
        sim.seeds.append(sim.Seed(mouse_x, mouse_y))
    return '', 204

@app.route('/set_soil_type', methods=['POST'])
def set_soil_type():
    data = request.get_json()
    soil_type = data['soil_type']
    if soil_type in SOIL_TYPES:
        sim.set_soil_type(soil_type)
        print(f"Soil type set to {soil_type}")
    return '', 204

@app.route('/update_mouse', methods=['POST'])
def update_mouse():
    data = request.get_json()

    sim.soil_info_pos = (data.get('x', 0), data.get('y', 0))
  
    return jsonify({"status": "ok"})


@app.route('/toggle_soil_info', methods=['POST'])
def toggle_soil_info():
  
    sim.display_info_mode = not sim.display_info_mode
    print("Toggled display_info_mode to", sim.display_info_mode)
    return jsonify({"display_info": sim.display_info_mode})

@app.route('/set_season', methods=['POST'])
def set_season():
    data = request.get_json()
    season = data['season']
    if season in SEASONS:
        sim.set_season(season)
        print(f"Season set to {season}")
    return '', 204

@app.route('/set_time_of_day', methods=['POST'])
def set_time_of_day():
    data = request.get_json()
    time_value = data.get('time', 0)
    sim.set_time_of_day(time_value)
    print(f"Time of day set to {time_value}")
    return '', 204

@app.route('/reset_simulation', methods=['POST'])
def reset_simulation():
    sim.seeds.clear()
    sim.water_blocks.clear()
    print("Simulation reset")
    return '', 204

@app.route('/start_simulation', methods=['POST'])
def start_simulation():
    sim.start_simulation()
    print("Simulation started")
    return '', 204

@app.route('/pause_simulation', methods=['POST'])
def pause_simulation():
    sim.pause_simulation()
    print("Simulation paused")
    return '', 204

@app.route('/get_plant_stats', methods=['GET'])
def get_plant_stats():
    stats_list = []
    for seed in sim.seeds:
        if seed.plant is not None:
            if seed.plant.alive:
                if seed.hydration >= seed.saturation_ratio:
                    stats_list.append(seed.plant.get_stats())
                else:
                    stats_list.append(seed.get_stats())
            else:
                stats_list.append({
                    "plant_type": seed.plant.plant_type,
                    "stage": seed.plant.stage,
                    "resource_status": "Dead",
                    "time_to_germinate": seed.time_to_germinate,
                    "health": "dead",
                    "weight": 0,
                    "height": 0,
                    "root_depth": 0,
                    "age": seed.age
                })
        else:
            # Handle seeds that haven't germinated or don't have a plant
            stats_list.append({
                "plant_type": "seed",
                "stage": "Not germinated",
                "resource_status": "Not germinated",
                "time_to_germinate": seed.time_to_germinate,
                "health": "N/A",
                "weight": 0,
                "height": 0,
                "root_depth": 0,
                "age": seed.age
            })
    return jsonify(stats_list)




@app.route('/set_rain', methods=['POST'])
def set_rain():
    data = request.get_json()
    sim.raining = data.get('raining', sim.raining)
    if 'rain_intensity' in data:
        sim.rain_intensity = data['rain_intensity']
    return jsonify({"raining": sim.raining, "rain_intensity": sim.rain_intensity})


@app.route('/set_time_scale', methods=['POST'])
def set_time_scale():
    data = request.get_json()
    preset = data.get('preset', None)

    preset_values = {
        "normal": 600 / 2,     
        "fast": 600 / 1,       
        "ultra_fast": 600 / 0.5 
    }
    if preset in preset_values:
        import config
        config.TIME_SCALE = preset_values[preset]
        print("Time scale updated to", config.TIME_SCALE, "for preset", preset)
        return '', 204
    else:
        return jsonify({"error": "Invalid preset"}), 400

@app.route('/set_temperature', methods=['POST'])
def set_temperature():
    data = request.get_json()
    new_temp = data.get('temperature', None)
    if new_temp is not None:
        try:
            new_temp = float(new_temp)
            
            from weather import SEASONS, current_season
            SEASONS[current_season]['temperature'] = new_temp
            print("Temperature updated to", new_temp)
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    return '', 204


@app.route('/set_ph', methods=['POST'])
def set_ph():
    data = request.get_json()
    new_ph = data.get('ph', None)
    if new_ph is not None:
        try:
            new_ph = float(new_ph)
   
            import soil
            soil.SOILPH = new_ph
            print("Soil pH updated to", new_ph)
        except Exception as e:
            return jsonify({'error': str(e)}), 400
    return '', 204


@app.route('/get_environment_info', methods=['GET'])
def get_environment_info():

    from weather import SEASONS, current_season, sun
    import soil
 
    grid = soil.soil_properties['grid']
    total_moisture = 0
    cells_count = 0
    for row in grid:
        for cell in row:
            total_moisture += cell.get('moisture', 0)
            cells_count += 1

    conversion_factor = 0.5 
    precipitation_value = sim.rain_intensity * conversion_factor if sim.raining else 0
    precipitation = f"{precipitation_value:.1f} mm/h"
    avg_moisture = total_moisture / cells_count if cells_count > 0 else 0

    info = {
        "temperature": SEASONS[current_season]['temperature'],
        "hours_of_daylight": SEASONS[current_season].get('light_hours', sun.day_length),
        "precipitation": precipitation, 
        "average_moisture": round(avg_moisture, 2), 
        "soil_ph": soil.SOILPH
    }
    return jsonify(info)


def run_flask():
        port = int(os.environ.get("PORT", 5000))
        socketio.run(app, host="0.0.0.0", port=port, debug=False, use_reloader=False)
        
# Start background tasks using Socket.IO's built-in support.
socketio.start_background_task(frame_emitter)
socketio.start_background_task(sim.game_loop)


# if __name__ == '__main__':
#     run_flask()
#     sim.game_loop()

if __name__ == '__main__':
    # Initialize Pygame display in the main thread
    # pygame.init()
    # sim.screen = pygame.display.set_mode(config.SCREEN_SIZE)
    # sim.clock = pygame.time.Clock()

    # Start Flask server in a background thread
    run_flask()
    flask_thread = threading.Thread(target=run_flask, daemon=True)
    flask_thread.start()

    # Start the frame emitter as a background task
    socketio.start_background_task(frame_emitter)
socketio.start_background_task(sim.game_loop)
    # # Now run your game loop (from main.py) in the main thread.
    # sim.game_loop()

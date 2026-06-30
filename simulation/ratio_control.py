import random
from collections import deque
from simulation.pid import PID

class RatioControlSimulation:
    def __init__(self):
        # Configuration
        self.max_colorant_flow = 15.0  # L/min
        self.nominal_milk_flow = 50.0  # L/min
        self.valve_tau = 0.8           # Valve time constant (seconds)
        self.sensor_delay_sec = 2.0    # Transport delay from mixing point to TCS3200 (seconds)
        
        # PIDs
        # Slave controller for colorant flow rate
        self.pid_flow = PID(kp=2.5, ki=1.5, kd=0.1, setpoint=0.0, output_limits=(0.0, 100.0))
        
        # State variables
        self.time = 0.0
        self.milk_flow = self.nominal_milk_flow
        self.valve_position = 0.0      # % (actual valve opening)
        self.valve_output = 0.0        # % (controller output)
        self.colorant_flow = 0.0       # L/min (actual flow)
        
        # Target parameters
        self.target_ratio = 0.10       # Default ratio (pewarna / susu)
        self.colorant_flow_sp = 0.0    # Target flow rate (L/min)
        
        # Delay queue for TCS3200 sensor
        self.delay_steps = int(self.sensor_delay_sec / 0.1)
        self.ratio_history = deque([0.0] * self.delay_steps, maxlen=self.delay_steps)
        
        # Process outputs
        self.sensor_color_reading = 0.0  # Raw value from TCS3200 (representing color intensity)
        self.clogging_factor = 1.0       # Valve clogging (1.0 = normal, 0.4 = clogged)
        self.milk_disturbance_active = False
        
        # Data logger for plotting
        self.history = {
            "time": [],
            "milk_flow": [],
            "colorant_flow": [],
            "colorant_flow_sp": [],
            "valve_position": [],
            "valve_output": [],
            "target_ratio": [],
            "actual_ratio": [],
            "sensor_color": [],
            "validation_ok": []
        }
        
    def reset(self):
        self.time = 0.0
        self.milk_flow = self.nominal_milk_flow
        self.valve_position = 0.0
        self.valve_output = 0.0
        self.colorant_flow = 0.0
        self.pid_flow.reset()
        self.ratio_history = deque([0.0] * self.delay_steps, maxlen=self.delay_steps)
        self.sensor_color_reading = 0.0
        self.clogging_factor = 1.0
        self.milk_disturbance_active = False
        
        for key in self.history:
            self.history[key].clear()

    def set_pid_params(self, kp, ki, kd):
        self.pid_flow.kp = kp
        self.pid_flow.ki = ki
        self.pid_flow.kd = kd

    def step(self, dt=0.1, auto_mode=True, manual_valve_input=0.0):
        # 1. Milk flow (wild flow) with random noise and disturbance
        base_milk = self.nominal_milk_flow
        if self.milk_disturbance_active:
            # Simulate a surge/drop in milk flow
            base_milk = 75.0 if (int(self.time / 10) % 2 == 0) else 35.0
        
        noise = random.uniform(-0.5, 0.5)
        self.milk_flow = max(10.0, base_milk + noise)
        
        # 2. Ratio Calculation & Setpoint
        self.colorant_flow_sp = self.target_ratio * self.milk_flow
        
        # 3. PID Control Logic
        if auto_mode:
            self.pid_flow.setpoint = self.colorant_flow_sp
            self.valve_output = self.pid_flow.compute(self.colorant_flow, dt)
        else:
            self.valve_output = manual_valve_input
            
        # 4. Valve Actuator Dynamics (First-Order Lag)
        d_valv = (self.valve_output - self.valve_position) / self.valve_tau
        self.valve_position += d_valv * dt
        self.valve_position = max(0.0, min(100.0, self.valve_position))
        
        # 5. Process flow rate based on valve position and clogging disturbance
        # Linear characteristic
        self.colorant_flow = (self.valve_position / 100.0) * self.max_colorant_flow * self.clogging_factor
        # Add small measurement noise
        self.colorant_flow = max(0.0, self.colorant_flow + random.uniform(-0.05, 0.05))
        
        # 6. Mixing & Sensor Transport Delay
        # Ratio at mixing point
        if self.milk_flow + self.colorant_flow > 0.1:
            mixing_ratio = self.colorant_flow / (self.milk_flow + self.colorant_flow)
        else:
            mixing_ratio = 0.0
            
        self.ratio_history.append(mixing_ratio)
        
        # Read ratio from TCS3200 sensor after transport delay
        delayed_ratio = self.ratio_history[0]
        
        # Map ratio to TCS3200 color frequency reading (e.g. 0 to 255 scaling)
        # Assuming maximum target ratio of 0.25 maps to 255 color intensity
        self.sensor_color_reading = min(255.0, delayed_ratio * 1000.0)
        
        # 7. Validation Logic (±10% tolerance from set ratio color)
        target_color = (self.target_ratio / (1.0 + self.target_ratio)) * 1000.0
        tolerance = target_color * 0.10
        validation_ok = 1.0 if abs(self.sensor_color_reading - target_color) <= max(5.0, tolerance) else 0.0
        
        # Log data
        self.history["time"].append(self.time)
        self.history["milk_flow"].append(self.milk_flow)
        self.history["colorant_flow"].append(self.colorant_flow)
        self.history["colorant_flow_sp"].append(self.colorant_flow_sp)
        self.history["valve_position"].append(self.valve_position)
        self.history["valve_output"].append(self.valve_output)
        self.history["target_ratio"].append(self.target_ratio)
        self.history["actual_ratio"].append(delayed_ratio)
        self.history["sensor_color"].append(self.sensor_color_reading)
        self.history["validation_ok"].append(validation_ok)
        
        # Increment time
        self.time += dt

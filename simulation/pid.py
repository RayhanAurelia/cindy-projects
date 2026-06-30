class PID:
    def __init__(self, kp, ki, kd, setpoint=0.0, output_limits=(0.0, 100.0)):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.output_limits = output_limits
        
        self.integral = 0.0
        self.last_error = 0.0
        
    def reset(self):
        self.integral = 0.0
        self.last_error = 0.0
        
    def compute(self, pv, dt=0.1):
        if dt <= 0.0:
            dt = 0.1
            
        error = self.setpoint - pv
        
        # Proportional
        p_term = self.kp * error
        
        # Integral with anti-windup clamping
        self.integral += error * dt
        i_term = self.ki * self.integral
        
        # Derivative
        d_term = self.kd * (error - self.last_error) / dt
        
        # Calculate raw output
        output = p_term + i_term + d_term
        
        # Clamp output to limits and prevent integral windup
        min_limit, max_limit = self.output_limits
        if output > max_limit:
            output = max_limit
            # Clamping integral to prevent windup
            self.integral -= error * dt 
        elif output < min_limit:
            output = min_limit
            # Clamping integral to prevent windup
            self.integral -= error * dt
            
        self.last_error = error
        return output

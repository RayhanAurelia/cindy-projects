class PID:
    def __init__(self, kp, ki, kd, setpoint=0.0, output_limits=(0.0, 100.0)):
        self.kp = kp
        self.ki = ki
        self.kd = kd
        self.setpoint = setpoint
        self.output_limits = output_limits
        
        self.integral = 0.0
        self.last_error = 0.0
        self.last_pv = None      # Previous measurement for derivative-on-measurement

    def reset(self):
        self.integral = 0.0
        self.last_error = 0.0
        self.last_pv = None

    def compute(self, pv, dt=0.1):
        if dt <= 0.0:
            dt = 0.1

        error = self.setpoint - pv

        # Proportional
        p_term = self.kp * error

        # Integral with anti-windup clamping
        self.integral += error * dt
        i_term = self.ki * self.integral

        # Derivative on Measurement (PV), bukan pada error.
        # Mencegah "derivative kick" saat setpoint berubah (mis. setpoint rasio yang
        # ikut fluktuasi/noise laju susu) dan meredam penguatan noise pengukuran.
        if self.last_pv is None:
            self.last_pv = pv  # Inisialisasi agar tidak ada lonjakan derivatif di langkah pertama
        d_term = -self.kd * (pv - self.last_pv) / dt

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
        self.last_pv = pv  # Simpan pengukuran untuk perhitungan derivatif berikutnya
        return output

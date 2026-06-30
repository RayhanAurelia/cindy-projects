def get_ratio_control_scl():
    return """FUNCTION_BLOCK FB_RatioControl
TITLE = 'Ratio Control for Milk and Color Mixing'
VERSION : '1.0'
AUTHOR  : 'Cindy dan Terran'

VAR_INPUT
    PV_WildFlow   : REAL;  // Laju aliran susu (Wild Flow) [L/min]
    Ratio_SP      : REAL;  // Setpoint Rasio (Pewarna / Susu)
    PV_SlaveFlow  : REAL;  // Laju aliran pewarna (Slave Flow) [L/min]
    ManualMode    : BOOL;  // TRUE: Manual, FALSE: Auto
    ManualVal     : REAL;  // Nilai bukaan katup manual (0-100%)
    
    // Parameter PID (Slave Flow Controller)
    Kp            : REAL := 2.5;
    Ki            : REAL := 1.5;
    Kd            : REAL := 0.1;
    Cycle         : REAL := 0.1; // Sample time dalam detik (100ms)
END_VAR

VAR_OUTPUT
    SlaveFlow_SP  : REAL;  // Setpoint Laju Aliran Pewarna [L/min]
    Valve_Out     : REAL;  // Output ke Katup Kendali (0-100%)
    Validation_OK : BOOL;  // Hasil Validasi Warna (TCS3200)
END_VAR

VAR
    // Variabel internal PID
    Error_Prev    : REAL := 0.0;
    Integral_Sum  : REAL := 0.0;
    
    // Variabel simulasi TCS3200 (untuk verifikasi)
    Sensor_Color  : REAL;
    Target_Color  : REAL;
END_VAR

BEGIN
    // 1. Menghitung Setpoint Aliran Slave (Pewarna) berdasarkan Aliran Wild (Susu)
    SlaveFlow_SP := PV_WildFlow * Ratio_SP;
    
    // 2. Logika Kontrol PID (Slave Flow Control Loop)
    IF ManualMode THEN
        Valve_Out := ManualVal;
        // Reset akumulator integral saat mode manual
        Integral_Sum := 0.0;
    ELSE
        // Hitung Error
        VAR
            Error : REAL;
            P_Term : REAL;
            I_Term : REAL;
            D_Term : REAL;
            PID_Out : REAL;
        END_VAR;
        
        Error := SlaveFlow_SP - PV_SlaveFlow;
        
        // Proportional Term
        P_Term := Kp * Error;
        
        // Integral Term dengan Anti-Windup sederhana
        Integral_Sum := Integral_Sum + (Error * Cycle);
        I_Term := Ki * Integral_Sum;
        
        // Derivative Term
        D_Term := Kd * (Error - Error_Prev) / Cycle;
        
        // Total output controller
        PID_Out := P_Term + I_Term + D_Term;
        
        // Batasi output katup kendali ke 0 - 100%
        IF PID_Out > 100.0 THEN
            Valve_Out := 100.0;
            // Anti-Windup: Clamping integral
            Integral_Sum := Integral_Sum - (Error * Cycle);
        ELSIF PID_Out < 0.0 THEN
            Valve_Out := 0.0;
            Integral_Sum := Integral_Sum - (Error * Cycle);
        ELSE
            Valve_Out := PID_Out;
        END_IF;
        
        Error_Prev := Error;
    END_IF;
    
    // 3. Validasi Konsentrasi Warna (Logika simulasi sensor TCS3200)
    // Dalam implementasi nyata, pembacaan sensor warna diperoleh dari modul input terpisah.
    // Asumsi: Sensor TCS3200 menghasilkan sinyal warna sebanding dengan rasio volume.
    IF (PV_WildFlow + PV_SlaveFlow) > 0.1 THEN
        Sensor_Color := (PV_SlaveFlow / (PV_WildFlow + PV_SlaveFlow)) * 1000.0;
    ELSE
        Sensor_Color := 0.0;
    END_IF;
    
    Target_Color := (Ratio_SP / (1.0 + Ratio_SP)) * 1000.0;
    
    // Validasi dengan toleransi 10%
    IF ABS(Sensor_Color - Target_Color) <= (Target_Color * 0.10) THEN
        Validation_OK := TRUE;
    ELSE
        Validation_OK := FALSE;
    END_IF;
    
END_FUNCTION_BLOCK
"""

def get_cascade_control_scl():
    return """FUNCTION_BLOCK FB_CascadeControl
TITLE = 'Cascade Control for Milk Coloring Process'
VERSION : '1.0'
AUTHOR  : 'Cindy dan Terran'

VAR_INPUT
    PV_Color      : REAL;  // Nilai pembacaan sensor warna TCS3200 (0-255)
    Color_SP      : REAL;  // Target warna susu hasil akhir (0-255)
    PV_Flow       : REAL;  // Laju aliran pewarna (Inner Process Variable) [L/min]
    
    ManualMode    : BOOL;  // TRUE: Manual, FALSE: Auto
    ManualVal     : REAL;  // Nilai bukaan katup manual (0-100%)
    
    // Parameter PID Loop Luar (Primary - Color Controller)
    Kp_Outer      : REAL := 0.15;
    Ki_Outer      : REAL := 0.03;
    Kd_Outer      : REAL := 0.01;
    
    // Parameter PID Loop Dalam (Secondary - Flow Controller)
    Kp_Inner      : REAL := 2.5;
    Ki_Inner      : REAL := 1.5;
    Kd_Inner      : REAL := 0.1;
    
    Cycle         : REAL := 0.1; // Sample time (100ms)
END_VAR

VAR_OUTPUT
    Flow_SP       : REAL;  // Setpoint Laju Aliran Pewarna hasil Outer PID [L/min]
    Valve_Out     : REAL;  // Output ke Katup Kendali (0-100%)
    Validation_OK : BOOL;  // Hasil Validasi Warna (TCS3200)
END_VAR

VAR
    // Variabel internal Outer PID (Warna)
    Err_Outer_Prev : REAL := 0.0;
    Int_Outer_Sum  : REAL := 0.0;
    
    // Variabel internal Inner PID (Aliran)
    Err_Inner_Prev : REAL := 0.0;
    Int_Inner_Sum  : REAL := 0.0;
END_VAR

BEGIN
    // 1. Loop Luar (Outer/Primary PID): Mengontrol Warna
    IF ManualMode THEN
        // Setpoint aliran diestimasi secara linear dalam mode manual
        Flow_SP := (Color_SP / 255.0) * 10.0; // Estimasi kasar
        Int_Outer_Sum := 0.0;
    ELSE
        VAR
            Err_Out  : REAL;
            P_Out    : REAL;
            I_Out    : REAL;
            D_Out    : REAL;
            Out_SP   : REAL;
        END_VAR;
        
        Err_Out := Color_SP - PV_Color;
        P_Out   := Kp_Outer * Err_Out;
        
        Int_Outer_Sum := Int_Outer_Sum + (Err_Out * Cycle);
        I_Out   := Ki_Outer * Int_Outer_Sum;
        
        D_Out   := Kd_Outer * (Err_Out - Err_Outer_Prev) / Cycle;
        
        Out_SP  := P_Out + I_Out + D_Out;
        
        // Batasi setpoint aliran pewarna ke rentang fisik katup (0 - 12 L/min)
        IF Out_SP > 12.0 THEN
            Flow_SP := 12.0;
            Int_Outer_Sum := Int_Outer_Sum - (Err_Out * Cycle); // Anti-windup
        ELSIF Out_SP < 0.0 THEN
            Flow_SP := 0.0;
            Int_Outer_Sum := Int_Outer_Sum - (Err_Out * Cycle); // Anti-windup
        ELSE
            Flow_SP := Out_SP;
        END_IF;
        
        Err_Outer_Prev := Err_Out;
    END_IF;

    // 2. Loop Dalam (Inner/Secondary PID): Mengontrol Aliran Pewarna
    IF ManualMode THEN
        Valve_Out := ManualVal;
        Int_Inner_Sum := 0.0;
    ELSE
        VAR
            Err_In   : REAL;
            P_In     : REAL;
            I_In     : REAL;
            D_In     : REAL;
            PID_Out  : REAL;
        END_VAR;
        
        Err_In := Flow_SP - PV_Flow;
        P_In   := Kp_Inner * Err_In;
        
        Int_Inner_Sum := Int_Inner_Sum + (Err_In * Cycle);
        I_In   := Ki_Inner * Int_Inner_Sum;
        
        D_In   := Kd_Inner * (Err_In - Err_Inner_Prev) / Cycle;
        
        PID_Out := P_In + I_In + D_In;
        
        // Batasi output katup kendali ke 0 - 100%
        IF PID_Out > 100.0 THEN
            Valve_Out := 100.0;
            Int_Inner_Sum := Int_Inner_Sum - (Err_In * Cycle); // Anti-windup
        ELSIF PID_Out < 0.0 THEN
            Valve_Out := 0.0;
            Int_Inner_Sum := Int_Inner_Sum - (Err_In * Cycle); // Anti-windup
        ELSE
            Valve_Out := PID_Out;
        END_IF;
        
        Err_Inner_Prev := Err_In;
    END_IF;

    // 3. Validasi Keberhasilan Kontrol Warna (Toleransi ketat ±5% pada Cascade)
    IF ABS(PV_Color - Color_SP) <= (Color_SP * 0.05) THEN
        Validation_OK := TRUE;
    ELSE
        Validation_OK := FALSE;
    END_IF;

END_FUNCTION_BLOCK
"""

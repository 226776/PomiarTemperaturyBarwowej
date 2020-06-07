def serial_ports():
    """ Lists serial port names

        :raises EnvironmentError:
            On unsupported or unknown platforms
        :returns:
            A list of the serial ports available on the system
    """
    if sys.platform.startswith('win'):
        ports = ['COM%s' % (i + 1) for i in range(256)]
    elif sys.platform.startswith('linux') or sys.platform.startswith('cygwin'):
        # this excludes your current terminal "/dev/tty"
        ports = glob.glob('/dev/tty[A-Za-z]*')
    elif sys.platform.startswith('darwin'):
        ports = glob.glob('/dev/tty.*')
    else:
        raise EnvironmentError('Unsupported platform')

    result = []
    for port in ports:
        try:
            s = serial.Serial(port)
            s.close()
            result.append(port)
        except (OSError, serial.SerialException):
            pass
    return result

def parseRGB_data(RGB_string):
    RGB_string = RGB_string.split('\r')
    for line in RGB_string:
        if not line == '':
            if line[0] == 'R':
                R_meas = int(line[1:len(line)])
            if line[0] == 'G':
                G_meas = int(line[1:len(line)])
            if line[0] == 'B':
                B_meas = int(line[1:len(line)])
    if R_meas and G_meas and B_meas:
        RGB_meas = [R_meas, G_meas, B_meas]
        return RGB_meas
    
def saveMeasurements(RGB_meas_list):
    if isinstance(RGB_meas_list, list):
        RGB_meas = np.asarray(RGB_meas_list)
        np.save(input("Type RGB measurements file name: "), RGB_meas)
    elif isinstance(RGB_meas_list, np.asarray):
        np.save(input("Type RGB measurements file name: "), RGB_meas)
    else:
        print("That's not a list!")
        
def normalize(rgb_t):
    rgb_t_np = np.asarray(rgb_t)
    return rgb_t_np/sum(rgb_t_np)

def invertData(rgb_t):
    rgb_t_np = np.asarray(rgb_t)
    inv_rgb_t = 1/rgb_t_np
    return normalize(inv_rgb_t)

def colorTempEstimation(RGB_meas, wsp):
    RGB_meas = invertData(RGB_meas)
    estym = ((wsp[0]*RGB_meas[0])+(wsp[1]*RGB_meas[1])+(wsp[2]*RGB_meas[2]))
    return round(estym)
    
def measureRGB(iteratoins, port):
    
    print("Wczytywanie modelu...")
    try:
        modelParams = np.load("ModelParams.npy")
    except Exception as e:
        print(e)
    
    # inform that programm has entered this function
    print("Otwieranie portu szeregowego: " + port)

    try:
        s = serial.Serial(port, 9600, timeout=2.5, rtscts=True)
        s.rts = False
        x = s.read()          # read one byte
        str_x = str(x, 'utf-8')
        if str_x == startByte:  # check if it's start bajt
            measurements = []
            
            print("Rozpoczęto pomiar: ")
            if iteratoins == "inf":
                try:
                    while True:
                        RGB_bytes = s.read(300)    # read up to ten bytes (timeout)
                        RGB_string = str(RGB_bytes, 'utf-8')
                        RGB_parsed = parseRGB_data(RGB_string)
                        ColorTemp = colorTempEstimation(RGB_parsed, modelParams)
                        print("Color temperature: ",ColorTemp, " RGB: ", RGB_parsed)
                        measurements.append([ColorTemp, RGB_parsed])
                except KeyboardInterrupt:
                    print("Saving measurements...")
                    saveMeasurements(measurements)
                    
            elif iteratoins == "single":
                RGB_measurements = []
                ColorTemps = []
                for i in range(5):
                    RGB_bytes = s.read(300)    # read up to ten bytes (timeout)
                    RGB_string = str(RGB_bytes, 'utf-8')
                    RGB_parsed = parseRGB_data(RGB_string)
                    RGB_measurements.append(RGB_parsed)
                if RGB_measurements:
                    for i in range(len(RGB_measurements)):
                        ColorTemps.append(colorTempEstimation(RGB_parsed, modelParams))
                    if (max(ColorTemps) - min(ColorTemps)) < 500:
                        colorTemp = sum(ColorTemps)/len(ColorTemps)
                        print("Color temperature: ", colorTemp)
            else:
                print("There is no such measure option!")
        print("Closing port")
        s.close()
    
    except Exception as e:
        print(e)
        s.close()

if __name__ == "__main__":
    import serial
    import sys
    import glob
    import numpy as np
    
    try:
        print("\nChoose serial port: ")
        ports = serial_ports()
        portChoice = ""
        for i in range(len(ports)):
            portChoice += str(i+1)+ ". " + ports[i] + "\n"
        port = ports[int(input(portChoice))-1]
    except Exception as e:
        print(e)
        
    # define start byte
    startByte = 'S';
    
    print("\nChoose measure type: ")
    measureChoice_str = "1. Single measure \n" + "2. Infinite measure"
    choice = input(measureChoice_str)
    if choice == "1":
        measureRGB("single", port)
    elif choice == "2": 
        measureRGB("inf", port)
    else:
        print("Wrong input!")

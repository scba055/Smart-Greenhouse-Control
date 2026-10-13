import serialize
import time

SERIAL_PORT = "/dev/ttyACM0" 
BAUD_RATE = 115200

def open_serial():
	ser = serial.Serial(SERIAL_PORT, BAUD_RATE, timeout=2)
	time.sleep(2) # allow Uno to reset after serial opens
	ser.reset_input_buffer()
	return ser
	
def send_command(ser, command):
	ser.write((command + "/n").encode())
	time.sleep(2.0) # wait for Uno to process and respond
	
	lines = []
	while ser.in_waiting:
		line = ser.readline().decode(errors="ignore").strip()
		if line:
			lines.append(line)
	return lines
	
def print_response(lines):
	if not lines:
		print("No response from Uno")
		return
	for line in lines:
		print(line)

def main():
	try:
		ser = open_serial()
		print(f"Connected to Uno on {SERIAL_PORT}")
		
		while True:
			print("/nCommands:")
			print("	7 = capture pH 7 buffer")
			print("	4 = capture pH 4 buffer")
			print("	c = compute calibration")
			print("	r = read calibrated pH")
			print("	q = quit")
			
			cmd = input("Enter command: ").strip().lower()
			
			if cmd == "q":
				break
			elif cmd in ["7", "4", "c", "r"]:
				response = send_command(ser, cmd)
				print_response(response)
			else:
				print("Invalid command.")
		
		ser.close()
		print("Serial connection closed.")
	
	except serial.SerialException as e:
		print(f"Serial error: {e}")
		print("Check the serial port with: ls /dev/ttyACM* or ls /dev/ttyUSB*")
	except KeyboardInterrupt:
		print("/nExiting program.")

if __name__ == "__main__":
	main()
			

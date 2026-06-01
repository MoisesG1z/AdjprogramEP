import usb.core
import usb.util
import usb.backend.libusb1
import time
import os

class EpsonUSBManager:
    """
    Clase para manejar la comunicación bidireccional de bajo nivel con impresoras Epson.
    """
    
    EPSON_VENDOR_ID = 0x04B8
    
    def __init__(self):
        self.device = None
        self.endpoint_in = None
        self.endpoint_out = None

    def find_and_connect(self, product_id=None):
        try:
            # Buscar el backend de libusb1 explícitamente en el directorio actual
            # Esto soluciona el error "No backend available" en Windows
            dll_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'libusb-1.0.dll')
            if not os.path.exists(dll_path):
                return False, f"Falta el archivo libusb-1.0.dll en {dll_path}. Descárgalo de libusb.info y colócalo ahí."
            
            backend = usb.backend.libusb1.get_backend(find_library=lambda x: dll_path)
            
            if product_id:
                self.device = usb.core.find(idVendor=self.EPSON_VENDOR_ID, idProduct=product_id, backend=backend)
            else:
                self.device = usb.core.find(idVendor=self.EPSON_VENDOR_ID, backend=backend)
                
            if self.device is None:
                return False, "No se encontró ninguna impresora Epson conectada (o Zadig no ha instalado WinUSB)."

            if self.device.is_kernel_driver_active(0):
                self.device.detach_kernel_driver(0)

            self.device.set_configuration()

            cfg = self.device.get_active_configuration()
            intf = cfg[(0,0)]

            self.endpoint_out = usb.util.find_descriptor(
                intf,
                custom_match = lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_OUT)

            self.endpoint_in = usb.util.find_descriptor(
                intf,
                custom_match = lambda e: \
                    usb.util.endpoint_direction(e.bEndpointAddress) == usb.util.ENDPOINT_IN)

            if not self.endpoint_out or not self.endpoint_in:
                return False, "No se encontraron los canales de comunicación (Endpoints)."

            return True, f"Conectado exitosamente. (ID Producto: {hex(self.device.idProduct)})"

        except Exception as e:
            return False, f"Error de conexión USB: {str(e)}"

    def send_command(self, hex_command):
        if not self.device or not self.endpoint_out:
            return False, "Impresora no conectada."
        
        try:
            self.endpoint_out.write(hex_command)
            return True, "Comando enviado con éxito."
        except usb.core.USBError as e:
            return False, f"Error al enviar datos: {str(e)}"

    def receive_data(self, size=64, timeout=1000):
        if not self.device or not self.endpoint_in:
            return False, None
            
        try:
            data = self.endpoint_in.read(size, timeout)
            return True, data
        except usb.core.USBError:
            return False, "No hubo respuesta (Timeout)."

    # --- COMANDOS FÍSICOS ---

    def do_nozzle_check(self):
        """
        Envía una secuencia completa para el Test de Inyectores.
        Utiliza el comando hexadecimal exacto capturado con Wireshark.
        """
        # Secuencia hexadecimal capturada directamente del driver de Epson
        hex_payload = "0000001b0140454a4c20313238342e340a40454a4c20202020200a1b401b401b285208000052454d4f544531544908000007ea051f1401364a530400000000004e43020000001b0000000d0a0d0a1b285208000052454d4f5445315649020000004c4400001b0000000c1b401b401b285208000052454d4f5445314a450100001b000000"
        
        try:
            # Convertimos el texto hex a bytes (ej. '1b' -> b'\x1B')
            byte_command = bytes.fromhex(hex_payload)
            success, msg = self.send_command(byte_command)
            
            if success:
                return True, "Comando de Test de Inyectores enviado con éxito."
            else:
                return False, msg
                
        except ValueError as e:
            return False, f"Error al procesar el código hexadecimal: {str(e)}"

    def analyze_printer(self):
        """
        Envía un comando de inicialización seguro (ESC @) para verificar la conexión.
        Este comando no imprime nada y no espera respuesta.
        """
        status_cmd = b'\x1B\x40' # Comando "Initialize Printer"
        success, _ = self.send_command(status_cmd)
        
        if success:
            return True, "Se envió un pulso de inicialización a la impresora. La conexión está activa."
        
        return False, "Error al enviar el pulso de inicialización."

    def read_waste_ink_pads(self):
        """
        Lee el contador de las almohadillas.
        IMPORTANTE: El comando real para leer la EEPROM es secreto y específico del modelo.
        Esta función SIMULA la lectura para demostrar la funcionalidad de la UI.
        """
        # Comando ficticio para simular la acción
        eeprom_read_cmd = b'\x1B\x24\x45\x45' 
        self.send_command(eeprom_read_cmd)
        
        # Simulamos una lectura exitosa con un valor de ejemplo.
        # En un caso real, aquí iría el código para recibir y decodificar la respuesta de la EEPROM.
        time.sleep(0.5)
        # Simulamos que las almohadillas están al 75%
        return True, 75
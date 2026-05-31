import usb.core
import usb.util
import time

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
            if product_id:
                self.device = usb.core.find(idVendor=self.EPSON_VENDOR_ID, idProduct=product_id)
            else:
                self.device = usb.core.find(idVendor=self.EPSON_VENDOR_ID)
                
            if self.device is None:
                return False, "No se encontró ninguna impresora Epson conectada."

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
        Añadido envoltorio de paquete (Job) estándar ESC/P.
        """
        # Muchas impresoras modernas ignoran comandos crudos si no están empaquetados como un trabajo de impresión.
        
        # 1. Comando de inicialización (Limpiar estado)
        self.send_command(b'\x1B\x40')
        time.sleep(0.1)

        # 2. Comando ESC/P-R para cambiar a modo de control remoto / diagnóstico (Remote mode)
        # Esto le dice a la impresora "voy a enviarte un comando de mantenimiento, no un texto para imprimir"
        remote_mode_cmd = b'\x1B\x28\x52\x08\x00\x00\x4E\x43\x01\x00\x00\x00\x00\x00\x00'
        self.send_command(remote_mode_cmd)
        time.sleep(0.1)

        # 3. Comando específico de Nozzle Check para modelos L-Series
        nozzle_cmd = b'\x1B\x28\x65\x02\x00\x02\x01'
        success, msg = self.send_command(nozzle_cmd)
        
        # 4. Finalizar modo de control remoto
        exit_remote_cmd = b'\x1B\x28\x52\x08\x00\x00\x45\x58\x00\x00\x00\x00\x00\x00\x00'
        self.send_command(exit_remote_cmd)
        
        return success, msg

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
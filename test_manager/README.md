Los Frameworks son estructuras o conjuntos de herramientas, librerias y convenciones usadas para desarrollar software mas eficientemente y consistente. En vez de empezar en bocetos, los framworks proporcionan una fundacion predefinida y estructura que permite a los desarrolladores enfocarse en la logica especifica de las aplicaciones.

En nuestro caso el Framework es el TestManager en donde se define una clase encargada de ejecutar cada test de forma individual especificado por el usuario. Se apoya del wrapper (declaracion y ejecucion de comandos), el logger (registro de mensajes) y de los test cases (que definen procedimientos completos de funcionalidades)

El script debe tomar como parametro el numero serial del ssd y el test que se va a realizar. Basandonos en el numero serial debemos obtener el Path fisico que utilizaran todos los test durante la ejecucion de los comandos nvme.
EL TestManager debera contemplar los siguientes metodos:

* __init__(): Se definen los atributos propios requeridos para el modulo
Numero Serial / testname/ nvme/ physical_path / logger / test (Checar los requerimientos)
* initialize(): se encargara de inicializar el objeto nvme con el physical path basado en el numero serial.
* run(): Este se encargara de invocar el metodo run() del test deseado.
* drive_check(): Se encargara de verificar la salud del ssd proporcionan informacion basica, como el numero serial, modelo, firmware y el estado de la salud. De no poder proveer esa informacion, o si el estado de salud no es saludable, se aborta el resultado y se levanta una excepcion.
* get_device_paht(): Retornara el physical path del ssd seleccionado por el usuario acorde al numero serial proporcionado.

Al crear un objeto del TestManager debemos seguir la siguiente secuencia:
drive_check(discovery=True)
run()
set_final_result()
drive_check(discovery=False)

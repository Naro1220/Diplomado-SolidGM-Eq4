Aqui se definen los Test Cases, estos son una serie de pasos a seguir para evaluar alguna funcionalidad del sistema, en nuestro caso es comprobar el funcionamiento de ciertos comandos.
Para ello, los test cases se apoyan del nvme wrapper (que define los comandos nvme a ejecutar) y el logger (para imprimir y guardar la informacion de dichos comandos)
De forma basica, la estructura de un test case se compone de una clase que guarda en si, 3 funciones (Pueden ser mas):

-Constructor: Los constructores son funciones que se ejecutan automaticamente cuando se crea un objeto de esa clase, se emplea para inicializar el objeto, dando valores iniciales, en python usualmente los constructores se definen como:

def __init__(self, logger, nvme):  (EJEMPLO: En este caso, cada que se crea un objeto se inicializa el logger y nvme)

-Run: Esta es una funcion que guarda la logica de todos los pasos a ejecutar, se crean archivos, se ejecutan los comandos necesarios, se usa el logger para guardar los resultados y se manda a llamar la funciona de validacion para determinar si el test case fue exitoso.

-Validate: Es una funcion que guarda la logica para validar los parametros que determinan si un test case fue exitoso o no. Por ejemplo, para el primer Test case debemos comparar la informacion obtenida del comando nvme id-ctrl con la informacion del archivo id-ctrl-main.json (de los maestros), AQUI VA ESA LOGICA que compara ambos archivos y va evaluando dato por dato si hay o no hay coincidencias (y en ambos casos se imprimen en pantalla y se guardan los mensajes en el archivo creado por el logger)

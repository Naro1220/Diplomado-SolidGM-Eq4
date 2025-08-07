El logger es un componente que facilita el proceso de registrar eventos y mensajes en la ejecucion de un programa. Se define una forma estructurada de mostrar la informacion (errores, advertencias, entre otra informacion relevante). El proposito es contestar preguntas para realizar un monitoreo del sistema.

(Que sucedio? -     [Ejemplo: Se ejecuto un comando nvme] 
Por que sucedio? -  [Ejemplo: Como parte de un test case para realizar pruebas] 
Cuando sucedio? -   [Ejemplo: El dia lunes a las 8 pm]) etc...

En el TestLogger debemos definir una clase con codigo que se encargara de mostrar la informacion de las acciones en consola y ademas, debera crear un archivo que contenga toda la informacion de la ejecucion. 

El nombre del archivo a guardar es el siguiente:
    testname_Timestamp.log
Ejemplo:
    test_read_write_2025-06-16_23-19-11.log

Y el formato para la informacion registrada debera ser el siguiente (tanto para consola como para el archivo):
    timestamp - testname - log level - message
Ejemplo:
    2025-06-18 17:30:00,695 - test_read_write - DEBUG - SN: PHA42142004Y1P2AGN

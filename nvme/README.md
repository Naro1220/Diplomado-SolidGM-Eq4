El Wrapper es un componente que encapsula piezas de codigo, librerias o un sistema, proporcionando una interfaz para facilitar la interaccion o modificar su comportamiento, es un intermediario, abstrayendo la complejidad y en ciertos casos, agregando funcionalidad.

En este caso, se requiere crear un nvme wrapper que almacene los comandos nvme a ejecutar, para ello se debe definir una clase cuyos metodos sean los comandos, y uno que se encarge de ejecutarlos, los comandos nvme a ejecutar no van a ser todos (estos dependen de los test cases). El metodo principal sera:

run_command()

Que se encargara de ejecutar el comando nvme seleccionado y retornara una respuesta a partir de ello.

Los comandos requeridos son:

TEST 1: 
  -nvme id-ctrl
TEST 2: 
  -nvme smart-log (Via admin-pasthru)
  -nvme read
  -nvme write
  -nvme set features
TEST 3: 
  -nvme id-ns (Via admin-pasthru)
  -nvme delete-ns
  -nvme create-ns
  -nvme attach-ns
  -Change the blocksize of the drive (No recuerdo con que comando se podia esto)
  -nvme write (repetido)
  


#**************************************************************************************************************
#<Name>RASA_RECIBIR_ACTIVOS</Name>
#<Summary>
#	Recibe los activos del cliente en fin renting y los coloca en usados o siniestro
#</Summary>
#<Returns> </Returns>
#<Autor> Stalyn Oviedo vargas </Autor>
#<Fecha> 14-09-2017 </Fecha>
#<Remarks> </Remarks>
#***************************************************************************************************************

from psdi.server import MXServer
from java.util import Date
from java.util import Calendar, GregorianCalendar



#definir una funcion para crear consecutivos para los consumos de inventario de fin renting
def generarConsecutivoFinRen():
	autoKeyServSet = mbo.getOwner().getMboSet("$AUTOKEY","AUTOKEY","autokeyname = 'RA_FINRENTING'");
	autoKeyServMbo = autoKeyServSet.moveFirst();
	consecutivo= autoKeyServMbo.getInt("SEED");
	prefijo= autoKeyServMbo.getString("PREFIX");
	consecutivo_finren = prefijo+str(consecutivo);
	autoKeyServMbo.setValue("SEED",consecutivo+1);				
	return consecutivo_finren

if mbo.getOwner().getString("RANUMFINRENTING") is None or mbo.getOwner().getString("RANUMFINRENTING")=='':
	#Obtener el consecutivo
	consecutivo = generarConsecutivoFinRen()

	#Obtener el cliente
	cliente = mbo.getOwner().getString("RACLIENTE")

	#Obtener los activos a recibir
	activosRecibir = mbo.getThisMboSet()
	currActivosRecibir = activosRecibir.moveFirst()

	#Crear un registro de consumo de inventario
	invuseSet = mbo.getMboSet("$invuse","INVUSE")
	invuseMbo = invuseSet.add()

	#Inicializar el destino
	destino = "RENTING USAD"
	#Determinar si es siniestro
	if mbo.getOwner().getString("RAESSINIESTRO")=="S":
		destino = "SINIESTRO"

	#Ingresar los valores de invusenum
	invuseMbo.setValue("INVUSENUM",consecutivo)
	invuseMbo.setValue("SITEID","RTAM",11L)
	invuseMbo.setValue("ORGID","RA")
	#invuseMbo.setValue("STATUS","EAPROB")
	invuseMbo.setValue("USETYPE","TRANSFER")
	invuseMbo.setValue("FROMSTORELOC",cliente)
	invuseMbo.setValue("RAESFINRENTING",1)
	invuselineSet = invuseMbo.getMboSet("INVUSELINE")

	#Crear las lineas con los activos seleccionados
	for i in range(activosRecibir.count()):
		invuselineMbo = invuselineSet.add()
		invuselineMbo.setValue("USETYPE","TRANSFER")
		invuselineMbo.setValue("LINETYPE","ITEM")
		invuselineMbo.setValue("ROTASSETNUM",currActivosRecibir.getString("RAACTIVO"),2L)
		invuselineMbo.setValue("QUANTITY",1)
		invuselineMbo.setValue("ENTERBY",user)
		invuselineMbo.setValue("TOSITEID","RTAM",11L)
		invuselineMbo.setValue("TOSTORELOC",destino)

		currActivosRecibir = activosRecibir.moveNext()

	mbo.getOwner().setValue("WONUM",consecutivo,2L)
	mbo.getOwner().setValue("RANUMFINRENTING",consecutivo,2L)

	#Actualizar consecutivos en al grilla, remover gestores de servicio y asignación de contrato
	currMbo = activosRecibir.moveFirst()
	for j in range(activosRecibir.count()):
		currMbo.setValue("RACODIGOFINRENTING",consecutivo,2L)

		#Desmarcar el asignado del activo en la tabla RA_activoXContrato
		activoXContratoSet = currMbo.getMboSet("$activoXContratoSet","RA_ACTIVOXCONTRATO","RAACTIVO='"+currMbo.getString("RAACTIVO")+"' and RACONTRATOCLIENTE='"+currMbo.getString("RACONTRATO")+"' and RACLIENTE='"+cliente+"' and RAASIGNADO=1")
		activoXContratoMbo = activoXContratoSet.moveFirst()
		
		#Verificación de nulos
		if activoXContratoMbo is not None:
			activoXContratoMbo.setValue("RAASIGNADO",0,2L)
		currMbo = activosRecibir.moveNext()

	fechaEstado = Calendar.getInstance()
	fechaEstado.setTime(MXServer.getMXServer().getDate())
	#Conversión a hora local -5 horas de diferencia
	fechaEstado.add(Calendar.HOUR, -5)

	invuseMbo.changeStatus("APROB",fechaEstado.getTime(),"Fin renting",11L)
else:
	errorgroup='#'
	errorkey='El recibo de activos para este registro ya fué ejecutado'